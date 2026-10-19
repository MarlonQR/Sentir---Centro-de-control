from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from con_db import obtener_conexion

app = FastAPI(
    title="API de Recursos",
    description="Servicio dueño del catálogo de recursos y su disponibilidad",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # en producción: poner solo el dominio del frontend
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class Recurso(BaseModel):
    tipo: str = Field(min_length=1, max_length=50)
    nombre: str = Field(min_length=1, max_length=100)
    cantidad_disponible: int = Field(ge=0)


@app.get("/")
def inicio():
    return {"mensaje": "API de Recursos funcionando"}


@app.get("/recursos")
def consultar_recursos():
    """Capacidad: Consultar recurso."""
    conexion = cursor = None
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute(
            """
            SELECT id_recurso, tipo, nombre, cantidad_disponible, fecha_actualizacion
            FROM recursos
            ORDER BY tipo, nombre;
            """
        )
        return [
            {
                "id_recurso": f[0],
                "tipo": f[1],
                "nombre": f[2],
                "cantidad_disponible": f[3],
                "fecha_actualizacion": f[4],
            }
            for f in cursor.fetchall()
        ]
    except Exception:
        raise HTTPException(status_code=500, detail="Error al consultar los recursos")
    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()


@app.post("/recursos")
def registrar_recurso(datos: Recurso):
    """Capacidad: Registrar recurso."""
    conexion = cursor = None
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute(
            """
            INSERT INTO recursos (tipo, nombre, cantidad_disponible)
            VALUES (%s, %s, %s)
            RETURNING id_recurso, fecha_actualizacion;
            """,
            (datos.tipo.lower(), datos.nombre, datos.cantidad_disponible),
        )
        fila = cursor.fetchone()
        conexion.commit()
        return {
            "mensaje": "Recurso registrado correctamente",
            "id_recurso": fila[0],
            "tipo": datos.tipo.lower(),
            "nombre": datos.nombre,
            "cantidad_disponible": datos.cantidad_disponible,
            "fecha_actualizacion": fila[1],
        }
    except Exception:
        if conexion:
            conexion.rollback()
        raise HTTPException(status_code=500, detail="Error al registrar el recurso")
    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()


@app.get("/recursos/disponibilidad/{tipo}")
def consultar_disponibilidad(tipo: str):
    """
    Contrato con Necesidades (solo lectura):
    recibe un tipo de recurso y devuelve la cantidad total disponible.
    """
    conexion = cursor = None
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute(
            """
            SELECT COALESCE(SUM(cantidad_disponible), 0), COUNT(*)
            FROM recursos
            WHERE LOWER(tipo) = LOWER(%s);
            """,
            (tipo,),
        )
        total, lotes = cursor.fetchone()
        if lotes == 0:
            raise HTTPException(status_code=404, detail="No existe ese tipo de recurso")
        return {
            "tipo": tipo.lower(),
            "cantidad_disponible": int(total),
            "estado": "disponible" if total > 0 else "agotado",
        }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Error al consultar la disponibilidad")
    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()
