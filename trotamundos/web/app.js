// Cliente web de Trotamundos (Capa 1). Toda la lógica de negocio vive en el backend;
// acá solo se presenta y se envían solicitudes a la API (ADR-0002).
"use strict";

const ICONOS = { vuelo: "✈️", hotel: "🏨", auto: "🚗", tren: "🚆", autobus: "🚌" };
const $ = sel => document.querySelector(sel);
const contenido = () => $("#contenido");
let vistaActual = "viajes";
let tipos = [];

function aviso(texto, error = false) {
  const el = $("#aviso");
  el.textContent = texto;
  el.style.background = error ? "var(--error)" : "";
  el.style.display = "block";
  clearTimeout(aviso.t);
  aviso.t = setTimeout(() => { el.style.display = "none"; }, 4000);
}

async function intentar(fn) {
  try { return await fn(); } catch (e) { aviso(e.message, true); }
}

function abrirDialogo(html, alMontar) {
  $("#dialogo-cuerpo").innerHTML = html;
  $("#dialogo").showModal();
  if (alMontar) alMontar($("#dialogo-cuerpo"));
}
const cerrarDialogo = () => $("#dialogo").close();

// ---------------------------------------------------------------- navegación
const VISTAS = {
  viajes: { t: "nav.viajes", render: () => renderViajes(false) },
  compartidos: { t: "nav.compartidos", render: renderCompartidos },
  historial: { t: "nav.historial", render: () => renderViajes(true) },
  correo: { t: "nav.correo", render: renderCorreo },
  perfil: { t: "nav.perfil", render: renderPerfil },
  analitica: { t: "nav.analitica", render: renderAnalitica, rol: "analista" },
  operaciones: { t: "nav.operaciones", render: renderOperaciones, rol: "operaciones" },
  simulacion: { t: "nav.simulacion", render: renderSimulacion },
};

function dibujarNav() {
  const nav = $("#nav");
  nav.innerHTML = "";
  for (const [clave, v] of Object.entries(VISTAS)) {
    if (v.rol && TM.perfil.rol !== v.rol) continue;
    const b = document.createElement("button");
    b.textContent = TM.t(v.t);
    b.className = clave === vistaActual ? "activo" : "";
    b.onclick = () => ir(clave);
    nav.appendChild(b);
  }
}

async function ir(vista) {
  vistaActual = vista;
  dibujarNav();
  contenido().innerHTML = '<p class="suave">…</p>';
  await intentar(VISTAS[vista].render);
}

// ---------------------------------------------------------------- viajes (US-04, US-05)
function chipEstadoReserva(r) {
  const clase = r.estado === "cancelada" ? "error" : r.estado === "modificada" ? "alerta" : "ok";
  let html = `<span class="chip ${clase}">${TM.t("reserva." + r.estado)}</span>`;
  if (r.sincronizacion === "desactualizada") {
    html += ` <span class="chip alerta" title="El proveedor no responde">⚠ ${TM.t("reserva.desactualizada")}: ${TM.fecha(r.ultima_actualizacion)}</span>`;
  }
  return html;
}

function htmlReserva(r, editable) {
  const det = Object.entries(r.detalles || {}).map(([k, v]) => `${TM.esc(k)}: ${TM.esc(v)}`).join(" · ");
  const lugar = [r.destino.nombre, r.destino.ciudad].filter(Boolean).join(", ");
  return `<div class="reserva">
    <div class="icono">${ICONOS[r.tipo] || "📌"}</div>
    <div class="${r.estado === "cancelada" ? "cancelada" : ""}">
      <strong>${TM.esc(r.titulo)}</strong> ${chipEstadoReserva(r)}<br>
      <span class="suave">${TM.fecha(r.inicio)} → ${TM.fecha(r.fin)} · ${TM.esc(lugar)}</span><br>
      <span class="suave">${TM.esc(r.proveedor)} · ${TM.esc(r.codigo_confirmacion)} · ${TM.t("reserva.fuente." + r.fuente)}${det ? " · " + det : ""}</span>
    </div>
    <div class="acciones fila">${editable ? `
      <button data-editar="${r.id}">${TM.t("reserva.editar")}</button>
      <button class="peligro" data-eliminar="${r.id}">${TM.t("reserva.eliminar")}</button>` : ""}
    </div></div>`;
}

