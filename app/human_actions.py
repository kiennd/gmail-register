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


def fill_slowly(page, field, value: str, min_delay: float = 0.2, max_delay: float = 0.4) -> bool:
    try:
        human_click(page, field)
        human_delay(200, 700)
        field.clear()
        human_delay(200, 700)
        for char in value:
            field.type(char)
            time.sleep(random.uniform(min_delay, max_delay))
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
    Move mouse to center of element with human-like movement, delay, then click.
    Uses Bezier curves, random noise, and realistic click simulation for natural behavior.
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
        
        target_x = box['x'] + box['width'] / 2
        target_y = box['y'] + box['height'] / 2
        
        # Get current mouse position (approximate center of viewport if unknown)
        viewport = page.viewport_size
        start_x = viewport['width'] / 2 if viewport else 0
        start_y = viewport['height'] / 2 if viewport else 0
        
        # Add minimal randomness to target position (like human aiming)
        target_x += random.uniform(-2, 2)
        target_y += random.uniform(-1, 1)
        
        # Create smoother control points for Bezier curve
        # Reduce curve by placing control points closer to the straight line
        control_x = start_x + (target_x - start_x) * 0.5 + random.uniform(-5, 5)
        control_y = start_y + (target_y - start_y) * 0.5 + random.uniform(-4, 4)
        
        # Generate much smoother path with more points
        steps = random.randint(25, 40)  # More steps for smoother movement
        
        for i in range(1, steps + 1):
            t = i / steps
            
            # Quadratic Bezier curve for smooth movement
            x = (1 - t)**2 * start_x + 2 * (1 - t) * t * control_x + t**2 * target_x
            y = (1 - t)**2 * start_y + 2 * (1 - t) * t * control_y + t**2 * target_y
            
            # Add very small random noise to each step (minimal hand tremor)
            x += random.uniform(-0.8, 0.8)
            y += random.uniform(-0.5, 0.5)
            
            # Move mouse to this point
            page.mouse.move(x, y)
            
            # Shorter, more consistent delays for smoother movement
            delay = random.uniform(2, 5)
            page.wait_for_timeout(delay)
        
        # Small pause before clicking (like human aiming and preparation)
        human_delay(min_delay // 4, max_delay // 4)
        
        # Simulate realistic human click behavior
        click_x = target_x + random.uniform(-0.5, 0.5)
        click_y = target_y + random.uniform(-0.5, 0.5)
        
        # Simulate mouse down with slight pressure variation
        page.mouse.down(button="left")
        
        # Small delay to simulate pressure holding (like human finger)
        pressure_delay = random.uniform(6, 18)
        page.wait_for_timeout(pressure_delay)
        
        # Simulate mouse up (release)
        page.mouse.up(button="left")
        
        # Sometimes add a tiny "bounce" after click (like human finger recoil)
        if random.random() < 0.25:  # 25% chance, reduced for smoother experience
            bounce_x = click_x + random.uniform(-1.5, 1.5)
            bounce_y = click_y + random.uniform(-1, 1)
            page.mouse.move(bounce_x, bounce_y)
            page.wait_for_timeout(random.uniform(8, 20))
        
        # Delay after click (like human reaction time)
        human_delay(min_delay, max_delay)
        return True
        
    except Exception:
        return False