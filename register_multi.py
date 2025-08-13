import argparse
import math
import os
import sys
import threading
import time
from pathlib import Path
from typing import List, Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from screeninfo import get_monitors
import requests

# Import registration logic từ code hiện có
from app.config_loader import load_config_from_file
from app.proxy_utils import parse_proxy, parse_proxy_legacy
from app.register import build_camoufox_kwargs, register_flow
from app.generator import generate_name, generate_username, generate_password, ensure_password_has_special

def build_proxy_config(cfg: Dict[str, Any], proxy_url: Optional[str], proxy_scheme: Optional[str]) -> Dict[str, Any]:
    """Build proxy configuration từ CLI args hoặc config file"""
    if proxy_url:
        if "://" in proxy_url:
            proxy = parse_proxy(proxy_url)
        else:
            scheme = proxy_scheme or cfg.get("proxy_scheme") or "http"
            proxy = parse_proxy_legacy(proxy_url, scheme)
        if proxy and proxy.get("server"):
            return proxy
        print(f"Invalid proxy provided: {proxy_url}", file=sys.stderr)
        return {}

    # Fallback to config
    proxy_input = cfg.get("proxy_legacy")
    if not proxy_input:
        print("Proxy is required. Provide proxy or set PROXY in config.json.", file=sys.stderr)
        return {}
    if "://" in proxy_input:
        proxy = parse_proxy(proxy_input)
    else:
        scheme = cfg.get("proxy_scheme") or "http"
        proxy = parse_proxy_legacy(proxy_input, scheme)
    if not proxy or not proxy.get("server"):
        print("Invalid proxy configuration.", file=sys.stderr)
        return {}
    return proxy


def run_single_registration(
    idx: int, 
    config_path: str, 
    proxy_url: Optional[str], 
    proxy_scheme: Optional[str],
    user_data_dir: str, 
    creds_out: str,
    lang: str,
    headless: Optional[str],
    wait_seconds: int,
    window_config: Optional[Dict[str, int]],
    log_file: Path
) -> bool:
    """Chạy một registration thread"""
    log_fh = log_file.open("w", encoding="utf-8")
    
    def log_print(*args, **kwargs):
        print(f"[{idx}]", *args, **kwargs)
        print(*args, file=log_fh, **kwargs)
        log_fh.flush()
    
    try:
        log_print("Starting registration...")
        
        # Load config
        cfg = load_config_from_file(config_path)
        
        # Generate random name and username
        first, last = generate_name()
        user = generate_username(first, last)
        
        # Password: use from config when provided, else generate
        pwd = ensure_password_has_special(cfg.get("password")) if cfg.get("password") else generate_password()
        
        log_print(f"Using identity: {first} {last}, username={user}")
        
        # Build proxy config
        proxy = build_proxy_config(cfg, proxy_url, proxy_scheme)
        if not proxy:
            log_print("Failed to configure proxy")
            return False
        
        # Create effective config
        effective_cfg = {
            **cfg,
            "first_name": first,
            "last_name": last,
            "username": user,
            "password": pwd,
            "headless": (headless if headless is not None else cfg.get("headless")),
            "humanize": cfg.get("humanize"),
            "user_data_dir": user_data_dir,
            "lang": lang,
        }
        
        # Add window config if provided
        if window_config:
            if "x" in window_config and "y" in window_config:
                effective_cfg["window_pos"] = (window_config["x"], window_config["y"])
            if "w" in window_config and "h" in window_config:
                effective_cfg["window_size"] = (window_config["w"], window_config["h"])
        
        # Build camoufox kwargs
        camou_kwargs = build_camoufox_kwargs(
            effective_cfg,
            proxy=proxy,
            debug=bool(cfg.get("debug")),
        )
        
        log_print("Starting registration flow...")
        
        # Run registration
        register_flow(
            cfg=effective_cfg,
            camou_kwargs=camou_kwargs,
            wait_seconds=wait_seconds,
        )
        
        # Save credentials
        try:
            email = f"{user}@gmail.com"
            with open(creds_out, "a", encoding="utf-8") as fh:
                fh.write(f"{email}|{pwd}\n")
            log_print(f"Saved credentials to {creds_out}")
        except Exception as e:
            log_print(f"Could not write credentials: {e}")
        
        log_print("Registration completed successfully")
        return True
        
    except Exception as e:
        log_print(f"Registration failed: {e}")
        import traceback
        traceback.print_exc(file=log_fh)
        return False
    finally:
        log_fh.close()


