import argparse
import sys
from typing import Dict, Any, Optional

from app.config_loader import load_config_from_file
from app.proxy_utils import parse_proxy, parse_proxy_legacy
from app.register import build_camoufox_kwargs, register_flow
from app.generator import generate_name, generate_username, generate_password


def build_proxy(args: argparse.Namespace, cfg: Dict[str, Any]) -> Dict[str, Any]:
    proxy_input = args.proxy if args.proxy else cfg.get("proxy_legacy")
    if not proxy_input:
        print("Proxy is required. Please set PROXY in config.json or pass --proxy.", file=sys.stderr)
        sys.exit(1)
    if "://" in proxy_input:
        proxy = parse_proxy(proxy_input)
    else:
        scheme = args.proxy_scheme if args.proxy_scheme else (cfg.get("proxy_scheme") or "http")
        proxy = parse_proxy_legacy(proxy_input, scheme)
    if not proxy or not proxy.get("server"):
        print("Invalid proxy configuration.", file=sys.stderr)
        sys.exit(1)
    return proxy


def main() -> None:
    parser = argparse.ArgumentParser(description="Assist Gmail registration using Camoufox.")
    parser.add_argument("--config", dest="config_path", default="config.json")

    args_pre = parser.parse_known_args()[0]
    cfg = load_config_from_file(args_pre.config_path)

    # CLI args (no overrides for name/username to keep them always random)
    parser.add_argument("--password", dest="password", default=None)
    parser.add_argument("--recovery-email", dest="recovery_email", default=cfg.get("recovery_email"))
    parser.add_argument("--phone", dest="phone_number", default=cfg.get("phone_number"))
    parser.add_argument("--proxy", dest="proxy", default=None, help="Proxy URL or legacy host:port[:user:pass]")
    parser.add_argument("--proxy-scheme", dest="proxy_scheme", default=None, choices=["http", "https", "socks5"], help="Scheme for legacy proxy")
    parser.add_argument("--headless", dest="headless", default=None, help="true|false|virtual")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--wait", dest="wait_seconds", type=int, default=300, help="Wait seconds in non-interactive mode")

    args = parser.parse_args()

    # Always random name and username
    first, last = generate_name()
    user = generate_username(first, last)

    # Password: generate if not provided
    pwd = args.password or generate_password()

    print(f"Using identity (random): {first} {last}, username={user}")

    # Proxy is mandatory
    proxy = build_proxy(args, cfg)

    effective_cfg = {
        **cfg,
        "first_name": first,
        "last_name": last,
        "username": user,
        "password": pwd,
        "recovery_email": args.recovery_email,
        "phone_number": args.phone_number,
        "headless": args.headless if args.headless is not None else cfg.get("headless"),
    }

    camou_kwargs = build_camoufox_kwargs(
        effective_cfg,
        proxy=proxy,
        debug=args.debug or bool(cfg.get("debug")),
    )

    register_flow(
        cfg=effective_cfg,
        camou_kwargs=camou_kwargs,
        wait_seconds=args.wait_seconds,
    )


if __name__ == "__main__":
    main() 