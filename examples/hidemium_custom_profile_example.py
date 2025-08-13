#!/usr/bin/env python3
"""
Example script demonstrating Hidemium custom profile creation with cookie import
"""
import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.hidemium_client import HidemiumClient


def main():
    """Example of creating custom Hidemium profiles"""
    
    # Initialize Hidemium client
    client = HidemiumClient(
        base_url="http://localhost:2222",
        api_token=None  # Set if your Hidemium requires authentication
    )
    
    try:
        # Step 1: Build custom profile configuration
        profile_config = client.build_default_profile_config(
            name="custom_profile_example",
            os_type="win",
            language="en-US",
            proxy={
                "server": "http://proxy.example.com:8080",
                "username": "user",
                "password": "pass"
            }
        )
        
        # You can customize any aspect of the profile
        profile_config.update({
            "browser": "chrome",
            "version": "136",
            "canvas": "noise",
            "webGLImage": "false",
            "resolution": "1920x1080",
            "deviceMemory": 16,
            "hardwareConcurrency": 16,
        })
        
        print("Profile configuration:")
        for key, value in profile_config.items():
            print(f"  {key}: {value}")
        
        # Step 2: Create profile with custom configuration
        print("\nCreating custom profile...")
        response = client.create_profile_custom(
            profile_config=profile_config,
            is_local=False  # Create cloud profile
        )
        
        if response.get("type") == "success":
            content = response.get("content", {})
            profile_uuid = content.get("uuid") or content.get("id")
            print(f"Successfully created profile with UUID: {profile_uuid}")
            
            # Step 3: Connect to profile and test
            print("Connecting to profile...")
            page = client.connect_to_profile(profile_uuid)
            
            try:
                # Navigate to Google to test profile
                print("Testing profile by navigating to Google...")
                page.goto("https://accounts.google.com")
                page.wait_for_timeout(3000)
                
                # Get page title
                title = page.title()
                print(f"Page title: {title}")
                
                # Check profile is working
                print("Profile test completed successfully!")
                
            finally:
                # Step 4: Cleanup (optional - set delete_profile=True to remove)
                print("Cleaning up...")
                client.cleanup_page(page, delete_profile=False)  # Keep profile for inspection
                print(f"Profile {profile_uuid} kept for inspection")
                
        else:
            print(f"Failed to create profile: {response}")
            return 1
            
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    print("Custom profile creation example completed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
