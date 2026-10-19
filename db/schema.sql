-- Base de datos: sentir_modulo
-- Crear:   psql -U postgres -c "CREATE DATABASE sentir_modulo;"
-- Tablas:  psql -U postgres -d sentir_modulo -f db/schema.sql

CREATE TABLE IF NOT EXISTS recursos (
    id_recurso          SERIAL PRIMARY KEY,
    tipo                VARCHAR(50)  NOT NULL,
    nombre              VARCHAR(100) NOT NULL,
    cantidad_disponible INTEGER      NOT NULL CHECK (cantidad_disponible >= 0),
    fecha_actualizacion TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS necesidades (
    id_necesidad  SERIAL PRIMARY KEY,
    id_persona    INTEGER      NOT NULL,
    tipo_recurso  VARCHAR(50)  NOT NULL,
    cantidad      INTEGER      NOT NULL CHECK (cantidad > 0),
    prioridad     VARCHAR(10)  NOT NULL DEFAULT 'media'
                  CHECK (prioridad IN ('alta','media','baja')),
    estado        VARCHAR(20)  NOT NULL DEFAULT 'pendiente',
    fecha_reporte TIMESTAMP    NOT NULL DEFAULT NOW()
);

INSERT INTO recursos (tipo, nombre, cantidad_disponible) VALUES
    ('agua',         'Botellones de agua 20L', 120),
    ('alimentos',    'Kits de alimentos',       45),
    ('medicamentos', 'Botiquines básicos',      10);
