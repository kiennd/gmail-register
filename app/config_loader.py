import json
import os
from typing import Any, Dict, Optional


def interpolate_vars(value: Optional[str], variables: Dict[str, Any]) -> Optional[str]:
    if value is None:
        return None
    result = str(value)
    for k, v in variables.items():
        result = result.replace(f"${{{k}}}", str(v) if v is not None else "")
    return result


def parse_bool(val: Any, default: bool) -> bool:
    if isinstance(val, bool):
        return val
    if val is None:
        return default
    v = str(val).strip().lower()
    if v in {"1", "true", "yes", "y"}:
        return True
    if v in {"0", "false", "no", "n"}:
        return False
    return default


def load_config_from_file(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    raw["USER_DATA_DIR"] = interpolate_vars(raw.get("USER_DATA_DIR"), raw)

    cfg: Dict[str, Any] = {
        "engine": raw.get("ENGINE", "hidemium").lower(),
        "camoufox_os": (raw.get("CAMOUFOX_OS") or "windows").strip().lower(),
        "camoufox_config": raw.get("CAMOUFOX_CONFIG") or None,
        "headless": raw.get("HEADLESS", False),
        "humanize": parse_bool(raw.get("HUMANIZE"), True),
        "persistent_context": parse_bool(raw.get("PERSISTENT_CONTEXT"), True),
        "user_data_dir": raw.get("USER_DATA_DIR") or None,
        "debug": parse_bool(raw.get("DEBUG"), False),
        # Camoufox options
        "camoufox_args": raw.get("CAMOUFOX_ARGS") or None,
        # UI language
        "lang": raw.get("LANG") or None,
        # Hidemium options
        "hidemium_api_url": raw.get("HIDEMIUM_API_URL", "http://localhost:2222"),
        "hidemium_os": raw.get("HIDEMIUM_OS", "win"),
        "hidemium_local_profile": parse_bool(raw.get("HIDEMIUM_LOCAL_PROFILE"), False),
        "hidemium_custom_config": raw.get("HIDEMIUM_CUSTOM_CONFIG", {}),
        # GoLogin options
        "gologin_access_token": raw.get("GOLOGIN_ACCESS_TOKEN", ""),
        "gologin_api_url": raw.get("GOLOGIN_API_URL", "https://api.gologin.com"),
        "gologin_os": raw.get("GOLOGIN_OS", "win"),
        "gologin_local_profile": parse_bool(raw.get("GOLOGIN_LOCAL_PROFILE"), False),
        "gologin_custom_config": raw.get("GOLOGIN_CUSTOM_CONFIG", {}),
        # Proxy options
        "proxy": raw.get("PROXY"),
        "proxy_scheme": raw.get("PROXY_SCHEME", "http"),
    }
    return cfg 