function htmlViaje(v, editable) {
  return `<section class="tarjeta">
    <div class="fila espaciar">
      <div><h3 style="margin:0">${TM.esc(v.nombre)}</h3>
        <span class="suave">${TM.fecha(v.inicio, false)} – ${TM.fecha(v.fin, false)} · ${TM.esc(v.destino)}</span>
        <span class="chip">${TM.t("estado." + v.estado)}</span></div>
      ${editable ? `<div class="fila">
        <button data-renombrar="${v.id}">${TM.t("viaje.renombrar")}</button>
        <button data-compartir="${v.id}">${TM.t("viaje.compartir")}</button>
        <button data-soporte="${v.id}">${TM.t("viaje.soporte")}</button></div>` : ""}
    </div>
    ${v.reservas.map(r => htmlReserva(r, editable)).join("")}
  </section>`;
}

let ultimoPanel = [];

async function renderViajes(historial) {
  if (!tipos.length) tipos = await TM.api("GET", "/tipos-reserva");
  const t0 = performance.now();
  const viajes = await TM.api("GET", "/viajes" + (historial ? "?incluir_archivados=true" : ""));
  const ms = Math.round(performance.now() - t0);
  const lista = historial ? viajes.filter(v => v.estado === "archivado") : viajes;
  ultimoPanel = viajes;
  contenido().innerHTML = `
    <div class="fila espaciar" style="margin-bottom:12px">
      <span class="suave">${lista.length} · ${ms} ms</span>
      ${historial ? "" : `<button class="primario" id="nueva">${TM.t("viajes.nueva")}</button>`}
    </div>
    ${lista.length ? lista.map(v => htmlViaje(v, true)).join("") : `<p class="tarjeta">${TM.t("viajes.vacio")}</p>`}`;
  if (!historial) $("#nueva").onclick = () => formularioReserva();
  conectarAccionesViaje();
}

function conectarAccionesViaje() {
  const buscar = id => ultimoPanel.flatMap(v => v.reservas).find(r => r.id === id);
  contenido().querySelectorAll("[data-editar]").forEach(b => b.onclick = () => formularioReserva(buscar(b.dataset.editar)));
  contenido().querySelectorAll("[data-eliminar]").forEach(b => b.onclick = async () => {
    if (!confirm(TM.t("reserva.confirmar_eliminar"))) return;
    await intentar(async () => { await TM.api("DELETE", "/reservas/" + b.dataset.eliminar); ir(vistaActual); });
  });
  contenido().querySelectorAll("[data-renombrar]").forEach(b => b.onclick = async () => {
    const nombre = prompt(TM.t("viaje.renombrar"));
    if (nombre) await intentar(async () => { await TM.api("PATCH", "/viajes/" + b.dataset.renombrar, { nombre }); ir(vistaActual); });
  });
  contenido().querySelectorAll("[data-compartir]").forEach(b => b.onclick = () => dialogoCompartir(b.dataset.compartir));
  contenido().querySelectorAll("[data-soporte]").forEach(b => b.onclick = () => dialogoSoporte(b.dataset.soporte));
}

