#!/usr/bin/env python3
"""
Example script demonstrating Hidemium integration with Playwright
"""
import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.hidemium_client import HidemiumClient


def main():
    """Example of using HidemiumClient with Playwright"""
    
    # Initialize Hidemium client
    client = HidemiumClient(
        base_url="http://localhost:2222",
        api_token=None  # Set if your Hidemium requires authentication
    )
    
    try:
        # Create temporary profile (new flow: create -> use -> delete)
        print("Creating temporary Hidemium profile...")
        import uuid
        import time
        
        timestamp = int(time.time())
        unique_name = f"temp_example_{timestamp}_{uuid.uuid4().hex[:8]}"
        
        response = client.create_profile(unique_name, {
            "name": unique_name,
            "proxy": {
                "type": "http",
                "host": "proxy.example.com",
                "port": 8080,
                "username": "user",
                "password": "pass"
            }
        })
        
        profile_uuid = response.get("uuid")
        
        print(f"Using profile: {profile_uuid}")
        
        # Connect to profile using Playwright
        print("Connecting to profile via Playwright...")
        page = client.connect_to_profile(profile_uuid)
        
        try:
            # Example automation
            print("Navigating to Google...")
            page.goto("https://www.google.com")
            
            # Wait for page to load
            page.wait_for_selector('input[name="q"]', timeout=10000)
            
            # Type search query
            search_box = page.locator('input[name="q"]')
            search_box.fill("Hidemium browser automation")
            
            # Press Enter
            page.keyboard.press("Enter")
            
            # Wait for results
            page.wait_for_selector('#search', timeout=10000)
            
            print("Search completed successfully!")
            
            # Get page title
            title = page.title()
            print(f"Page title: {title}")
            
        finally:
            # Cleanup Playwright resources and DELETE temporary profile
            print("Cleaning up and deleting temporary profile...")
            client.cleanup_page(page, delete_profile=True)
            
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    print("Example completed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
