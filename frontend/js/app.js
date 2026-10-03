import { api, session, setUnauthorizedHandler } from "./api.js";
import { h, clear, icon, ROLE_LABEL, timeAgo, toast } from "./ui.js";
import { loginView, registerView } from "./views/auth.js";
import { complaintListView, complaintNewView, complaintDetailView } from "./views/complaints.js";
import { dashboardView } from "./views/dashboard.js";
import { usersView, categoriesView, slaView } from "./views/admin.js";
import { notificationsView } from "./views/notifications.js";

const root = document.getElementById("app");
export const state = { user: null };

const ROUTES = [
  { path: /^\/login$/, view: loginView, public: true },
  { path: /^\/register$/, view: registerView, public: true },
  { path: /^\/complaints$/, view: complaintListView, title: "Complaints" },
  { path: /^\/complaints\/new$/, view: complaintNewView, title: "New complaint" },
  { path: /^\/complaints\/([0-9a-f-]{36})$/, view: complaintDetailView, title: "Complaint" },
  { path: /^\/dashboard$/, view: dashboardView, title: "Dashboard", roles: ["STAFF", "ADMIN"] },
  { path: /^\/admin\/users$/, view: usersView, title: "Users", roles: ["ADMIN"] },
  { path: /^\/admin\/categories$/, view: categoriesView, title: "Categories", roles: ["ADMIN"] },
  { path: /^\/admin\/sla$/, view: slaView, title: "SLA rules", roles: ["ADMIN"] },
  { path: /^\/notifications$/, view: notificationsView, title: "Notifications" },
];

export function navigate(hash) {
  if (location.hash === hash) render();
  else location.hash = hash;
}

export function homeFor(user) {
  return user?.role === "ADMIN" ? "#/dashboard" : user?.role === "STAFF" ? "#/complaints?scope=assigned" : "#/complaints";
}

