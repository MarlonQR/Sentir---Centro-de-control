import os
import psycopg2

# La cadena de conexion NUNCA va en el codigo: se lee de una variable de entorno.
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "Falta la variable de entorno DATABASE_URL "
        "(ej. postgresql://usuario:clave@host:puerto/base)"
    )


def obtener_conexion():
    return psycopg2.connect(DATABASE_URL)