def _auto_layout_if_needed(args: argparse.Namespace) -> None:
    if args.win_w and args.win_h:
        return
    monitors = get_monitors()
    monitor = None
    for m in monitors:
        if getattr(m, "is_primary", False):
            monitor = m
            break
    if monitor is None and monitors:
        monitor = monitors[0]
    if monitor is None:
        return
    width = getattr(monitor, "width", 1366)
    height = getattr(monitor, "height", 768)
    args.cols = min(max(1, int(math.ceil(math.sqrt(max(1, args.concurrency))))) , args.concurrency)
    rows = int(math.ceil(args.concurrency / args.cols))
    # Ensure non-negative gaps
    gap_x = max(0, args.gap_x)
    gap_y = max(0, args.gap_y)
    args.win_w = int((width - (args.cols - 1) * gap_x) / args.cols)
    args.win_h = int((height - (rows - 1) * gap_y) / rows)
    args.x0 = getattr(monitor, "x", 0)
    args.y0 = getattr(monitor, "y", 0)


def _normalize_proxy_url(raw: str, default_scheme: str = "socks5") -> Optional[str]:
    if not raw:
        return None
    raw = raw.strip().strip('"')
    # Split off optional IPv6 suffix "|..."
    proxy_part = raw.split("|")[0].strip()
    # Already in user:pass@host:port form
    if "://" in proxy_part and "@" in proxy_part:
        return proxy_part
    # Extract scheme if present
    if "://" in proxy_part:
        scheme, rest = proxy_part.split("://", 1)
    else:
        scheme, rest = default_scheme, proxy_part
    # If rest already has user:pass@host:port, return
    if "@" in rest:
        return f"{scheme}://{rest}"
    # Expect rest like host:port or host:port:user:pass
    parts = rest.split(":")
    if len(parts) >= 4:
        host, port, user, password = parts[0], parts[1], parts[2], parts[3]
        return f"{scheme}://{user}:{password}@{host}:{port}"
    if len(parts) == 2:
        host, port = parts[0], parts[1]
        return f"{scheme}://{host}:{port}"
    return None


def rotate_port_and_get_proxy(port: int, api_template: str) -> Optional[str]:
    try:
        url = api_template.replace("{port}", str(port))
        resp = requests.get(url, timeout=15)
        if resp.status_code != 200:
            print(f"[rotate] port {port} failed: HTTP {resp.status_code}")
            return None
        return _normalize_proxy_url(resp.text, default_scheme="socks5")
    except Exception as e:
        print(f"[rotate] port {port} error: {e}")
        return None


