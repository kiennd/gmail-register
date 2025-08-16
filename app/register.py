import sys
from typing import Any, Dict, Optional

from .human_actions import fill_slowly, human_click, human_delay
from .steps import (
    maybe_fill_basic_info,
    maybe_fill_name_page,
    maybe_fill_privacy_terms_page,
    maybe_fill_recovery_email,
    maybe_fill_review_page,
    maybe_fill_username_page,
    maybe_fill_password_page,
    is_verification_block_page,
    maybe_choose_recommended_email,
)
from .hidemium_client import HidemiumClient
# Keep Camoufox import as fallback
try:
    from camoufox.sync_api import Camoufox
    CAMOUFOX_AVAILABLE = True
except ImportError:
    CAMOUFOX_AVAILABLE = False
    print("Warning: Camoufox not available. Only Hidemium engine supported.")

# Warm-up landing before actual sign-up flow
WORKSPACE_LANDING_URL = "https://workspace.google.com/intl/en-US/gmail/"

# Actual Google account creation endpoint
SIGNUP_URL = (
    "https://accounts.google.com/signup/v2/createaccount?service=mail&continue=https://mail.google.com/mail/&flowName=GlifWebSignIn&flowEntry=SignUp&ec=asw-gmail-hero-create&theme=glif"
)


def _normalize_headless(value: Any) -> Any:
    if isinstance(value, bool):
        return value
    s = str(value).strip().lower()
    if s in ("true", "1", "yes", "y"):
        return True
    if s == "virtual":
        return "virtual"
    return False


def _normalize_locale(lang: Optional[str]) -> Optional[str]:
    if not lang:
        return None
    s = str(lang).strip()
    if "-" in s:
        return s
    mapping = {"vi": "vi-VN", "en": "en-US"}
    return mapping.get(s.lower(), f"{s}-{s.upper()}")


def _primary_language_from_locale(locale: Optional[str]) -> Optional[str]:
    if not locale:
        return None
    return str(locale).split("-", 1)[0].lower()


def build_camoufox_kwargs(cfg: Dict[str, Any], proxy: Optional[Dict[str, Any]], debug: bool) -> Dict[str, Any]:
    """Build Camoufox launch arguments (fallback engine)"""
    if not CAMOUFOX_AVAILABLE:
        raise ImportError("Camoufox is not available")
        
    kwargs: Dict[str, Any] = {
        "headless": _normalize_headless(cfg.get("headless", False)),
        "humanize": cfg.get("humanize", True),
        "os": cfg.get("camoufox_os", "windows"),
        "debug": debug,
    }
    if cfg.get("lang"):
        kwargs["locale"] = _normalize_locale(cfg.get("lang"))

    if cfg.get("camoufox_args"):
        kwargs["args"] = cfg.get("camoufox_args")
    if cfg.get("camoufox_config") and isinstance(cfg.get("camoufox_config"), dict):
        # Advanced: merge low-level camoufox config options
        kwargs.update(cfg.get("camoufox_config"))
    # Window placement via Chromium flags so multiple windows tile instead of stacking
    win_args: list[str] = []
    try:
        if cfg.get("window_pos") and isinstance(cfg.get("window_pos"), tuple):
            x, y = cfg.get("window_pos")
            win_args.append(f"--window-position={int(x)},{int(y)}")
        if cfg.get("window_size") and isinstance(cfg.get("window_size"), tuple):
            w, h = cfg.get("window_size")
            win_args.append(f"--window-size={int(w)},{int(h)}")
    except Exception:
        pass
    if win_args:
        if "args" in kwargs:
            existing = kwargs.get("args")
            if isinstance(existing, list):
                kwargs["args"] = existing + win_args
            else:
                kwargs["args"] = [existing] + win_args
        else:
            kwargs["args"] = win_args
    if proxy:
        kwargs["proxy"] = proxy
        kwargs["geoip"] = False
    return kwargs



