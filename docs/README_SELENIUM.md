# Humble Bundle Sync - Selenium Authentication

This version uses Selenium WebDriver to handle modern JavaScript-based authentication and MFA challenges.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Activate virtual environment
source .venv/bin/activate

# Install new dependencies
pip install -r requirements.txt
```

### 2. Configure Credentials

Make sure your `.env` file contains:
```bash
HUMBLE_EMAIL=your_email@example.com
HUMBLE_PASSWORD=your_password
```

### 3. Test Authentication

#### Interactive Mode (Recommended for first run)
```bash
python test_selenium_auth.py
```
This opens a visible browser window so you can see the login process and handle MFA challenges.

#### Headless Mode (Production)
```bash
python test_sync_selenium.py
```

### 4. Run Sync

```bash
python main.py sync
```

## 🔐 Authentication Features

### ✅ **Modern Login Support**
- Handles JavaScript-based login forms
- Automatically detects form fields
- Supports various login page layouts

### ✅ **MFA Challenge Handling**
- Automatically detects MFA/2FA challenges
- Waits for user input (up to 5 minutes)
- Handles various MFA implementations
- Graceful error handling

### ✅ **Session Management**
- Saves authenticated sessions
- Reuses sessions when possible
- Automatic session verification
- Secure cookie storage

## 🖥️ Browser Options

### Interactive Mode (`headless=False`)
- Opens visible browser window
- Good for debugging and first-time setup
- Required for MFA challenges
- Use: `HumbleBundleAuthSelenium(headless=False)`

### Headless Mode (`headless=True`)
- Runs in background
- Good for production/automation
- Faster execution
- Use: `HumbleBundleAuthSelenium(headless=True)`

## 🔧 Troubleshooting

### Common Issues

#### 1. **ChromeDriver Not Found**
```bash
# The script automatically downloads ChromeDriver
# If you have issues, install manually:
brew install chromedriver  # macOS
```

#### 2. **MFA Timeout**
- Keep the browser window open during MFA
- The script waits up to 5 minutes for MFA completion
- Check your MFA app for new codes

#### 3. **Login Form Not Found**
- The script tries multiple selectors
- If issues persist, run in interactive mode to debug

#### 4. **Session Expired**
- Sessions are automatically refreshed
- If persistent issues, delete `.session_cache/` folder

### Debug Mode

For debugging, modify `auth_selenium.py`:
```python
# Change headless to False
self.headless = False

# Add more logging
print(f"Debug: Current URL: {self.driver.current_url}")
```

## 📁 File Structure

```
humblebundle/
├── auth_selenium.py          # New Selenium-based authentication
├── test_selenium_auth.py     # Interactive authentication test
├── test_sync_selenium.py     # Headless sync test
├── .session_cache/           # Session storage
│   ├── selenium_session.json # Session metadata
│   └── cookies.pkl          # Encrypted cookies
└── requirements.txt          # Updated dependencies
```

## 🔄 Migration from Old System

The old `auth.py` has been replaced with `auth_selenium.py`. The sync system automatically uses the new authentication.

### What Changed
- ✅ **Before**: Traditional form-based login (broken)
- ✅ **After**: Selenium-based login (working)
- ✅ **MFA Support**: Automatic detection and handling
- ✅ **Modern Web**: JavaScript-based authentication support

## 🚨 Important Notes

1. **First Run**: Use interactive mode to handle MFA
2. **Browser**: Keep Chrome/Chromium updated
3. **MFA**: Don't close browser during MFA challenges
4. **Sessions**: Sessions are cached for 24 hours
5. **Headless**: Production runs should use headless mode

## 🎯 Next Steps

1. **Test Authentication**: Run `test_selenium_auth.py` first
2. **Handle MFA**: Complete MFA challenge in browser
3. **Test Sync**: Run `test_sync_selenium.py` 
4. **Production**: Use `python main.py sync`

## 🆘 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Run in interactive mode to see what's happening
3. Check browser console for errors
4. Verify your credentials and MFA setup 