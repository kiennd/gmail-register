"""
Hidemium API client for remote profile management
Based on: https://docs.hidemium.io/hidemium-4/i.-bat-dau-voi-hidemium/api-automation-v4/remote-profile
"""
import requests
import json
import time
from typing import Dict, Any, Optional, List
from playwright.sync_api import sync_playwright, Browser, Page
from .browser_client_base import BrowserClientBase


class HidemiumClient(BrowserClientBase):
    def __init__(self, base_url: str = "http://localhost:2222", api_token: Optional[str] = None):
        """
        Initialize Hidemium API client
        
        Args:
            base_url: Hidemium API endpoint (default: http://localhost:2222)
            api_token: API token for authentication (if required)
        """
        super().__init__(base_url, api_token)
        self.session = requests.Session()
        
        if self.api_token:
            self.session.headers.update({'Authorization': f'Bearer {self.api_token}'})

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
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

    def open_profile(self, profile_uuid: str, command: Optional[str] = None, proxy: Optional[str] = None) -> Dict[str, Any]:
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



    def delete_profile(self, profile_uuid: str, is_local: Optional[bool] = None) -> Dict[str, Any]:
        """
        Delete a profile using Hidemium destroy endpoint
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



    def create_browser_profile(self, profile_name: str, is_local: bool = True) -> dict:
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
        config['config']['name'] = profile_name
        params = {
            "_source": "hidemium_application_ui",
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