function formularioReserva(r) {
  const opciones = tipos.map(t => `<option value="${t.codigo}" ${r && r.tipo === t.codigo ? "selected" : ""}>${t.nombre}</option>`).join("");
  const ahora = new Date().toISOString();
  const numero = r ? (r.detalles.numero_vuelo || r.detalles.numero_tren || "") : "";
  abrirDialogo(`<h3>${r ? TM.t("reserva.editar") : TM.t("viajes.nueva")}</h3>
    <form id="f-reserva"><div class="grilla">
      <div><label>${TM.t("form.tipo")}</label><select name="tipo" ${r ? "disabled" : ""}>${opciones}</select></div>
      <div><label>${TM.t("form.proveedor")}</label><input name="proveedor" required value="${TM.esc(r?.proveedor || "")}" ${r ? "disabled" : ""}></div>
      <div><label>${TM.t("form.codigo")}</label><input name="codigo" required value="${TM.esc(r?.codigo_confirmacion || "")}" ${r ? "disabled" : ""}></div>
      <div><label>${TM.t("form.numero")}</label><input name="numero" value="${TM.esc(numero)}"></div>
    </div>
    <label>${TM.t("form.titulo")}</label><input name="titulo" required value="${TM.esc(r?.titulo || "")}">
    <div class="grilla">
      <div><label>${TM.t("form.inicio")}</label><input type="datetime-local" name="inicio" required value="${TM.aInputLocal(r?.inicio || ahora)}"></div>
      <div><label>${TM.t("form.fin")}</label><input type="datetime-local" name="fin" required value="${TM.aInputLocal(r?.fin || ahora)}"></div>
      <div><label>${TM.t("form.destino")}</label><input name="lugar" required value="${TM.esc(r?.destino.nombre || "")}"></div>
      <div><label>${TM.t("form.ciudad")}</label><input name="ciudad" value="${TM.esc(r?.destino.ciudad || "")}"></div>
      <div><label>${TM.t("form.pais")}</label><input name="pais" maxlength="2" value="${TM.esc(r?.destino.pais || "")}"></div>
    </div>
    <p class="fila"><button class="primario">${TM.t("form.guardar")}</button>
      <button type="button" id="cancelar">${TM.t("form.cancelar")}</button></p></form>`, raiz => {
    raiz.querySelector("#cancelar").onclick = cerrarDialogo;
    raiz.querySelector("#f-reserva").onsubmit = async ev => {
      ev.preventDefault();
      const f = Object.fromEntries(new FormData(ev.target));
      const tipo = r ? r.tipo : f.tipo;
      const detalles = { ...(r?.detalles || {}) };
      if (f.numero) detalles[tipo === "tren" ? "numero_tren" : "numero_vuelo"] = f.numero;
      const cuerpo = {
        titulo: f.titulo, inicio: TM.deInputLocal(f.inicio), fin: TM.deInputLocal(f.fin), detalles,
        destino: { ...(r?.destino || {}), nombre: f.lugar, ciudad: f.ciudad, pais: f.pais },
      };
      await intentar(async () => {
        if (r) await TM.api("PATCH", "/reservas/" + r.id, cuerpo);
        else await TM.api("POST", "/reservas", { ...cuerpo, tipo, proveedor: f.proveedor, codigo_confirmacion: f.codigo });
        cerrarDialogo(); aviso(TM.t("comun.guardado")); ir(vistaActual);
      });
    };
  });
}

// ---------------------------------------------------------------- compartir (QA-S1, QA-I2)
async function dialogoCompartir(viajeId) {
  const pintar = lista => lista.map(c => `<li>${TM.esc(c.email_invitado)} <span class="chip">${c.permiso}</span>
    <button data-quitar="${TM.esc(c.email_invitado)}">✕</button></li>`).join("");
  const lista = await TM.api("GET", `/viajes/${viajeId}/comparticiones`);
  abrirDialogo(`<h3>${TM.t("compartir.titulo")}</h3><p class="suave">${TM.t("compartir.ayuda")}</p>
    <ul id="lista-acl">${pintar(lista)}</ul>
    <form id="f-acl" class="fila"><input name="email" type="email" required placeholder="persona@correo.com" style="flex:1">
      <button class="primario">${TM.t("correo.agregar")}</button></form>
    <p><button id="publicar">${TM.t("compartir.publicar")}</button> <button id="cerrar">${TM.t("comun.cerrar")}</button></p>`, raiz => {
    const conectar = () => raiz.querySelectorAll("[data-quitar]").forEach(b => b.onclick = () => intentar(async () => {
      raiz.querySelector("#lista-acl").innerHTML = pintar(await TM.api("DELETE", `/viajes/${viajeId}/comparticiones/${encodeURIComponent(b.dataset.quitar)}`));
      conectar();
    }));
    conectar();
    raiz.querySelector("#f-acl").onsubmit = ev => {
      ev.preventDefault();
      intentar(async () => {
        raiz.querySelector("#lista-acl").innerHTML = pintar(await TM.api("POST", `/viajes/${viajeId}/comparticiones`, { email: ev.target.email.value }));
        ev.target.reset(); conectar();
      });
    };
    raiz.querySelector("#publicar").onclick = () => intentar(async () => {
      const p = await TM.api("POST", `/viajes/${viajeId}/publicar`, { red: "redsocial" });
      aviso(`${p.publicacion}: ${p.nota}`);
    });
    raiz.querySelector("#cerrar").onclick = cerrarDialogo;
  });
}

