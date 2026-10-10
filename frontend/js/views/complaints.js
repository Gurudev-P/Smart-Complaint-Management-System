import { api } from "../api.js";
import {
  h, clear, icon, field, showErrors, modal, toast, spinner, emptyState,
  statusBadge, priorityBadge, slaBadge, formatDate, timeAgo, timeLeft, formatMinutes,
  STATUS_LABEL, PRIORITY_LABEL,
} from "../ui.js";
import { LIMITS, collectErrors, validateDescription, validateRequired, validateResolution } from "../validators.js";
import { navigate } from "../app.js";

const PAGE_SIZE = 15;

function scopesFor(user) {
  if (user.role === "USER") return [["mine", "My complaints"]];
  if (user.role === "STAFF") return [["assigned", "Assigned to me"], ["unassigned", "Unassigned"], ["mine", "Raised by me"]];
  return [["all", "All"], ["unassigned", "Unassigned"], ["assigned", "Assigned to me"], ["mine", "Raised by me"]];
}

// ------------------------------------------------------------------ list
export async function complaintListView(root, { query, user }) {
  const scopes = scopesFor(user);
  const scope = scopes.some(([k]) => k === query.get("scope")) ? query.get("scope") : scopes[0][0];
  const filters = { status: "", priority: "", category_id: "", q: "", overdue: false, offset: 0 };

  const categories = await api.categories();
  const heading = user.role === "USER" ? "My complaints" : user.role === "STAFF" ? "My queue" : "All complaints";
  const subtitle = user.role === "USER"
    ? "Track the status of everything you have reported."
    : "Filter, open and act on complaints.";

  const headActions = h("div", { class: "row-between" });
  if (user.role === "ADMIN") {
    headActions.append(h("button", { class: "btn btn-secondary", onclick: exportCsv }, icon("download"), "Export CSV"));
  }
  headActions.append(h("a", { class: "btn", href: "#/complaints/new" }, icon("plus"), "New complaint"));

  const tabs = scopes.length > 1
    ? h("div", { class: "tabs", role: "tablist" }, scopes.map(([key, label]) =>
        h("button", { class: `tab${key === scope ? " active" : ""}`, role: "tab", "aria-selected": String(key === scope), onclick: () => navigate(`#/complaints?scope=${key}`) }, label)))
    : null;

  const search = h("input", { class: "input search", type: "search", placeholder: "Search description or category", "aria-label": "Search" });
  const statusSel = h("select", { class: "input", "aria-label": "Filter by status" },
    h("option", { value: "" }, "All statuses"), Object.entries(STATUS_LABEL).map(([k, v]) => h("option", { value: k }, v)));
  const prioritySel = h("select", { class: "input", "aria-label": "Filter by priority" },
    h("option", { value: "" }, "All priorities"), Object.entries(PRIORITY_LABEL).map(([k, v]) => h("option", { value: k }, v)));
  const categorySel = h("select", { class: "input", "aria-label": "Filter by category" },
    h("option", { value: "" }, "All categories"), categories.map((c) => h("option", { value: c.category_id }, c.name)));
  const overdueBox = h("input", { type: "checkbox", id: "overdue" });
  const filterBar = h("div", { class: "filters" }, search, statusSel, prioritySel, categorySel,
    h("label", { class: "switch", for: "overdue" }, overdueBox, "Overdue only"));

  const body = h("div", {});
  const card = h("section", { class: "card" }, filterBar, body);
  root.append(h("div", {},
    h("div", { class: "page-head" }, h("div", {}, h("h1", {}, heading), h("p", {}, subtitle)), headActions),
    tabs ? h("div", { style: "margin-bottom:16px" }, tabs) : null,
    card,
  ));

  let timer;
  search.addEventListener("input", () => { clearTimeout(timer); timer = setTimeout(() => { filters.q = search.value; filters.offset = 0; load(); }, 300); });
  statusSel.addEventListener("change", () => { filters.status = statusSel.value; filters.offset = 0; load(); });
  prioritySel.addEventListener("change", () => { filters.priority = prioritySel.value; filters.offset = 0; load(); });
  categorySel.addEventListener("change", () => { filters.category_id = categorySel.value; filters.offset = 0; load(); });
  overdueBox.addEventListener("change", () => { filters.overdue = overdueBox.checked; filters.offset = 0; load(); });

  function params() {
    return { scope, status: filters.status, priority: filters.priority, category_id: filters.category_id, q: filters.q.trim(), overdue: filters.overdue, limit: PAGE_SIZE, offset: filters.offset };
  }

  async function exportCsv() {
    try {
      const res = await api.reportCsv({
        status: filters.status,
        priority: filters.priority,
        category_id: filters.category_id,
        scope,
        q: filters.q.trim(),
        overdue: filters.overdue,
      });
      const blob = await res.blob();
      const a = h("a", { href: URL.createObjectURL(blob), download: "complaints_report.csv" });
      document.body.append(a); a.click(); a.remove();
    } catch (err) { toast(err.message, "error"); }
  }

  async function load() {
    clear(body).append(spinner());
    const page = await api.complaints(params());
    clear(body);
    if (!page.items.length) {
      const filtered = filters.status || filters.priority || filters.category_id || filters.q || filters.overdue;
      body.append(filtered
        ? emptyState("No matching complaints", "Try clearing some filters.")
        : emptyState("No complaints yet", scope === "unassigned" ? "Every complaint has an owner." : "Complaints will appear here once they are submitted.",
            user.role === "USER" ? h("a", { class: "btn", href: "#/complaints/new" }, "Submit a complaint") : null));
      return;
    }
    const rows = page.items.map((c) => {
      const tr = h("tr", { class: "clickable", tabindex: "0", "data-id": c.complaint_id, onclick: () => navigate(`#/complaints/${c.complaint_id}`) },
        h("td", {}, h("span", { class: "ref" }, c.reference)),
        h("td", {}, h("div", { class: "clamp" }, c.description), h("div", { class: "muted small" }, c.category.name)),
        h("td", {}, priorityBadge(c.priority)),
        h("td", {}, statusBadge(c.status)),
        user.role === "USER" ? null : h("td", {}, c.assignee ? c.assignee.name : h("span", { class: "muted" }, "Unassigned")),
        h("td", {}, slaBadge(c.sla), c.sla && !["RESOLVED", "CLOSED"].includes(c.status) ? h("div", { class: "muted small" }, timeLeft(c.sla.deadline)) : null),
        h("td", { class: "muted small" }, timeAgo(c.created_at)),
      );
      tr.addEventListener("keydown", (e) => { if (e.key === "Enter") navigate(`#/complaints/${c.complaint_id}`); });
      return tr;
    });
    const end = Math.min(filters.offset + PAGE_SIZE, page.total);
    body.append(
      h("div", { class: "table-wrap" }, h("table", { class: "table", "aria-label": "Complaints" },
        h("thead", {}, h("tr", {},
          h("th", {}, "Ref"), h("th", {}, "Complaint"), h("th", {}, "Priority"), h("th", {}, "Status"),
          user.role === "USER" ? null : h("th", {}, "Assignee"), h("th", {}, "SLA"), h("th", {}, "Created"))),
        h("tbody", {}, rows))),
      h("div", { class: "pager" },
        h("span", {}, `Showing ${filters.offset + 1}–${end} of ${page.total}`),
        h("div", { class: "row-between" },
          h("button", { class: "btn btn-secondary btn-sm", disabled: filters.offset === 0, onclick: () => { filters.offset -= PAGE_SIZE; load(); } }, "Previous"),
          h("button", { class: "btn btn-secondary btn-sm", disabled: end >= page.total, onclick: () => { filters.offset += PAGE_SIZE; load(); } }, "Next"))),
    );
  }
  await load();
}

