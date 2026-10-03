import { api } from "../api.js";
import { h, clear, icon, field, showErrors, modal, toast, spinner, emptyState, ROLE_LABEL, PRIORITY_LABEL, priorityBadge, formatDate, formatMinutes } from "../ui.js";
import { collectErrors, validateCategoryName, validateEmail, validateName, validatePassword, validatePositiveInt } from "../validators.js";

// ------------------------------------------------------------------ users (Manage Users use case)
export async function usersView(root, { user: me }) {
  const roleFilter = h("select", { class: "input", "aria-label": "Filter by role" },
    h("option", { value: "" }, "All roles"), Object.entries(ROLE_LABEL).map(([k, v]) => h("option", { value: k }, v)));
  const body = h("div", {});
  root.append(
    h("div", { class: "page-head" },
      h("div", {}, h("h1", {}, "Users"), h("p", {}, "Create staff and administrator accounts, change roles, and deactivate access.")),
      h("button", { class: "btn", onclick: () => createDialog().then((ok) => ok && load()) }, icon("plus"), "Add user")),
    h("section", { class: "card" }, h("div", { class: "filters" }, roleFilter), body));
  roleFilter.addEventListener("change", load);

  async function update(u, changes, message) {
    try { await api.updateUser(u.user_id, changes); toast(message, "success"); load(); } catch (err) { toast(err.message, "error"); }
  }

  async function load() {
    clear(body).append(spinner());
    const users = await api.users({ role: roleFilter.value });
    clear(body);
    if (!users.length) return body.append(emptyState("No users", "No accounts match this filter."));
    body.append(h("div", { class: "table-wrap" }, h("table", { class: "table", "aria-label": "Users" },
      h("thead", {}, h("tr", {}, h("th", {}, "Name"), h("th", {}, "Email"), h("th", {}, "Role"), h("th", {}, "Status"), h("th", {}, "Joined"), h("th", {}, h("span", { class: "sr-only" }, "Actions")))),
      h("tbody", {}, users.map((u) => {
        const self = u.user_id === me.user_id;
        const role = h("select", { class: "input", style: "height:32px;width:auto", "aria-label": `Role for ${u.name}`, disabled: self },
          Object.entries(ROLE_LABEL).map(([k, v]) => h("option", { value: k, selected: k === u.role }, v)));
        role.addEventListener("change", () => update(u, { role: role.value }, `${u.name} is now ${ROLE_LABEL[role.value]}`));
        const active = u.account_status === "ACTIVE";
        return h("tr", { "data-email": u.email },
          h("td", {}, h("strong", {}, u.name), self ? h("span", { class: "muted small" }, " (you)") : null),
          h("td", {}, u.email),
          h("td", {}, role),
          h("td", {}, h("span", { class: `badge ${active ? "s-RESOLVED" : "s-CLOSED"}` }, active ? "Active" : "Inactive")),
          h("td", { class: "muted small" }, formatDate(u.created_at)),
          h("td", {}, self ? null : h("button", {
            class: `btn btn-sm ${active ? "btn-secondary" : "btn-success"}`,
            onclick: () => update(u, { account_status: active ? "INACTIVE" : "ACTIVE" }, `${u.name} ${active ? "deactivated" : "activated"}`),
          }, active ? "Deactivate" : "Activate")));
      })))));
  }
  await load();
}

function createDialog() {
  const name = h("input", { class: "input", autocomplete: "off" });
  const email = h("input", { class: "input", type: "email", autocomplete: "off" });
  const password = h("input", { class: "input", type: "password", autocomplete: "new-password" });
  const role = h("select", { class: "input" }, ["STAFF", "ADMIN", "USER"].map((r) => h("option", { value: r }, ROLE_LABEL[r])));
  const body = h("div", {},
    field({ id: "new-name", label: "Full name", input: name, required: true }),
    field({ id: "new-email", label: "Email", input: email, required: true }),
    field({ id: "new-password", label: "Temporary password", input: password, hint: "At least 8 characters with a letter and a digit. Share it securely.", required: true }),
    field({ id: "new-role", label: "Role", input: role }));
  return modal({
    title: "Add user", body, confirmText: "Create user",
    onConfirm: async () => {
      const errors = collectErrors({ "new-name": validateName(name.value), "new-email": validateEmail(email.value), "new-password": validatePassword(password.value) });
      if (!showErrors(body, errors)) return false;
      await api.createUser({ name: name.value.trim(), email: email.value.trim(), password: password.value, role: role.value });
      toast("User created", "success");
    },
  });
}

