import random
import time
from typing import Optional
import platform

try:
    import pyperclip  # type: ignore
    _CLIPBOARD_AVAILABLE = True
except Exception:
    _CLIPBOARD_AVAILABLE = False


def human_delay(min_ms: int = 500, max_ms: int = 1500) -> None:
    delay = random.randint(min_ms, max_ms) / 1000.0
    time.sleep(delay)


def fill_slowly(page, selector: str, value: str) -> bool:
    try:
        locator = page.locator(selector)
        if locator.count() == 0:
            return False
        field = locator.first
        field.click()
        human_delay(200, 500)
        field.clear()
        human_delay(100, 300)
        for char in value:
            field.type(char)
            time.sleep(random.uniform(0.05, 0.15))
        human_delay(200, 400)
        return True
    except Exception:
        return False


def type_into_locator_slowly(field, value: str) -> bool:
    try:
        field.click()
        human_delay(200, 500)
        try:
            field.clear()
        except Exception:
            pass
        human_delay(100, 300)
        for char in value:
            field.type(char)
            time.sleep(random.uniform(0.1, 0.2))
        human_delay(200, 400)
        return True
    except Exception:
        return False


def fill_first_present_slowly(page, selectors: list[str], value: Optional[str]) -> bool:
    if not value:
        return False
    for sel in selectors:
        try:
            if fill_slowly(page, sel, value):
                return True
        except Exception:
            continue
    return False 


def paste_text_via_clipboard(page, field, text: str) -> bool:
    try:
        field.click()
        human_delay(120, 220)
        try:
            field.clear()
        except Exception:
            pass
        human_delay(80, 160)

        # Windows-only clipboard paste; otherwise fallback to insert
        if _CLIPBOARD_AVAILABLE and platform.system() == "Windows":
            try:
                pyperclip.copy(text)
                human_delay(60, 120)
                page.keyboard.press("Control+V")
                human_delay(120, 220)
                return True
            except Exception:
                pass

        # Fallback to direct insert if clipboard fails
        page.keyboard.insert_text(text)
        human_delay(120, 220)
        return True
    except Exception:
        return False