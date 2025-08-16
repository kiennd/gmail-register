import argparse
import sys
import math
import threading
import signal
import os
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, Optional, Tuple
import requests

import tkinter as tk


from app.config_loader import load_config_from_file
from app.register import build_camoufox_kwargs, register_flow, create_temp_hidemium_profile
from app.generator import generate_name, generate_username, generate_password, ensure_password_has_special


def get_screen_size() -> Tuple[int, int]:
    """
    Get the current screen size automatically.
    Falls back to default values if detection fails.
    
    Returns:
        Tuple of (width, height) in pixels
    """
    try:
        if tk:
            root = tk.Tk()
            root.withdraw()  # Hide the window
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()
            root.destroy()
            print(f"Detected screen size: {screen_width}x{screen_height}")
            return screen_width, screen_height
        else:
            # Fallback for systems without tkinter
            print("Warning: tkinter not available, using default screen size 1920x1080")
            return 1920, 1080
    except Exception as e:
        print(f"Warning: Failed to detect screen size: {e}, using default 1920x1080")
        return 1920, 1080


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


def _to_hidemium_proxy_param(proxy: Optional[Dict[str, Any]]) -> Optional[str]:
    if not proxy:
        return None
    server = proxy.get("server") or ""
    username = proxy.get("username") or ""
    password = proxy.get("password") or ""
    if "://" in server:
        scheme, host_port = server.split("://", 1)
    else:
        scheme, host_port = ("http", server)
    if ":" in host_port:
        host, port = host_port.split(":", 1)
    else:
        host, port = host_port, "8080"
    ptype = scheme.upper()
    if username and password:
        return f"{ptype}|{host}|{port}|{username}|{password}"
    return f"{ptype}|{host}|{port}"


def _fetch_proxy_from_api(api_tpl: Optional[str], port: int) -> Optional[Dict[str, Any]]:
    if not api_tpl:
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


