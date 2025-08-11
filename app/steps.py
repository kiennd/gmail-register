from datetime import date
import random
from typing import Optional

from .human_actions import human_delay, fill_first_present_slowly, fill_slowly

MONTH_LABELS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]


def click_next(page) -> None:
    try:
        page.get_by_role("button", name="Next").click()
        return
    except Exception:
        pass
    try:
        page.locator('button:has-text("Next")').first.click()
        return
    except Exception:
        pass
    try:
        page.locator('div[role="button"]:has-text("Next")').first.click()
    except Exception:
        raise RuntimeError("Could not locate a 'Next' button. UI may have changed or is localized.")


def select_first_present_by_label(page, selectors: list[str], label: str) -> bool:
    for sel in selectors:
        try:
            locator = page.locator(sel)
            if locator.count() > 0:
                try:
                    locator.first.select_option(label=label)
                    return True
                except Exception:
                    return False
        except Exception:
            continue
    return False


def choose_dropdown(page, field_label: str, option_text: str) -> bool:
    if select_by_label_if_present(page, field_label, option_text):
        return True
    try:
        combo = page.get_by_role("combobox", name=field_label)
        if combo.count() == 0:
            combo = page.get_by_role("button", name=field_label)
        if combo.count() == 0:
            combo = page.get_by_label(field_label)
        if combo.count() > 0:
            combo.first.click()
            try:
                page.get_by_role("option", name=option_text).first.click()
            except Exception:
                page.locator(f'text="{option_text}"').first.click()
            return True
    except Exception:
        pass
    return False


def select_by_label_if_present(page, field_label: str, option_label: str) -> bool:
    try:
        loc = page.get_by_label(field_label)
        if loc.count() > 0:
            loc.first.select_option(label=option_label)
            return True
    except Exception:
        pass
    return False


def fill_by_label_if_present(page, field_label: str, value: str) -> bool:
    try:
        loc = page.get_by_label(field_label)
        if loc.count() > 0:
            loc.first.fill(value)
            return True
    except Exception:
        pass
    return False


def maybe_fill_basic_info(page) -> bool:
    try:
        for _ in range(10):
            if page.get_by_label("Month").count() or page.get_by_role("heading", name="Basic information").count():
                break
            page.wait_for_timeout(300)

        today = date.today()
        age = random.randint(19, 40)
        year_val = today.year - age
        month_idx = random.randint(1, 12)
        day_val = random.randint(1, 28)
        month_label = MONTH_LABELS[month_idx - 1]
        gender_label = random.choice(["Male", "Female", "Rather not say"])

        for attempt in range(5):
            ok_month = choose_dropdown(page, "Month", month_label) or select_first_present_by_label(
                page, ['select[name="month"]', 'select#month', 'select[aria-label="Month"]'], month_label
            )
            human_delay(300, 500)
            
            ok_day = False
            for day_sel in ['input[name="day"]', 'input#day', 'input[aria-label="Day"]', 'input[placeholder="Day"]']:
                try:
                    day_field = page.locator(day_sel)
                    if day_field.count() > 0:
                        day_field.first.click()
                        day_field.first.clear()
                        day_field.first.fill(str(day_val))
                        ok_day = True
                        break
                except Exception:
                    continue
            if not ok_day:
                ok_day = fill_by_label_if_present(page, "Day", str(day_val))
            human_delay(300, 500)
            
            ok_year = fill_by_label_if_present(page, "Year", str(year_val)) or True
            human_delay(300, 500)
            
            ok_gender = choose_dropdown(page, "Gender", gender_label)
            
            if ok_month and ok_day and ok_year and ok_gender:
                break
            elif attempt < 4:
                page.wait_for_timeout(500)

        human_delay(800, 1200)
        click_next(page)
        return True
    except Exception:
        return False


def maybe_fill_username_page(page, username: str) -> bool:
    try:
        detected = False
        for _ in range(10):
            if page.get_by_label("Username").count() or page.get_by_role("heading", name="How you'll sign in").count():
                detected = True
                break
            page.wait_for_timeout(300)
        if not detected:
            return False

        attempt_username = username
        for _ in range(5):
            try:
                filled = fill_first_present_slowly(page, [
                    'input[name="Username"]', 'input#username', 'input[aria-label="Username"]'
                ], attempt_username)
                if not filled and page.get_by_label("Username").count():
                    fill_slowly(page, 'input[aria-label="Username"]', attempt_username)
            except Exception:
                pass

            human_delay(800, 1200)
            click_next(page)

            page.wait_for_timeout(1000)
            taken = False
            try:
                if page.locator('text="That username is taken"').count() or page.locator('text="Try another"').count():
                    taken = True
            except Exception:
                taken = False

            if not taken:
                return True

            suffix = str(random.randint(100, 9999))
            attempt_username = f"{username}{suffix}"
            human_delay(500, 1000)

        return True
    except Exception:
        return False


def maybe_fill_password_page(page, password: str) -> bool:
    try:
        for _ in range(10):
            if (page.get_by_label("Password").count() or 
                page.get_by_label("Create a password").count() or 
                page.locator('input[name="Passwd"], input#passwd').count() or
                page.locator('input[type="password"]').count()):
                break
            page.wait_for_timeout(300)

        filled_password = False
        filled_confirm = False

        if page.get_by_label("Password").count():
            try:
                page.get_by_label("Password").first.click()
                page.get_by_label("Password").first.fill(password)
                filled_password = True
                human_delay(400, 700)
            except Exception:
                pass
        if page.get_by_label("Confirm").count():
            try:
                page.get_by_label("Confirm").first.click()
                page.get_by_label("Confirm").first.fill(password)
                filled_confirm = True
                human_delay(400, 700)
            except Exception:
                pass

        if not filled_password or not filled_confirm:
            pw_inputs = page.locator('input[type="password"]').all()
            if len(pw_inputs) >= 2:
                try:
                    if not filled_password:
                        pw_inputs[0].click(); pw_inputs[0].fill(password)
                        filled_password = True
                        human_delay(400, 700)
                    if not filled_confirm:
                        pw_inputs[1].click(); pw_inputs[1].fill(password)
                        filled_confirm = True
                        human_delay(400, 700)
                except Exception:
                    pass

        if not filled_password:
            filled_password = fill_first_present_slowly(page, [
                'input[name="Passwd"]', 'input#passwd', 'input[type="password"]'
            ], password)
            human_delay(400, 700)
        if not filled_confirm:
            filled_confirm = fill_first_present_slowly(page, [
                'input[name="ConfirmPasswd"]', 'input#confirm-passwd', 'input[type="password"]:nth-of-type(2)'
            ], password)

        if filled_password and filled_confirm:
            human_delay(800, 1200)
            click_next(page)
            return True
        elif filled_password or filled_confirm:
            return True
        return False
    except Exception:
        return False 