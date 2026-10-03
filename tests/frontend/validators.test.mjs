// Run with: node --test tests/frontend/
import { test } from "node:test";
import assert from "node:assert/strict";
import {
  validateName, validateEmail, validatePassword, validateConfirm, validateDescription,
  validateResolution, validateCategoryName, validatePositiveInt, validateRequired, collectErrors,
} from "../../frontend/js/validators.js";

test("name rules", () => {
  assert.equal(validateName("  "), "Name is required");
  assert.match(validateName("A"), /at least 2/);
  assert.equal(validateName("Asha"), null);
  assert.match(validateName("x".repeat(101)), /at most 100/);
});

test("email rules", () => {
  assert.equal(validateEmail(""), "Email is required");
  for (const bad of ["plain", "a@b", "a b@c.com", "@x.com"]) assert.ok(validateEmail(bad), bad);
  assert.equal(validateEmail(" user@college.edu "), null);
});

test("password rules match the server", () => {
  assert.ok(validatePassword(""));
  assert.match(validatePassword("Ab1"), /at least 8/);
  assert.match(validatePassword("abcdefgh"), /letter and one digit/);
  assert.match(validatePassword("12345678"), /letter and one digit/);
  assert.equal(validatePassword("abcdefg1"), null);
  assert.equal(validateConfirm("abcdefg1", "abcdefg2"), "Passwords do not match");
  assert.equal(validateConfirm("abcdefg1", "abcdefg1"), null);
});

test("complaint description boundaries (10–2000 after trimming)", () => {
  assert.ok(validateDescription("   short   "));
  assert.equal(validateDescription("x".repeat(10)), null);
  assert.equal(validateDescription("x".repeat(2000)), null);
  assert.ok(validateDescription("x".repeat(2001)));
});

test("resolution, category and numeric rules", () => {
  assert.ok(validateResolution("   "));
  assert.equal(validateResolution("Fixed"), null);
  assert.ok(validateCategoryName("A"));
  assert.equal(validatePositiveInt("24", "Hours", 1, 2160), null);
  for (const bad of ["", "0", "2161", "1.5", "abc"]) assert.ok(validatePositiveInt(bad, "Hours", 1, 2160), bad);
  assert.equal(validateRequired("", "Category"), "Category is required");
});

test("collectErrors keeps only failures", () => {
  assert.deepEqual(collectErrors({ a: null, b: "bad" }), { b: "bad" });
});
