const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const usernamePattern = /^[A-Za-z0-9_]{3,32}$/;

export function validateRegistration(values) {
  const errors = {};
  if (!usernamePattern.test(values.username.trim())) {
    errors.username = "Use 3-32 letters, numbers, or underscores.";
  }
  if (!emailPattern.test(values.email.trim())) {
    errors.email = "Enter a valid email address.";
  }
  if (
    !values.full_name.trim() ||
    Array.from(values.full_name.trim()).length > 100
  ) {
    errors.full_name = "Full name must be 1-100 characters.";
  }
  const passwordLength = Array.from(values.password).length;
  if (passwordLength < 12 || passwordLength > 128) {
    errors.password = "Use a password between 12 and 128 characters.";
  }
  return errors;
}

export function validateProfile(values) {
  const errors = {};
  if (
    !values.full_name.trim() ||
    Array.from(values.full_name.trim()).length > 100
  ) {
    errors.full_name = "Full name must be 1-100 characters.";
  }
  if (
    values.email.trim().length > 254 ||
    !emailPattern.test(values.email.trim())
  ) {
    errors.email = "Enter a valid email address.";
  }
  return errors;
}