// ---------------------------------------------------------------- soporte (US-06)
function dialogoSoporte(viajeId) {
  const viaje = ultimoPanel.find(v => v.id === viajeId);
  const casillas = viaje.reservas.map(r => `<label style="color:inherit"><input type="checkbox" name="r" value="${r.id}" style="width:auto"> ${ICONOS[r.tipo] || ""} ${TM.esc(r.titulo)}</label>`).join("");
  abrirDialogo(`<h3>${TM.t("viaje.soporte")}</h3><form id="f-soporte">
    <label>${TM.t("soporte.motivo")}</label>
    <select name="motivo"><option>cancelacion</option><option>retraso</option><option>cambio</option><option>reembolso</option><option>otro</option></select>
    ${casillas}
    <label>${TM.t("soporte.descripcion")}</label><textarea name="descripcion" required rows="3"></textarea>
    <p class="fila"><button class="primario">${TM.t("soporte.enviar")}</button><button type="button" id="cancelar">${TM.t("form.cancelar")}</button></p></form>`, raiz => {
    raiz.querySelector("#cancelar").onclick = cerrarDialogo;
    raiz.querySelector("#f-soporte").onsubmit = ev => {
      ev.preventDefault();
      const fd = new FormData(ev.target);
      intentar(async () => {
        const res = await TM.api("POST", `/viajes/${viajeId}/soporte`, {
          motivo: fd.get("motivo"), descripcion: fd.get("descripcion"), reservas_afectadas: fd.getAll("r"),
        });
        cerrarDialogo(); aviso(`${TM.t("soporte.enviado")}: ${res.agencia} ${res.caso}`);
      });
    };
  });
}

async function renderCompartidos() {
  const viajes = await TM.api("GET", "/viajes/compartidos");
  contenido().innerHTML = viajes.length ? viajes.map(v => htmlViaje(v, false)).join("") : `<p class="tarjeta">—</p>`;
}

// ---------------------------------------------------------------- correo (US-01, US-02, QA-S2)
async function renderCorreo() {
  const [cuenta, whitelist] = await Promise.all([TM.api("GET", "/correo/cuenta"), TM.api("GET", "/correo/whitelist")]);
  const estado = cuenta.vinculada
    ? `<p><strong>${TM.esc(cuenta.direccion)}</strong> <span class="chip ${cuenta.estado === "activa" ? "ok" : "error"}">${cuenta.estado}</span>
       <span class="chip">${cuenta.alcances.join(", ")}</span></p>
       <p class="suave">${cuenta.ultimo_sondeo ? TM.fecha(cuenta.ultimo_sondeo) : "—"} · ${TM.esc(JSON.stringify(cuenta.correos))}</p>
       <p class="fila"><button class="primario" id="sondear">${TM.t("correo.sondear")}</button>
       <button class="peligro" id="desvincular">${TM.t("correo.desvincular")}</button></p>`
    : `<form id="f-vincular" class="fila"><input name="direccion" type="email" value="ana@gmail.demo" style="flex:1">
       <button class="primario">${TM.t("correo.vincular")}</button></form>`;
  contenido().innerHTML = `<section class="tarjeta"><h3>${TM.t("correo.titulo")}</h3>${estado}</section>
    <section class="tarjeta"><h3>${TM.t("correo.whitelist")}</h3><p class="suave">${TM.t("correo.whitelist_ayuda")}</p>
      <ul>${whitelist.map(w => `<li>${TM.esc(w)} <button data-quitar="${TM.esc(w)}">✕</button></li>`).join("")}</ul>
      <form id="f-wl" class="fila"><input name="remitente" placeholder="aerolinea.com" required style="flex:1">
      <button>${TM.t("correo.agregar")}</button></form></section>`;
  const f = $("#f-vincular");
  if (f) f.onsubmit = ev => { ev.preventDefault(); intentar(async () => { await TM.api("POST", "/correo/vincular", { proveedor: "gmail", direccion: ev.target.direccion.value }); ir("correo"); }); };
  if ($("#sondear")) $("#sondear").onclick = () => intentar(async () => {
    const r = await TM.api("POST", "/correo/sondear");
    aviso(`📥 ${r.encolados} → cola · 🗑 ${r.descartados}`);
    setTimeout(() => ir("correo"), 1500);
  });
  if ($("#desvincular")) $("#desvincular").onclick = () => intentar(async () => { await TM.api("DELETE", "/correo/cuenta"); ir("correo"); });
  $("#f-wl").onsubmit = ev => { ev.preventDefault(); intentar(async () => { await TM.api("POST", "/correo/whitelist", { remitente: ev.target.remitente.value }); ir("correo"); }); };
  contenido().querySelectorAll("[data-quitar]").forEach(b => b.onclick = () => intentar(async () => {
    await TM.api("DELETE", "/correo/whitelist/" + encodeURIComponent(b.dataset.quitar)); ir("correo");
  }));
}

