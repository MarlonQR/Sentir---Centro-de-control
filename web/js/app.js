"use strict";

// ==================================================
// 1. CONFIGURACIÓN DE LAS API
// ==================================================
// Local: API de Necesidades en :8000 y API de Recursos en :8001.
// Al desplegar, reemplaza por las URL públicas de cada servicio.
const API_NECESIDADES = "http://127.0.0.1:8000";
const API_RECURSOS = "http://127.0.0.1:8001";


// ==================================================
// 2. UTILIDADES
// ==================================================
function mostrarMensaje(texto, tipo = "") {
    const mensaje = document.getElementById("mensaje");
    mensaje.textContent = texto;
    mensaje.className = `mensaje ${tipo}`;
}

function celda(texto) {
    const td = document.createElement("td");
    td.textContent = texto ?? "";
    return td;
}

function filaVacia(columnas, texto) {
    const tr = document.createElement("tr");
    const td = document.createElement("td");
    td.colSpan = columnas;
    td.textContent = texto;
    tr.appendChild(td);
    return tr;
}

function etiqueta(clase, texto) {
    const span = document.createElement("span");
    span.className = clase;
    span.textContent = texto ?? "";
    return span;
}

function formatearFecha(valor) {
    if (!valor) return "";
    const fecha = new Date(valor);
    return Number.isNaN(fecha.getTime()) ? String(valor) : fecha.toLocaleString("es-CO");
}

async function pedirJSON(url, opciones) {
    const respuesta = await fetch(url, opciones);
    if (!respuesta.ok) {
        let detalle = `Error HTTP ${respuesta.status}`;
        try {
            const cuerpo = await respuesta.json();
            if (cuerpo.detail) {
                detalle = typeof cuerpo.detail === "string"
                    ? cuerpo.detail
                    : "Datos inválidos. Revisa el formulario.";
            }
        } catch (_) { /* respuesta sin JSON */ }
        throw new Error(detalle);
    }
    return respuesta.json();
}


// ==================================================
// 3. NECESIDADES  (GET /necesidades, POST /necesidades)
// ==================================================
async function consultarNecesidades() {
    const tabla = document.getElementById("tabla-necesidades");
    try {
        const necesidades = await pedirJSON(`${API_NECESIDADES}/necesidades`);
        tabla.replaceChildren();

        if (necesidades.length === 0) {
            tabla.appendChild(filaVacia(7, "No hay necesidades registradas."));
            return;
        }

        necesidades.forEach(n => {
            const fila = document.createElement("tr");
            fila.appendChild(celda(n.id_necesidad));
            fila.appendChild(celda(n.id_persona));
            fila.appendChild(celda(n.tipo_recurso));
            fila.appendChild(celda(n.cantidad));

            const tdPrioridad = document.createElement("td");
            tdPrioridad.appendChild(etiqueta(`prioridad ${n.prioridad}`, n.prioridad));
            fila.appendChild(tdPrioridad);

            const tdEstado = document.createElement("td");
            tdEstado.appendChild(etiqueta("estado", n.estado));
            fila.appendChild(tdEstado);

            const tdAccion = document.createElement("td");
            const boton = document.createElement("button");
            boton.type = "button";
            boton.textContent = "Ver disponibilidad";
            boton.addEventListener("click", () => consultarDisponibilidad(n.id_necesidad));
            tdAccion.appendChild(boton);
            fila.appendChild(tdAccion);

            tabla.appendChild(fila);
        });
    } catch (error) {
        console.error(error);
        tabla.replaceChildren(filaVacia(7, "No fue posible cargar las necesidades."));
        mostrarMensaje("No se pudo consultar la API de Necesidades.", "error");
    }
}

async function registrarNecesidad(evento) {
    evento.preventDefault();
    const form = evento.target;
    const datos = new FormData(form);

    const cuerpo = {
        id_persona: Number(datos.get("id_persona")),
        tipo_recurso: String(datos.get("tipo_recurso")).trim(),
        cantidad: Number(datos.get("cantidad")),
        prioridad: String(datos.get("prioridad")),
    };

    try {
        const resultado = await pedirJSON(`${API_NECESIDADES}/necesidades`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(cuerpo),
        });
        mostrarMensaje(`${resultado.mensaje} (#${resultado.id_necesidad})`, "exito");
        form.reset();
        consultarNecesidades();
    } catch (error) {
        mostrarMensaje(error.message, "error");
    }
}


