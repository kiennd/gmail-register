import subprocess
from urllib.parse import urlparse
from typing import Any, Dict, Optional


def parse_proxy(proxy_url: Optional[str]) -> Optional[Dict[str, Any]]:
    if not proxy_url:
        return None
    parsed = urlparse(proxy_url)
    if not parsed.scheme or not parsed.hostname:
        raise ValueError(f"Invalid PROXY_URL: {proxy_url}")
    username = parsed.username
    password = parsed.password
    host = parsed.hostname
    port = parsed.port
    scheme = parsed.scheme
    server = f"{scheme}://{host}{':' + str(port) if port else ''}"
    proxy_dict: Dict[str, Any] = {"server": server}
    if username:
        proxy_dict["username"] = username
    if password:
        proxy_dict["password"] = password
    return proxy_dict


def parse_proxy_legacy(colon_string: str, scheme: str) -> Dict[str, Any]:
    parts = colon_string.split(":")
    if len(parts) not in (2, 4):
        raise ValueError("Legacy proxy must be host:port or host:port:user:pass")
    host = parts[0]
    port = parts[1]
    username = parts[2] if len(parts) == 4 else None
    password = parts[3] if len(parts) == 4 else None
    server = f"{scheme}://{host}:{port}"
    out: Dict[str, Any] = {"server": server}
    if username:
        out["username"] = username
    if password:
        out["password"] = password
    return out


def test_proxy_connection(proxy_config: Dict[str, Any]) -> bool:
    try:
        server = proxy_config.get("server", "")
        if "://" in server:
            parsed = urlparse(server)
            host = parsed.hostname
            port = parsed.port
            scheme = parsed.scheme
        else:
            return False

        username = proxy_config.get("username")
        password = proxy_config.get("password")

        if username and password:
            proxy_url = f"{scheme}://{username}:{password}@{host}:{port}"
        else:
            proxy_url = f"{scheme}://{host}:{port}"

        result = subprocess.run([
            "curl", "-sS", "--max-time", "10",
            "-x", proxy_url,
            "https://httpbin.org/ip"
        ], capture_output=True, text=True, timeout=15)

        return result.returncode == 0 and "origin" in result.stdout
    except Exception:
        return False 