// ---------------------------------------------------------------- perfil (QA-U2)
async function renderPerfil() {
  const [p, agencias] = await Promise.all([TM.api("GET", "/usuarios/yo"), TM.api("GET", "/agencias")]);
  const opt = (valor, lista) => lista.map(([v, n]) => `<option value="${v}" ${v === valor ? "selected" : ""}>${n}</option>`).join("");
  contenido().innerHTML = `<section class="tarjeta"><h3>${TM.esc(p.nombre)}</h3><form id="f-perfil" class="grilla">
    <div><label>${TM.t("perfil.idioma")}</label><select name="idioma">${opt(p.idioma, [["es", "Español"], ["en", "English"], ["pt", "Português"]])}</select></div>
    <div><label>${TM.t("perfil.zona")}</label><select name="zona_horaria">${opt(p.zona_horaria, [
      ["America/Argentina/Buenos_Aires", "Buenos Aires"], ["Europe/Madrid", "Madrid"], ["America/Sao_Paulo", "São Paulo"],
      ["America/New_York", "New York"], ["Asia/Tokyo", "Tokyo"], ["UTC", "UTC"]])}</select></div>
    <div><label>${TM.t("perfil.moneda")}</label><select name="moneda">${opt(p.moneda, [["ARS", "ARS"], ["USD", "USD"], ["EUR", "EUR"], ["BRL", "BRL"]])}</select></div>
    <div><label>${TM.t("perfil.agencia")}</label><select name="agencia_preferida"><option value="">—</option>${opt(p.agencia_preferida, agencias.map(a => [a.codigo, a.nombre]))}</select></div>
    <p><button class="primario">${TM.t("form.guardar")}</button></p></form>
    <p class="suave">${new Intl.NumberFormat(p.idioma, { style: "currency", currency: p.moneda }).format(1234.5)} ·
      ${TM.fecha(new Date().toISOString())}</p></section>`;
  $("#f-perfil").onsubmit = ev => {
    ev.preventDefault();
    const datos = Object.fromEntries(new FormData(ev.target));
    if (!datos.agencia_preferida) delete datos.agencia_preferida;
    intentar(async () => {
      TM.perfil = await TM.api("PATCH", "/usuarios/yo", datos);
      localStorage.setItem("tm_perfil", JSON.stringify(TM.perfil));
      await TM.cargarIdioma(TM.perfil.idioma);
      aviso(TM.t("comun.guardado")); ir("perfil");
    });
  };
}

// ---------------------------------------------------------------- analítica (US-07)
function tabla(filas) {
  if (!filas.length) return "<p class='suave'>—</p>";
  const cols = Object.keys(filas[0]);
  return `<table><tr>${cols.map(c => `<th>${c}</th>`).join("")}</tr>${filas.map(f => `<tr>${cols.map(c => `<td>${TM.esc(f[c])}</td>`).join("")}</tr>`).join("")}</table>`;
}