// ==================================================
// 4. DISPONIBILIDAD  (Necesidades -> Recursos, solo lectura)
// ==================================================
async function consultarDisponibilidad(idNecesidad) {
    const detalle = document.getElementById("detalle-disponibilidad");
    detalle.textContent = "Consultando disponibilidad...";

    try {
        const datos = await pedirJSON(
            `${API_NECESIDADES}/necesidades/${encodeURIComponent(idNecesidad)}/disponibilidad`
        );
        const n = datos.necesidad;
        const d = datos.disponibilidad;

        detalle.replaceChildren();

        const lineas = [
            ["Necesidad:", `#${n.id_necesidad}`],
            ["Persona:", n.id_persona],
            ["Recurso solicitado:", n.tipo_recurso],
            ["Cantidad solicitada:", n.cantidad],
            ["Disponible en inventario:", d.cantidad_disponible],
            ["Estado del recurso:", d.estado],
        ];

        lineas.forEach(([titulo, valor]) => {
            const linea = document.createElement("div");
            const fuerte = document.createElement("strong");
            fuerte.textContent = `${titulo} `;
            linea.appendChild(fuerte);
            linea.appendChild(document.createTextNode(String(valor ?? "")));
            detalle.appendChild(linea);
        });

        const veredicto = document.createElement("p");
        veredicto.className = datos.se_puede_atender ? "aviso-ok" : "aviso-no";
        veredicto.textContent = datos.se_puede_atender
            ? "Hay inventario suficiente para atender esta necesidad."
            : "El inventario NO alcanza para atender esta necesidad.";
        detalle.appendChild(veredicto);

        const nota = document.createElement("small");
        nota.textContent = "Solo consulta: Necesidades nunca descuenta ni reserva inventario.";
        detalle.appendChild(nota);

    } catch (error) {
        const p = document.createElement("p");
        p.className = "error";
        p.textContent = error.message;
        detalle.replaceChildren(p);
    }
}


// ==================================================
// 5. RECURSOS  (GET /recursos, POST /recursos)
// ==================================================
async function consultarRecursos() {
    const tabla = document.getElementById("tabla-recursos");
    try {
        const recursos = await pedirJSON(`${API_RECURSOS}/recursos`);
        tabla.replaceChildren();

        if (recursos.length === 0) {
            tabla.appendChild(filaVacia(5, "No hay recursos registrados."));
            return;
        }

        recursos.forEach(r => {
            const fila = document.createElement("tr");
            fila.appendChild(celda(r.id_recurso));
            fila.appendChild(celda(r.tipo));
            fila.appendChild(celda(r.nombre));
            fila.appendChild(celda(r.cantidad_disponible));
            fila.appendChild(celda(formatearFecha(r.fecha_actualizacion)));
            tabla.appendChild(fila);
        });
    } catch (error) {
        console.error(error);
        tabla.replaceChildren(filaVacia(5, "No fue posible cargar los recursos."));
        mostrarMensaje("No se pudo consultar la API de Recursos.", "error");
    }
}

async function registrarRecurso(evento) {
    evento.preventDefault();
    const form = evento.target;
    const datos = new FormData(form);

    const cuerpo = {
        tipo: String(datos.get("tipo")).trim(),
        nombre: String(datos.get("nombre")).trim(),
        cantidad_disponible: Number(datos.get("cantidad_disponible")),
    };

    try {
        const resultado = await pedirJSON(`${API_RECURSOS}/recursos`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(cuerpo),
        });
        mostrarMensaje(`${resultado.mensaje} (#${resultado.id_recurso})`, "exito");
        form.reset();
        consultarRecursos();
    } catch (error) {
        mostrarMensaje(error.message, "error");
    }
}


// ==================================================
// 6. INICIALIZAR
// ==================================================
document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("btn-actualizar-necesidades")
        .addEventListener("click", consultarNecesidades);
    document.getElementById("btn-actualizar-recursos")
        .addEventListener("click", consultarRecursos);
    document.getElementById("form-necesidad")
        .addEventListener("submit", registrarNecesidad);
    document.getElementById("form-recurso")
        .addEventListener("submit", registrarRecurso);

    consultarNecesidades();
    consultarRecursos();
});
