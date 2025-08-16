from datetime import date
import re
import random
from typing import Optional

from .human_actions import human_delay, fill_first_present_slowly, fill_slowly, paste_text_via_clipboard, human_click

MONTH_LABELS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]


def click_next(page) -> None:
    print("[DEBUG] Clicking Next button...")
    labels = ["Next", "Tiếp theo", "Siguiente", "Suivant", "Weiter", "Avanti", "Далее"]
    for text in labels:
        try:
            for selector in [
                page.get_by_role("button", name=text),
                page.locator(f'button:has-text("{text}")'),
                page.locator(f'div[role="button"]:has-text("{text}")'),
            ]:
                if selector.count():
                    print(f"[DEBUG] Found Next button with text: {text}")
                    human_click(page, selector.first)
                    return
        except Exception:
            continue

    raise RuntimeError("Could not locate a Next/Submit button.")


def is_verification_block_page(page) -> bool:
    print("[DEBUG] Checking for verification block page...")
    block_texts = [
        "Verify some info before creating an account",
        "Scan the QR code with your phone",
        "Confirm you're not a robot",
        "Get a verification code sent to your phone",
        "Xác minh một số thông tin trước khi tạo tài khoản",
        "Quét mã QR bằng điện thoại của bạn",
        "Xác nhận bạn không phải là robot",
        "Gửi mã xác minh đến điện thoại của bạn",
        "Xác nhận bạn không phải là rô bốt"
    ]
    try:
        # Robust role-based detection for the heading
        try:
            if page.get_by_role("heading", name=re.compile(r"verify some info", re.I)).count() > 0:
                print("[DEBUG] Found heading role indicating verification block")
                return True
        except Exception:
            pass
        try:
            h = page.locator("#headingText")
            if h.count() and re.search(r"verify some info", (h.first.inner_text() or ""), re.I):
                print("[DEBUG] Found #headingText with verification text")
                return True
        except Exception:
            pass
        for text in block_texts:
            if page.locator(f'text="{text}"').count() > 0:
                print(f"[DEBUG] Found verification block text: {text}")
                return True
        # QR code heuristic
        if page.locator('img[alt*="QR" i], canvas[aria-label*="QR" i]').count() > 0:
            print("[DEBUG] Found QR code elements - verification block detected")
            return True
        print("[DEBUG] No verification block detected")
        return False
    except Exception as e:
        print(f"[DEBUG] Error checking verification block: {e}")
        return False


def maybe_choose_recommended_email(page) -> str | None:
    print("[DEBUG] Checking for email recommendation page...")
    try:
        headings = ["Choose your Gmail address", "Chọn địa chỉ Gmail của bạn"]
        detected = False
        for _ in range(10):
            for h in headings:
                if page.get_by_role("heading", name=h).count():
                    print(f"[DEBUG] Found email recommendation page with heading: {h}")
                    detected = True; break
            if detected: break
            page.wait_for_timeout(200)
        if not detected:
            # Heuristic: presence of usernameRadio inputs indicates recommendation screen
            try:
                if page.locator('input[name="usernameRadio"]').count() > 0:
                    print("[DEBUG] Heuristic: Found usernameRadio inputs; assuming recommendation page")
                    detected = True
            except Exception:
                pass
        if not detected:
            print("[DEBUG] No email recommendation page detected")
            return None

        # Prefer direct input[name="usernameRadio"] and skip the 'custom' option
        selected_local = None
        try:
            options = page.locator('input[name="usernameRadio"]').all()
            for opt in options:
                try:
                    val = (opt.get_attribute("value") or "").strip()
                    if not val or val.lower() == "custom":
                        continue
                    opt.check()
                    selected_local = val
                    print(f"[DEBUG] Selected suggested username local-part via input: {selected_local}")
                    break
                except Exception:
                    continue
        except Exception:
            pass

        # Fallback: role=radio if direct inputs fail
        if not selected_local:
            radios = page.get_by_role("radio")
            if radios.count() == 0:
                print("[DEBUG] No radio options found")
                return None
            first = radios.first
            try:
                suggested = first.get_attribute("aria-label") or first.inner_text()
                print(f"[DEBUG] Suggested email: {suggested}")
                if suggested and "@" in suggested:
                    selected_local = suggested.split("@", 1)[0].strip()
            except Exception:
                print("[DEBUG] Could not extract suggested email text")
            human_click(page, first)
            human_delay(200, 400)
            print("[DEBUG] Selected first radio option via role=radio")

        click_next(page); human_delay(600, 900)

        if selected_local:
            print(f"[DEBUG] Using selected local part: {selected_local}")
            return selected_local
        print("[DEBUG] Could not extract local part from suggested email")
        return None
    except Exception as e:
        print(f"[DEBUG] Error in email recommendation: {e}")
        return None


