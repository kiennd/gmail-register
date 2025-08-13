#!/usr/bin/env python3
"""
Debug script to explore Hidemium API endpoints
"""
import requests
import json

def test_hidemium_api():
    base_url = "http://localhost:2222"
    
    # Test basic connectivity
    print("Testing Hidemium API connectivity...")
    
    # Try some common endpoints
    # Test POST endpoints that might work for starting profiles
    post_endpoints = [
        "/start-profile",
        "/open-profile", 
        "/launch-profile",
        "/start-browser",
        "/open-browser",
        "/connect-profile",
        "/run-profile",
        "/execute-profile",
    ]
    
    # Test payload that might work
    test_payload = {"uuid": "test-uuid-123"}
    
    for endpoint in post_endpoints:
        try:
            url = f"{base_url}{endpoint}"
            print(f"\nTesting POST: {url}")
            response = requests.post(url, json=test_payload, timeout=5)
            print(f"  Status: {response.status_code}")
            if response.status_code != 404:
                try:
                    data = response.json()
                    print(f"  Response: {json.dumps(data, indent=2)[:300]}...")
                except:
                    print(f"  Response: {response.text[:300]}...")
        except Exception as e:
            print(f"  Error: {e}")
    
    print("\n" + "="*50)
    print("API Exploration Summary:")
    print("- Check which endpoints returned 200 status")
    print("- Look for patterns in successful endpoints")
    print("- Update the profile start endpoint accordingly")

if __name__ == "__main__":
    test_hidemium_api()
