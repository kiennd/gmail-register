#!/usr/bin/env python3
"""
GoLogin Gmail Registration Example
Demo using GoLogin for Gmail account creation
"""

import os
import sys
import time
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.gologin_client import GoLoginClient
from app.config_loader import load_config_from_file
from app.generator import generate_name, generate_username, generate_password


def create_gologin_profile_for_gmail(client: GoLoginClient, profile_name: str, proxy_config: dict = None):
    """Create a GoLogin profile optimized for Gmail registration"""
    
    # Build profile configuration
    profile_config = client.build_default_profile_config(
        name=profile_name,
        proxy=proxy_config,
        os_type="win",
        language="en-US"
    )
    
    # Optimize for Gmail registration
    profile_config.update({
        "startUrl": "https://workspace.google.com/intl/en-US/gmail/",
        "notes": f"Gmail registration profile - {profile_name}",
        "tags": ["gmail", "registration", "automation"],
        "navigator": {
            "hardwareConcurrency": 8,
            "deviceMemory": 8,
            "maxTouchPoints": 0,
            "doNotTrack": "1"
        },
        "screen": {
            "width": 1920,
            "height": 1080,
            "colorDepth": 24,
            "pixelDepth": 24
        },
        "permissions": {
            "notifications": "prompt",
            "geolocation": "prompt",
            "microphone": "prompt",
            "camera": "prompt",
            "midi": "prompt",
            "payment": "prompt",
            "usb": "prompt"
        },
        "webRTC": {
            "mode": "alerted",
            "ipAddress": "1.1.1.1"
        }
    })
    
    # Create profile
    response = client.create_profile_custom(profile_config)
    profile_id = response.get('id')
    
    if not profile_id:
        raise ValueError(f"Failed to create profile: {response}")
    
    print(f"✅ Created GoLogin profile: {profile_name} (ID: {profile_id})")
    return profile_id


def run_gmail_registration_with_gologin():
    """Run Gmail registration using GoLogin"""
    print("🚀 GoLogin Gmail Registration Demo")
    print("=" * 60)
    
    # Load configuration
    try:
        config = load_config_from_file("config.json")
        access_token = config.get("gologin_access_token")
        if not access_token:
            print("❌ GoLogin access token not found in config.json")
            print("Please add your GoLogin access token to config.json")
            return
        
        print(f"✅ Using GoLogin API: {config.get('gologin_api_url')}")
        
    except Exception as e:
        print(f"❌ Failed to load config: {e}")
        return
    
    # Initialize GoLogin client
    try:
        client = GoLoginClient(access_token=access_token)
        print("✅ GoLogin client initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize GoLogin client: {e}")
        return
    
    # Generate test data
    first_name, last_name = generate_name()
    username = generate_username(first_name, last_name)
    password = generate_password(12)
    
    print(f"\n👤 Generated test data:")
    print(f"  - First Name: {first_name}")
    print(f"  - Last Name: {last_name}")
    print(f"  - Username: {username}")
    print(f"  - Password: {password}")
    
    # Build proxy configuration if available
    proxy_config = None
    if config.get("proxy"):
        proxy_config = {
            "server": config.get("proxy"),
            "username": config.get("proxy_username"),
            "password": config.get("proxy_password"),
            "scheme": config.get("proxy_scheme", "http")
        }
        print(f"🌐 Using proxy: {config.get('proxy')}")
    
    # Create GoLogin profile
    profile_name = f"gmail_register_{username}_{int(time.time())}"
    try:
        profile_id = create_gologin_profile_for_gmail(client, profile_name, proxy_config)
        
        print(f"\n🔄 Profile created successfully!")
        print(f"  - Profile ID: {profile_id}")
        print(f"  - Profile Name: {profile_name}")
        
        # Start profile
        print("\n🚀 Starting GoLogin profile...")
        start_response = client.start_profile(profile_id)
        ws_endpoint = start_response.get('wsEndpoint')
        
        if not ws_endpoint:
            raise ValueError("No WebSocket endpoint returned")
        
        print(f"✅ Profile started successfully!")
        print(f"  - WebSocket Endpoint: {ws_endpoint}")
        
        # Connect using Playwright
        print("\n🔗 Connecting to profile with Playwright...")
        page = client.connect_to_profile(profile_id)
        
        print(f"✅ Connected to profile successfully!")
        print(f"  - Current URL: {page.url}")
        
        # Inject mouse tracker for debugging
        print("\n🔴 Injecting mouse tracker...")
        client.inject_mouse_tracker(page)
        
        # Navigate to Gmail signup
        print("\n📧 Navigating to Gmail signup...")
        signup_url = "https://accounts.google.com/signup/v2/createaccount?service=mail&continue=https://mail.google.com/mail/&flowName=GlifWebSignIn&flowEntry=SignUp"
        page.goto(signup_url, timeout=60000)
        
        print(f"✅ Navigated to Gmail signup: {page.url}")
        
        # Wait for page to load
        print("\n⏳ Waiting for page to load...")
        page.wait_for_selector('input[name="firstName"]', timeout=30000)
        
        print("✅ Gmail signup page loaded successfully!")
        print("\n🎯 Ready for manual registration or automation!")
        print("   - The profile is now running and connected")
        print("   - You can manually complete the registration")
        print("   - Or implement automation using Playwright commands")
        
        # Keep the profile running for manual testing
        print("\n⏸️ Profile will remain open for manual testing...")
        print("   Press Ctrl+C to stop and cleanup")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n⏹️ Stopping profile...")
        
    except Exception as e:
        print(f"❌ Gmail registration demo failed: {e}")
        
    finally:
        # Cleanup
        try:
            if 'page' in locals():
                print("\n🧹 Cleaning up...")
                client.cleanup_page(page, delete_profile=True)
                print("✅ Cleanup completed")
        except Exception as e:
            print(f"⚠️ Warning: Cleanup failed: {e}")


def main():
    """Main function"""
    print("🎯 GoLogin Gmail Registration Example")
    print("=" * 60)
    
    # Check if config exists
    if not os.path.exists("config.json"):
        print("❌ config.json not found")
        print("Please create config.json with your GoLogin access token")
        return
    
    # Run demo
    try:
        run_gmail_registration_with_gologin()
        
    except KeyboardInterrupt:
        print("\n⏹️ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")


if __name__ == "__main__":
    main()