async function renderAnalitica() {
  const [d, c, e] = await Promise.all(["destinos", "cancelaciones", "estacionalidad"].map(x => TM.api("GET", "/analitica/" + x)));
  const max = Math.max(1, ...d.map(x => x.reservas));
  contenido().innerHTML = `<section class="tarjeta"><h3>Tendencias de destinos</h3>
      ${d.map(x => `<div class="fila"><span style="width:160px">${TM.esc(x.ciudad_destino)} (${x.pais_destino})</span>
        <div class="barra" style="width:${(x.reservas / max) * 60}%"></div><span class="suave">${x.reservas}</span></div>`).join("")}</section>
    <section class="tarjeta"><h3>Cancelaciones por proveedor</h3>${tabla(c)}</section>
    <section class="tarjeta"><h3>Estacionalidad</h3>${tabla(e)}</section>
    <p class="suave">Fuente: almacén analítico OLAP (datos anonimizados), separado de la base operacional.</p>`;
}

// ---------------------------------------------------------------- operaciones
async function renderOperaciones() {
  const [estado, notif, audit] = await Promise.all([
    TM.api("GET", "/operaciones/estado"), TM.api("GET", "/operaciones/notificaciones"), TM.api("GET", "/operaciones/auditoria"),
  ]);
  contenido().innerHTML = `<section class="tarjeta"><h3>Atributos de calidad (región ${TM.esc(estado.region)})</h3><pre>${TM.esc(JSON.stringify(estado, null, 2))}</pre></section>
    <section class="tarjeta"><h3>Notificaciones a operaciones</h3>${tabla(notif.map(({ momento, tipo, mensaje }) => ({ momento, tipo, mensaje })))}</section>
    <section class="tarjeta"><h3>Auditoría</h3>${tabla(audit.map(({ momento, actor, accion, recurso, resultado, detalle }) => ({ momento, actor, accion, recurso, resultado, detalle })))}</section>`;
}

