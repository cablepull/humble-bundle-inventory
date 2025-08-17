# Testing the Humble Bundle Synchronizer

## 🧪 Testing Overview

The system includes comprehensive testing for authentication, MFA handling, and data synchronization.

## 📋 Test Files Available

1. **`test_basic.py`** - Basic functionality without authentication
2. **`test_mfa_flow.py`** - Specific MFA email code testing  
3. **`test_integration.py`** - Full end-to-end integration tests

## 🔐 MFA Testing

### Enhanced MFA Support

The system now includes robust MFA handling for Humble Bundle's email-based verification codes:

**Features:**
- ✅ **Multiple Detection Methods**: Detects MFA fields using various CSS selectors
- ✅ **Clear Instructions**: Guides user through email verification process
- ✅ **Code Validation**: Validates format (digits only, 4-8 characters)
- ✅ **Multiple Attempts**: Allows 3 attempts to enter correct code
- ✅ **Smart Submission**: Tries multiple ways to submit the form
- ✅ **Success Verification**: Confirms MFA was accepted

### Testing MFA Flow

To test the MFA functionality:

```bash
# Test MFA flow specifically (opens browser)
python test_mfa_flow.py

# Or test through main CLI
python main.py login --force-new
```

**What to Expect:**
1. Browser opens to Humble Bundle login page
2. System enters your credentials automatically
3. Humble Bundle sends MFA code to your email
4. System prompts you to check email and enter code
5. System validates and submits the code
6. Session is saved for future use

### MFA Process Flow

```
Login → Email/Password → MFA Challenge Detected
  ↓
📧 "Check your email for verification code"
  ↓  
🔢 User enters code from email
  ↓
✅ Code validated and submitted
  ↓
💾 Session saved with encryption
```

## 🚀 Quick Test Commands

```bash
# 1. Test basic functionality
python test_basic.py

# 2. Initialize database
python main.py init

# 3. Test MFA login (interactive)
python test_mfa_flow.py

# 4. Check session status
python main.py session

# 5. Run full sync
python main.py sync --force

# 6. View library stats
python main.py status
```

## 📧 MFA Troubleshooting

**If MFA detection fails:**
- Check that email credentials are correct in `.env`
- Ensure you have access to the email account
- Check spam folder for verification emails
- Codes typically expire in 5-10 minutes

**If MFA codes are rejected:**
- Ensure you enter only letters and numbers (no spaces or symbols)
- Check code hasn't expired  
- Verify you're using the latest email from Humble Bundle

**Common MFA code formats:**
- ✅ `123456` (6 digits)
- ✅ `12345678` (8 digits)  
- ✅ `ABC123` (alphanumeric)
- ✅ `XY7K9M` (letters and numbers)
- ✅ `VERIFY123` (longer alphanumeric)
- ❌ `12-34-56` (contains dashes/symbols)
- ❌ `AB C123` (contains spaces)

## 🔄 Session Management

The enhanced system maintains sessions until explicitly logged out or expired:

```bash
# View current session
python main.py session

# Force new login (clears existing session)
python main.py login --force-new

# Logout (clears session)
python main.py logout
```

## 🎯 Expected Test Results

**Successful MFA Flow:**
```
🔐 MFA challenge detected!
📧 Humble Bundle has sent a verification code to your email.
📱 Please check your email inbox (and spam folder) for the code.
⏱️  The code is usually 6-8 digits and expires in a few minutes.

🔢 Enter the MFA code from your email: 123456
🔄 Entering MFA code: 123456
🔄 Clicking submit button: button[type='submit']
⏳ Waiting for MFA verification...
✅ MFA verification successful!
✅ Login with MFA successful!
💾 Session saved (signature: a1b2c3d4)
```

The system is now production-ready with comprehensive MFA support for Humble Bundle's email-based verification system.