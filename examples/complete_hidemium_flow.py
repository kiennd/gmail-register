#!/usr/bin/env python3
"""
Complete demonstration of Hidemium flow: Create → Use → Delete
"""
import sys
import os
import json

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.hidemium_client import HidemiumClient


def main():
    """Demonstrate complete Hidemium flow with custom profile creation"""
    
    print("=== Hidemium Complete Flow Demo ===")
    print("Flow: Create Custom Profile → Use → Delete")
    print()
    
    # Initialize Hidemium client
    client = HidemiumClient(
        base_url="http://localhost:2222",
        api_token=None
    )
    
    profile_uuid = None
    page = None
    
    try:
        # Step 1: Build custom profile configuration
        print("Step 1: Building custom profile configuration...")
        import time
        import uuid
        
        timestamp = int(time.time())
        profile_name = f"demo_profile_{timestamp}_{uuid.uuid4().hex[:8]}"
        
        profile_config = client.build_default_profile_config(
            name=profile_name,
            os_type="win",
            language="en-US"
        )
        
        # Customize profile settings
        profile_config.update({
            "browser": "chrome",
            "version": "136",
            "canvas": "noise",
            "webGLImage": "false",
            "resolution": "1920x1080",
            "deviceMemory": 8,
            "hardwareConcurrency": 8,
            "StartURL": "https://accounts.google.com"
        })
        
        print(f"✓ Profile name: {profile_name}")
        print(f"✓ OS: {profile_config['os']} {profile_config['osVersion']}")
        print(f"✓ Browser: {profile_config['browser']} {profile_config['version']}")
        print(f"✓ Resolution: {profile_config['resolution']}")
        print()
        
        # Step 2: Create profile with custom API
        print("Step 2: Creating custom profile via API...")
        print("⚠️  Note: API rate limit is 50 requests per minute")
        
        response = client.create_profile_custom(
            profile_config=profile_config,
            is_local=True  # Create cloud profile
        )
        
        if response.get("type") == "success":
            content = response.get("content", {})
            profile_uuid = content.get("uuid") or content.get("id")
            print(f"✓ Profile created successfully!")
            print(f"✓ Profile UUID: {profile_uuid}")
        else:
            raise ValueError(f"Profile creation failed: {response}")
        print()
        
        # Step 3: Launch profile and connect
        print("Step 3: Launching profile and connecting via Playwright...")
        page = client.connect_to_profile(profile_uuid)
        print("✓ Connected to profile via Chrome DevTools Protocol")
        print()
        
        # Step 4: Use profile for automation
        print("Step 4: Using profile for automation...")
        print("→ Navigating to Google Accounts...")
        page.goto("https://accounts.google.com", timeout=30000)
        
        # Wait for page to load
        page.wait_for_timeout(3000)
        
        # Check page title
        title = page.title()
        print(f"✓ Page loaded: {title}")
        
        # Simple interaction test
        try:
            # Look for sign-in elements
            signin_elements = page.locator('[data-l10n-id="signin"], [aria-label*="Sign in"], text="Sign in"').count()
            print(f"✓ Sign-in elements found: {signin_elements}")
        except Exception:
            print("→ Page interaction test skipped")
        
        print("✓ Profile automation test completed successfully!")
        print()
        
        # Step 5: Cleanup and delete profile
        print("Step 5: Cleaning up and deleting profile...")
        client.cleanup_page(page, delete_profile=True)
        print(f"✓ Profile {profile_uuid} deleted successfully")
        print("✓ All Playwright resources cleaned up")
        print()
        
        print("=== Demo Completed Successfully! ===")
        print()
        print("Summary:")
        print(f"• Created custom profile: {profile_name}")
        print(f"• Connected via CDP and tested automation")
        print(f"• Cleaned up and deleted profile")
        print()
        print("This demonstrates the complete Hidemium flow:")
        print("Create → Configure → Use → Delete")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        
        # Emergency cleanup
        if page and profile_uuid:
            try:
                print("Attempting emergency cleanup...")
                client.cleanup_page(page, delete_profile=True)
                print("✓ Emergency cleanup completed")
            except Exception:
                print("❌ Emergency cleanup failed")
                if profile_uuid:
                    try:
                        client.delete_profile(profile_uuid)
                        print(f"✓ Manually deleted profile {profile_uuid}")
                    except Exception:
                        print(f"❌ Failed to delete profile {profile_uuid}")
        
        return 1


if __name__ == "__main__":
    sys.exit(main())
