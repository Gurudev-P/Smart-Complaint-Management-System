import { api } from "../api.js";
import { h, clear, icon, toast, spinner, STATUS_LABEL, PRIORITY_LABEL, formatDate } from "../ui.js";

const STATUS_COLOR = {
  SUBMITTED: "var(--ink-3)", ASSIGNED: "var(--info)", IN_PROGRESS: "var(--warning)",
  ESCALATED: "var(--danger)", RESOLVED: "var(--success)", CLOSED: "var(--ink-3)",
};
const PRIORITY_COLOR = { LOW: "var(--ink-3)", MEDIUM: "var(--info)", HIGH: "var(--warning)", CRITICAL: "var(--danger)" };

function kpi(label, value, note, tone, testid) {
  return h("div", { class: `card kpi${tone ? " alert-tone" : ""}`, "data-testid": testid },
    h("div", { class: "label" }, label), h("div", { class: "value" }, value ?? "—"), note ? h("div", { class: "note" }, note) : null);
}

function bars(title, entries, labels, colors) {
  const max = Math.max(1, ...entries.map(([, v]) => v));
  return h("section", { class: "card" },
    h("div", { class: "card-head" }, h("h2", {}, title)),
    h("div", { class: "bars" }, entries.length
      ? entries.map(([k, v]) => h("div", { class: "bar-row" },
          h("span", { title: labels?.[k] || k }, labels?.[k] || k),
          h("div", { class: "track", role: "img", "aria-label": `${labels?.[k] || k}: ${v}` },
            h("div", { class: "fill", style: `width:${(v / max) * 100}%;background:${colors?.[k] || "var(--primary)"}` })),
          h("span", { class: "num" }, v)))
      : h("p", { class: "muted small" }, "No data yet.")));
}

function trendChart(points) {
  const W = 600, H = 160, P = 24;
  const max = Math.max(1, ...points.map((p) => p.count));
  const x = (i) => P + (i * (W - 2 * P)) / Math.max(1, points.length - 1);
  const y = (v) => H - P - (v / max) * (H - 2 * P);
  const line = points.map((p, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(p.count).toFixed(1)}`).join(" ");
  const area = `${line} L${x(points.length - 1)},${H - P} L${x(0)},${H - P} Z`;
  const ns = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(ns, "svg");
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  svg.setAttribute("role", "img");
  svg.setAttribute("aria-label", `Complaints per day over the last ${points.length} days`);
  const el = (tag, attrs) => { const n = document.createElementNS(ns, tag); for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, v); svg.append(n); return n; };
  el("line", { x1: P, x2: W - P, y1: H - P, y2: H - P, stroke: "var(--border)" });
  el("path", { d: area, fill: "var(--primary-soft)" });
  el("path", { d: line, fill: "none", stroke: "var(--primary)", "stroke-width": 2.5, "stroke-linejoin": "round" });
  points.forEach((p, i) => {
    const c = el("circle", { cx: x(i), cy: y(p.count), r: 3.5, fill: "var(--surface)", stroke: "var(--primary)", "stroke-width": 2 });
    const t = document.createElementNS(ns, "title"); t.textContent = `${p.date}: ${p.count}`; c.append(t);
  });
  [0, points.length - 1].forEach((i) => {
    const t = el("text", { x: x(i), y: H - 6, "font-size": 11, fill: "var(--ink-3)", "text-anchor": i ? "end" : "start" });
    t.textContent = new Date(points[i].date).toLocaleDateString(undefined, { day: "numeric", month: "short" });
  });
  const top = el("text", { x: P, y: 14, "font-size": 11, fill: "var(--ink-3)" });
  top.textContent = `max ${max}/day`;
  return svg;
}

export async function dashboardView(root, { user }) {
  const isAdmin = user.role === "ADMIN";
  const from = h("input", { class: "input", type: "date", "aria-label": "From date" });
  const to = h("input", { class: "input", type: "date", "aria-label": "To date" });
  const body = h("div", {});
  const head = h("div", { class: "page-head" },
    h("div", {}, h("h1", {}, "Dashboard"),
      h("p", {}, isAdmin ? "Complaint volume, status and resolution performance across the organisation." : "Your assigned workload and service-level performance.")),
    h("div", { class: "row-between" }, from, to,
      isAdmin ? h("button", { class: "btn btn-secondary", onclick: runCheck, title: "Run the SLA monitor now" }, icon("refresh"), "Run SLA check") : null));
  root.append(head, body);
  from.addEventListener("change", load);
  to.addEventListener("change", load);

  async function runCheck() {
    try {
      const r = await api.runSlaCheck();
      toast(`SLA check: ${r.checked} open checked, ${r.escalated} escalated, ${r.approaching_notified} due-soon alerts`, "success");
      load();
    } catch (err) { toast(err.message, "error"); }
  }

  async function load() {
    if (from.value && to.value && from.value > to.value) { toast("'From' date must be before 'To' date", "error"); return; }
    clear(body).append(spinner());
    const s = await api.summary({
      from: from.value ? new Date(`${from.value}T00:00:00`).toISOString() : null,
      to: to.value ? new Date(`${to.value}T23:59:59`).toISOString() : null,
    });
    clear(body).append(
      h("div", { class: "grid grid-4", style: "margin-bottom:16px" },
        kpi("Total complaints", s.total, `${s.open} open`, false, "kpi-total"),
        kpi("Overdue", s.overdue, "Open past SLA deadline", s.overdue > 0, "kpi-overdue"),
        kpi("Escalated", s.escalated, "Escalated at least once", false, "kpi-escalated"),
        kpi("SLA compliance", s.sla_compliance_percent == null ? "—" : `${s.sla_compliance_percent}%`,
          s.avg_resolution_hours == null ? "No resolutions yet" : `Avg. resolution ${s.avg_resolution_hours < 1 ? "under 1 h" : `${s.avg_resolution_hours} h`}`, false, "kpi-sla")),
      h("div", { class: "grid grid-2", style: "margin-bottom:16px" },
        bars("By status", Object.entries(s.by_status), STATUS_LABEL, STATUS_COLOR),
        bars("By priority", Object.entries(s.by_priority).reverse(), PRIORITY_LABEL, PRIORITY_COLOR)),
      h("div", { class: "grid grid-2" },
        bars("By category", Object.entries(s.by_category)),
        h("section", { class: "card" }, h("div", { class: "card-head" }, h("h2", {}, "New complaints, last 14 days")), h("div", { class: "trend" }, trendChart(s.trend)))),
      h("p", { class: "muted small", style: "margin-top:12px" }, `Updated ${formatDate(s.generated_at)}${s.scope === "assigned" ? " · showing complaints assigned to you" : ""}`),
    );
  }
  await load();
}