def create_temp_hidemium_profile(cfg: Dict[str, Any], proxy: Optional[Dict[str, Any]]) -> str:
    """Create a temporary Hidemium profile with proxy configuration"""
    import uuid
    import time
    
    client = HidemiumClient()
    
    # Generate unique profile name for one-time use
    timestamp = int(time.time())
    username = cfg.get("username", "gmail_register")
    profile_name = f"temp_{username}_{timestamp}_{uuid.uuid4().hex[:8]}"
    
    print(f"Creating temporary Hidemium profile: {profile_name}")
    
    # Determine OS and language from config
    os_type = cfg.get("hidemium_os", "win")
    language = cfg.get("lang", "en-US")
    if language == "vi":
        language = "vi-VN"
    elif language == "en":
        language = "en-US"
    
    # Build complete profile configuration using new custom API
    try:
        # Create profile using custom API with full configuration        
        response = client.create_browser_profile(profile_name)
        
        # Extract UUID from response (support both cloud and local formats)
        profile_uuid = None
        if isinstance(response, dict):
            if response.get("status") == "success":
                content = response.get("content", {})
                if isinstance(content, dict):
                    profile_uuid = content.get("uuid")
        
        if not profile_uuid:
            raise ValueError(f"Profile creation failed: {response}")
            
        print(f"Created temporary profile with UUID: {profile_uuid}")
        try:
            client.update_fingerprint(profile_uuid)
        except Exception as e:
            print(f"Warning: Failed to update fingerprint: {e}")
        return profile_uuid
        # return "local-c34620b3-3ccb-4fdc-951f-cf08513b6143"
        
    except Exception as e:
        print(f"Failed to create temporary profile: {e}")
        raise


def _fill_signup_flow(page, cfg: Dict[str, Any], client: HidemiumClient) -> None:
        # If explicit window_size provided, set viewport accordingly
        size = cfg.get("window_size")
        w, h = size
        page.set_viewport_size({"width": int(w), "height": int(h)})

        print("Opening Google sign-up...", flush=True)
        
        # Step 1: Visit Workspace Gmail landing (warm-up)
        try:
            page.goto(WORKSPACE_LANDING_URL, timeout=90_000)
            human_delay(1200, 2000)

        except Exception:
            pass
        # Step 2: Continue with current flow at the actual sign-up URL
        # Respect UI language via hl parameter for Google flows
        final_url = SIGNUP_URL
        try:
            locale = _normalize_locale(cfg.get("lang")) if cfg.get("lang") else None
            hl = _primary_language_from_locale(locale) if locale else None
            if hl and "hl=" not in final_url:
                joiner = "&" if "?" in final_url else "?"
                final_url = f"{final_url}{joiner}hl={hl}"
        except Exception:
            pass
        page.goto(final_url, timeout=90_000)
        # Inject mouse tracker
        if client:
            print("🔴 Injecting mouse tracker overlay...")
            success = client.inject_mouse_tracker(page)
            if success:
                print("✅ Mouse tracker injected successfully!")
                print("🔴 Red dot will follow mouse movements during registration")
            else:
                print("⚠️ Failed to inject mouse tracker, continuing without it")

        page.wait_for_selector('input[name="firstName"]', timeout=60_000)

        # Poll briefly for verification block; if found, return to close
        recovery_email = generate_recovery_email()
        is_finished_fill_name = False
        is_finished_fill_basic_info = False
        is_finished_fill_username = False
        is_finished_fill_password = False
        is_finished_fill_recovery_email = False
        is_finished_fill_review = False
        is_finished_all = False
        for _ in range(20):
            try:
                if not is_finished_fill_name:
                    is_finished_fill_name = maybe_fill_name_page(page, cfg.get("first_name", ""), cfg.get("last_name", ""))

                if not is_finished_fill_basic_info:
                    is_finished_fill_basic_info = maybe_fill_basic_info(page)


                chosen_local = maybe_choose_recommended_email(page)
                if chosen_local:
                    # Update cfg username to the recommended email local-part for downstream use
                    cfg["username"] = chosen_local
                    

                if not is_finished_fill_username:
                    is_finished_fill_username = maybe_fill_username_page(page, cfg.get("username", ""))

                if not is_finished_fill_password:
                    is_finished_fill_password = maybe_fill_password_page(page, cfg.get("password", ""))

                if is_verification_block_page(page):
                    print("Verification block detected (QR/device/phone). Closing.")
                    human_delay(1000, 1000)
                    return

                if not is_finished_fill_recovery_email:
                    is_finished_fill_recovery_email = maybe_fill_recovery_email(page, recovery_email)

                if not is_finished_fill_review:
                    is_finished_fill_review = maybe_fill_review_page(page)

                if not is_finished_all:
                    is_finished_all = maybe_fill_privacy_terms_page(page)

                if is_finished_all:
                    write_success_to_file(cfg, recovery_email)
                    page.wait_for_timeout(1000)
                    return  # Exit successfully after agreeing to terms

                

                
            except Exception:
                pass
            page.wait_for_timeout(1000)

        # Remove mouse tracker when done
        try:
            if success:  # Only remove if we successfully injected
                print("🗑️ Removing mouse tracker overlay...")
                client.remove_mouse_tracker(page)
                print("✅ Mouse tracker removed successfully")
        except Exception as e:
            print(f"⚠️ Warning: Failed to remove mouse tracker: {e}")

        print("Done.")