def _get_random_proxy_from_file(file_path: str = "proxies.txt") -> Optional[Dict[str, Any]]:
    """
    Pick a random proxy from the proxies.txt file.
    
    Returns:
        Random proxy dictionary or None if no proxies available
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        if not lines:
            return None
            
        # Pick a random line
        random_line = random.choice(lines)
        
        # Parse the proxy line (format: ip:port:username:password)
        parts = random_line.split(':')
        if len(parts) >= 2:
            host = parts[0]
            port = parts[1]
            username = parts[2] if len(parts) > 2 else None
            password = parts[3] if len(parts) > 3 else None
            
            return {
                "server": f"socks5://{host}:{port}",
                "username": username,
                "password": password
            }
        else:
            print(f"Warning: Invalid proxy format: {random_line}")
            return None
            
    except FileNotFoundError:
        print(f"Warning: Proxy file {file_path} not found")
        return None
    except Exception as e:
        print(f"Error reading proxy file: {e}")
        return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Assist Gmail registration using Camoufox.")
    parser.add_argument("--config", dest="config_path", default="config.json")

    args_pre = parser.parse_known_args()[0]
    cfg = load_config_from_file(args_pre.config_path)

    # Minimal CLI overrides to support tiling and per-run profiles
    parser.add_argument("--engine", choices=["camoufox", "hidemium"], default=cfg.get("engine", "hidemium"))
    parser.add_argument("--lang", dest="lang", default=cfg.get("lang"))
    # Hidemium settings (fixed defaults; no token, URL fixed to localhost:2222, random profile name internal, delete profile always true)
    # Proxy via API per launch
    parser.add_argument("--proxy-api", dest="proxy_api", default="http://192.168.100.100:5555/changeipv6/?port={port}&apikey=2222")
    # Concurrency and window tiling
    parser.add_argument("--threads", dest="threads", type=int, default=1)
    # Window tiling from multi-run
    
    args = parser.parse_args()

    # Automatically detect screen size
    screen_w, screen_h = get_screen_size()
    print(f"Using screen size: {screen_w}x{screen_h}")

    # Thread-safe file write
    write_lock = threading.Lock()

    def compute_tile(total: int, idx: int, screen_w: int, screen_h: int) -> Tuple[int, int, int, int]:
        cols = math.ceil(math.sqrt(total))
        rows = math.ceil(total / cols)
        tile_w = max(640, screen_w // cols)
        tile_h = max(480, screen_h // rows)
        col = idx % cols
        row = idx // cols
        x = col * tile_w
        y = row * tile_h
        return x, y, tile_w, tile_h

    def run_one(thread_id: int, total_threads: int, stop_event: threading.Event) -> None:
        # Per-thread constants
        proxy_port = 10000 + thread_id
        x, y, w, h = compute_tile(total_threads, thread_id, screen_w, screen_h)
        engine = args.engine
        lang_primary = (args.lang or cfg.get("lang") or "en").split("-")[0]
        open_command = f"--lang={lang_primary} --window-position={x},{y} --window-size={w},{h}"
        # open_command = f"--lang={lang_primary}"
        while not stop_event.is_set():
            # Identity per iteration
            first, last = generate_name()
            user = generate_username(first, last)
            pwd = generate_password()

            # Proxy per iteration (file-based or API fallback)
            # proxy = _get_random_proxy_from_file("proxies.txt")
            # if not proxy and args.proxy_api:
            #     print(f"[t{thread_id}] No proxies from file, trying API fallback...")
            #     proxy = _fetch_proxy_from_api(args.proxy_api, proxy_port)

            proxy = _fetch_proxy_from_api(args.proxy_api, proxy_port)

            print(f"[t{thread_id}] Using proxy: {proxy}")

            # Per-iteration cfg
            hidemium_custom = {"command": open_command}
            effective_cfg = {
                **cfg,
                "first_name": first,
                "last_name": last,
                "username": user,
                "password": pwd,
                "engine": engine,
                "headless": False,
                "humanize": cfg.get("humanize"),
                "window_pos": (x, y),
                "window_size": (w, h),
                "hidemium_delete_profile": True,
                "hidemium_custom_config": hidemium_custom,
                "lang": args.lang,
            }

            # Prepare engine-specific kwargs
            if engine == "hidemium":
                print(f"[t{thread_id}] Creating temporary Hidemium profile...")
                try:
                    profile_uuid = create_temp_hidemium_profile(effective_cfg, proxy)
                    open_proxy_param = _to_hidemium_proxy_param(proxy)
                    print(f"[t{thread_id}] Open proxy param: {open_proxy_param}")
                    engine_kwargs = {"profile_uuid": profile_uuid, "open_command": open_command, "open_proxy_param": open_proxy_param}
                    print(f"[t{thread_id}] Created temporary profile: {profile_uuid}")
                except Exception as e:
                    print(f"[t{thread_id}] Failed to create temporary Hidemium profile: {e}")
                    continue
            else:
                engine_kwargs = build_camoufox_kwargs(
                    effective_cfg,
                    proxy=proxy,
                    debug=bool(cfg.get("debug")),
                )

            try:
                register_flow(
                    cfg=effective_cfg,
                    engine_kwargs=engine_kwargs,
                )
            except Exception as e:
                print(f"[t{thread_id}] Run error: {e}")
            # brief yield to allow stop signal processing between cycles
            time.sleep(0.2)

    # Run single or multiple threads
    # Graceful shutdown via Ctrl+C
    stop_event = threading.Event()
    
    def _sig_handler(signum, frame):
        stop_event.set()
        print("\n[main] Stop signal received, waiting for threads to finish current cycle...")
    try:
        signal.signal(signal.SIGINT, _sig_handler)
    except Exception:
        pass

    if args.threads <= 1:
        try:
            run_one(0, 1, stop_event)
        except KeyboardInterrupt:
            stop_event.set()
    else:
        with ThreadPoolExecutor(max_workers=args.threads) as executor:
            futures = [executor.submit(run_one, i, args.threads, stop_event) for i in range(args.threads)]
            try:
                # Keep main thread responsive to Ctrl+C on Windows by polling
                while any(not f.done() for f in futures):
                    time.sleep(0.3)
            except KeyboardInterrupt:
                stop_event.set()
                print("\n[main] Ctrl+C detected. Signaled threads to stop.")
                # Graceful wait for threads to finish current cycle
                timeout_at = time.time() + 15
                while any(not f.done() for f in futures) and time.time() < timeout_at:
                    time.sleep(0.3)
                # Force exit if threads still blocking
                if any(not f.done() for f in futures):
                    print("[main] Forcing process exit.")
                    os._exit(0)


if __name__ == "__main__":
    main() 