// ---------------------------------------------------------------- simulación de sistemas externos
async function renderSimulacion() {
  const prov = await TM.api("GET", "/simulacion/proveedores");
  const filas = Object.entries(prov).map(([c, p]) => `<tr><td>${c}</td><td>${p.reservas.join(", ")}</td>
    <td><button data-caida="${c}" data-estado="${!p.caido}">${p.caido ? "▶ Recuperar" : "⏹ Simular caída"}</button></td></tr>`).join("");
  contenido().innerHTML = `
    <section class="tarjeta"><h3>Proveedores externos (QA-D2)</h3>
      <p class="suave">Al caer un proveedor, sus reservas muestran "Última actualización" y las consultas se reintentan con backoff.</p>
      <table><tr><th>Proveedor</th><th>Reservas</th><th></th></tr>${filas}</table></section>
    <section class="tarjeta"><h3>Cambio emitido por un proveedor (QA-R1)</h3>
      <p class="suave">La aerolínea cambia la puerta y demora el vuelo AS7K2P; llega por webhook → cola → worker → panel.</p>
      <button id="cambio-puerta">Cambiar puerta a C7 y demorar 45 min</button>
      <button id="cancelar-auto">rentacar cancela RC-99812</button></section>
    <section class="tarjeta"><h3>Correo entrante (US-01 / US-02)</h3>
      <button id="correo-viaje">Llega confirmación de tren a ana@gmail.demo</button>
      <button id="correo-personal">Llega correo personal</button></section>
    <section class="tarjeta"><h3>Token de correo robado (QA-S2)</h3>
      <p class="suave">Un atacante usa el token de ana@gmail.demo desde otro origen: se detecta, se revoca, se notifica y se audita.</p>
      <button id="token-robado" class="peligro">Usar token robado</button></section>
    <section class="tarjeta"><h3>Tareas programadas (ADR-0006)</h3>
      <button data-tarea="archivado-viajes">Archivar viajes finalizados</button>
      <button data-tarea="sondeo-correo">Sondear casillas</button>
      <button data-tarea="salud-proveedores">Heartbeat proveedores</button>
      <button data-tarea="sondeo-proveedores">Sondear proveedores</button></section>
    <pre id="salida-sim">—</pre>`;
  const mostrar = x => { $("#salida-sim").textContent = JSON.stringify(x, null, 2); };
  contenido().querySelectorAll("[data-caida]").forEach(b => b.onclick = () => intentar(async () => {
    mostrar(await TM.api("POST", `/simulacion/proveedores/${b.dataset.caida}/caida`, { caido: b.dataset.estado === "true" }));
    setTimeout(() => ir("simulacion"), 300);
  }));
  $("#cambio-puerta").onclick = () => intentar(async () => {
    const actual = (await TM.api("GET", "/viajes")).flatMap(v => v.reservas).find(r => r.codigo_confirmacion === "AS7K2P");
    const mas = iso => new Date(new Date(iso).getTime() + 45 * 60000).toISOString();
    mostrar(await TM.api("POST", "/simulacion/proveedores/aerolineas-sur/cambio", {
      codigo_confirmacion: "AS7K2P",
      cambios: { status: "DELAYED", gate: "C7", flight: actual ? { departure: mas(actual.inicio), arrival: mas(actual.fin) } : {} },
    }));
  });
  $("#cancelar-auto").onclick = () => intentar(async () => mostrar(await TM.api("POST", "/simulacion/proveedores/rentacar/cambio",
    { codigo_confirmacion: "RC-99812", cambios: { status: "CANCELLED" } })));
  $("#correo-viaje").onclick = () => intentar(async () => {
    const salida = new Date(Date.now() + 26 * 86400000).toISOString();
    const llegada = new Date(Date.now() + 26 * 86400000 + 9000000).toISOString();
    mostrar(await TM.api("POST", "/simulacion/correo/entregar", {
      direccion: "ana@gmail.demo", remitente: "billetes@trenes-del-sur.demo", asunto: "Tu billete de tren",
      cuerpo: `Tipo: tren\nProveedor: trenes-del-sur\nLocalizador: TS-9001\nTren: AVE 2240\nDesde: Sevilla Santa Justa | Sevilla | ES | 37.392 | -5.975\nHacia: Córdoba Central | Córdoba | ES | 37.888 | -4.789\nSalida: ${salida}\nLlegada: ${llegada}\nAsiento: 7C`,
    }));
    aviso("Recordá agregar trenes-del-sur.demo a la whitelist para que se lea.");
  });
  $("#correo-personal").onclick = () => intentar(async () => mostrar(await TM.api("POST", "/simulacion/correo/entregar", {
    direccion: "ana@gmail.demo", remitente: "mama@familia.demo", asunto: "Fotos", cuerpo: "Contenido privado",
  })));
  $("#token-robado").onclick = () => intentar(async () => mostrar(await TM.api("POST", "/simulacion/correo/uso-token", { direccion: "ana@gmail.demo" })));
  contenido().querySelectorAll("[data-tarea]").forEach(b => b.onclick = () => intentar(async () => mostrar(await TM.api("POST", "/simulacion/tareas/" + b.dataset.tarea))));
}

// ---------------------------------------------------------------- arranque
async function iniciar() {
  await TM.cargarIdioma();
  $("#salir").onclick = TM.salir;
  if (!TM.token) {
    $("#vista-login").hidden = false;
    $("#form-login").onsubmit = async ev => {
      ev.preventDefault();
      try {
        TM.guardarSesion(await TM.api("POST", "/auth/login", { email: ev.target.email.value, clave: ev.target.clave.value }));
        location.reload();
      } catch { aviso(TM.t("login.error"), true); }
    };
    return;
  }
  $("#vista-app").hidden = false;
  $("#quien").textContent = `${TM.perfil.nombre} · ${TM.perfil.rol}`;
  const inicial = { analista: "analitica", operaciones: "operaciones" }[TM.perfil.rol] || "viajes";
  const m = location.hash.match(/^#\/viaje\/(\w+)/);
  if (m) {
    vistaActual = "compartidos"; dibujarNav();
    await intentar(async () => { contenido().innerHTML = htmlViaje(await TM.api("GET", "/viajes/" + m[1]), false); });
    return;
  }
  ir(inicial);
}

iniciar();
