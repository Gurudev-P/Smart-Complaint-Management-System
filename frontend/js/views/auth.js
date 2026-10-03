import { api, session } from "../api.js";
import { h, field, showErrors } from "../ui.js";
import { collectErrors, validateConfirm, validateEmail, validateName, validatePassword } from "../validators.js";
import { state, navigate, homeFor } from "../app.js";

function brandPanel() {
  return h("section", { class: "auth-brand" },
    h("div", { class: "logo" }, h("div", { class: "logo-mark" }, "SC"), "Smart Complaints"),
    h("div", {},
      h("h1", {}, "Every complaint tracked, from first report to resolution."),
      h("p", {}, "Submit issues in seconds, follow their progress live, and let the right team resolve them within their service levels."),
      h("ul", {},
        h("li", {}, "Real-time status and full history"),
        h("li", {}, "Automatic SLA monitoring and escalation"),
        h("li", {}, "Dashboards for staff and administrators")),
    ),
    h("p", { class: "small" }, "PES University · Project 67"),
  );
}

function input(type, autocomplete) {
  return h("input", { class: "input", type, autocomplete });
}

export function loginView(root) {
  const alert = h("div", { class: "alert alert-error", role: "alert", hidden: true });
  const email = input("email", "username");
  const password = input("password", "current-password");
  const submit = h("button", { class: "btn btn-block", type: "submit" }, "Sign in");
  const form = h("form", { novalidate: true, "aria-label": "Sign in" },
    alert,
    field({ id: "email", label: "Email", input: email, required: true }),
    field({ id: "password", label: "Password", input: password, required: true }),
    submit);

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    alert.hidden = true;
    const errors = collectErrors({ email: validateEmail(email.value), password: password.value ? null : "Password is required" });
    if (!showErrors(form, errors)) return;
    submit.disabled = true;
    submit.textContent = "Signing in…";
    try {
      const res = await api.login(email.value.trim(), password.value);
      session.set({ token: res.access_token });
      state.user = res.user;
      navigate(homeFor(res.user));
    } catch (err) {
      alert.textContent = err.message;
      alert.hidden = false;
      password.value = "";
      password.focus();
    } finally {
      submit.disabled = false;
      submit.textContent = "Sign in";
    }
  });

  root.append(h("div", { class: "auth" }, brandPanel(),
    h("section", { class: "auth-panel" }, h("div", { class: "auth-card" },
      h("h2", {}, "Welcome back"),
      h("p", { class: "sub" }, "Sign in to submit and track complaints."),
      form,
      h("p", { class: "auth-switch" }, "New here? ", h("a", { href: "#/register" }, "Create an account")),
    ))));
  email.focus();
}

export function registerView(root) {
  const alert = h("div", { class: "alert alert-error", role: "alert", hidden: true });
  const name = input("text", "name");
  const email = input("email", "email");
  const password = input("password", "new-password");
  const confirm = input("password", "new-password");
  const submit = h("button", { class: "btn btn-block", type: "submit" }, "Create account");
  const form = h("form", { novalidate: true, "aria-label": "Create account" },
    alert,
    field({ id: "name", label: "Full name", input: name, required: true }),
    field({ id: "email", label: "Email", input: email, required: true }),
    field({ id: "password", label: "Password", input: password, hint: "At least 8 characters, with a letter and a digit.", required: true }),
    field({ id: "confirm", label: "Confirm password", input: confirm, required: true }),
    submit);

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    alert.hidden = true;
    const errors = collectErrors({
      name: validateName(name.value),
      email: validateEmail(email.value),
      password: validatePassword(password.value),
      confirm: validateConfirm(password.value, confirm.value),
    });
    if (!showErrors(form, errors)) return;
    submit.disabled = true;
    try {
      await api.register(name.value.trim(), email.value.trim(), password.value);
      const res = await api.login(email.value.trim(), password.value);
      session.set({ token: res.access_token });
      state.user = res.user;
      navigate(homeFor(res.user));
    } catch (err) {
      alert.textContent = err.message;
      alert.hidden = false;
    } finally {
      submit.disabled = false;
    }
  });

  root.append(h("div", { class: "auth" }, brandPanel(),
    h("section", { class: "auth-panel" }, h("div", { class: "auth-card" },
      h("h2", {}, "Create your account"),
      h("p", { class: "sub" }, "It takes less than a minute."),
      form,
      h("p", { class: "auth-switch" }, "Already registered? ", h("a", { href: "#/login" }, "Sign in")),
    ))));
  name.focus();
}
