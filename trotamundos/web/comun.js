// Utilidades compartidas por el cliente web y la vista móvil (Capa 1).
// - api(): cliente REST del contrato /api/v1 (ADR-0002).
// - i18n: paquetes de recursos externos /static/i18n/<idioma>.json (ADR-0016).
// - fechas: el backend entrega UTC; la conversión a la zona del viajero se hace acá.
"use strict";

const TM = {
  token: localStorage.getItem("tm_token"),
  perfil: JSON.parse(localStorage.getItem("tm_perfil") || "null"),
  textos: {},

  async api(metodo, ruta, cuerpo) {
    const opciones = { method: metodo, headers: {} };
    if (TM.token) opciones.headers.Authorization = "Bearer " + TM.token;
    if (cuerpo !== undefined) {
      opciones.headers["Content-Type"] = "application/json";
      opciones.body = JSON.stringify(cuerpo);
    }
    const r = await fetch("/api/v1" + ruta, opciones);
    if (r.status === 401 && ruta !== "/auth/login") { TM.salir(); throw new Error("Sesión vencida"); }
    if (r.status === 204) return null;
    const datos = await r.json().catch(() => null);
    if (!r.ok) {
      const det = datos && datos.detail;
      throw new Error(typeof det === "string" ? det : JSON.stringify(det || r.statusText));
    }
    return datos;
  },

  guardarSesion(sesion) {
    TM.token = sesion.token;
    TM.perfil = sesion.usuario;
    localStorage.setItem("tm_token", sesion.token);
    localStorage.setItem("tm_perfil", JSON.stringify(sesion.usuario));
  },

  salir() {
    TM.token = null; TM.perfil = null;
    localStorage.removeItem("tm_token"); localStorage.removeItem("tm_perfil");
    location.reload();
  },

  async cargarIdioma(idioma) {
    const lang = idioma || (TM.perfil && TM.perfil.idioma) || (navigator.language || "es").slice(0, 2);
    try {
      TM.textos = await (await fetch(`/static/i18n/${lang}.json`)).json();
    } catch {
      TM.textos = await (await fetch("/static/i18n/es.json")).json();
    }
    document.documentElement.lang = lang;
    document.querySelectorAll("[data-t]").forEach(el => { el.textContent = TM.t(el.dataset.t); });
  },

  t(clave) { return TM.textos[clave] || clave; },

  locale() { return (TM.perfil && TM.perfil.idioma) || "es"; },
  zona() { return (TM.perfil && TM.perfil.zona_horaria) || Intl.DateTimeFormat().resolvedOptions().timeZone; },

  fecha(iso, conHora = true) {
    const opciones = { timeZone: TM.zona(), day: "2-digit", month: "short", year: "numeric" };
    if (conHora) Object.assign(opciones, { hour: "2-digit", minute: "2-digit" });
    return new Intl.DateTimeFormat(TM.locale(), opciones).format(new Date(iso));
  },

  // Convierte UTC ISO a valor de <input type=datetime-local> en la zona del navegador.
  aInputLocal(iso) {
    const d = new Date(iso);
    return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
  },
  deInputLocal(valor) { return new Date(valor).toISOString(); },

  esc(texto) {
    return String(texto ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  },
};
