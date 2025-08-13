import random
import time
from typing import Optional


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
            time.sleep(random.uniform(0.05, 0.15))
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