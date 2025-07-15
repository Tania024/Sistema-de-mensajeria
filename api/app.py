from flask import Flask, request, jsonify
import psycopg2
import redis
import os
import time

app = Flask(__name__)

# 🔧 Configuración Redis
r = redis.Redis(host=os.getenv("REDIS_HOST", "redis"), port=6379, decode_responses=True)

# 🔧 Configuración PostgreSQL con reintento inicial
while True:
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "db"),
            port=os.getenv("DB_PORT", 5432),
            dbname=os.getenv("DB_NAME", "chat"),
            user=os.getenv("DB_USER", "user"),
            password=os.getenv("DB_PASS", "pass"),
            connect_timeout=5  # Timeout de conexión inicial
        )
        print("✅ Conectado a PostgreSQL")
        break
    except psycopg2.OperationalError:
        print("⏳ Esperando a que PostgreSQL esté listo...")
        time.sleep(2)

# Crear tabla historial si no existe
cur = conn.cursor()
cur.execute("""
    CREATE TABLE IF NOT EXISTS historial (
        id SERIAL PRIMARY KEY,
        emisor VARCHAR(50),
        receptor VARCHAR(50),
        mensaje TEXT
    )
""")
conn.commit()
cur.close()

@app.route('/health', methods=['GET'])
def health():
    return "OK", 200

@app.route('/enviar', methods=['POST'])
def enviar_mensaje():
    data = request.get_json()
    emisor = data.get('emisor')
    receptor = data.get('receptor')
    mensaje = data.get('mensaje')

    if not emisor or not receptor or not mensaje:
        return jsonify({'error': 'Datos incompletos'}), 400

    #  Reintentos para Redis
    for intento in range(3):
        try:
            r.rpush(f"mensajes_{receptor}", f"{emisor}: {mensaje}")
            break
        except redis.exceptions.RedisError as e:
            print(f"⚠️ Error en Redis (intento {intento+1}): {e}")
            time.sleep(1)
    else:
        return jsonify({'error': 'No se pudo guardar el mensaje en Redis'}), 500

    # Reintentos para PostgreSQL
    for intento in range(3):
        try:
            cur = conn.cursor()
            cur.execute("INSERT INTO historial (emisor, receptor, mensaje) VALUES (%s, %s, %s)", (emisor, receptor, mensaje))
            conn.commit()
            cur.close()
            break
        except Exception as e:
            print(f"⚠️ Error en PostgreSQL (intento {intento+1}): {e}")
            time.sleep(1)
    else:
        return jsonify({'error': 'No se pudo guardar el mensaje en la base de datos'}), 500

    return jsonify({'estado': 'mensaje enviado'})

@app.route('/recibir/<usuario>', methods=['GET'])
def recibir_mensaje(usuario):
    mensaje = None
    for intento in range(3):
        try:
            mensaje = r.lpop(f"mensajes_{usuario}")
            break
        except redis.exceptions.RedisError as e:
            print(f"⚠️ Error en Redis (intento {intento+1}): {e}")
            time.sleep(1)

    if mensaje:
        return jsonify({'mensaje': mensaje})
    else:
        return jsonify({'mensaje': 'No hay mensajes'})

@app.route('/historial', methods=['GET'])
def ver_historial():
    try:
        cur = conn.cursor()
        cur.execute("SELECT emisor, receptor, mensaje FROM historial")
        rows = cur.fetchall()
        cur.close()

        historial = [{'emisor': row[0], 'receptor': row[1], 'mensaje': row[2]} for row in rows]
        return jsonify(historial)
    except Exception as e:
        print(f"⚠️ Error al consultar historial: {e}")
        return jsonify({'error': 'No se pudo obtener el historial'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