// ------------------------------------------------------------------ categories (FR-09)
export async function categoriesView(root) {
  const body = h("div", {});
  root.append(
    h("div", { class: "page-head" },
      h("div", {}, h("h1", {}, "Categories"), h("p", {}, "Complaints are classified using these categories. Inactive categories are hidden from the submission form.")),
      h("button", { class: "btn", onclick: () => categoryDialog().then((ok) => ok && load()) }, icon("plus"), "Add category")),
    h("section", { class: "card" }, body));

  async function load() {
    clear(body).append(spinner());
    const cats = await api.categories(true);
    clear(body);
    if (!cats.length) return body.append(emptyState("No categories", "Add the first category so users can submit complaints."));
    body.append(h("div", { class: "table-wrap" }, h("table", { class: "table", "aria-label": "Categories" },
      h("thead", {}, h("tr", {}, h("th", {}, "Name"), h("th", {}, "Description"), h("th", {}, "Status"), h("th", {}, h("span", { class: "sr-only" }, "Actions")))),
      h("tbody", {}, cats.map((c) => h("tr", { "data-name": c.name },
        h("td", {}, h("strong", {}, c.name)),
        h("td", { class: "muted" }, c.description || "—"),
        h("td", {}, h("span", { class: `badge ${c.active_flag ? "s-RESOLVED" : "s-CLOSED"}` }, c.active_flag ? "Active" : "Inactive")),
        h("td", { style: "white-space:nowrap" },
          h("button", { class: "btn btn-ghost btn-sm", onclick: () => categoryDialog(c).then((ok) => ok && load()) }, "Edit"),
          h("button", {
            class: "btn btn-secondary btn-sm",
            onclick: async () => {
              try { await api.updateCategory(c.category_id, { active_flag: !c.active_flag }); toast(`${c.name} ${c.active_flag ? "deactivated" : "activated"}`, "success"); load(); }
              catch (err) { toast(err.message, "error"); }
            },
          }, c.active_flag ? "Deactivate" : "Activate"))))))));
  }
  await load();
}

function categoryDialog(existing) {
  const name = h("input", { class: "input", value: existing?.name || "" });
  const description = h("textarea", { class: "input", style: "min-height:80px", maxlength: "500" });
  description.value = existing?.description || "";
  const body = h("div", {},
    field({ id: "cat-name", label: "Name", input: name, required: true }),
    field({ id: "cat-description", label: "Description", input: description, hint: "Optional. Helps users choose the right category." }));
  return modal({
    title: existing ? "Edit category" : "Add category", body, confirmText: existing ? "Save" : "Add category",
    onConfirm: async () => {
      if (!showErrors(body, collectErrors({ "cat-name": validateCategoryName(name.value) }))) return false;
      const payload = { name: name.value.trim(), description: description.value.trim() || null };
      if (existing) await api.updateCategory(existing.category_id, payload);
      else await api.createCategory(payload);
      toast(existing ? "Category updated" : "Category added", "success");
    },
  });
}

// ------------------------------------------------------------------ SLA rules (FR-16, BR-06)
export async function slaView(root) {
  const body = h("div", {});
  root.append(
    h("div", { class: "page-head" },
      h("div", {}, h("h1", {}, "SLA rules"), h("p", {}, "Target resolution time per priority. Changes apply to new complaints and to complaints whose priority is changed."))),
    h("section", { class: "card" }, body));

  async function load() {
    clear(body).append(spinner());
    const rules = await api.slaRules();
    clear(body).append(h("div", { class: "table-wrap" }, h("table", { class: "table", "aria-label": "SLA rules" },
      h("thead", {}, h("tr", {}, h("th", {}, "Priority"), h("th", {}, "Target"), h("th", {}, "Due-soon alert at"), h("th", {}, h("span", { class: "sr-only" }, "Actions")))),
      h("tbody", {}, rules.map((r) => h("tr", { "data-priority": r.priority },
        h("td", {}, priorityBadge(r.priority)),
        h("td", {}, formatMinutes(r.target_minutes)),
        h("td", {}, `${r.approaching_percent}% of target elapsed`),
        h("td", {}, h("button", { class: "btn btn-ghost btn-sm", onclick: () => ruleDialog(r).then((ok) => ok && load()) }, "Edit"))))))));
  }
  await load();
}

function ruleDialog(rule) {
  const hours = h("input", { class: "input", type: "number", min: "1", step: "1", value: String(Math.round(rule.target_minutes / 60) || 1) });
  const percent = h("input", { class: "input", type: "number", min: "1", max: "99", step: "1", value: String(rule.approaching_percent) });
  const body = h("div", {},
    field({ id: "sla-hours", label: "Target (hours)", input: hours, hint: "Between 1 and 2160 hours (90 days)." }),
    field({ id: "sla-percent", label: "Send due-soon alert at (% elapsed)", input: percent }));
  return modal({
    title: `Edit ${PRIORITY_LABEL[rule.priority]} SLA`, body, confirmText: "Save",
    onConfirm: async () => {
      const errors = collectErrors({
        "sla-hours": validatePositiveInt(hours.value, "Target hours", 1, 2160),
        "sla-percent": validatePositiveInt(percent.value, "Alert percentage", 1, 99),
      });
      if (!showErrors(body, errors)) return false;
      await api.updateSlaRule(rule.rule_id, { target_minutes: Number(hours.value) * 60, approaching_percent: Number(percent.value) });
      toast("SLA rule updated", "success");
    },
  });
}
