import psycopg2
import os

conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASS")
)

def init_db():
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS mensajes (
        id SERIAL PRIMARY KEY,
        usuario TEXT,
        mensaje TEXT,
        fecha TIMESTAMP DEFAULT NOW()
    )
    """)
    conn.commit()
    cur.close()

def insert_message(usuario, mensaje):
    cur = conn.cursor()
    cur.execute("INSERT INTO mensajes (usuario, mensaje) VALUES (%s, %s)", (usuario, mensaje))
    conn.commit()
    cur.close()
