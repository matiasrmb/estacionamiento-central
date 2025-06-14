""" import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import bcrypt
from utils.db import get_connection

usuario = "admin"
clave_plana = "admin123"
rol = "administrador"

clave_hash = bcrypt.hashpw(clave_plana.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

conn = get_connection()
cursor = conn.cursor()

query = "INSERT INTO usuarios (usuario, clave_hash, rol) VALUES (%s, %s, %s)"
cursor.execute(query, (usuario, clave_hash, rol))
conn.commit()

cursor.close()
conn.close()

print("Usuario administrador creado correctamente.") """
