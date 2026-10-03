// Client-side validation (Software Design §10.1, layer 1).
// Mirrors the server rules for fast feedback; the server remains the security boundary.

export const LIMITS = {
  nameMin: 2, nameMax: 100,
  passwordMin: 8, passwordMax: 128,
  descriptionMin: 10, descriptionMax: 2000,
  resolutionMin: 5, resolutionMax: 4000,
  categoryMin: 2, categoryMax: 100,
};

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

export function validateName(value) {
  const v = (value || "").trim();
  if (!v) return "Name is required";
  if (v.length < LIMITS.nameMin) return `Name must be at least ${LIMITS.nameMin} characters`;
  if (v.length > LIMITS.nameMax) return `Name must be at most ${LIMITS.nameMax} characters`;
  return null;
}

export function validateEmail(value) {
  const v = (value || "").trim();
  if (!v) return "Email is required";
  if (!EMAIL_RE.test(v)) return "Enter a valid email address";
  return null;
}

export function validatePassword(value) {
  const v = value || "";
  if (!v) return "Password is required";
  if (v.length < LIMITS.passwordMin) return `Password must be at least ${LIMITS.passwordMin} characters`;
  if (v.length > LIMITS.passwordMax) return `Password must be at most ${LIMITS.passwordMax} characters`;
  if (!/[A-Za-z]/.test(v) || !/\d/.test(v)) return "Password must contain at least one letter and one digit";
  return null;
}

export function validateConfirm(password, confirm) {
  if (!confirm) return "Confirm your password";
  return password === confirm ? null : "Passwords do not match";
}

export function validateRequired(value, label) {
  return value ? null : `${label} is required`;
}

export function validateText(value, label, min, max) {
  const v = (value || "").trim();
  if (!v) return `${label} is required`;
  if (v.length < min) return `${label} must be at least ${min} characters`;
  if (v.length > max) return `${label} must be at most ${max} characters`;
  return null;
}

export const validateDescription = (v) => validateText(v, "Description", LIMITS.descriptionMin, LIMITS.descriptionMax);
export const validateResolution = (v) => validateText(v, "Resolution details", LIMITS.resolutionMin, LIMITS.resolutionMax);
export const validateCategoryName = (v) => validateText(v, "Category name", LIMITS.categoryMin, LIMITS.categoryMax);

export function validatePositiveInt(value, label, min, max) {
  const n = Number(value);
  if (value === "" || value === null || value === undefined || !Number.isInteger(n)) return `${label} must be a whole number`;
  if (n < min || n > max) return `${label} must be between ${min} and ${max}`;
  return null;
}

/** Runs {field: errorOrNull} and returns only the failures. */
export function collectErrors(map) {
  return Object.fromEntries(Object.entries(map).filter(([, v]) => v));
}