def run_many(args: argparse.Namespace) -> int:
    _auto_layout_if_needed(args)
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    
    ports = [int(args.port_base) + i for i in range(args.count)]

    creds_out = str(Path(args.output_dir) / "accounts.txt")
    
    def create_registration_task(idx: int) -> tuple:
        """Create registration task parameters"""
        profile_dir = os.path.join(args.profiles_dir, f"{args.profile_prefix}{idx}")
        Path(profile_dir).mkdir(parents=True, exist_ok=True)

        proxy_url: Optional[str] = None
        proxy_scheme: Optional[str] = args.proxy_scheme
        
        rel = idx - args.start_index
        port = ports[rel] if 0 <= rel < len(ports) else ports[rel % len(ports)]
        proxy_url = rotate_port_and_get_proxy(port, args.proxy_api)

        window_config: Optional[Dict[str, int]] = None
        if args.win_w and args.win_h:
            # Compute grid position
            col = (idx - args.start_index) % max(1, args.cols)
            row = (idx - args.start_index) // max(1, args.cols)
            x = args.x0 + col * (args.win_w + args.gap_x)
            y = args.y0 + row * (args.win_h + args.gap_y)
            window_config = {"x": x, "y": y, "w": args.win_w, "h": args.win_h}

        log_path = Path(args.output_dir) / f"run_{idx}.log"
        
        return (
            idx, args.config_path, proxy_url, proxy_scheme,
            profile_dir, creds_out, args.lang, args.headless,
            args.wait_seconds, window_config, log_path
        )

    # Create task parameters for all registrations
    task_params = []
    for i in range(args.count):
        task_params.append(create_registration_task(i + args.start_index))

    # Run registrations using ThreadPoolExecutor
    print(f"Starting {args.count} registrations with max {args.concurrency} concurrent threads...")
    
    success_count = 0
    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        # Submit all tasks
        future_to_idx = {
            executor.submit(run_single_registration, *params): params[0] 
            for params in task_params
        }
        
        # Process completed tasks
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                success = future.result()
                if success:
                    success_count += 1
                    print(f"Registration {idx} completed successfully")
                else:
                    print(f"Registration {idx} failed")
            except Exception as e:
                print(f"Registration {idx} raised exception: {e}")

    failures = args.count - success_count
    print(f"Completed: {success_count}/{args.count} successful, {failures} failed")
    return 1 if failures else 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Run multiple concurrent Gmail registrations.")
    parser.add_argument("--config", dest="config_path", default="config.json")
    parser.add_argument("--engine", choices=["camoufox"], default="camoufox")
    parser.add_argument("--count", type=int, default=3, help="Total number of accounts to create")
    parser.add_argument("--concurrency", type=int, default=3, help="Maximum parallel runs")
    parser.add_argument("--profiles-dir", default="profiles", help="Base directory for generated profiles")
    parser.add_argument("--profile-prefix", default="acc_", help="Prefix for per-run profile directory names")
    parser.add_argument("--start-index", type=int, default=1)
    parser.add_argument("--proxies-file", default=None, help="Path to file with one proxy per line")
    parser.add_argument("--proxy-scheme", choices=["http", "https", "socks5"], default="socks5")
    parser.add_argument("--reuse-proxies", action="store_true", help="Cycle proxies if count > proxies")
    parser.add_argument("--lang", default="vi")
    parser.add_argument("--headless", default=None)
    parser.add_argument("--wait", dest="wait_seconds", type=int, default=300)
    parser.add_argument("--output-dir", default="runs", help="Directory to write per-run logs")
    # Proxy rotation per fixed port
    parser.add_argument("--proxy-api", default="http://192.168.100.100:5555/changeipv6/?port={port}&apikey=2222", help="API template; use {port} placeholder")
    parser.add_argument("--ports", default=None, help="Comma-separated list or ranges, e.g. 15000-15003,15010")
    parser.add_argument("--ports-file", default=None, help="File containing one port per line")
    parser.add_argument("--port-base", dest="port_base", type=int, default=10000, help="Base port for per-thread fixed mapping (default 10000)")
    # Window tiling options (pixels)
    parser.add_argument("--win-w", type=int, default=None)
    parser.add_argument("--win-h", type=int, default=None)
    parser.add_argument("--cols", type=int, default=2)
    parser.add_argument("--x0", type=int, default=0)
    parser.add_argument("--y0", type=int, default=0)
    parser.add_argument("--gap-x", type=int, default=10)
    parser.add_argument("--gap-y", type=int, default=10)

    # Removed Hidemium options

    args = parser.parse_args()
    code = run_many(args)
    raise SystemExit(code)


if __name__ == "__main__":
    main()


