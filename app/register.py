import sys
from typing import Any, Dict, Optional
from camoufox.sync_api import Camoufox

from .human_actions import human_delay
from .steps import (
    maybe_fill_basic_info,
    maybe_fill_username_page,
    maybe_fill_password_page,
)

SIGNUP_URL = (
    "https://accounts.google.com/signup/v2/webcreateaccount"
    "?flowName=GlifWebSignIn&flowEntry=SignUp"
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


def build_camoufox_kwargs(cfg: Dict[str, Any], proxy: Optional[Dict[str, Any]], debug: bool) -> Dict[str, Any]:
    kwargs: Dict[str, Any] = {
        "headless": _normalize_headless(cfg.get("headless", False)),
        "humanize": cfg.get("humanize", True),
        "os": cfg.get("camoufox_os", "windows"),
        "debug": debug,
    }
    if cfg.get("persistent_context", True):
        kwargs["persistent_context"] = True
        if cfg.get("user_data_dir"):
            kwargs["user_data_dir"] = cfg.get("user_data_dir")
    if proxy:
        kwargs["proxy"] = proxy
        kwargs["geoip"] = False
    return kwargs


def register_flow(cfg: Dict[str, Any], camou_kwargs: Dict[str, Any], wait_seconds: int) -> None:
    print("Launching Camoufox...", flush=True)
    with Camoufox(**camou_kwargs) as browser:
        page = browser.new_page()
        page.set_viewport_size({"width": 1366, "height": 768})

        print("Opening Google sign-up...", flush=True)
        page.goto(SIGNUP_URL, timeout=90_000)

        page.wait_for_selector('input[name="firstName"]', timeout=60_000)
        human_delay(800, 1400)
        page.locator('input[name="firstName"]').fill(cfg["first_name"]) if cfg.get("first_name") else None
        human_delay(300, 700)
        page.locator('input[name="lastName"]').fill(cfg["last_name"]) if cfg.get("last_name") else None
        human_delay(600, 1000)

        human_delay(700, 1200)
        page.get_by_role("button", name="Next").click()
        human_delay(1500, 2500)

        maybe_fill_basic_info(page)
        human_delay(1200, 2000)
        maybe_fill_username_page(page, cfg.get("username", ""))
        human_delay(1200, 2000)
        maybe_fill_password_page(page, cfg.get("password", ""))

        # Phone verification handling left to the caller
        print("If phone verification is shown, complete it in the browser.")
        print(f"Waiting up to {wait_seconds}s... Press Enter to continue earlier.")
        try:
            input()
        except EOFError:
            page.wait_for_timeout(wait_seconds * 1000)

        print("Done.") 