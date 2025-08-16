#!/usr/bin/env python3
"""
GoLogin Example - Demo GoLogin client functionality
Based on the existing Hidemium examples
"""

import os
import sys
import time
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.gologin_client import GoLoginClient
from app.config_loader import load_config_from_file


def demo_gologin_basic():
    """Demo basic GoLogin functionality"""
    print("🚀 GoLogin Basic Demo")
    print("=" * 50)
    
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
    
    # Demo 1: List profiles
    print("\n📋 Demo 1: Listing profiles...")
    try:
        profiles = client.list_profiles(limit=5)
        print(f"✅ Found {len(profiles.get('data', []))} profiles")
        for profile in profiles.get('data', [])[:3]:  # Show first 3
            print(f"  - {profile.get('name', 'Unknown')} (ID: {profile.get('id', 'Unknown')})")
    except Exception as e:
        print(f"❌ Failed to list profiles: {e}")
    
    # Demo 2: Create a test profile
    print("\n🆕 Demo 2: Creating test profile...")
    try:
        profile_name = f"test_profile_{int(time.time())}"
        profile_config = client.build_default_profile_config(
            name=profile_name,
            os_type="win",
            language="en-US"
        )
        
        created_profile = client.create_profile_custom(profile_config)
        profile_id = created_profile.get('id')
        print(f"✅ Created test profile: {profile_name} (ID: {profile_id})")
        
        # Demo 3: Get profile details
        print("\n🔍 Demo 3: Getting profile details...")
        profile_details = client.get_profile_by_id(profile_id)
        print(f"✅ Profile details: {profile_details.get('name')} - {profile_details.get('platform')}")
        
        # Demo 4: Update profile
        print("\n✏️ Demo 4: Updating profile...")
        update_response = client.update_profile(profile_id, {"notes": "Updated via API demo"})
        print(f"✅ Profile updated successfully")
        
        # Demo 5: Delete test profile
        print("\n🗑️ Demo 5: Cleaning up test profile...")
        delete_response = client.delete_profile(profile_id)
        print(f"✅ Test profile deleted successfully")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")


def demo_gologin_with_proxy():
    """Demo GoLogin with proxy configuration"""
    print("\n🌐 GoLogin Proxy Demo")
    print("=" * 50)
    
    # Load configuration
    try:
        config = load_config_from_file("config.json")
        access_token = config.get("gologin_access_token")
        if not access_token:
            print("❌ GoLogin access token not found in config.json")
            return
        
        # Check if proxy is configured
        proxy_server = config.get("proxy")
        if not proxy_server:
            print("⚠️ No proxy configured, skipping proxy demo")
            return
            
        print(f"✅ Using proxy: {proxy_server}")
        
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
    
    # Demo: Create profile with proxy
    print("\n🆕 Creating profile with proxy...")
    try:
        profile_name = f"proxy_test_{int(time.time())}"
        
        # Parse proxy configuration
        proxy_config = {
            "server": proxy_server,
            "scheme": config.get("proxy_scheme", "http")
        }
        
        profile_config = client.build_default_profile_config(
            name=profile_name,
            proxy=proxy_config,
            os_type="win",
            language="en-US"
        )
        
        created_profile = client.create_profile_custom(profile_config)
        profile_id = created_profile.get('id')
        print(f"✅ Created proxy profile: {profile_name} (ID: {profile_id})")
        
        # Show proxy configuration
        profile_details = client.get_profile_by_id(profile_id)
        proxy_info = profile_details.get('proxy', {})
        if proxy_info:
            print(f"  - Proxy mode: {proxy_info.get('mode')}")
            print(f"  - Proxy host: {proxy_info.get('host')}:{proxy_info.get('port')}")
        
        # Clean up
        client.delete_profile(profile_id)
        print(f"✅ Proxy test profile deleted")
        
    except Exception as e:
        print(f"❌ Proxy demo failed: {e}")


def demo_gologin_profile_management():
    """Demo GoLogin profile management features"""
    print("\n⚙️ GoLogin Profile Management Demo")
    print("=" * 50)
    
    # Load configuration
    try:
        config = load_config_from_file("config.json")
        access_token = config.get("gologin_access_token")
        if not access_token:
            print("❌ GoLogin access token not found in config.json")
            return
        
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
    
    # Demo: Profile lifecycle management
    print("\n🔄 Profile Lifecycle Demo...")
    try:
        # Create profile
        profile_name = f"lifecycle_test_{int(time.time())}"
        profile_config = client.build_default_profile_config(
            name=profile_name,
            os_type="win",
            language="en-US"
        )
        
        created_profile = client.create_profile_custom(profile_config)
        profile_id = created_profile.get('id')
        print(f"✅ Created profile: {profile_name}")
        
        # Check status
        status = client.get_profile_status(profile_id)
        print(f"✅ Profile status: {status.get('status', 'Unknown')}")
        
        # Start profile (this would normally launch the browser)
        print("🚀 Starting profile...")
        start_response = client.start_profile(profile_id)
        print(f"✅ Profile started: {start_response.get('wsEndpoint', 'Unknown')}")
        
        # Wait a bit
        time.sleep(2)
        
        # Stop profile
        print("⏹️ Stopping profile...")
        stop_response = client.stop_profile(profile_id)
        print(f"✅ Profile stopped")
        
        # Clean up
        client.delete_profile(profile_id)
        print(f"✅ Profile deleted")
        
    except Exception as e:
        print(f"❌ Profile management demo failed: {e}")


def main():
    """Main demo function"""
    print("🎯 GoLogin Client Demo")
    print("=" * 60)
    
    # Check if config exists
    if not os.path.exists("config.json"):
        print("❌ config.json not found")
        print("Please create config.json with your GoLogin access token")
        return
    
    # Run demos
    try:
        demo_gologin_basic()
        demo_gologin_with_proxy()
        demo_gologin_profile_management()
        
        print("\n🎉 All demos completed successfully!")
        print("\n💡 Next steps:")
        print("  1. Set your GoLogin access token in config.json")
        print("  2. Configure proxy settings if needed")
        print("  3. Run the main registration script with ENGINE=gologin")
        
    except KeyboardInterrupt:
        print("\n⏹️ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")


if __name__ == "__main__":
    main()
