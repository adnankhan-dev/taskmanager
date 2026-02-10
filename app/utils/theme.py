import re


HEX_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")

BUTTON_COLOR_DEFAULTS = {
    "ui_btn_primary": "#0d6efd",
    "ui_btn_secondary": "#6c757d",
    "ui_btn_success": "#198754",
    "ui_btn_warning": "#ffc107",
    "ui_btn_danger": "#dc3545",
}


def sanitize_hex_color(value: str | None, fallback: str) -> str:
    if not value:
        return fallback

    cleaned = value.strip()
    if HEX_COLOR_RE.fullmatch(cleaned):
        return cleaned.lower()

    return fallback