// ------------------------------------------------------------------ new complaint (FR-05, FR-08)
const PRIORITY_HINT = { LOW: "Minor, no rush", MEDIUM: "Needs attention", HIGH: "Affecting work", CRITICAL: "Urgent / unsafe" };

export async function complaintNewView(root) {
  const categories = await api.categories();
  const alert = h("div", { class: "alert alert-error", role: "alert", hidden: true });
  const category = h("select", { class: "input" }, h("option", { value: "" }, "Select a category"),
    categories.map((c) => h("option", { value: c.category_id }, c.name)));
  const priorityGroup = h("div", { class: "segmented", role: "radiogroup", "aria-label": "Priority", id: "priority" },
    ["LOW", "MEDIUM", "HIGH", "CRITICAL"].flatMap((p) => [
      h("input", { type: "radio", name: "priority", id: `prio-${p}`, value: p, checked: p === "MEDIUM" }),
      h("label", { for: `prio-${p}` }, PRIORITY_LABEL[p], h("small", {}, PRIORITY_HINT[p])),
    ]));
  const description = h("textarea", { class: "input", maxlength: String(LIMITS.descriptionMax), placeholder: "What happened, where, and since when?" });
  const counter = h("span", { class: "hint" }, `0 / ${LIMITS.descriptionMax}`);
  description.addEventListener("input", () => (counter.textContent = `${description.value.length} / ${LIMITS.descriptionMax}`));
  const submit = h("button", { class: "btn", type: "submit" }, "Submit complaint");

  const priorityField = h("div", { class: "field" },
    h("label", { id: "priority-label" }, "Priority"), priorityGroup,
    h("div", { class: "hint" }, "Staff may adjust the priority after review."),
    h("div", { class: "error", id: "priority-error" }));
  const descField = field({ id: "description", label: "Description", input: description, required: true });
  descField.insertBefore(h("div", { class: "row-between" }, h("span", { class: "hint" }, `At least ${LIMITS.descriptionMin} characters.`), counter), descField.querySelector(".error"));

  const form = h("form", { class: "card card-pad", novalidate: true, "aria-label": "New complaint", style: "max-width:720px" },
    alert,
    field({ id: "category", label: "Category", input: category, required: true }),
    priorityField,
    descField,
    h("div", { class: "row-between" }, h("a", { class: "btn btn-ghost", href: "#/complaints" }, "Cancel"), submit));

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    alert.hidden = true;
    const priority = form.querySelector("input[name=priority]:checked")?.value;
    const errors = collectErrors({
      category: validateRequired(category.value, "Category"),
      priority: validateRequired(priority, "Priority"),
      description: validateDescription(description.value),
    });
    if (!showErrors(form, errors)) return;
    submit.disabled = true;
    submit.textContent = "Submitting…";
    try {
      const created = await api.createComplaint({ category_id: category.value, priority, description: description.value.trim() });
      toast(`${created.reference} submitted`, "success");
      navigate(`#/complaints/${created.complaint_id}`);
    } catch (err) {
      alert.textContent = err.message;
      alert.hidden = false;
      submit.disabled = false;
      submit.textContent = "Submit complaint";
    }
  });

  root.append(
    h("div", { class: "page-head" }, h("div", {}, h("h1", {}, "New complaint"), h("p", {}, "Describe the issue clearly so it can be routed to the right team."))),
    categories.length ? form : h("div", { class: "alert alert-info" }, "No complaint categories are available yet. Please contact an administrator."),
  );
  category.focus();
}