def fill_by_label_if_present(page, field_label: str, value: str) -> bool:
    try:
        loc = page.get_by_label(field_label)
        if loc.count() > 0:
            try:
                return fill_slowly(page, loc.first, value)
            except Exception:
                loc.first.fill(value); return True
    except Exception:
        pass
    return False



def first_present_label(page, labels: list[str]) -> str | None:
    for lab in labels:
        try:
            if page.get_by_label(lab).count() > 0:
                return lab
        except Exception:
            continue
    return None


def choose_month(page, month_label: str, month_idx: int) -> bool:
    print(f"[DEBUG] Choosing month: {month_label} (index {month_idx})")
    try:
        # Try localized comboboxes by accessible name or label
        for label in ["Month", "Tháng"]:
            for opener in [page.get_by_role("combobox", name=label), page.get_by_label(label)]:
                try:
                    if opener.count() > 0:
                        print(f"[DEBUG] Found month combobox via '{label}', clicking...")
                        human_click(page, opener.first)
                        human_delay(500, 800)  # Wait longer for dropdown to open
                        
                        try:
                            # Try multiple approaches to find and select month
                            
                            # Approach 1: Try to find month by text content
                            month_texts = [str(month_idx), month_label, f"{month_idx:02d}"]
                            for month_text in month_texts:
                                try:
                                    month_option = page.locator(f'option:has-text("{month_text}"), option[value="{month_text}"]')
                                    if month_option.count() > 0:
                                        print(f"[DEBUG] Found month option by text: {month_text}")
                                        human_click(page, month_option.first)
                                        human_delay(200, 400)
                                        return True
                                except Exception:
                                    continue
                            
                            # Approach 2: Try to find all options and click by index
                            print(f"[DEBUG] Trying to find month options by index...")
                            month_options = page.locator("option")
                            option_count = month_options.count()
                            print(f"[DEBUG] Found {option_count} month options")
                            
                            if option_count >= month_idx:
                                target_month = month_options.nth(month_idx - 1)
                                print(f"[DEBUG] Clicking month option at index {month_idx - 1}")
                                human_click(page, target_month)
                                human_delay(200, 400)
                                return True
                            
                            # Approach 3: Try to find by aria-label or role
                            try:
                                aria_month = page.locator(f'[role="option"]:has-text("{month_idx}"), [role="option"]:has-text("{month_label}")')
                                if aria_month.count() > 0:
                                    print(f"[DEBUG] Found month option by aria-label")
                                    human_click(page, aria_month.first)
                                    human_delay(200, 400)
                                    return True
                            except Exception:
                                pass
                                
                        except Exception as e:
                            print(f"[DEBUG] Month selection failed: {e}")
                            pass
                    
                except Exception:
                    continue
        
        # Try select element fallbacks
        print("[DEBUG] Trying month select elements...")
        for sel in ['select[name="month"]', 'select#month', 'select[aria-label="Month"]', 'select[aria-label="Tháng"]']:
            try:
                loc = page.locator(sel)
                if loc.count() > 0:
                    print(f"[DEBUG] Found select element: {sel}")
                    loc.first.select_option(index=month_idx - 1)
                    print(f"[DEBUG] Selected month by index: {month_idx - 1}")
                    return True
            except Exception:
                continue
        
        print("[DEBUG] Could not select month")
        return False
        
    except Exception as e:
        print(f"[DEBUG] Error choosing month: {e}")
        return False


