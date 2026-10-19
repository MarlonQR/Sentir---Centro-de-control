# SENTIR · Módulo Necesidades + Recursos

Mismo patrón que `coordinacion-emergencia` (Emergencias + Ubicación), con otras dos capacidades de SENTIR.

```
web/ (HTML+CSS+JS)  ──REST──►  api-necesidades (:8000) ──REST (solo lectura)──►  api-recursos (:8001)
                                       │                                                  │
                                       └────────────── PostgreSQL: sentir_modulo ─────────┘
```

| Servicio | Capacidades | Endpoints |
|---|---|---|
| **Necesidades** (consumidor) | Registrar necesidad, Consultar necesidades, Recomendar atención | `POST/GET /necesidades`, `GET /necesidades/{id}/disponibilidad` |
| **Recursos** (proveedor) | Registrar recurso, Consultar recurso, Consultar disponibilidad | `POST/GET /recursos`, `GET /recursos/disponibilidad/{tipo}` |

**Contrato Necesidades → Recursos:** envía el *tipo* de recurso; recibe cantidad disponible y estado.
Regla: **solo lectura**. Necesidades nunca descuenta ni reserva inventario.

## Ejecutar en local

```bash
# 1. Base de datos
psql -U postgres -c "CREATE DATABASE sentir_modulo;"
psql -U postgres -d sentir_modulo -f db/schema.sql

# 2. Variables de entorno (opcionales, estos son los valores por defecto)
export DB_HOST=localhost DB_NAME=sentir_modulo DB_USER=postgres DB_PASSWORD=tu_clave DB_PORT=5432

# 3. API de Recursos (terminal 1)
cd api-recursos && pip install -r requirements.txt
uvicorn main:app --port 8001

# 4. API de Necesidades (terminal 2)
cd api-necesidades && pip install -r requirements.txt
API_RECURSOS_URL=http://127.0.0.1:8001 uvicorn main:app --port 8000

# 5. Frontend (terminal 3)
cd web && python -m http.server 5500      # abrir http://localhost:5500
```

Documentación interactiva automática: http://127.0.0.1:8000/docs y http://127.0.0.1:8001/docs

## Despliegue
Igual que el repo de referencia: cada API tiene `api/index.py` (`from main import app`) para Vercel.
Allí `DB_HOST` no puede ser `localhost`: usa una base PostgreSQL en la nube (Neon, Supabase, etc.),
define las variables `DB_*` y `API_RECURSOS_URL` en el panel, y cambia las URL en `web/js/app.js`.
