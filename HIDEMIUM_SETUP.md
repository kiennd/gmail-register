# Hidemium Integration Setup

This project now supports both Hidemium and Camoufox browser engines for Gmail registration automation. Both engines use **Playwright** for consistent API and better performance.

## Key Features

- **Unified Playwright API**: Both Hidemium and Camoufox use Playwright for consistent automation
- **CDP Connection**: Hidemium profiles connect via Chrome DevTools Protocol
- **Automatic Profile Management**: Creates/reuses profiles with proxy configuration
- **Robust Error Handling**: Fallback mechanisms and proper resource cleanup
- **No Selenium Dependency**: Pure Playwright implementation for better performance

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure you have Hidemium installed and running on your system.

## Configuration

### Method 1: Environment Variables
Create a `.env` file (copy from `env.example`):
```bash
# Engine: hidemium or camoufox
ENGINE=hidemium

# Hidemium settings (fixed defaults)
HIDEMIUM_API_URL=http://localhost:2222

# Other settings...
```

### Method 2: Config File
Update `config.json`:
```json
{
  "ENGINE": "hidemium",
  "HIDEMIUM_API_URL": "http://localhost:2222",
  "HIDEMIUM_API_TOKEN": null,
  "HIDEMIUM_PROFILE_NAME": null,
  ...
}
```

### Method 3: Command Line Arguments
```bash
python register_gmail.py --engine hidemium
```

## Hidemium API Configuration

The integration uses the [Hidemium Remote Profile API](https://docs.hidemium.io/hidemium-4/i.-bat-dau-voi-hidemium/api-automation-v4/remote-profile) with the following endpoints:

- **Profile Management**: `/v4/profile/start`, `/v4/profile/stop`, `/v4/profile/check`
- **Profile Creation**: `/v4/profile` (POST)
- **Profile Listing**: `/v4/profile` (GET)
- **Proxy Updates**: `/v4/profile/proxy`

### Default Settings
- **API URL**: `http://localhost:2222` (fixed)
- **API Token**: Not used for local API
- **Profile Name**: Auto-generated per run

## Usage

### Basic Usage
```bash
# Use Hidemium (default engine in config)
python register_gmail.py

# Explicitly specify Hidemium
python register_gmail.py --engine hidemium

# Use Camoufox as fallback
python register_gmail.py --engine camoufox
```

### Advanced Usage
```bash
# No extra flags needed; API URL fixed and profiles are auto-deleted after registration

# Multi-run with window positioning
python register_multi.py --count 3 --engine hidemium
```

## How It Works

### Hidemium Flow
1. **Create Custom Profile**: Creates a new unique Hidemium profile with full configuration
2. **Proxy Configuration**: Configures proxy settings for the temporary profile
3. **Profile Launch**: Opens the profile via Hidemium API
4. **Browser Connection**: Connects to the profile using Playwright via CDP
5. **Registration Process**: Executes the Gmail registration flow with fresh profile
6. **Profile Deletion**: Automatically deletes the temporary profile after completion
7. **Cleanup**: Closes all Playwright connections and resources

### Camoufox Fallback
If Hidemium is not available or fails, the system falls back to Camoufox with Playwright.

## Profile Management

### Temporary Profile System
- **Always Creates New**: Each registration creates a fresh temporary profile
- **Unique Names**: Profiles use timestamp + UUID for guaranteed uniqueness (e.g., `temp_username_1703123456_a8b9c1d2`)
- **Auto-Deletion**: Profiles are automatically deleted after registration completion
- **Proxy Integration**: Proxy settings are automatically configured during creation
- **Clean State**: Every registration starts with a completely clean browser profile
- **Fresh Sessions**: No previous cookies or browsing history for maximum registration success



### Manual Profile Management
You can also create and manage profiles manually through the Hidemium API:

```python
from app.hidemium_client import HidemiumClient

client = HidemiumClient("http://localhost:2222")

# List existing profiles
profiles = client.list_profiles()

# Create a new profile
new_profile = client.create_profile("my_profile", {
    "proxy": {
        "type": "socks5",
        "host": "proxy.example.com",
        "port": 1080,
        "username": "user",
        "password": "pass"
    }
})

# Open profile for automation
response = client.open_profile(new_profile["uuid"])
```

## Troubleshooting

### Common Issues

1. **Hidemium API Connection Failed**
   - Ensure Hidemium is running and accessible at the configured URL
   - Check if API token is required and properly configured

2. **Profile Creation Failed**
   - Verify Hidemium has sufficient resources to create new profiles
   - Check proxy configuration format

3. **Playwright Connection Failed**
   - Ensure Playwright browsers are installed: `playwright install`
   - Check if the debug port is accessible

4. **Import Errors**
   - Run `pip install -r requirements.txt` to install all dependencies
   - Ensure Playwright is properly installed

### Debug Mode
Enable debug mode for detailed logging:
```bash
python register_gmail.py --engine hidemium --debug
```

### Fallback to Camoufox
If Hidemium fails, you can always fallback to Camoufox:
```bash
python register_gmail.py --engine camoufox
```

## API Reference

### HidemiumClient Class

#### Constructor
```python
HidemiumClient(base_url="http://localhost:2222", api_token=None)
```

#### Key Methods
- `open_profile(profile_uuid)`: Open a profile for automation
- `close_profile(profile_uuid)`: Close an active profile
- `create_profile(name, config)`: Create a new profile (legacy method)
- `create_profile_custom(profile_config, is_local)`: Create custom profile with full config
- `build_default_profile_config(name, proxy, os_type, language)`: Build default configuration
- `connect_to_profile(profile_uuid)`: Connect Playwright to profile via CDP
- `update_proxy(profile_uuid, proxy_config)`: Update proxy settings

### Configuration Keys
- `ENGINE`: "hidemium" or "camoufox"
- `HIDEMIUM_API_URL`: Hidemium API endpoint (fixed to localhost)
- `HIDEMIUM_OS`: Operating system for profiles ("win", "mac", "linux", "android", "ios")
- `HIDEMIUM_LOCAL_PROFILE`: Whether to create local (true) or cloud (false) profiles
- `HIDEMIUM_CUSTOM_CONFIG`: Additional custom configuration for profiles
- `HIDEMIUM_OS`: Operating system for profiles ("win", "mac", "linux", "android", "ios")
- `HIDEMIUM_LOCAL_PROFILE`: Whether to create local (true) or cloud (false) profiles
- `HIDEMIUM_CUSTOM_CONFIG`: Additional custom configuration for profiles

## Performance Considerations

- **Fresh Profiles**: Each registration uses a completely clean profile for maximum success
- **Automatic Cleanup**: Profiles are automatically deleted to prevent resource accumulation
- **Fast Creation**: Profile creation is optimized for speed with minimal configuration
- **Error Handling**: Robust error handling with automatic profile deletion even on failures
- **Resource Management**: Proper cleanup of all Playwright and Hidemium resources

## Security Notes

- API tokens should be kept secure and not committed to version control
- Proxy credentials are handled securely through the Hidemium API
- Profile data is managed by Hidemium with its built-in security features
