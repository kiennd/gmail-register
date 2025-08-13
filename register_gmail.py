import argparse
import sys
from typing import Dict, Any, Optional
import requests

from app.config_loader import load_config_from_file
from app.register import build_camoufox_kwargs, register_flow
from app.generator import generate_name, generate_username, generate_password, ensure_password_has_special


def _normalize_proxy_response(raw: str) -> Optional[Dict[str, Any]]:
    if not raw:
        return None
    s = raw.strip().strip('"')
    left = s.split("|", 1)[0].strip()
    if "://" in left:
        scheme, rest = left.split("://", 1)
    else:
        scheme, rest = ("socks5", left)
    parts = rest.split(":")
    if len(parts) >= 4:
        host, port, user, pwd = parts[0], parts[1], parts[2], parts[3]
        server = f"{scheme}://{host}:{port}"
        return {"server": server, "username": user, "password": pwd}
    if len(parts) == 2:
        host, port = parts[0], parts[1]
        server = f"{scheme}://{host}:{port}"
        return {"server": server}
    return None


def build_proxy(cfg: Dict[str, Any], args: argparse.Namespace) -> Optional[Dict[str, Any]]:
    api_tpl: Optional[str] = getattr(args, "proxy_api", None)
    port: Optional[int] = getattr(args, "port", None)
    if not api_tpl or not port:
        return None
    try:
        url = api_tpl.replace("{port}", str(port))
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            return _normalize_proxy_response(resp.text)
        else:
            print(f"Proxy API HTTP {resp.status_code}", file=sys.stderr)
    except Exception as e:
        print(f"Proxy API error: {e}", file=sys.stderr)
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Assist Gmail registration using Camoufox.")
    parser.add_argument("--config", dest="config_path", default="config.json")

    args_pre = parser.parse_known_args()[0]
    cfg = load_config_from_file(args_pre.config_path)

    # Minimal CLI overrides to support tiling and per-run profiles
    parser.add_argument("--engine", choices=["camoufox"], default="camoufox")
    parser.add_argument("--lang", dest="lang", default=cfg.get("lang"))
    parser.add_argument("--wait", dest="wait_seconds", type=int, default=int(cfg.get("wait_seconds", 30)))
    parser.add_argument("--headless", dest="headless", default=None, help="true|false|virtual")
    parser.add_argument("--user-data-dir", dest="user_data_dir", default=None)
    parser.add_argument("--creds-out", dest="creds_out", default=None)
    # Proxy via API per launch
    parser.add_argument("--proxy-api", dest="proxy_api", default="http://192.168.100.100:5555/changeipv6/?port={port}&apikey=2222")
    parser.add_argument("--port", dest="port", type=int, default=None)
    # Window tiling from multi-run
    parser.add_argument("--win-x", dest="win_x", type=int, default=None)
    parser.add_argument("--win-y", dest="win_y", type=int, default=None)
    parser.add_argument("--win-w", dest="win_w", type=int, default=None)
    parser.add_argument("--win-h", dest="win_h", type=int, default=None)
    
    args = parser.parse_args()

    # Always random name and username
    first, last = generate_name()
    user = generate_username(first, last)

    # Password: use from config when provided, else generate
    pwd = generate_password()

    print(f"Using identity (random): {first} {last}, username={user}")

    # Proxy is mandatory (accept CLI override for multi-run)
    proxy = build_proxy(cfg, args)
    print(f"Using proxy: {proxy}")
    # Profile handling based on engine from config
    engine = "camoufox"
    user_data_dir = args.user_data_dir or cfg.get("user_data_dir") or f"profiles/{user}"

    effective_cfg = {
        **cfg,
        "first_name": first,
        "last_name": last,
        "username": user,
        "password": pwd,
        "headless": (args.headless if args.headless is not None else cfg.get("headless")),
        "humanize": cfg.get("humanize"),
        "user_data_dir": user_data_dir,
        "window_pos": ( (args.win_x, args.win_y) if args.win_x is not None and args.win_y is not None else cfg.get("window_pos") ),
        "window_size": ( (args.win_w, args.win_h) if args.win_w is not None and args.win_h is not None else cfg.get("window_size") ),
    }

    camou_kwargs = build_camoufox_kwargs(
        effective_cfg,
        proxy=proxy,
        debug=bool(cfg.get("debug")),
    )

    # Merge engine-specific overrides
    effective_cfg.update({
        "engine": engine,
        "lang": args.lang,
    })

    register_flow(
        cfg=effective_cfg,
        camou_kwargs=camou_kwargs,
        wait_seconds=args.wait_seconds,
    )

    # After run, append credentials if requested
    creds_out = args.creds_out or cfg.get("creds_out")
    if creds_out:
        try:
            email = f"{user}@gmail.com"
            with open(creds_out, "a", encoding="utf-8") as fh:
                fh.write(f"{email}|{pwd}\n")
            print(f"Saved credentials to {creds_out}")
        except Exception as e:
            print(f"Could not write credentials: {e}", file=sys.stderr)


if __name__ == "__main__":
    main() 