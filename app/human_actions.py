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


def fill_slowly(page, field, value: str) -> bool:
    try:

        # locator = page.locator(selector)
        # if locator.count() == 0:
        #     return False
        # print(f"[DEBUG] Filling slowly: {selector}")
        # field = locator.first
        human_click(page, field)
        human_delay(500, 1000)
        field.clear()
        human_delay(500, 700)
        for char in value:
            field.type(char)
            time.sleep(random.uniform(0.3, 0.7))
        human_delay(200, 400)
        return True
    except Exception:
        return False


def fill_first_present_slowly(page, selectors: list[str], value: Optional[str]) -> bool:
    if not value:
        return False
    for sel in selectors:
        try:
            if fill_slowly(page, page.locator(sel).first, value):
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
                page.keyboard.press("Control+V")
                human_delay(300, 500)
                return True
            except Exception:
                pass

        # Fallback to direct insert if clipboard fails
        page.keyboard.insert_text(text)
        human_delay(120, 220)
        return True
    except Exception:
        return False


def human_click(page, locator_or_element, min_delay: int = 200, max_delay: int = 1000) -> bool:
    """
    Move mouse to center of element, delay, then click (simulate human click).
    locator_or_element: Playwright Locator or ElementHandle
    """
    try:
        # Support both Locator and ElementHandle
        if hasattr(locator_or_element, 'bounding_box'):
            box = locator_or_element.bounding_box()
        else:
            box = locator_or_element.first.bounding_box()
        if not box:
            return False
        x = box['x'] + box['width'] / 2
        y = box['y'] + box['height'] / 2
        page.mouse.move(x, y, steps=30)
        human_delay(min_delay, max_delay)
        page.mouse.click(x, y)
        human_delay(min_delay, max_delay)
        return True
    except Exception:
        return False