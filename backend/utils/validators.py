"""
Input validation helpers shared by auth, profile and admin routes.

Every value that ends up inside a MongoDB filter MUST pass through one of
these first: a JSON body like {"email": {"$gt": ""}} is otherwise a query
operator, not a string (NoSQL injection).
"""
import re

from config import PASSWORD_MIN_LENGTH, PASSWORD_MAX_LENGTH

# Pragmatic email shape check (RFC 5322 is not worth implementing here); the
# OTP / reset flows are what actually prove ownership.
_EMAIL_RE = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,253}\.[^@\s]{2,63}$")


class ValidationError(ValueError):
    """Raised with a short machine-readable code (e.g. 'invalid_email')."""


def normalize_email(value):
    """Return a lower-cased, trimmed email or raise ValidationError('invalid_email')."""
    if not isinstance(value, str):
        raise ValidationError("invalid_email")
    email = value.strip().lower()
    if len(email) > 254 or not _EMAIL_RE.match(email):
        raise ValidationError("invalid_email")
    return email


def validate_password(value):
    """Enforce the password policy for NEW passwords (signup / change / reset)."""
    if not isinstance(value, str):
        raise ValidationError("invalid_password")
    if len(value) < PASSWORD_MIN_LENGTH:
        raise ValidationError("password_too_short")
    if len(value) > PASSWORD_MAX_LENGTH:
        raise ValidationError("password_too_long")
    if value.strip() == "":
        raise ValidationError("invalid_password")
    return value


def clean_str(value, field, max_len=200, required=False, allow_empty=True):
    """Coerce an optional free-text field to a trimmed string with a length cap."""
    if value is None:
        if required:
            raise ValidationError(f"missing_{field}")
        return None
    if not isinstance(value, (str, int, float)) or isinstance(value, bool):
        raise ValidationError(f"invalid_{field}")
    s = str(value).strip()
    if not s and (required or not allow_empty):
        raise ValidationError(f"missing_{field}")
    if len(s) > max_len:
        raise ValidationError(f"{field}_too_long")
    return s


def is_object_id(value):
    """True if `value` is a 24-hex-char string (a valid ObjectId)."""
    return isinstance(value, str) and bool(re.fullmatch(r"[0-9a-fA-F]{24}", value))


def safe_regex(term, max_len=100):
    """Escape a user search term for use in a $regex (prevents ReDoS / regex injection)."""
    if not isinstance(term, str):
        return ""
    return re.escape(term.strip()[:max_len])
