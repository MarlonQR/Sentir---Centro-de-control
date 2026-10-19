import os
from typing import Literal

import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from con_db import obtener_conexion

API_RECURSOS_URL = os.getenv("API_RECURSOS_URL", "http://127.0.0.1:8001").rstrip("/")

app = FastAPI(
    title="API de Necesidades",
    description="Servicio que gestiona qué necesitan las personas. Solo CONSULTA recursos.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # en producción: poner solo el dominio del frontend
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class Necesidad(BaseModel):
    id_persona: int = Field(gt=0)
    tipo_recurso: str = Field(min_length=1, max_length=50)
    cantidad: int = Field(gt=0)
    prioridad: Literal["alta", "media", "baja"] = "media"


@app.get("/")
def inicio():
    return {"mensaje": "API de Necesidades funcionando"}


@app.get("/necesidades")
def consultar_necesidades():
    """Capacidad: Consultar necesidades."""
    conexion = cursor = None
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute(
            """
            SELECT id_necesidad, id_persona, tipo_recurso, cantidad,
                   prioridad, estado, fecha_reporte
            FROM necesidades
            ORDER BY fecha_reporte DESC;
            """
        )
        return [
            {
                "id_necesidad": f[0],
                "id_persona": f[1],
                "tipo_recurso": f[2],
                "cantidad": f[3],
                "prioridad": f[4],
                "estado": f[5],
                "fecha_reporte": f[6],
            }
            for f in cursor.fetchall()
        ]
    except Exception:
        raise HTTPException(status_code=500, detail="Error al consultar las necesidades")
    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()


@app.post("/necesidades")
def registrar_necesidad(datos: Necesidad):
    """Capacidad: Registrar necesidad."""
    conexion = cursor = None
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute(
            """
            INSERT INTO necesidades (id_persona, tipo_recurso, cantidad, prioridad)
            VALUES (%s, %s, %s, %s)
            RETURNING id_necesidad, estado, fecha_reporte;
            """,
            (datos.id_persona, datos.tipo_recurso.lower(), datos.cantidad, datos.prioridad),
        )
        fila = cursor.fetchone()
        conexion.commit()
        return {
            "mensaje": "Necesidad registrada correctamente",
            "id_necesidad": fila[0],
            "id_persona": datos.id_persona,
            "tipo_recurso": datos.tipo_recurso.lower(),
            "cantidad": datos.cantidad,
            "prioridad": datos.prioridad,
            "estado": fila[1],
            "fecha_reporte": fila[2],
        }
    except Exception:
        if conexion:
            conexion.rollback()
        raise HTTPException(status_code=500, detail="Error al registrar la necesidad")
    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()


@app.get("/necesidades/{id_necesidad}/disponibilidad")
def consultar_disponibilidad_necesidad(id_necesidad: int):
    """
    Capacidad: Recomendar atención (lectura, no transacción).
    1) busca la necesidad en su propia BD
    2) pregunta a la API de Recursos cuánto hay disponible (HTTP síncrono)
    3) devuelve los datos integrados. NUNCA descuenta ni reserva inventario.
    """
    conexion = cursor = None
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute(
            """
            SELECT id_necesidad, id_persona, tipo_recurso, cantidad, prioridad, estado
            FROM necesidades
            WHERE id_necesidad = %s;
            """,
            (id_necesidad,),
        )
        n = cursor.fetchone()
        if n is None:
            raise HTTPException(status_code=404, detail="Necesidad no encontrada")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Error al consultar la necesidad")
    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()

    try:
        r = requests.get(
            f"{API_RECURSOS_URL}/recursos/disponibilidad/{n[2]}", timeout=10
        )
        if r.status_code == 404:
            raise HTTPException(
                status_code=404, detail="No hay recursos de ese tipo registrados"
            )
        r.raise_for_status()
        disponibilidad = r.json()
    except HTTPException:
        raise
    except requests.RequestException:
        raise HTTPException(
            status_code=502, detail="No fue posible consultar el servicio de Recursos"
        )

    return {
        "necesidad": {
            "id_necesidad": n[0],
            "id_persona": n[1],
            "tipo_recurso": n[2],
            "cantidad": n[3],
            "prioridad": n[4],
            "estado": n[5],
        },
        "disponibilidad": disponibilidad,
        "se_puede_atender": disponibilidad["cantidad_disponible"] >= n[3],
    }