def pick_gender_any(page) -> bool:
    print("[DEBUG] Picking gender...")
    try:
        # Open dropdown
        opened = False
        for opener in [
            page.get_by_label("Gender"),
            page.get_by_role("combobox", name="Gender"),
            page.get_by_role("combobox", name="Giới tính"),
            page.get_by_label("Giới tính")
        ]:
            if opener.count() > 0:
                print("[DEBUG] Found gender dropdown, clicking...")
                human_click(page, opener.first)
                human_delay(100, 200); opened = True; break
        if not opened:
            print("[DEBUG] No gender dropdown found")
        # Pick first available
        for text in ["Male", "Female", "Nam", "Nữ"]:
            for method_name, method in [
                ("role=option", lambda t: page.get_by_role("option", name=t)),
                ("text", lambda t: page.locator(f'text="{t}"'))
            ]:
                try:
                    loc = method(text)
                    if loc.count() > 0:
                        print(f"[DEBUG] Found gender option '{text}' via {method_name}")
                        human_click(page, loc.first)
                        human_delay(120, 200); return True
                except Exception:
                    continue
        # Keyboard fallback
        print("[DEBUG] Using keyboard fallback for gender...")
        try:
            page.keyboard.press("Home"); page.keyboard.press("ArrowDown"); page.keyboard.press("Enter")
            print("[DEBUG] Gender selected via keyboard")
            return True
        except Exception:
            pass
        print("[DEBUG] Could not select gender")
        return False
    except Exception as e:
        print(f"[DEBUG] Error picking gender: {e}")
        return False


def maybe_fill_basic_info(page) -> bool:
    print("[DEBUG] Filling basic info page...")
    try:
        # Wait for page
        print("[DEBUG] Waiting for basic info page to load...")
        for _ in range(10):
            if (page.get_by_label("Month").count() or page.get_by_label("Tháng").count() or
                page.get_by_role("heading", name="Basic information").count()):
                print("[DEBUG] Basic info page detected")
                break
            page.wait_for_timeout(300)

        # Generate data
        today = date.today()
        age = random.randint(19, 40)
        year_val = today.year - age
        month_idx = random.randint(1, 3)
        day_val = random.randint(1, 28)
        month_label = MONTH_LABELS[month_idx - 1]
        print(f"[DEBUG] Generated data - Age: {age}, Date: {month_label} {day_val}, {year_val}")

        for attempt in range(3):
            print(f"[DEBUG] Basic info attempt {attempt + 1}/3")
            # Month
            ok_month = choose_month(page, month_label, month_idx)
            human_delay(300, 500)
            
            # Day
            print(f"[DEBUG] Filling day: {day_val}")
            ok_day = False
            for day_sel in ['input[name="day"]', 'input#day', 'input[aria-label="Day"]', 'input[aria-label="Ngày"]']:
                try:
                    day_field = page.locator(day_sel)
                    if day_field.count() > 0:
                        print(f"[DEBUG] Found day field: {day_sel}")
                        fill_slowly(page, day_field.first, str(day_val))
                        ok_day = True; break
                except Exception:
                    continue
            if not ok_day:
                print("[DEBUG] Trying day field by label...")
                day_label_name = first_present_label(page, ["Day", "Ngày"]) or "Day"
                ok_day = fill_by_label_if_present(page, day_label_name, str(day_val))
            print(f"[DEBUG] Day filled: {ok_day}")
            human_delay(300, 500)
            
            # Year
            print(f"[DEBUG] Filling year: {year_val}")
            ok_year = False
            year_label_name = first_present_label(page, ["Year", "Năm"]) or "Year"
            try:
                year_field = page.get_by_label(year_label_name)
                if year_field.count() > 0:
                    print(f"[DEBUG] Found year field by label: {year_label_name}")
                    ok_year = fill_slowly(page, year_field.first, str(year_val))
                    
            except Exception:
                pass
            if not ok_year:
                print("[DEBUG] Trying year field fallback...")
                ok_year = fill_by_label_if_present(page, year_label_name, str(year_val)) or True
            print(f"[DEBUG] Year filled: {ok_year}")
            human_delay(300, 500)
            
            # Gender
            ok_gender = pick_gender_any(page)
            print(f"[DEBUG] Gender selected: {ok_gender}")
            
            if ok_month and ok_day and ok_year and ok_gender:
                print("[DEBUG] All basic info fields completed successfully")
                break
            elif attempt < 2:
                print(f"[DEBUG] Some fields failed - Month: {ok_month}, Day: {ok_day}, Year: {ok_year}, Gender: {ok_gender}")
                page.wait_for_timeout(500)

        human_delay(800, 1200)
        click_next(page)
        print("[DEBUG] Basic info page completed")
        return True
    except Exception as e:
        print(f"[DEBUG] Error in basic info page: {e}")
        return False