// ------------------------------------------------------------------ detail (FR-07, FR-10, FR-12–FR-15, FR-18/19)
export async function complaintDetailView(root, { params, user }) {
  const [id] = params;
  root.append(spinner());
  let c;
  try {
    c = await api.complaint(id);
  } catch (err) {
    clear(root).append(emptyState("Complaint not found", "It may not exist, or you may not have access to it.", h("a", { class: "btn", href: "#/complaints" }, "Back to complaints")));
    return;
  }
  clear(root);
  const p = c.permissions;

  const run = (fn, success) => async () => {
    try {
      await fn();
      toast(success, "success");
      clear(root);
      await complaintDetailView(root, { params, user });
    } catch (err) {
      toast(err.message, "error");
    }
  };

  // -- actions
  const actions = [];
  if (p.start) actions.push(h("button", { class: "btn", onclick: run(() => api.changeStatus(id, "IN_PROGRESS", c.status), "Work started") }, c.status === "ESCALATED" ? "Resume work" : "Start work"));
  if (p.resolve) actions.push(h("button", { class: "btn btn-success", onclick: () => resolveDialog(id).then((ok) => ok && run(async () => {}, "Complaint resolved")()) }, "Resolve"));
  if (p.assign) actions.push(h("button", { class: "btn btn-secondary", onclick: () => assignDialog(c, user).then((ok) => ok && run(async () => {}, "Complaint assigned")()) }, c.assignee ? "Reassign" : "Assign"));
  if (p.change_priority) actions.push(h("button", { class: "btn btn-secondary", onclick: () => priorityDialog(c).then((ok) => ok && run(async () => {}, "Priority updated")()) }, "Change priority"));
  if (p.edit) actions.push(h("button", { class: "btn btn-secondary", onclick: () => editDialog(c).then((ok) => ok && run(async () => {}, "Complaint updated")()) }, "Edit"));
  if (p.escalate) actions.push(h("button", { class: "btn btn-secondary", onclick: () => confirmDialog("Escalate complaint", "Escalate this complaint now? Administrators and the assignee will be notified.", "Escalate", "btn btn-danger").then((ok) => ok && run(() => api.changeStatus(id, "ESCALATED", c.status), "Complaint escalated")()) }, "Escalate"));
  if (p.close) actions.push(h("button", { class: "btn btn-secondary", onclick: () => confirmDialog("Close complaint", "Close this resolved complaint? This is the final status.", "Close complaint").then((ok) => ok && run(() => api.changeStatus(id, "CLOSED", c.status), "Complaint closed")()) }, "Close"));

  const historyItems = c.history.map((item, i) => h("li", {},
    h("div", {}, i === 0 && item.old_status === item.new_status ? "Complaint submitted" : h("span", {}, "Status changed to ", h("strong", {}, STATUS_LABEL[item.new_status]))),
    h("div", { class: "muted small" }, `${item.changed_by.name} · ${formatDate(item.changed_at)}`)));

  root.append(
    h("div", { class: "page-head" },
      h("div", {},
        h("a", { href: "#/complaints", class: "small" }, "← All complaints"),
        h("h1", { style: "margin-top:6px" }, h("span", { class: "ref", style: "font-size:22px" }, c.reference)),
        h("p", {}, `${c.category.name} · Submitted ${formatDate(c.created_at)} by ${c.creator.name}`)),
      h("div", { class: "row-between" }, statusBadge(c.status), priorityBadge(c.priority))),
    h("div", { class: "detail-layout" },
      h("div", { class: "grid" },
        h("section", { class: "card" }, h("div", { class: "card-head" }, h("h2", {}, "Description")), h("div", { class: "description" }, c.description)),
        c.resolution ? h("section", { class: "card" }, h("div", { class: "card-head" }, h("h2", {}, "Resolution")),
          h("div", { class: "resolution", style: "margin-top:16px" },
            h("strong", {}, `Resolved by ${c.resolution.resolver.name}`),
            h("div", { class: "muted small" }, formatDate(c.resolution.resolved_at)),
            h("p", {}, c.resolution.resolution_details))) : null,
        h("section", { class: "card" }, h("div", { class: "card-head" }, h("h2", {}, "History")), h("ol", { class: "timeline", "aria-label": "Status history" }, historyItems)),
      ),
      h("aside", { class: "card" },
        h("dl", { class: "meta-list" },
          h("div", {}, h("dt", {}, "Status"), h("dd", {}, statusBadge(c.status))),
          h("div", {}, h("dt", {}, "Priority"), h("dd", {}, priorityBadge(c.priority))),
          h("div", {}, h("dt", {}, "Assigned to"), h("dd", {}, c.assignee ? c.assignee.name : h("span", { class: "muted" }, "Not yet assigned"))),
          c.sla ? h("div", {}, h("dt", {}, "Service level"), h("dd", {}, slaBadge(c.sla)),
            h("dd", { class: "muted small" }, `Target ${formatMinutes(c.sla.target_duration)} · due ${formatDate(c.sla.deadline)}`),
            !["RESOLVED", "CLOSED"].includes(c.status) ? h("dd", { class: "small" }, timeLeft(c.sla.deadline)) : null,
            c.sla.escalation_level > 0 ? h("dd", { class: "small", style: "color:var(--danger)" }, `Escalated ${formatDate(c.sla.escalated_at)}`) : null) : null,
          h("div", {}, h("dt", {}, "Last updated"), h("dd", {}, formatDate(c.updated_at))),
        ),
        actions.length ? h("div", { class: "actions", "aria-label": "Actions" }, actions) : null,
      ),
    ),
  );
}

