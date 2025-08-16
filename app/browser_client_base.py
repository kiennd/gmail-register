"""
Base class for browser client implementations
Provides common interface and functionality for different browser automation clients
"""
import json
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from playwright.sync_api import Page


class BrowserClientBase(ABC):
    """
    Abstract base class for browser automation clients
    
    This class defines the common interface and provides shared functionality
    that all browser clients should implement.
    """
    
    def __init__(self, base_url: str, api_token: Optional[str] = None):
        """
        Initialize browser client base
        
        Args:
            base_url: API endpoint for the browser client
            api_token: API token for authentication (if required)
        """
        self.base_url = base_url.rstrip('/')
        self.api_token = api_token
    
    @abstractmethod
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make HTTP request to browser API
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            **kwargs: Additional request parameters
            
        Returns:
            Response JSON from API
        """
        pass
    
    @abstractmethod
    def open_profile(self, profile_uuid: str, command: Optional[str] = None, proxy: Optional[str] = None) -> Dict[str, Any]:
        """
        Open a browser profile
        
        Args:
            profile_uuid: UUID of the profile to open
            command: Optional command line arguments
            proxy: Optional proxy configuration
            
        Returns:
            Response from profile opening operation
        """
        pass
    
    @abstractmethod
    def close_profile(self, profile_uuid: str) -> Dict[str, Any]:
        """
        Close a browser profile
        
        Args:
            profile_uuid: UUID of the profile to close
            
        Returns:
            Response confirming profile closure
        """
        pass
    
    @abstractmethod
    def delete_profile(self, profile_uuid: str, **kwargs) -> Dict[str, Any]:
        """
        Delete a browser profile
        
        Args:
            profile_uuid: UUID of the profile to delete
            **kwargs: Additional deletion parameters
            
        Returns:
            Deletion confirmation response
        """
        pass
    
    @abstractmethod
    def create_browser_profile(self, profile_name: str, **kwargs) -> Dict[str, Any]:
        """
        Create a new browser profile
        
        Args:
            profile_name: Name for the new profile
            **kwargs: Additional creation parameters
            
        Returns:
            Response with created profile details
        """
        pass
    
    @abstractmethod
    def connect_to_profile(self, profile_uuid: str, **kwargs) -> Page:
        """
        Connect to an opened browser profile using Playwright
        
        Args:
            profile_uuid: UUID of the profile to connect to
            **kwargs: Additional connection parameters
            
        Returns:
            Playwright Page instance connected to the profile
        """
        pass
    
    def cleanup_page(self, page: Page, delete_profile: bool = False) -> None:
        """
        Cleanup Playwright resources and close browser profile
        
        Args:
            page: Playwright page instance to cleanup
            delete_profile: Whether to delete the profile after closing
        """
        try:
            # Try different cleanup attribute names for compatibility
            cleanup_info = getattr(page, '_browser_cleanup', None) or getattr(page, '_hidemium_cleanup', None)
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
                
                # Close browser profile
                try:
                    self.close_profile(profile_uuid)
                    print(f"Closed browser profile: {profile_uuid}")
                except Exception as e:
                    print(f"Warning: Failed to close profile: {e}")
                
                # Delete profile if requested
                if delete_profile:
                    try:
                        self.delete_profile(profile_uuid)
                        print(f"Deleted temporary browser profile: {profile_uuid}")
                    except Exception as e:
                        print(f"Warning: Failed to delete profile {profile_uuid}: {e}")
            
        except Exception as e:
            print(f"Error during cleanup: {e}")
    
    def inject_mouse_tracker(self, page: Page) -> bool:
        """
        Inject JavaScript mouse tracker overlay into browser page
        
        Args:
            page: Playwright page instance connected to browser profile
            
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
                
                console.log('✅ Mouse tracker overlay injected successfully into browser!');
                console.log('🔴 Red dot will follow your mouse movements');
            })();
            """
            
            # Inject JavaScript vào page
            page.evaluate(mouse_tracker_js)
            print(f"✅ Injected mouse tracker into browser: {page.url}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to inject mouse tracker: {e}")
            return False
    
    def remove_mouse_tracker(self, page: Page) -> bool:
        """
        Remove mouse tracker overlay from browser page
        
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
                console.log('✅ Mouse tracker overlay removed from browser');
            }
            """
            page.evaluate(remove_js)
            print(f"✅ Removed mouse tracker from browser: {page.url}")
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
    