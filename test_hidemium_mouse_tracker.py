"""
Test Hidemium Mouse Tracker
Test script để inject chấm đỏ theo dõi chuột vào Hidemium browser
"""
import time
from app.hidemium_client import HidemiumClient

def test_mouse_tracker():
    """Test mouse tracker injection vào Hidemium browser"""
    
    # Khởi tạo Hidemium client
    client = HidemiumClient(base_url="http://localhost:2222")
    
    try:
        print("🚀 Testing Hidemium Mouse Tracker")
        print("=" * 50)
        
        # Tạo hoặc lấy profile
        profile_name = "test_mouse_tracker"
        try:
            profile_uuid = client.get_or_create_profile(profile_name)
            print(f"✅ Using profile: {profile_uuid}")
        except Exception as e:
            print(f"❌ Failed to get/create profile: {e}")
            return
        
        # Kết nối với profile
        try:
            print("🔌 Connecting to Hidemium profile...")
            page = client.connect_to_profile(profile_uuid)
            print(f"✅ Connected to profile: {profile_uuid}")
            
            # Navigate đến Gmail registration
            print("🌐 Navigating to Gmail registration...")
            page.goto("https://accounts.google.com/signup")
            time.sleep(3)  # Đợi trang load
            
            # Inject mouse tracker
            print("🔴 Injecting mouse tracker overlay...")
            success = client.inject_mouse_tracker(page)
            
            if success:
                print("✅ Mouse tracker injected successfully!")
                print("🔴 Red dot will now follow your mouse movements")
                print("📱 Move your mouse around the page to see the red dot")
                print("⏹️  Press Enter to remove tracker and close browser...")
                
                # Giữ browser mở để test
                input()
                
                # Remove mouse tracker
                print("🗑️ Removing mouse tracker...")
                client.remove_mouse_tracker(page)
                
            else:
                print("❌ Failed to inject mouse tracker")
            
        except Exception as e:
            print(f"❌ Failed to connect to profile: {e}")
            return
        
        finally:
            # Cleanup
            try:
                print("🧹 Cleaning up...")
                client.cleanup_page(page, delete_profile=False)
                print("✅ Cleanup completed")
            except Exception as e:
                print(f"⚠️ Cleanup warning: {e}")
    
    except Exception as e:
        print(f"💥 Error: {e}")

if __name__ == "__main__":
    test_mouse_tracker()