// ------------------------------------------------------------------ dialogs
function confirmDialog(title, message, confirmText, confirmClass) {
  return modal({ title, body: h("p", {}, message), confirmText, confirmClass });
}

function resolveDialog(id) {
  const details = h("textarea", { class: "input", maxlength: String(LIMITS.resolutionMax), placeholder: "What was done to fix the issue?" });
  const body = h("div", {}, field({ id: "resolution", label: "Resolution details", input: details, hint: "Required before a complaint can be marked resolved.", required: true }));
  return modal({
    title: "Resolve complaint", body, confirmText: "Mark resolved", confirmClass: "btn btn-success",
    onConfirm: async () => {
      if (!showErrors(body, collectErrors({ resolution: validateResolution(details.value) }))) return false;
      await api.resolve(id, details.value.trim());
    },
  });
}

async function assignDialog(c, user) {
  const staff = await api.users({ role: "STAFF" });
  const select = h("select", { class: "input" }, h("option", { value: "" }, "Select a staff member"),
    staff.filter((s) => s.user_id !== c.assignee?.user_id).map((s) => h("option", { value: s.user_id }, s.user_id === user.user_id ? `${s.name} (me)` : s.name)));
  const body = h("div", {}, field({ id: "staff", label: "Staff member", input: select, required: true }),
    staff.length ? null : h("p", { class: "muted small" }, "No active staff accounts exist. Create one under Users."));
  return modal({
    title: c.assignee ? "Reassign complaint" : "Assign complaint", body, confirmText: "Assign",
    onConfirm: async () => {
      if (!showErrors(body, collectErrors({ staff: validateRequired(select.value, "Staff member") }))) return false;
      await api.assign(c.complaint_id, select.value);
    },
  });
}

