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
        "first_name": raw.get("FIRST_NAME"),
        "last_name": raw.get("LAST_NAME"),
        "username": raw.get("GMAIL_USERNAME"),
        "password": raw.get("GMAIL_PASSWORD"),
        "recovery_email": raw.get("RECOVERY_EMAIL") or None,
        "phone_number": raw.get("PHONE_NUMBER") or None,
        "proxy_legacy": raw.get("PROXY") or None,
        "proxy_scheme": raw.get("PROXY_SCHEME") or None,
        "camoufox_os": (raw.get("CAMOUFOX_OS") or "windows").strip().lower(),
        "headless": raw.get("HEADLESS", False),
        "humanize": parse_bool(raw.get("HUMANIZE"), True),
        "persistent_context": parse_bool(raw.get("PERSISTENT_CONTEXT"), True),
        "user_data_dir": raw.get("USER_DATA_DIR") or None,
        "debug": parse_bool(raw.get("DEBUG"), False),
    }
    return cfg 