def maybe_fill_username_page(page, username: str) -> bool:
    print("[DEBUG] Filling username page...")
    try:
        detected = False
        for _ in range(20):
            if (page.get_by_label("Username").count() or
                page.get_by_label("Tên người dùng").count() or
                page.get_by_role("heading", name="How you'll sign in").count() or
                page.get_by_role("heading", name="Cách bạn sẽ đăng nhập").count()):
                detected = True; break
            page.wait_for_timeout(250)
        if not detected:
            print("[DEBUG] Username page not detected")
            return False

        attempt_username = username
        for attempt in range(4):
            print(f"[DEBUG] Username attempt {attempt+1}: {attempt_username}")
            try:
                filled = fill_first_present_slowly(page, [
                    'input[name="Username"]', 'input#username',
                    'input[aria-label="Username"]', 'input[aria-label="Tên người dùng"]'
                ], attempt_username)
                if not filled:
                    for label in ["Username", "Tên người dùng"]:
                        try:
                            if page.get_by_label(label).count():
                                fill_slowly(page, page.get_by_label(label).first, attempt_username)
                                filled = True; 
                                break
                        except Exception:
                            continue
            except Exception as e:
                print(f"[DEBUG] Error while filling username: {e}")

            human_delay(600, 1000)
            click_next(page)
            page.wait_for_timeout(1200)

            taken = False
            try:
                if (page.locator('text="That username is taken"').count() or
                    page.locator('text="Try another"').count() or
                    page.locator('text="Tên người dùng đã được sử dụng"').count() or
                    page.locator('text="Hãy thử tên khác"').count() or
                    page.locator('text="Hãy thử một cái khác"').count()):
                    taken = True
                    print("[DEBUG] Username appears taken; retrying with new suffix")
            except Exception:
                pass

            if not taken:
                print("[DEBUG] Username accepted")
                return True

            extra_digits = ''.join(str(random.randint(0, 9)) for _ in range(random.randint(5, 8)))
            attempt_username = f"{username}{extra_digits}"
            human_delay(400, 800)

        return True
    except Exception as e:
        print(f"[DEBUG] Error in username page: {e}")
        return False


def maybe_fill_password_page(page, password: str) -> bool:
    try:
        # Wait for password page
        for _ in range(10):
            if (page.get_by_label("Password").count() or 
                page.locator('input[type="password"]').count()):
                break
            page.wait_for_timeout(300)

        pw_inputs = page.locator('input[type="password"]').all()
        if len(pw_inputs) >= 2:
            try:
                fill_slowly(page, pw_inputs[0], password, 0.5, 1)
                human_delay(2000, 4000)
                try:
                    paste_text_via_clipboard(page, pw_inputs[1], password)
                    human_delay(2000, 4000)
                except Exception:
                    pass
            except Exception:
                pass

        human_delay(800, 1200)
        click_next(page)
        return True
        # return filled_password or filled_confirm
    except Exception:
        return False



def fill_recovery_email(page, recovery_email: str) -> bool:
    """Fill recovery email field on the page using fill_slowly"""
    try:
        # Try multiple selectors for recovery email field
        selectors = [
            'input[aria-label*="recovery"]',
            'input[aria-label*="khôi phục"]',
            'input[name*="recovery"]',
            'input[type="email"]'
        ]
        
        for selector in selectors:
            try:
                field = page.locator(selector)
                if field.count() > 0:
                    print(f"📝 Found recovery email field: {selector}")
                    # Fill with recovery email using fill_slowly for human-like typing
                    fill_slowly(page, field.first, recovery_email, 0.1, 0.3)
                    print(f"✅ Filled recovery email using fill_slowly: {recovery_email}")
                    return True
            except Exception as e:
                print(f"⚠️ Selector {selector} failed: {e}")
                continue
        
        print("❌ Could not find recovery email field")
        return False
        
    except Exception as e:
        print(f"❌ Error filling recovery email: {e}")
        return False
