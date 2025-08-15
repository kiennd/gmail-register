"""
Hidemium API client for remote profile management
Based on: https://docs.hidemium.io/hidemium-4/i.-bat-dau-voi-hidemium/api-automation-v4/remote-profile
"""
import requests
import json
import time
from typing import Dict, Any, Optional, List
from playwright.sync_api import sync_playwright, Browser, Page


class HidemiumClient:
    def __init__(self, base_url: str = "http://localhost:2222", api_token: Optional[str] = None):
        """
        Initialize Hidemium API client
        
        Args:
            base_url: Hidemium API endpoint (default: http://localhost:2222)
            api_token: API token for authentication (if required)
        """
        self.base_url = base_url.rstrip('/')
        self.api_token = api_token
        self.session = requests.Session()
        self._last_request_time = 0
        self._request_count = 0
        self._rate_limit_window = 60  # 1 minute
        self._rate_limit_max = 50     # 50 requests per minute
        
        if self.api_token:
            self.session.headers.update({'Authorization': f'Bearer {self.api_token}'})

    def _check_rate_limit(self) -> None:
        """Check and handle API rate limiting (50 requests per minute)"""
        current_time = time.time()
        
        # Reset counter if window has passed
        if current_time - self._last_request_time > self._rate_limit_window:
            self._request_count = 0
            self._last_request_time = current_time
        
        # Check if we're approaching rate limit
        if self._request_count >= self._rate_limit_max:
            sleep_time = self._rate_limit_window - (current_time - self._last_request_time)
            if sleep_time > 0:
                print(f"Rate limit reached (50 req/min). Waiting {sleep_time:.1f}s...")
                time.sleep(sleep_time)
                self._request_count = 0
                self._last_request_time = time.time()
        
        self._request_count += 1

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to Hidemium API with rate limiting"""
        # Check rate limit before making request
        self._check_rate_limit()
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Hidemium API error: {e}")
            raise
        except json.JSONDecodeError as e:
            print(f"Invalid JSON response: {e}")
            raise

    def open_profile(self, profile_uuid: str, command: Optional[str] = None, proxy: Optional[str] = None, debug_port: Optional[int] = None) -> Dict[str, Any]:
        """
        Open a Hidemium profile (GET /openProfile per docs)
        
        Args:
            profile_uuid: UUID of the profile to open
            debug_port: Optional debug port to request (passed via command flag)
            
        Returns:
            Raw response JSON from Hidemium API
        """
        params: Dict[str, Any] = {"uuid": profile_uuid}
        cmd_parts: list[str] = []
        if command:
            cmd_parts.append(command)
        if debug_port:
            cmd_parts.append(f"--remote-debugging-port={debug_port}")
        
        # Hardcoded Hidemium browser parameters
        cmd_parts.append("--hidemium-sync")
        cmd_parts.append("--threadindex=4h")
        
        if cmd_parts:
            params["command"] = " ".join(cmd_parts)
        if proxy:
            params["proxy"] = proxy

        # Retry a few times on 400/temporary errors
        last_err: Optional[Exception] = None
        for _ in range(3):
            try:
                return self._make_request('GET', '/openProfile', params=params)
            except requests.exceptions.RequestException as e:
                last_err = e
                try:
                    if e.response is not None:
                        body = e.response.text
                        print(f"openProfile error body: {body}")
                except Exception:
                    pass
                time.sleep(1.0)
        if last_err:
            raise last_err
        raise RuntimeError("Failed to open profile: unknown error")

    def close_profile(self, profile_uuid: str) -> Dict[str, Any]:
        """
        Close a Hidemium profile
        
        Args:
            profile_uuid: UUID of the profile to close
            
        Returns:
            Response confirming profile closure
        """
        params = {"uuid": profile_uuid}
        return self._make_request('GET', '/closeProfile', params=params)

    def check_profile_status(self, profile_uuid: str) -> Dict[str, Any]:
        """
        Check if a profile is running
        
        Args:
            profile_uuid: UUID of the profile to check
            
        Returns:
            Status information about the profile
        """
        params = {"uuid": profile_uuid}
        return self._make_request('GET', '/checking', params=params)

    def list_profiles(self, page: int = 1, limit: int = 50) -> Dict[str, Any]:
        """
        Get list of profiles
        
        Args:
            page: Page number (default: 1)
            limit: Number of profiles per page (default: 50)
            
        Returns:
            List of profiles with pagination info
        """
        params = {"page": page, "limit": limit}
        return self._make_request('GET', '/v4/profile', params=params)

    def get_profile_by_uuid(self, profile_uuid: str) -> Dict[str, Any]:
        """
        Get profile details by UUID
        
        Args:
            profile_uuid: UUID of the profile
            
        Returns:
            Detailed profile information
        """
        return self._make_request('GET', f'/v4/profile/{profile_uuid}')

    def create_profile(self, name: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a new profile (legacy method)
        
        Args:
            name: Profile name
            config: Optional profile configuration
            
        Returns:
            Created profile information including UUID
        """
        payload = {"name": name}
        if config:
            payload.update(config)
            
        return self._make_request('POST', '/v4/profile', json=payload)

    def create_profile_custom(self, profile_config: Dict[str, Any], is_local: bool = False) -> Dict[str, Any]:
        """
        Create a custom profile with full configuration
        
        Args:
            profile_config: Complete profile configuration
            is_local: Whether to create local (True) or cloud (False) profile
            
        Returns:
            Created profile information
            
        Note:
            API rate limit is 50 requests per minute. Exceeding may result in temporary blocking.
        """
        # Prepare the payload with all configuration
        payload = dict(profile_config)
        
        # Create the profile using the custom endpoint
        params = {"is_local": str(is_local).lower()}
        
        return self._make_request('POST', '/create-profile-custom', json=payload, params=params)

    def build_default_profile_config(self, name: str, proxy: Optional[Dict[str, Any]] = None, 
                                   os_type: str = "win", language: str = "en-US") -> Dict[str, Any]:
        """
        Build a default profile configuration for Gmail registration
        
        Args:
            name: Profile name
            proxy: Optional proxy configuration
            os_type: Operating system (win, mac, linux, android, ios)
            language: Browser language (e.g., "en-US", "vi-VN")
            
        Returns:
            Complete profile configuration ready for create_profile_custom
        """
        # Default configuration optimized for Gmail registration
        config = {
            "name": name,
            "os": os_type,
            "osVersion": "10" if os_type == "win" else "14.3.0" if os_type == "mac" else "linux_x86_64",
            "browser": "chrome",
            "version": "139",
            "userAgent": "",  # Auto-generated by Hidemium
            "canvas": "prefect",
            "webGLImage": "true",
            "audioContext": "true", 
            "webGLMetadata": "true",
            "webGLVendor": "",
            "webGLMetadataRenderer": "",
            "clientRectsEnable": "true",
            "noiseFont": "true",
            "language": language,
            "deviceMemory": 8,
            "hardwareConcurrency": 8,
            "resolution": "1920x1080",
            "StartURL": "https://workspace.google.com/intl/en-US/gmail/",
            "command": f"--lang={language.split('-')[0]}"
        }
        
        # Add proxy if provided
        if proxy and proxy.get("server"):
            server = proxy.get("server", "")
            username = proxy.get("username", "")
            password = proxy.get("password", "")
            
            # Parse proxy type and details
            if "://" in server:
                proxy_type, host_port = server.split("://", 1)
            else:
                proxy_type = "HTTP"
                host_port = server
            
            if ":" in host_port:
                host, port = host_port.split(":", 1)
            else:
                host = host_port
                port = "8080"
            
            # Format proxy string for Hidemium
            if username and password:
                config["proxy"] = f"{proxy_type.upper()}|{host}|{port}|{username}|{password}"
            else:
                config["proxy"] = f"{proxy_type.upper()}|{host}|{port}"
            
        return config

    def delete_profile(self, profile_uuid: str, is_local: Optional[bool] = None) -> Dict[str, Any]:
        """
        Delete a profile using Hidemium destroy endpoint
        
        Docs: GET/DELETE /v1/browser/destroy?is_local=true|false with body {"uuid_browser": [uuid]}
        Reference: https://docs.hidemium.io/hidemium-4/i.-bat-dau-voi-hidemium/api-automation-v4/interact-profile/8.-delete-profile
        
        Args:
            profile_uuid: UUID of the profile to delete ("local-..." for local profiles)
            is_local: Explicitly specify local/cloud; inferred by prefix when None
            
        Returns:
            Deletion confirmation structure
        """
        # Infer local vs cloud by UUID prefix if not provided
        if is_local is None:
            is_local = str(profile_uuid).startswith('local-')
        params = {"is_local": str(is_local).lower()}
        payload = {"uuid_browser": [profile_uuid]}
        return self._make_request('DELETE', '/v1/browser/destroy', params=params, json=payload)

    def update_proxy(self, profile_uuid: str, proxy_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update proxy settings for a profile
        
        Args:
            profile_uuid: UUID of the profile
            proxy_config: Proxy configuration
            
        Returns:
            Update confirmation
        """
        payload = {
            "uuid": profile_uuid,
            "proxy": proxy_config
        }
        return self._make_request('POST', '/v4/profile/proxy', json=payload)

    def update_fingerprint(self, profile_uuid: str, is_local: bool = True) -> dict:
        """
        Update fingerprint for a profile (PUT /v2/browser/change-fingerprint)
        Args:
            profile_uuid: UUID of the profile
            is_local: Whether the profile is local (default: True)
        Returns:
            Response JSON from Hidemium API
        """
        params = {"is_local": str(is_local).lower()}
        payload = {"profile_uuid": profile_uuid}
        return self._make_request('PUT', '/v2/browser/change-fingerprint', params=params, json=payload)

    def load_browser_profile_config_from_file(self, json_path: str, profile_name: str) -> dict:
        """
        Load browser profile config from a JSON file and set the profile name.
        Args:
            json_path: Path to the JSON config file
            profile_name: Name for the new profile
        Returns:
            Config dict with updated name
        """
        with open(json_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        config['name'] = profile_name
        return config

    def create_browser_profile(self, profile_name: str, is_local: bool = True, source: str = "hidemium_application_ui") -> dict:
        """
        Create a new browser profile using /v2/browser endpoint with config loaded from browser_profile_template.json.
        Args:
            profile_name: Name for the new profile
            is_local: True for local profile
            source: Source string for _source param
        Returns:
            Response JSON from Hidemium API
        """
        import os
        template_path = os.path.join(os.path.dirname(__file__), '../browser_profile_template.json')
        with open(template_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        config['name'] = profile_name
        params = {
            "_source": source,
            "is_local": str(is_local).lower()
        }
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Hidemium_4/4.1.6 Chrome/122.0.6261.156 Electron/29.4.6 Safari/537.36"
        }
        payload = config
        return self._make_request('POST', '/v2/browser', params=params, json=payload, headers=headers)

    def connect_to_profile(self, profile_uuid: str, command: Optional[str] = None, proxy: Optional[str] = None, max_retries: int = 10) -> Page:
        """
        Connect to an opened Hidemium profile using Playwright
        
        Args:
            profile_uuid: UUID of the profile to connect to
            max_retries: Maximum number of connection attempts
            
        Returns:
            Playwright Page instance connected to the profile
        """
        # First, try to open the profile and get remote debugging port
        try:
            response = self.open_profile(profile_uuid, command=command, proxy=proxy)
            debug_port: Optional[int] = None
            if isinstance(response, dict):
                data = response.get('data') or {}
                if isinstance(data, dict):
                    debug_port = data.get('remote_port')
                if not debug_port:
                    debug_port = response.get('remote_port') or response.get('debug_port')
            if not debug_port:
                raise ValueError("No remote_port/debug_port returned from openProfile")
        except Exception as e:
            print(f"Failed to open profile {profile_uuid}: {e}")
            raise

        # Retry connection with exponential backoff
        for attempt in range(max_retries):
            try:
                # Launch Playwright and connect to existing browser
                playwright = sync_playwright().start()
                browser = playwright.chromium.connect_over_cdp(f"http://127.0.0.1:{debug_port}")
                
                # Get the default context and page, or create new ones
                contexts = browser.contexts
                if contexts:
                    context = contexts[0]
                    pages = context.pages
                    if pages:
                        page = pages[0]
                    else:
                        page = context.new_page()
                else:
                    context = browser.new_context()
                    page = context.new_page()
                
                print(f"Successfully connected to Hidemium profile {profile_uuid} on port {debug_port}")
                
                # Store references for cleanup
                page._hidemium_cleanup = {
                    'playwright': playwright,
                    'browser': browser,
                    'context': context,
                    'profile_uuid': profile_uuid,
                    'client': self
                }
                
                return page
                
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"Connection attempt {attempt + 1} failed, retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    print(f"Failed to connect to profile after {max_retries} attempts: {e}")
                    raise

    def get_or_create_profile(self, name: str, config: Optional[Dict[str, Any]] = None) -> str:
        """
        Get existing profile by name or create new one
        
        Args:
            name: Profile name to search for or create
            config: Configuration for new profile if creation is needed
            
        Returns:
            Profile UUID
        """
        # Search for existing profile by name
        try:
            profiles_response = self.list_profiles(limit=100)
            profiles = profiles_response.get('data', [])
            
            for profile in profiles:
                if profile.get('name') == name:
                    print(f"Found existing profile '{name}' with UUID: {profile['uuid']}")
                    return profile['uuid']
                    
        except Exception as e:
            print(f"Error searching for existing profiles: {e}")

        # Create new profile if not found
        try:
            print(f"Creating new Hidemium profile: {name}")
            create_response = self.create_profile(name, config)
            profile_uuid = create_response.get('uuid')
            
            if not profile_uuid:
                raise ValueError("No UUID returned from profile creation")
                
            print(f"Created new profile '{name}' with UUID: {profile_uuid}")
            return profile_uuid
            
        except Exception as e:
            print(f"Failed to create profile '{name}': {e}")
            raise

    def cleanup_page(self, page: Page, delete_profile: bool = False) -> None:
        """
        Cleanup Playwright resources and close Hidemium profile
        
        Args:
            page: Playwright page instance to cleanup
            delete_profile: Whether to delete the profile after closing
        """
        try:
            cleanup_info = getattr(page, '_hidemium_cleanup', None)
            if cleanup_info:
                profile_uuid = cleanup_info['profile_uuid']
                
                # Close Playwright resources
                try:
                    cleanup_info['context'].close()
                except Exception:
                    pass
                
                try:
                    cleanup_info['browser'].close()
                except Exception:
                    pass
                
                try:
                    cleanup_info['playwright'].stop()
                except Exception:
                    pass
                
                # Close Hidemium profile
                try:
                    self.close_profile(profile_uuid)
                    print(f"Closed Hidemium profile: {profile_uuid}")
                except Exception as e:
                    print(f"Warning: Failed to close profile: {e}")
                
                # Delete profile if requested
                if delete_profile:
                    try:
                        self.delete_profile(profile_uuid)
                        print(f"Deleted temporary Hidemium profile: {profile_uuid}")
                    except Exception as e:
                        print(f"Warning: Failed to delete profile {profile_uuid}: {e}")
            
        except Exception as e:
            print(f"Error during cleanup: {e}")

    def inject_mouse_tracker(self, page: Page) -> bool:
        """
        Inject JavaScript mouse tracker overlay into Hidemium browser page
        Hiển thị chấm đỏ trực tiếp trên trang web để theo dõi vị trí chuột
        
        Args:
            page: Playwright page instance connected to Hidemium profile
            
        Returns:
            True if injection successful, False otherwise
        """
        try:
            # JavaScript code để tạo overlay chấm đỏ
            mouse_tracker_js = """
            (function() {
                // Kiểm tra xem đã có overlay chưa
                if (window.mouseTrackerOverlay) {
                    console.log('Mouse tracker already exists');
                    return;
                }
                
                // Tạo overlay container
                const overlay = document.createElement('div');
                overlay.id = 'mouseTrackerOverlay';
                overlay.style.cssText = `
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    pointer-events: none;
                    z-index: 999999;
                    overflow: hidden;
                `;
                
                // Tạo chấm đỏ
                const dot = document.createElement('div');
                dot.id = 'mouseTrackerDot';
                dot.style.cssText = `
                    position: absolute;
                    width: 12px;
                    height: 12px;
                    background: red;
                    border: 2px solid darkred;
                    border-radius: 50%;
                    transform: translate(-50%, -50%);
                    pointer-events: none;
                    z-index: 1000000;
                    box-shadow: 0 0 10px rgba(255,0,0,0.5);
                    transition: all 0.1s ease;
                `;
                
                // Tạo crosshair lines
                const horizontalLine = document.createElement('div');
                horizontalLine.id = 'mouseTrackerHorizontal';
                horizontalLine.style.cssText = `
                    position: absolute;
                    height: 1px;
                    width: 100%;
                    background: red;
                    opacity: 0.5;
                    pointer-events: none;
                    z-index: 999999;
                `;
                
                const verticalLine = document.createElement('div');
                verticalLine.id = 'mouseTrackerVertical';
                verticalLine.style.cssText = `
                    position: absolute;
                    width: 1px;
                    height: 100%;
                    background: red;
                    opacity: 0.5;
                    pointer-events: none;
                    z-index: 999999;
                `;
                
                // Thêm vào overlay
                overlay.appendChild(horizontalLine);
                overlay.appendChild(verticalLine);
                overlay.appendChild(dot);
                
                // Thêm vào body
                document.body.appendChild(overlay);
                
                // Theo dõi chuột
                let mouseX = 0, mouseY = 0;
                
                document.addEventListener('mousemove', function(e) {
                    mouseX = e.clientX;
                    mouseY = e.clientY;
                    
                    // Cập nhật vị trí chấm đỏ
                    dot.style.left = mouseX + 'px';
                    dot.style.top = mouseY + 'px';
                    
                    // Cập nhật crosshair
                    horizontalLine.style.top = mouseY + 'px';
                    verticalLine.style.left = mouseX + 'px';
                    
                    // Thêm hiệu ứng trail
                    dot.style.boxShadow = '0 0 20px rgba(255,0,0,0.8), 0 0 40px rgba(255,0,0,0.4)';
                    
                    // Reset hiệu ứng sau 100ms
                    setTimeout(() => {
                        dot.style.boxShadow = '0 0 10px rgba(255,0,0,0.5)';
                    }, 100);
                });
                
                // Theo dõi scroll để cập nhật vị trí
                window.addEventListener('scroll', function() {
                    // Cập nhật vị trí chấm đỏ khi scroll
                    dot.style.left = mouseX + 'px';
                    dot.style.top = mouseY + 'px';
                    horizontalLine.style.top = mouseY + 'px';
                    verticalLine.style.left = mouseX + 'px';
                });
                
                // Lưu reference
                window.mouseTrackerOverlay = overlay;
                window.mouseTrackerDot = dot;
                window.mouseTrackerHorizontal = horizontalLine;
                window.mouseTrackerVertical = verticalLine;
                
                console.log('✅ Mouse tracker overlay injected successfully into Hidemium browser!');
                console.log('🔴 Red dot will follow your mouse movements');
            })();
            """
            
            # Inject JavaScript vào page
            page.evaluate(mouse_tracker_js)
            print(f"✅ Injected mouse tracker into Hidemium browser: {page.url}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to inject mouse tracker: {e}")
            return False
    
    def remove_mouse_tracker(self, page: Page) -> bool:
        """
        Remove mouse tracker overlay from Hidemium browser page
        
        Args:
            page: Playwright page instance
            
        Returns:
            True if removal successful, False otherwise
        """
        try:
            remove_js = """
            if (window.mouseTrackerOverlay) {
                window.mouseTrackerOverlay.remove();
                window.mouseTrackerOverlay = null;
                window.mouseTrackerDot = null;
                window.mouseTrackerHorizontal = null;
                window.mouseTrackerVertical = null;
                console.log('✅ Mouse tracker overlay removed from Hidemium browser');
            }
            """
            page.evaluate(remove_js)
            print(f"✅ Removed mouse tracker from Hidemium browser: {page.url}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to remove mouse tracker: {e}")
            return False
