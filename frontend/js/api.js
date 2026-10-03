// Thin REST client for /api/v1. Stores the bearer token for the browser tab only.
const BASE = "/api/v1";
const KEY = "scms.session";

export class ApiError extends Error {
  constructor(status, detail, errors) {
    super(detail || `Request failed (${status})`);
    this.status = status;
    this.errors = errors || [];
  }
}

export const session = {
  get() {
    try { return JSON.parse(sessionStorage.getItem(KEY)); } catch { return null; }
  },
  set(value) {
    try { sessionStorage.setItem(KEY, JSON.stringify(value)); } catch { /* storage unavailable */ }
  },
  clear() {
    try { sessionStorage.removeItem(KEY); } catch { /* ignore */ }
  },
};

let onUnauthorized = () => {};
export function setUnauthorizedHandler(fn) { onUnauthorized = fn; }

function qs(params = {}) {
  const sp = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null || v === "" || v === false) continue;
    if (Array.isArray(v)) v.forEach((x) => sp.append(k, x));
    else sp.append(k, v);
  }
  const s = sp.toString();
  return s ? `?${s}` : "";
}

export async function request(method, path, { body, params, raw } = {}) {
  const headers = { Accept: "application/json" };
  const s = session.get();
  if (s?.token) headers.Authorization = `Bearer ${s.token}`;
  if (body !== undefined) headers["Content-Type"] = "application/json";
  let res;
  try {
    res = await fetch(BASE + path + qs(params), { method, headers, body: body === undefined ? undefined : JSON.stringify(body) });
  } catch {
    throw new ApiError(0, "Cannot reach the server. Check your connection and try again.");
  }
  if (res.status === 401 && s?.token && !path.startsWith("/auth/login")) {
    session.clear();
    onUnauthorized();
  }
  if (raw && res.ok) return res;
  if (res.status === 204) return null;
  let data = null;
  try { data = await res.json(); } catch { /* non-JSON */ }
  if (!res.ok) throw new ApiError(res.status, data?.detail || res.statusText, data?.errors);
  return data;
}

export const api = {
  login: (email, password) => request("POST", "/auth/login", { body: { email, password } }),
  register: (name, email, password) => request("POST", "/auth/register", { body: { name, email, password } }),
  me: () => request("GET", "/auth/me"),
  logout: () => request("POST", "/auth/logout").catch(() => null),

  complaints: (params) => request("GET", "/complaints", { params }),
  complaint: (id) => request("GET", `/complaints/${id}`),
  createComplaint: (body) => request("POST", "/complaints", { body }),
  updateComplaint: (id, body) => request("PATCH", `/complaints/${id}`, { body }),
  changeStatus: (id, new_status, expected_status) => request("PATCH", `/complaints/${id}/status`, { body: { new_status, expected_status } }),
  assign: (id, staff_id) => request("POST", `/complaints/${id}/assign`, { body: { staff_id } }),
  resolve: (id, resolution_details) => request("POST", `/complaints/${id}/resolve`, { body: { resolution_details } }),

  categories: (include_inactive) => request("GET", "/categories", { params: { include_inactive } }),
  createCategory: (body) => request("POST", "/categories", { body }),
  updateCategory: (id, body) => request("PATCH", `/categories/${id}`, { body }),

  users: (params) => request("GET", "/users", { params }),
  createUser: (body) => request("POST", "/users", { body }),
  updateUser: (id, body) => request("PATCH", `/users/${id}`, { body }),

  slaRules: () => request("GET", "/sla/rules"),
  updateSlaRule: (id, body) => request("PATCH", `/sla/rules/${id}`, { body }),
  runSlaCheck: () => request("POST", "/sla/check"),

  notifications: (params) => request("GET", "/notifications", { params }),
  markRead: (id) => request("PATCH", `/notifications/${id}/read`),
  markAllRead: () => request("POST", "/notifications/read-all"),

  summary: (params) => request("GET", "/reports/summary", { params }),
  reportCsv: (params) => request("GET", "/reports/complaints.csv", { params, raw: true }),
};