def generate_recovery_email() -> str:
    """Generate random recovery email using provided domains"""
    import random
    import string
    
    domains = [
        "blondmail.com", "chapsmail.com", "clowmail.com", "dropjar.com",
        "fivermail.com", "getairmail.com", "getmule.com", "getnada.com",
        "gimpmail.com", "givmail.com", "guysmail.com", "inboxbear.com",
        "replyloop.com", "robot-mail.com", "spicysoda.com", "tafmail.com",
        "temptami.com", "tupmail.com", "vomoto.com"
    ]
    
    # Generate random username (8-12 characters)
    username_length = random.randint(8, 12)
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=username_length))
    
    # Pick random domain
    domain = random.choice(domains)
    
    return f"{username}@{domain}"


def write_success_to_file(cfg: Dict[str, Any], recovery_email: str) -> None:
    """Write successful registration to success.txt file"""
    try:
        import os
        
        # Get email and password from config
        username = cfg.get("username", "unknown")
        password = cfg.get("password", "unknown")
        
        # Format: email|pass|recover email
        line = f"{username}@gmail.com|{password}|{recovery_email}"
        
        # Write to success.txt
        with open("success.txt", "a", encoding="utf-8") as f:
            f.write(line + "\n")
        
        print(f"💾 Success written to file: {line}")
        
    except Exception as e:
        print(f"❌ Error writing to success file: {e}")


def register_flow(cfg: Dict[str, Any], engine_kwargs: Dict[str, Any]) -> None:
    engine = cfg.get("engine", "camoufox").lower()
    
    if engine == "hidemium":
        print("Starting Hidemium registration flow...", flush=True)
        client = None
        page = None
        
        try:
            # Step 1: Create temporary profile
            client = HidemiumClient()
            profile_uuid = engine_kwargs.get("profile_uuid")
            
            if not profile_uuid:
                raise ValueError("Hidemium profile UUID not provided")
            
            # Step 2: Launch profile and connect
            print("Launching Hidemium profile for registration...", flush=True)
            # Pass through command and proxy for openProfile to reduce 400 errors
            open_command = engine_kwargs.get("open_command")
            open_proxy_param = engine_kwargs.get("open_proxy_param")
            page = client.connect_to_profile(profile_uuid, command=open_command, proxy=open_proxy_param)
            
            # Step 3: Execute registration flow
            print("Executing Gmail registration flow...", flush=True)
            _fill_signup_flow(page, cfg, client)
            
            print("Registration flow completed successfully!", flush=True)
            
        except Exception as e:
            print(f"Hidemium registration failed: {e}")
            raise
            
        finally:
            # Step 4: Cleanup and optionally delete temporary profile
            if page and client:
                try:
                    # Check if profile deletion is enabled (default: True for temp profiles)
                    delete_profile = cfg.get("hidemium_delete_profile", True)
                    
                    if delete_profile:
                        print("Cleaning up and deleting temporary profile...", flush=True)
                    else:
                        print("Cleaning up profile (keeping for reuse)...", flush=True)
                    
                    client.cleanup_page(page, delete_profile=delete_profile)
                    
                except Exception as e:
                    print(f"Warning: Failed to cleanup profile: {e}")
                    # Try to delete profile even if cleanup failed (only if deletion was requested)
                    if cfg.get("hidemium_delete_profile", True):
                        try:
                            if hasattr(page, '_hidemium_cleanup'):
                                profile_uuid = page._hidemium_cleanup.get('profile_uuid')
                                if profile_uuid:
                                    client.delete_profile(profile_uuid)
                                    print(f"Force deleted profile: {profile_uuid}")
                        except Exception:
                            pass
    
    else:  # camoufox fallback
        print("Launching Camoufox...", flush=True)
        try:
            browser_cm = Camoufox(**engine_kwargs)
            browser = browser_cm.__enter__()
        except ValueError as e:
            msg = str(e)
            if "No headers based on this input can be generated" in msg:
                print("[fallback] Relaxing fingerprint constraints (locale/window/screen) and retrying...", flush=True)
                relaxed = dict(engine_kwargs)
                # Remove potential constraints
                for k in ["screen", "window", "locale"]:
                    relaxed.pop(k, None)
                try:
                    browser_cm = Camoufox(**relaxed)
                    browser = browser_cm.__enter__()
                except Exception:
                    raise
            else:
                raise
        with browser:
            page = browser.new_page()
            try:
                page.bring_to_front()
            except Exception:
                try:
                    page.evaluate("() => window.focus()")
                except Exception:
                    pass
            _fill_signup_flow(page, cfg, None)  # Pass None for client in fallback