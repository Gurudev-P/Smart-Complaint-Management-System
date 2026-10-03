// DOM helpers. All dynamic text goes through textContent (never innerHTML) to prevent XSS.

export function h(tag, attrs = {}, ...children) {
  const el = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs || {})) {
    if (value === undefined || value === null || value === false) continue;
    if (key === "class") el.className = value;
    else if (key === "dataset") Object.assign(el.dataset, value);
    else if (key.startsWith("on") && typeof value === "function") el.addEventListener(key.slice(2).toLowerCase(), value);
    else if (key === "value") el.value = value;
    else if (value === true) el.setAttribute(key, "");
    else el.setAttribute(key, value);
  }
  append(el, children);
  return el;
}

function append(el, children) {
  for (const child of children.flat(Infinity)) {
    if (child === null || child === undefined || child === false) continue;
    el.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
}

export function clear(el) { while (el.firstChild) el.removeChild(el.firstChild); return el; }

// Inline icons (static, trusted markup).
const ICONS = {
  inbox: '<path d="M3 13h5l2 3h4l2-3h5"/><path d="M5 5h14l2 8v6H3v-6z"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  list: '<path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/>',
  chart: '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
  users: '<circle cx="9" cy="8" r="4"/><path d="M2 21c0-4 3-6 7-6s7 2 7 6M16 4a4 4 0 0 1 0 8M22 21c0-3-2-5-4-5.5"/>',
  tag: '<path d="M20 12 12 20l-9-9V3h8z"/><circle cx="7.5" cy="7.5" r="1.5"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  bell: '<path d="M6 8a6 6 0 1 1 12 0c0 7 3 8 3 8H3s3-1 3-8M10 21a2 2 0 0 0 4 0"/>',
  logout: '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9"/>',
  menu: '<path d="M3 6h18M3 12h18M3 18h18"/>',
  user: '<circle cx="12" cy="8" r="4"/><path d="M4 21c0-4 4-6 8-6s8 2 8 6"/>',
  back: '<path d="M15 18l-6-6 6-6"/>',
  download: '<path d="M12 3v12M7 10l5 5 5-5M4 21h16"/>',
  refresh: '<path d="M21 12a9 9 0 1 1-3-6.7L21 8M21 3v5h-5"/>',
};

export function icon(name) {
  const wrap = document.createElement("span");
  wrap.setAttribute("aria-hidden", "true");
  wrap.style.display = "inline-flex";
  wrap.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="18" height="18">${ICONS[name] || ""}</svg>`;
  return wrap;
}

export const STATUS_LABEL = {
  SUBMITTED: "Submitted", ASSIGNED: "Assigned", IN_PROGRESS: "In Progress",
  ESCALATED: "Escalated", RESOLVED: "Resolved", CLOSED: "Closed",
};
export const PRIORITY_LABEL = { LOW: "Low", MEDIUM: "Medium", HIGH: "High", CRITICAL: "Critical" };
export const SLA_LABEL = { ON_TRACK: "On track", APPROACHING: "Due soon", OVERDUE: "Overdue", MET: "SLA met", BREACHED: "SLA missed" };
export const ROLE_LABEL = { USER: "User", STAFF: "Staff", ADMIN: "Administrator" };

export const statusBadge = (s) => h("span", { class: `badge s-${s}`, "data-status": s }, STATUS_LABEL[s] || s);
export const priorityBadge = (p) => h("span", { class: `badge plain p-${p}` }, PRIORITY_LABEL[p] || p);
export const slaBadge = (sla) => (sla ? h("span", { class: `badge sla-${sla.state}`, title: `Deadline ${formatDate(sla.deadline)}` }, SLA_LABEL[sla.state]) : "—");

export function formatDate(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleString(undefined, { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" });
}

export function timeAgo(iso) {
  const diff = (Date.now() - new Date(iso).getTime()) / 1000;
  if (diff < 60) return "just now";
  const units = [[60, "minute"], [3600, "hour"], [86400, "day"], [604800, "week"]];
  let label = "";
  for (let i = units.length - 1; i >= 0; i--) {
    const [secs, name] = units[i];
    if (diff >= secs) { const n = Math.floor(diff / secs); label = `${n} ${name}${n > 1 ? "s" : ""} ago`; break; }
  }
  return label;
}

export function timeLeft(iso) {
  const diff = (new Date(iso).getTime() - Date.now()) / 60000;
  const abs = Math.abs(diff);
  const text = abs >= 1440 ? `${Math.round(abs / 1440)}d` : abs >= 60 ? `${Math.round(abs / 60)}h` : `${Math.max(1, Math.round(abs))}m`;
  return diff >= 0 ? `${text} left` : `${text} overdue`;
}

export function formatMinutes(min) {
  if (min % 1440 === 0) return `${min / 1440} day${min === 1440 ? "" : "s"}`;
  if (min % 60 === 0) return `${min / 60} hour${min === 60 ? "" : "s"}`;
  return `${min} minutes`;
}

// ---------- toasts ----------
export function toast(message, kind = "info") {
  let box = document.querySelector(".toasts");
  if (!box) { box = h("div", { class: "toasts", role: "status", "aria-live": "polite" }); document.body.append(box); }
  while (box.children.length >= 3) box.firstChild.remove();
  const t = h("div", { class: `toast ${kind}` }, message);
  box.append(t);
  setTimeout(() => t.remove(), 4000);
}

// ---------- modal ----------
export function modal({ title, body, confirmText = "Save", confirmClass = "btn", onConfirm }) {
  return new Promise((resolve) => {
    const error = h("div", { class: "alert alert-error", hidden: true });
    const confirm = h("button", { class: confirmClass, type: "submit" }, confirmText);
    const form = h("form", { class: "modal", role: "dialog", "aria-modal": "true", "aria-label": title, novalidate: true },
      h("div", { class: "card-head" }, h("h2", {}, title)),
      h("div", { class: "modal-body" }, error, body),
      h("div", { class: "modal-foot" },
        h("button", { class: "btn btn-secondary", type: "button", onclick: () => close(null) }, "Cancel"),
        confirm),
    );
    const backdrop = h("div", { class: "modal-backdrop", onclick: (e) => { if (e.target === backdrop) close(null); } }, form);
    const onKey = (e) => { if (e.key === "Escape") close(null); };
    function close(value) { document.removeEventListener("keydown", onKey); backdrop.remove(); resolve(value); }
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      error.hidden = true;
      confirm.disabled = true;
      try {
        const result = onConfirm ? await onConfirm() : true;
        if (result !== false) close(result ?? true);
      } catch (err) {
        error.textContent = err.message;
        error.hidden = false;
      } finally {
        confirm.disabled = false;
      }
    });
    document.addEventListener("keydown", onKey);
    document.body.append(backdrop);
    const first = form.querySelector("input, textarea, select, button[type=submit]");
    first?.focus();
  });
}

// ---------- form fields ----------
export function field({ id, label, input, hint, required }) {
  const err = h("div", { class: "error", id: `${id}-error`, "aria-live": "polite" });
  input.id = id;
  input.setAttribute("aria-describedby", `${id}-error`);
  if (required) input.setAttribute("aria-required", "true");
  return h("div", { class: "field" }, h("label", { for: id }, label), input, hint ? h("div", { class: "hint" }, hint) : null, err);
}

export function showErrors(form, errors) {
  form.querySelectorAll(".input").forEach((el) => {
    el.classList.remove("invalid");
    el.removeAttribute("aria-invalid");
  });
  form.querySelectorAll(".field .error").forEach((el) => (el.textContent = ""));
  let first = null;
  for (const [id, message] of Object.entries(errors)) {
    const input = form.querySelector(`#${id}`);
    const slot = form.querySelector(`#${id}-error`);
    if (input) { input.classList.add("invalid"); input.setAttribute("aria-invalid", "true"); first ||= input; }
    if (slot) slot.textContent = message;
  }
  first?.focus();
  return Object.keys(errors).length === 0;
}

export function spinner() { return h("div", { class: "spinner", role: "status", "aria-label": "Loading" }); }

export function emptyState(title, text, action) {
  return h("div", { class: "empty" }, h("h3", {}, title), h("p", {}, text), action || null);
}
