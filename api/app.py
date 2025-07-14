from flask import Flask, request, jsonify
import redis
import psycopg2
import os

app = Flask(__name__)

# 🔧 Configuración Redis
r = redis.Redis(host=os.getenv("REDIS_HOST", "redis"), port=6379)

# 🔧 Configuración PostgreSQL
conn = psycopg2.connect(
    host=os.getenv("DB_HOST", "db"),
    port=os.getenv("DB_PORT", 5432),
    dbname=os.getenv("DB_NAME", "chat"),
    user=os.getenv("DB_USER", "user"),
    password=os.getenv("DB_PASS", "pass")
)

# 🗃️ Crear tabla mensajes si no existe
with conn.cursor() as cur:
    cur.execute("""
        CREATE TABLE IF NOT EXISTS mensajes (
            id SERIAL PRIMARY KEY,
            usuario TEXT NOT NULL,
            mensaje TEXT NOT NULL,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

# ✅ Prueba de salud
@app.route('/health')
def health():
    return 'OK', 200

# 📩 Enviar mensaje (guarda en Redis y PostgreSQL)
@app.route('/enviar', methods=['POST'])
def enviar():
    data = request.get_json()
    usuario = data.get('usuario')
    mensaje = data.get('mensaje')

    if not usuario or not mensaje:
        return jsonify({"error": "Faltan campos: usuario y mensaje"}), 400

    # Redis (cola de mensajes)
    r.rpush("mensajes", f"{usuario}: {mensaje}")

    # PostgreSQL (registro permanente)
    with conn.cursor() as cur:
        cur.execute("INSERT INTO mensajes (usuario, mensaje) VALUES (%s, %s)", (usuario, mensaje))
        conn.commit()

    return jsonify({"estado": "mensaje enviado"}), 200

# 📥 Recibir mensaje desde Redis (se elimina al leer)
@app.route('/recibir', methods=['GET'])
def recibir():
    mensaje = r.lpop("mensajes")
    if mensaje:
        return jsonify({"mensaje": mensaje.decode()}), 200
    return jsonify({"mensaje": "No hay mensajes"}), 200

# 📜 Historial completo desde PostgreSQL
@app.route('/historial', methods=['GET'])
def historial():
    with conn.cursor() as cur:
        cur.execute("SELECT usuario, mensaje, fecha FROM mensajes ORDER BY fecha DESC")
        resultados = cur.fetchall()
    mensajes = [
        {"usuario": u, "mensaje": m, "fecha": str(f)}
        for u, m, f in resultados
    ]
    return jsonify(mensajes), 200

# ▶️ Iniciar servidor Flask
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
