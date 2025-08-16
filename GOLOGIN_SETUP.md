# GoLogin Setup Guide

Hướng dẫn thiết lập và sử dụng GoLogin trong dự án Gmail Registration.

## 🚀 Giới thiệu

GoLogin là một dịch vụ quản lý profile trình duyệt (browser profile management) tương tự như Hidemium, cung cấp:

- **Quản lý profile trình duyệt** với fingerprint riêng biệt
- **Anti-detection** để tránh bị phát hiện khi automation
- **Proxy support** với nhiều loại proxy khác nhau
- **API integration** để tích hợp với các tool automation
- **Cloud-based** profile management

## 📋 Yêu cầu

1. **GoLogin Account**: Đăng ký tài khoản tại [gologin.com](https://gologin.com)
2. **Access Token**: Lấy API access token từ GoLogin dashboard
3. **Python Dependencies**: Cài đặt các thư viện cần thiết

## 🔧 Cài đặt

### 1. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### 2. Cấu hình GoLogin

#### Cách 1: Sử dụng config.json

Cập nhật file `config.json`:

```json
{
  "ENGINE": "gologin",
  "GOLOGIN_ACCESS_TOKEN": "your_access_token_here",
  "GOLOGIN_API_URL": "https://api.gologin.com",
  "GOLOGIN_OS": "win",
  "GOLOGIN_LOCAL_PROFILE": false,
  "PROXY": "your_proxy_server:port",
  "PROXY_SCHEME": "http"
}
```

#### Cách 2: Sử dụng biến môi trường

Tạo file `.env` từ `env.example`:

```bash
cp env.example .env
```

Cập nhật file `.env`:

```env
ENGINE=gologin
GOLOGIN_ACCESS_TOKEN=your_access_token_here
GOLOGIN_API_URL=https://api.gologin.com
GOLOGIN_OS=win
```

### 3. Lấy GoLogin Access Token

1. Đăng nhập vào [GoLogin Dashboard](https://app.gologin.com/)
2. Vào **Settings** → **API**
3. Copy **Access Token**
4. Paste vào `config.json` hoặc `.env`

## 🧪 Testing

### 1. Test cơ bản

```bash
python examples/gologin_example.py
```

### 2. Test Gmail Registration

```bash
python examples/gologin_gmail_register_example.py
```

## 📚 Sử dụng trong code

### 1. Khởi tạo GoLogin Client

```python
from app.gologin_client import GoLoginClient

# Khởi tạo client
client = GoLoginClient(access_token="your_token")

# Hoặc sử dụng config
from app.config_loader import load_config_from_file
config = load_config_from_file("config.json")
client = GoLoginClient(access_token=config["gologin_access_token"])
```

### 2. Tạo Profile

```python
# Tạo profile cơ bản
profile_config = client.build_default_profile_config(
    name="test_profile",
    os_type="win",
    language="en-US"
)

response = client.create_profile_custom(profile_config)
profile_id = response["id"]
```

### 3. Tạo Profile với Proxy

```python
# Cấu hình proxy
proxy_config = {
    "server": "proxy.example.com:8080",
    "username": "user",
    "password": "pass",
    "scheme": "http"
}

profile_config = client.build_default_profile_config(
    name="proxy_profile",
    proxy=proxy_config,
    os_type="win",
    language="en-US"
)

response = client.create_profile_custom(profile_config)
```

### 4. Kết nối và sử dụng

```python
# Khởi động profile
start_response = client.start_profile(profile_id)

# Kết nối với Playwright
page = client.connect_to_profile(profile_id)

# Sử dụng page như bình thường
page.goto("https://example.com")
page.click("button")

# Cleanup
client.cleanup_page(page, delete_profile=True)
```

## 🔄 Chuyển đổi từ Hidemium

### 1. Thay đổi Engine

```json
{
  "ENGINE": "gologin"  // Thay vì "hidemium"
}
```

### 2. Cập nhật cấu hình

```json
{
  "GOLOGIN_ACCESS_TOKEN": "your_token",
  "GOLOGIN_OS": "win",  // Thay vì HIDEMIUM_OS
  "GOLOGIN_LOCAL_PROFILE": false
}
```

### 3. Cập nhật code

```python
# Thay vì HidemiumClient
from app.gologin_client import GoLoginClient

# Thay vì profile_uuid, sử dụng profile_id
profile_id = "gologin_profile_id"
```

## 🌐 Proxy Configuration

### 1. HTTP/HTTPS Proxy

```json
{
  "PROXY": "proxy.example.com:8080",
  "PROXY_SCHEME": "http"
}
```

### 2. SOCKS5 Proxy

```json
{
  "PROXY": "proxy.example.com:1080",
  "PROXY_SCHEME": "socks5"
}
```

### 3. Proxy với Authentication

```json
{
  "PROXY": "proxy.example.com:8080:username:password",
  "PROXY_SCHEME": "http"
}
```

## 🎯 Gmail Registration với GoLogin

### 1. Tạo Profile tối ưu cho Gmail

```python
def create_gmail_profile(client, name, proxy=None):
    config = client.build_default_profile_config(
        name=name,
        proxy=proxy,
        os_type="win",
        language="en-US"
    )
    
    # Tối ưu cho Gmail
    config.update({
        "startUrl": "https://workspace.google.com/intl/en-US/gmail/",
        "notes": f"Gmail registration - {name}",
        "tags": ["gmail", "registration"],
        "webRTC": {"mode": "alerted"},
        "permissions": {
            "notifications": "prompt",
            "geolocation": "prompt"
        }
    })
    
    return client.create_profile_custom(config)
```

### 2. Chạy Registration Flow

```python
# Tạo profile
profile_response = create_gmail_profile(client, "gmail_test")
profile_id = profile_response["id"]

# Khởi động và kết nối
page = client.connect_to_profile(profile_id)

# Thực hiện registration
page.goto("https://accounts.google.com/signup")
# ... automation code ...

# Cleanup
client.cleanup_page(page, delete_profile=True)
```

## 🚨 Troubleshooting

### 1. Lỗi Access Token

```
❌ GoLogin access token not found in config.json
```

**Giải pháp**: Kiểm tra `GOLOGIN_ACCESS_TOKEN` trong config

### 2. Lỗi API Connection

```
❌ Failed to connect to GoLogin API
```

**Giải pháp**: 
- Kiểm tra internet connection
- Kiểm tra access token
- Kiểm tra API URL

### 3. Lỗi Profile Creation

```
❌ Profile creation failed
```

**Giải pháp**:
- Kiểm tra profile configuration
- Kiểm tra proxy settings
- Kiểm tra API rate limits

### 4. Lỗi Playwright Connection

```
❌ Failed to connect to profile
```

**Giải pháp**:
- Kiểm tra profile status
- Kiểm tra port availability
- Restart profile

## 📊 So sánh với Hidemium

| Tính năng | GoLogin | Hidemium |
|-----------|---------|----------|
| **API Rate Limit** | 100 req/min | 50 req/min |
| **Cloud Profiles** | ✅ | ✅ |
| **Local Profiles** | ❌ | ✅ |
| **Proxy Support** | ✅ | ✅ |
| **Fingerprint** | ✅ | ✅ |
| **Playwright** | ✅ | ✅ |
| **Cost** | Pay-per-use | Free local |

## 🔗 Links hữu ích

- [GoLogin Website](https://gologin.com)
- [GoLogin API Docs](https://gologin.com/docs/api)
- [GoLogin Dashboard](https://app.gologin.com/)
- [GoLogin Pricing](https://gologin.com/pricing)

## 📝 Notes

- GoLogin yêu cầu access token để sử dụng
- Không hỗ trợ local profiles như Hidemium
- API rate limit cao hơn (100 req/min vs 50 req/min)
- Tích hợp tốt với Playwright
- Hỗ trợ nhiều loại proxy
- Cloud-based profile management
