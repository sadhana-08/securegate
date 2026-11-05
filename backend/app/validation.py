import re


USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,32}$")
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
PASSWORD_MIN_LENGTH = 12
PASSWORD_MAX_LENGTH = 128


def validate_password(password):
    if not isinstance(password, str) or not (
        PASSWORD_MIN_LENGTH <= len(password) <= PASSWORD_MAX_LENGTH
    ):
        return (
            f"Password must be between {PASSWORD_MIN_LENGTH} and "
            f"{PASSWORD_MAX_LENGTH} characters."
        )
    if not any(character.islower() for character in password):
        return "Password must include a lowercase letter."
    if not any(character.isupper() for character in password):
        return "Password must include an uppercase letter."
    if not any(character.isdigit() for character in password):
        return "Password must include a number."
    if not any(not character.isalnum() for character in password):
        return "Password must include a symbol."
    return None


def validate_registration(data):
    errors = {}
    username = data.get("username")
    email = data.get("email")
    full_name = data.get("full_name")
    password = data.get("password")

    if not isinstance(username, str) or not USERNAME_PATTERN.fullmatch(username.strip()):
        errors["username"] = "Use 3-32 letters, numbers, or underscores."

    if (
        not isinstance(email, str)
        or len(email.strip()) > 254
        or not EMAIL_PATTERN.fullmatch(email.strip())
    ):
        errors["email"] = "Enter a valid email address."

    if not isinstance(full_name, str):
        errors["full_name"] = "Full name is required."
    else:
        normalized_name = full_name.strip()
        if (
            not normalized_name
            or len(normalized_name) > 100
            or not all(character.isprintable() for character in normalized_name)
        ):
            errors["full_name"] = "Full name must be 1-100 printable characters."

    password_error = validate_password(password)
    if password_error:
        errors["password"] = password_error

    return errors
