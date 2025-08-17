#!/usr/bin/env python3
"""
Test script specifically for MFA flow testing.
"""

from rich.console import Console
from scripts.persistent_session_auth import PersistentSessionAuth
from src.humble_bundle_inventory.config import settings

console = Console()

def test_mfa_flow():
    """Test the MFA flow with Humble Bundle."""
    console.print("🔐 Testing MFA Flow with Humble Bundle", style="bold blue")
    console.print("=" * 50)
    
    if not settings.humble_email or not settings.humble_password:
        console.print("❌ Missing credentials in .env file", style="red")
        console.print("Please ensure HUMBLE_EMAIL and HUMBLE_PASSWORD are set")
        return False
    
    console.print(f"📧 Using email: {settings.humble_email}", style="blue")
    console.print("🔄 Starting authentication process...", style="blue")
    console.print("")
    
    # Use non-headless mode so user can see what's happening
    auth = PersistentSessionAuth(headless=False)
    
    try:
        # Clear any existing session to force a fresh login
        auth.logout()
        console.print("🧹 Cleared any existing session", style="yellow")
        
        # Attempt login which should trigger MFA
        console.print("🔄 Attempting login (this should trigger MFA)...", style="blue")
        console.print("📱 [bold yellow]Be ready to check your email for MFA code![/bold yellow]")
        print()  # Add space before login process
        
        success = auth.login(force_new=True)
        
        if success:
            console.print("✅ Login with MFA successful!", style="green")
            
            # Verify session
            console.print("🔍 Verifying session...", style="blue")
            if auth._verify_persistent_session():
                console.print("✅ Session verification passed!", style="green")
                
                # Show session info
                session_info = auth.get_session_info()
                console.print(f"💾 Session saved (signature: {session_info.get('signature', 'Unknown')})", style="blue")
                
                return True
            else:
                console.print("❌ Session verification failed", style="red")
                return False
        else:
            console.print("❌ Login failed", style="red")
            return False
            
    except Exception as e:
        console.print(f"❌ Error during MFA test: {e}", style="red")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Keep session for future use - don't logout
        pass

def main():
    """Run MFA flow test."""
    console.print("🧪 Humble Bundle MFA Flow Test", style="bold magenta")
    console.print("")
    console.print("This test will:")
    console.print("1. Clear any existing session")
    console.print("2. Attempt fresh login to Humble Bundle")
    console.print("3. Handle MFA code from email")
    console.print("4. Verify the resulting session")
    console.print("")
    console.print("📧 Make sure you have access to the email account for MFA codes!")
    console.print("")
    
    if not console.input("Continue with MFA test? (y/n): ").lower().startswith('y'):
        console.print("Test cancelled.", style="yellow")
        return
    
    success = test_mfa_flow()
    
    console.print("")
    if success:
        console.print("🎉 MFA Flow Test PASSED!", style="bold green")
        console.print("✅ The system can successfully handle email-based MFA codes")
        console.print("✅ Session persistence is working correctly")
        console.print("")
        console.print("Next steps:")
        console.print("  • Try 'python main.py session' to view session status")
        console.print("  • Try 'python main.py sync' to test library synchronization")
    else:
        console.print("❌ MFA Flow Test FAILED!", style="bold red")
        console.print("Please check the error messages above and try again")

if __name__ == "__main__":
    main()