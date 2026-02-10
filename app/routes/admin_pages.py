from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app.ui import templates
from app.models.user import User
from app.models.app_setting import AppSetting
from app.utils.theme import BUTTON_COLOR_DEFAULTS, sanitize_hex_color

router = APIRouter(prefix="/ui/admin")

THEMES = {
    "classic": {
        "label": "Classic Blue",
        "description": "Current default look with blue navigation."
    },
    "ocean": {
        "label": "Ocean Teal",
        "description": "Cool teal and slate tones."
    },
    "emerald": {
        "label": "Emerald Green",
        "description": "Green-accented look for admin branding."
    },
}


@router.get("/theme")
def theme_settings_form(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if not user or user.role != "admin":
        return RedirectResponse("/dashboard", status_code=303)

    current_setting = (
        db.query(AppSetting)
        .filter(AppSetting.key == "ui_theme")
        .first()
    )
    current_theme = current_setting.value if current_setting and current_setting.value in THEMES else "classic"
    button_settings = (
        db.query(AppSetting)
        .filter(AppSetting.key.in_(list(BUTTON_COLOR_DEFAULTS.keys())))
        .all()
    )
    button_map = {item.key: item.value for item in button_settings}
    button_colors = {
        key: sanitize_hex_color(button_map.get(key), default)
        for key, default in BUTTON_COLOR_DEFAULTS.items()
    }

    return templates.TemplateResponse(
        "admin/theme.html",
        {
            "request": request,
            "user": user,
            "themes": THEMES,
            "current_theme": current_theme,
            "button_colors": button_colors
        }
    )


@router.post("/theme")
def theme_settings_submit(
    theme: str = Form(...),
    ui_btn_primary: str = Form(...),
    ui_btn_secondary: str = Form(...),
    ui_btn_success: str = Form(...),
    ui_btn_warning: str = Form(...),
    ui_btn_danger: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if not user or user.role != "admin":
        return RedirectResponse("/dashboard", status_code=303)

    if theme not in THEMES:
        return RedirectResponse("/ui/admin/theme", status_code=303)

    setting = (
        db.query(AppSetting)
        .filter(AppSetting.key == "ui_theme")
        .first()
    )
    if not setting:
        setting = AppSetting(key="ui_theme", value=theme)
        db.add(setting)
    else:
        setting.value = theme

    submitted_colors = {
        "ui_btn_primary": ui_btn_primary,
        "ui_btn_secondary": ui_btn_secondary,
        "ui_btn_success": ui_btn_success,
        "ui_btn_warning": ui_btn_warning,
        "ui_btn_danger": ui_btn_danger,
    }

    for key, default in BUTTON_COLOR_DEFAULTS.items():
        color_value = sanitize_hex_color(submitted_colors.get(key), default)
        color_setting = (
            db.query(AppSetting)
            .filter(AppSetting.key == key)
            .first()
        )
        if not color_setting:
            db.add(AppSetting(key=key, value=color_value))
        else:
            color_setting.value = color_value

    db.commit()
    return RedirectResponse("/ui/admin/theme", status_code=303)
