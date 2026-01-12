#!/usr/bin/env python3
"""
Interactive Credential Setup for Visier API

This script helps you set up your API credentials by creating or updating
a .env file in the project root.

Usage:
    python aggregate/setup_credentials.py
    # or
    python aggregate/run_aggregate_query.py --setup
"""

import os
import sys
from pathlib import Path


def get_project_root() -> Path:
    """Find the project root (where .env should be located)."""
    # Start from this script's directory
    current = Path(__file__).parent
    
    # Look for project root indicators (.env.example, requirements.txt, etc.)
    while current != current.parent:
        if (current / ".env.example").exists() or (current / "visier.env.example").exists() or (current / "requirements.txt").exists():
            return current
        current = current.parent
    
    # Fallback: use script's directory (for standalone repo)
    return Path(__file__).parent


def print_header(text: str):
    """Print a formatted header."""
    width = 70
    print("\n" + "=" * width)
    print(f"  {text}")
    print("=" * width)


def print_success(text: str):
    """Print success message."""
    print(f"✓ {text}")


def print_info(text: str):
    """Print info message."""
    print(f"ℹ {text}")


def get_input(prompt: str, default: str = None, password: bool = False) -> str:
    """
    Get user input with optional default value.
    
    Args:
        prompt: The prompt text
        default: Optional default value
        password: If True, hide input (for passwords)
    
    Returns:
        User input or default value
    """
    if default:
        prompt_text = f"{prompt} [{default}]: "
    else:
        prompt_text = f"{prompt}: "
    
    if password:
        import getpass
        value = getpass.getpass(prompt_text)
    else:
        value = input(prompt_text).strip()
    
    return value if value else (default or "")


def validate_url(url: str) -> bool:
    """Basic URL validation."""
    return url.startswith(("http://", "https://"))


def setup_credentials_interactive():
    """Interactive credential setup."""
    print_header("Visier API Credential Setup")
    
    print_info("This script will help you configure your Visier API credentials.")
    print_info("You'll need the following information:")
    print("  • Visier API Host URL (e.g., https://your-tenant.api.visier.io)")
    print("  • API Key")
    print("  • Vanity name")
    print("  • Username")
    print("  • Password")
    print()
    
    # Find project root
    project_root = get_project_root()
    env_file = project_root / ".env"
    
    # Check if .env already exists
    existing_values = {}
    if env_file.exists():
        print_info(f"Found existing .env file at: {env_file}")
        response = get_input("Do you want to update it? (yes/no)", "yes")
        if response.lower() not in ["yes", "y"]:
            print_info("Setup cancelled.")
            return
        
        # Try to read existing values
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        existing_values[key.strip()] = value.strip()
        except Exception:
            pass
    
    print_header("Enter Your Credentials")
    print_info("Press Enter to keep existing values (if updating)")
    print()
    
    # Collect credentials
    credentials = {}
    
    # Host
    default_host = existing_values.get("VISIER_HOST", "")
    while True:
        host = get_input("Visier API Host URL", default_host)
        if not host:
            print("  ⚠ Host URL is required")
            continue
        if not validate_url(host):
            print("  ⚠ URL should start with http:// or https://")
            continue
        credentials["VISIER_HOST"] = host
        break
    
    # API Key
    default_apikey = existing_values.get("VISIER_APIKEY", "")
    apikey = get_input("API Key", default_apikey)
    if not apikey:
        print("  ⚠ API Key is required")
        return
    credentials["VISIER_APIKEY"] = apikey
    
    # Vanity
    default_vanity = existing_values.get("VISIER_VANITY", "")
    vanity = get_input("Vanity Name", default_vanity)
    if not vanity:
        print("  ⚠ Vanity name is required")
        return
    credentials["VISIER_VANITY"] = vanity
    
    # Username
    default_username = existing_values.get("VISIER_USERNAME", "")
    username = get_input("Username", default_username)
    if not username:
        print("  ⚠ Username is required")
        return
    credentials["VISIER_USERNAME"] = username
    
    # Password
    default_password = existing_values.get("VISIER_PASSWORD", "")
    password = get_input("Password", default_password, password=True)
    if not password:
        print("  ⚠ Password is required")
        return
    credentials["VISIER_PASSWORD"] = password
    
    # Optional tenant code
    default_tenant = existing_values.get("VISIER_TENANT_CODE", "")
    tenant_code = get_input("Tenant Code (optional)", default_tenant)
    if tenant_code:
        credentials["VISIER_TENANT_CODE"] = tenant_code
    
    # Write to .env file
    print_header("Saving Credentials")
    try:
        with open(env_file, 'w') as f:
            f.write("# Visier API Credentials\n")
            f.write("# Generated by setup_credentials.py\n")
            f.write("# DO NOT commit this file to version control\n\n")
            
            for key, value in credentials.items():
                f.write(f"{key}={value}\n")
        
        print_success(f"Credentials saved to: {env_file}")
        print_info("⚠ Important: Keep this file secure and do not share it")
        
        # Test credentials
        print_header("Testing Credentials")
        print_info("Attempting to authenticate...")
        
        try:
            # Add current directory to path
            current_dir = os.path.dirname(os.path.abspath(__file__))
            if current_dir not in sys.path:
                sys.path.insert(0, current_dir)
            
            from aggregate_query_vanilla import get_api_config, get_asid_token
            config = get_api_config()
            token = get_asid_token(config)
            print_success("Authentication successful!")
            print_info("Your credentials are working correctly.")
        except Exception as e:
            print(f"  ⚠ Authentication test failed: {e}")
            print_info("This might be normal if your credentials are correct but there's a network issue.")
            print_info("You can still try running a query to verify.")
        
    except Exception as e:
        print(f"✗ Failed to save credentials: {e}")
        return
    
    print_header("Setup Complete")
    print_success("You're ready to run queries!")
    print_info("Next steps:")
    print("  1. Edit a JSON payload file in examples/")
    print("  2. Run: python aggregate/run_aggregate_query.py --payload examples/query_payload_examples.json")


if __name__ == "__main__":
    try:
        setup_credentials_interactive()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
        sys.exit(1)
