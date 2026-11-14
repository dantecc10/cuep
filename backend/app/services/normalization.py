import re
import unicodedata


def normalize_email(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().lower()
    return normalized or None


def _digits(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        raw = str(int(value))
    else:
        raw = str(value).strip()
        if raw.endswith(".0"):
            raw = raw[:-2]
    return re.sub(r"\D", "", raw)


def normalize_phone_mx(value: object) -> str | None:
    """Return a 10 digit Mexican phone or None when the value is empty.

    Accepts local numbers, 52 + 10 digits and 521 + 10 digits. Values with a
    different length are rejected so we never silently store a truncated phone.
    """
    digits = _digits(value)
    if not digits:
        return None
    if len(digits) == 13 and digits.startswith("521"):
        digits = digits[3:]
    elif len(digits) == 12 and digits.startswith("52"):
        digits = digits[2:]
    elif len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) != 10:
        raise ValueError("El teléfono debe tener 10 dígitos (México).")
    return digits


def extract_phone(value: object) -> str | None:
    if value is None:
        return None
    text = str(value)
    matches = re.findall(r"(?:\+?52\s*)?(?:1\s*)?(\d{10})", re.sub(r"[^\d+]", " ", text))
    if not matches:
        return None
    try:
        return normalize_phone_mx(matches[-1])
    except ValueError:
        return None


def split_emergency_contact(value: str | None) -> tuple[str | None, str | None]:
    if not value:
        return None, None
    phone = extract_phone(value)
    if phone is None:
        return value.strip() or None, None
    name = re.sub(r"[\d()+\-.]{7,}", " ", value)
    name = re.sub(r"\s+", " ", name).strip(" ,;/-")
    return name or None, phone


def normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = re.sub(r"\s+", " ", value).strip()
    return normalized or None


def name_key(value: str | None) -> str:
    normalized = normalize_text(value) or ""
    decomposed = unicodedata.normalize("NFKD", normalized)
    without_accents = "".join(char for char in decomposed if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", without_accents).casefold().strip()


def initial(value: str | None) -> str:
    normalized = normalize_text(value)
    if not normalized:
        return "X"
    return normalized[0].upper()