function parseHash() {
  const raw = location.hash.replace(/^#/, "") || "/";
  const [path, query = ""] = raw.split("?");
  return { path, query: new URLSearchParams(query) };
}

setUnauthorizedHandler(() => {
  state.user = null;
  toast("Your session has ended. Please sign in again.", "error");
  navigate("#/login");
});

async function ensureUser() {
  if (state.user) return state.user;
  if (!session.get()?.token) return null;
  try {
    state.user = await api.me();
  } catch {
    session.clear();
    state.user = null;
  }
  return state.user;
}

export async function render() {
  const { path, query } = parseHash();
  const route = ROUTES.find((r) => r.path.test(path));
  const user = await ensureUser();

  if (!route) return navigate(user ? homeFor(user) : "#/login");
  if (route.public) {
    if (user) return navigate(homeFor(user));
    clear(root);
    document.title = "Sign in · Smart Complaint Management";
    return route.view(root, {});
  }
  if (!user) return navigate("#/login");
  if (route.roles && !route.roles.includes(user.role)) return navigate(homeFor(user));

  const params = path.match(route.path).slice(1);
  const content = renderShell(route.title);
  document.title = `${route.title} · Smart Complaint Management`;
  try {
    await route.view(content, { params, query, user });
  } catch (err) {
    clear(content).append(h("div", { class: "alert alert-error" }, err.message || "Something went wrong"));
  }
}

// ------------------------------------------------------------------ shell
function navLink(href, label, iconName) {
  const current = location.hash.split("?")[0];
  const target = href.split("?")[0];
  const active = current === target || (target !== "#/complaints" && current.startsWith(target));
  return h("a", { class: `nav-link${active ? " active" : ""}`, href, "aria-current": active ? "page" : null }, icon(iconName), label);
}

function renderShell(title) {
  const u = state.user;
  const nav = [h("div", { class: "nav-label" }, "Complaints")];
  if (u.role === "USER") {
    nav.push(navLink("#/complaints", "My complaints", "inbox"), navLink("#/complaints/new", "New complaint", "plus"));
  } else if (u.role === "STAFF") {
    nav.push(
      navLink("#/dashboard", "Dashboard", "chart"),
      navLink("#/complaints?scope=assigned", "My queue", "inbox"),
      navLink("#/complaints/new", "New complaint", "plus"),
    );
  } else {
    nav.push(
      navLink("#/dashboard", "Dashboard", "chart"),
      navLink("#/complaints?scope=all", "All complaints", "list"),
      h("div", { class: "nav-label" }, "Administration"),
      navLink("#/admin/users", "Users", "users"),
      navLink("#/admin/categories", "Categories", "tag"),
      navLink("#/admin/sla", "SLA rules", "clock"),
    );
  }

  const shell = h("div", { class: "shell" });
  const bell = h("button", { class: "btn btn-ghost icon-btn", "aria-label": "Notifications", "aria-haspopup": "true", id: "bell" }, icon("bell"));
  const content = h("main", { class: "content", id: "content", tabindex: "-1" });
  const sidebar = h("nav", { class: "sidebar", "aria-label": "Main" },
    h("div", { class: "logo" }, h("div", { class: "logo-mark" }, "SC"), "Smart Complaints"),
    nav,
    h("div", { class: "spacer" }),
    h("div", { class: "me" }, h("strong", {}, u.name), h("span", {}, ROLE_LABEL[u.role] || u.role)),
  );
  sidebar.addEventListener("click", (e) => { if (e.target.closest("a")) shell.classList.remove("nav-open"); });

  shell.append(
    sidebar,
    h("div", { class: "main" },
      h("header", { class: "topbar" },
        h("div", { class: "row-between" },
          h("button", { class: "btn btn-ghost icon-btn menu-btn", "aria-label": "Open menu", onclick: () => shell.classList.toggle("nav-open") }, icon("menu")),
          h("span", { class: "title" }, title)),
        h("div", { class: "topbar-actions" },
          bell,
          h("button", { class: "btn btn-ghost btn-sm", onclick: logout, "aria-label": "Sign out" }, icon("logout"), h("span", {}, "Sign out")),
        ),
      ),
      content,
    ),
  );
  clear(root).append(shell);
  setupNotifications(bell);
  return content;
}

async function logout() {
  await api.logout();
  session.clear();
  state.user = null;
  navigate("#/login");
}

// ------------------------------------------------------------------ notifications popover
let pollTimer = null;
async function refreshBadge(bell) {
  try {
    const data = await api.notifications({ limit: 1 });
    bell.querySelector(".dot-count")?.remove();
    if (data.unread > 0) bell.append(h("span", { class: "dot-count", "data-testid": "unread-count" }, data.unread > 99 ? "99+" : data.unread));
    bell.setAttribute("aria-label", `Notifications, ${data.unread} unread`);
  } catch { /* ignore polling errors */ }
}

function setupNotifications(bell) {
  clearInterval(pollTimer);
  refreshBadge(bell);
  pollTimer = setInterval(() => document.body.contains(bell) && refreshBadge(bell), 30000);
  let pop = null;
  const closePop = () => { pop?.remove(); pop = null; document.removeEventListener("click", outside); };
  const outside = (e) => { if (pop && !pop.contains(e.target) && !bell.contains(e.target)) closePop(); };

  bell.addEventListener("click", async () => {
    if (pop) return closePop();
    pop = h("div", { class: "popover", role: "dialog", "aria-label": "Notifications" }, h("div", { class: "spinner" }));
    bell.closest(".topbar").append(pop);
    setTimeout(() => document.addEventListener("click", outside));
    const data = await api.notifications({ limit: 8 });
    clear(pop).append(
      h("div", { class: "card-head" },
        h("h3", {}, "Notifications"),
        h("button", { class: "btn btn-ghost btn-sm", onclick: async () => { await api.markAllRead(); closePop(); refreshBadge(bell); } }, "Mark all read")),
      h("div", {}, data.items.length
        ? data.items.map((n) => h("a", {
            class: `notif${n.read_status ? "" : " unread"}`,
            href: n.complaint_id ? `#/complaints/${n.complaint_id}` : "#/notifications",
            onclick: async () => { if (!n.read_status) await api.markRead(n.notification_id).catch(() => {}); closePop(); },
          }, h("div", {}, n.message), h("div", { class: "when" }, timeAgo(n.created_at))))
        : h("div", { class: "empty" }, "You're all caught up.")),
      h("a", { class: "notif small", href: "#/notifications", onclick: closePop }, "View all notifications"),
    );
  });
}

window.addEventListener("hashchange", render);
render();