function priorityDialog(c) {
  const select = h("select", { class: "input" }, Object.entries(PRIORITY_LABEL).map(([k, v]) => h("option", { value: k, selected: k === c.priority }, v)));
  const body = h("div", {}, field({ id: "new-priority", label: "Priority", input: select, hint: "The SLA deadline is recalculated from the submission time." }));
  return modal({
    title: "Change priority", body, confirmText: "Update",
    onConfirm: async () => { if (select.value !== c.priority) await api.updateComplaint(c.complaint_id, { priority: select.value }); },
  });
}

async function editDialog(c) {
  const categories = await api.categories();
  const select = h("select", { class: "input" }, categories.map((cat) => h("option", { value: cat.category_id, selected: cat.category_id === c.category.category_id }, cat.name)));
  const desc = h("textarea", { class: "input", maxlength: String(LIMITS.descriptionMax) });
  desc.value = c.description;
  const body = h("div", {},
    field({ id: "edit-category", label: "Category", input: select }),
    field({ id: "edit-description", label: "Description", input: desc }));
  return modal({
    title: "Edit complaint", body, confirmText: "Save changes",
    onConfirm: async () => {
      if (!showErrors(body, collectErrors({ "edit-description": validateDescription(desc.value) }))) return false;
      await api.updateComplaint(c.complaint_id, { category_id: select.value, description: desc.value.trim() });
    },
  });
}
