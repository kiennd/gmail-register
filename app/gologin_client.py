"""
GoLogin API client for remote profile management
Based on: https://gologin.com/docs/api
"""
import requests
import json
import time
import os
from typing import Dict, Any, Optional, List
from playwright.sync_api import sync_playwright, Browser, Page


class GoLoginClient:
    def __init__(self, access_token: str, base_url: str = "https://api.gologin.com"):
        """
        Initialize GoLogin API client
        
        Args:
            access_token: GoLogin API access token
            base_url: GoLogin API endpoint (default: https://api.gologin.com)
        """
        self.base_url = base_url.rstrip('/')
        self.access_token = access_token
        self.session = requests.Session()
        self._last_request_time = 0
        self._request_count = 0
        self._rate_limit_window = 60  # 1 minute
        self._rate_limit_max = 100    # 100 requests per minute for GoLogin
        
        # Set authorization header
        self.session.headers.update({
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        })

    def _check_rate_limit(self) -> None:
        """Check and handle API rate limiting (100 requests per minute)"""
        current_time = time.time()
        
        # Reset counter if window has passed
        if current_time - self._last_request_time > self._rate_limit_window:
            self._request_count = 0
            self._last_request_time = current_time
        
        # Check if we're approaching rate limit
        if self._request_count >= self._rate_limit_max:
            sleep_time = self._rate_limit_window - (current_time - self._last_request_time)
            if sleep_time > 0:
                print(f"Rate limit reached (100 req/min). Waiting {sleep_time:.1f}s...")
                time.sleep(sleep_time)
                self._request_count = 0
                self._last_request_time = time.time()
        
        self._request_count += 1

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to GoLogin API with rate limiting"""
        # Check rate limit before making request
        self._check_rate_limit()
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"GoLogin API error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_body = e.response.text
                    print(f"Error response body: {error_body}")
                except Exception:
                    pass
            raise
        except json.JSONDecodeError as e:
            print(f"Invalid JSON response: {e}")
            raise

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
        return self._make_request('GET', '/browser', params=params)

    def get_profile_by_id(self, profile_id: str) -> Dict[str, Any]:
        """
        Get profile details by ID
        
        Args:
            profile_id: Profile ID
            
        Returns:
            Detailed profile information
        """
        return self._make_request('GET', f'/browser/{profile_id}')

    def create_profile(self, name: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a new profile
        
        Args:
            name: Profile name
            config: Optional profile configuration
            
        Returns:
            Created profile information including ID
        """
        payload = {"name": name}
        if config:
            payload.update(config)
            
        return self._make_request('POST', '/browser', json=payload)

    def create_profile_custom(self, profile_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a custom profile with full configuration
        
        Args:
            profile_config: Complete profile configuration
            
        Returns:
            Created profile information
        """
        return self._make_request('POST', '/browser', json=profile_config)

    def build_default_profile_config(self, name: str, proxy: Optional[Dict[str, Any]] = None, 
                                   os_type: str = "win", language: str = "en-US") -> Dict[str, Any]:
        """
        Build a default profile configuration for Gmail registration
        
        Args:
            name: Profile name
            proxy: Optional proxy configuration
            os_type: Operating system (win, mac, lin, android, android-cloud)
            language: Browser language (e.g., "en-US", "vi-VN")
            
        Returns:
            Complete profile configuration ready for create_profile_custom
        """
        # Default configuration optimized for Gmail registration
        config = {
            "name": name,
            "notes": f"Gmail registration profile - {name}",
            "tags": ["gmail", "registration"],
            "os": os_type,
            "browserType": "chrome",
            "userAgent": "",  # Auto-generated by GoLogin

            "canvas": {"mode": "noise"},
            "webGL": {"mode": "noise"},
            "webGLMetadata": {"mode": "mask"},
            "webGLVendor": {"mode": "noise"},
            "webGLRenderer": {"mode": "noise"},
            "clientRects": {"mode": "noise"},
            "audioContext": {"mode": "noise"},
            "mediaDevices": {"mode": "noise"},
            "webRTC": {"mode": "disabled"},
            "timezone": {
                "id": "Asia/Ho_Chi_Minh" if language.startswith("vi") else "America/New_York",
                "gmtOffset": 7 if language.startswith("vi") else -5
            },
            "geolocation": {
                "mode": "prompt",
                "latitude": 10.8231 if language.startswith("vi") else 40.7128,
                "longitude": 106.6297 if language.startswith("vi") else -74.0060,
                "accuracy": 100
            },
            "permissions": {
                "notifications": "prompt",
                "geolocation": "prompt",
                "microphone": "prompt",
                "camera": "prompt"
            },
            "navigator": {
                "hardwareConcurrency": 8,
                "deviceMemory": 8,
                "maxTouchPoints": 0,
                "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                "resolution": "1920x1080",
                "language": language,
                "platform": "Win32"
            },
            "startUrl": "https://workspace.google.com/intl/en-US/gmail/",
            "proxy": None
        }
        
        # Add proxy if provided
        if proxy and proxy.get("server"):
            server = proxy.get("server", "")
            username = proxy.get("username", "")
            password = proxy.get("password", "")
            scheme = proxy.get("scheme", "http").lower()
            
            # Parse proxy details
            if "://" in server:
                proxy_type, host_port = server.split("://", 1)
            else:
                proxy_type = scheme
                host_port = server
            
            if ":" in host_port:
                host, port = host_port.split(":", 1)
            else:
                host = host_port
                port = "8080"
            
            # Format proxy for GoLogin
            config["proxy"] = {
                "mode": "http" if proxy_type in ["http", "https"] else "socks5",
                "host": host,
                "port": int(port),
                "username": username if username else None,
                "password": password if password else None
            }
            
        return config

    def update_profile(self, profile_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update profile settings
        
        Args:
            profile_id: Profile ID
            updates: Fields to update
            
        Returns:
            Updated profile information
        """
        return self._make_request('PUT', f'/browser/{profile_id}', json=updates)

    def delete_profile(self, profile_id: str) -> Dict[str, Any]:
        """
        Delete a profile
        
        Args:
            profile_id: Profile ID to delete
            
        Returns:
            Deletion confirmation
        """
        return self._make_request('DELETE', f'/browser/{profile_id}')

    def start_profile(self, profile_id: str, port: Optional[int] = None) -> Dict[str, Any]:
        """
        Start a GoLogin profile and get connection details
        
        Args:
            profile_id: Profile ID to start
            port: Optional port to use
            
        Returns:
            Profile start response with connection details
        """
        payload = {"profileId": profile_id}
        if port:
            payload["port"] = port
            
        return self._make_request('POST', '/browser/start-remote-debugging', json=payload)

    def stop_profile(self, profile_id: str) -> Dict[str, Any]:
        """
        Stop a running profile
        
        Args:
            profile_id: Profile ID to stop
            
        Returns:
            Stop confirmation
        """
        return self._make_request('POST', f'/browser/{profile_id}/stop')

    def get_profile_status(self, profile_id: str) -> Dict[str, Any]:
        """
        Get profile running status
        
        Args:
            profile_id: Profile ID to check
            
        Returns:
            Profile status information
        """
        return self._make_request('GET', f'/browser/{profile_id}/status')

    def connect_to_profile(self, profile_id: str, port: Optional[int] = None, max_retries: int = 10) -> Page:
        """
        Connect to a started GoLogin profile using Playwright
        
        Args:
            profile_id: Profile ID to connect to
            port: Optional port to use
            max_retries: Maximum number of connection attempts
            
        Returns:
            Playwright Page instance connected to the profile
        """
        # Start the profile first
        try:
            start_response = self.start_profile(profile_id, port=port)
            debug_port = start_response.get('wsEndpoint', '').split(':')[-1]
            if not debug_port.isdigit():
                raise ValueError("No valid debug port returned from start_profile")
            debug_port = int(debug_port)
        except Exception as e:
            print(f"Failed to start profile {profile_id}: {e}")
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
                
                print(f"Successfully connected to GoLogin profile {profile_id} on port {debug_port}")
                
                # Store references for cleanup
                page._gologin_cleanup = {
                    'playwright': playwright,
                    'browser': browser,
                    'context': context,
                    'profile_id': profile_id,
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
            Profile ID
        """
        # Search for existing profile by name
        try:
            profiles_response = self.list_profiles(limit=100)
            profiles = profiles_response.get('data', [])
            
            for profile in profiles:
                if profile.get('name') == name:
                    print(f"Found existing profile '{name}' with ID: {profile['id']}")
                    return profile['id']
                    
        except Exception as e:
            print(f"Error searching for existing profiles: {e}")

        # Create new profile if not found
        try:
            print(f"Creating new GoLogin profile: {name}")
            create_response = self.create_profile(name, config)
            profile_id = create_response.get('id')
            
            if not profile_id:
                raise ValueError("No ID returned from profile creation")
                
            print(f"Created new profile '{name}' with ID: {profile_id}")
            return profile_id
            
        except Exception as e:
            print(f"Failed to create profile '{name}': {e}")
            raise

    def cleanup_page(self, page: Page, delete_profile: bool = False) -> None:
        """
        Cleanup Playwright resources and stop GoLogin profile
        
        Args:
            page: Playwright page instance to cleanup
            delete_profile: Whether to delete the profile after stopping
        """
        try:
            cleanup_info = getattr(page, '_gologin_cleanup', None)
            if cleanup_info:
                profile_id = cleanup_info['profile_id']
                
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
                
                # Stop GoLogin profile
                try:
                    self.stop_profile(profile_id)
                    print(f"Stopped GoLogin profile: {profile_id}")
                except Exception as e:
                    print(f"Warning: Failed to stop profile: {e}")
                
                # Delete profile if requested
                if delete_profile:
                    try:
                        self.delete_profile(profile_id)
                        print(f"Deleted temporary GoLogin profile: {profile_id}")
                    except Exception as e:
                        print(f"Warning: Failed to delete profile {profile_id}: {e}")
            
        except Exception as e:
            print(f"Error during cleanup: {e}")

    def inject_mouse_tracker(self, page: Page) -> bool:
        """
        Inject JavaScript mouse tracker overlay into GoLogin browser page
        Hiển thị chấm đỏ trực tiếp trên trang web để theo dõi vị trí chuột
        
        Args:
            page: Playwright page instance connected to GoLogin profile
            
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
                
                console.log('✅ Mouse tracker overlay injected successfully into GoLogin browser!');
                console.log('🔴 Red dot will follow your mouse movements');
            })();
            """
            
            # Inject JavaScript vào page
            page.evaluate(mouse_tracker_js)
            print(f"✅ Injected mouse tracker into GoLogin browser: {page.url}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to inject mouse tracker: {e}")
            return False
    
    def remove_mouse_tracker(self, page: Page) -> bool:
        """
        Remove mouse tracker overlay from GoLogin browser page
        
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
                console.log('✅ Mouse tracker overlay removed from GoLogin browser');
            }
            """
            page.evaluate(remove_js)
            print(f"✅ Removed mouse tracker from GoLogin browser: {page.url}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to remove mouse tracker: {e}")
            return False

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

    def create_browser_profile(self, profile_name: str, source: str = "gologin_api") -> dict:
        """
        Create a new browser profile using GoLogin API with config loaded from browser_profile_template.json.
        Args:
            profile_name: Name for the new profile
            source: Source string for tracking
        Returns:
            Response JSON from GoLogin API
        """
        template_path = os.path.join(os.path.dirname(__file__), '../browser_profile_template.json')
        with open(template_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        config['name'] = profile_name
        config['notes'] = f"Created via {source} - {profile_name}"
        
        return self._make_request('POST', '/browser', json=config)
