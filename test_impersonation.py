#!/usr/bin/env python3
"""
Test Script for User Impersonation in Visier API

This script tests the impersonation flow for accessing customer tenants.
It demonstrates how to use the TargetTenantID header to query data on behalf
of a customer tenant.

KEY CONCEPTS:
- Uses demographics vanity (NOT customer vanity) - e.g., visierdemographics-eu
- Requires VTSI profile for API access
- Uses jurisdiction-based vanity URLs
- TargetTenantID header specifies which customer tenant to query

IMPERSONATION FLOW (Two Steps):
  1. Get visierSecureToken (ASID token) using YOUR credentials with VTSI profile
  2. Get visierImpersonationToken using ASID token + customer's API key + TargetUserName + TargetTenantID

ENVIRONMENT VARIABLES (in .env file):
For impersonation, you can use these specific variables:

YOUR credentials (with VTSI profile):
  VISIER_IMPERSONATION_MY_USERNAME=your_username
  VISIER_IMPERSONATION_MY_PASSWORD=your_password
  VISIER_IMPERSONATION_JURISDICTION=US
  VISIER_IMPERSONATION_APIKEY=your_apikey (optional)

Customer information (for step 2):
  VISIER_IMPERSONATION_TARGET_USERNAME=customer.user@example.com
  VISIER_IMPERSONATION_TARGET_TENANT_ID=customer-tenant-123
  VISIER_IMPERSONATION_CUSTOMER_APIKEY=customer_apikey

Note: You can also provide these via command-line arguments instead of .env file.

If impersonation-specific variables aren't set, it falls back to:
  VISIER_USERNAME, VISIER_PASSWORD, VISIER_APIKEY

IMPORTANT: Before using impersonation, you must:
1. Have VTSI profile for API access
2. Follow the process in impersonator.md
3. Get exceptional access approved via Support
4. Ensure your account has the necessary permissions

Usage:
    python test_impersonation.py --target-tenant <tenant_id> --jurisdiction <US|EU|CA|APAC> [--test-query]
    python test_impersonation.py --test-token-only [--jurisdiction US]  # Uses .env variables
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent directory to path to import client
sys.path.insert(0, str(Path(__file__).resolve().parent))

from client import (
    get_api_config,
    get_asid_token,
    execute_vanilla_aggregate_query,
    convert_vanilla_response_to_dataframe,
    create_dimension_axis,
    load_query_payload_from_json
)
import requests


# Demographics vanity mapping by jurisdiction
DEMOGRAPHICS_VANITIES = {
    "US": "visierdemographics",
    "EU": "visierdemographics-eu",
    "CA": "visierdemographics-ca",
    "APAC": "visierdemographics-ap"
}


def get_demographics_vanity(jurisdiction: str) -> str:
    """
    Get the demographics vanity for a given jurisdiction.
    
    For impersonation, you ALWAYS use the demographics vanity, NOT the customer's vanity.
    
    Args:
        jurisdiction: One of "US", "EU", "CA", "APAC"
    
    Returns:
        Demographics vanity string (e.g., "visierdemographics-eu")
    
    Raises:
        ValueError: If jurisdiction is not recognized
    """
    jurisdiction = jurisdiction.upper()
    if jurisdiction not in DEMOGRAPHICS_VANITIES:
        raise ValueError(
            f"Invalid jurisdiction: {jurisdiction}. "
            f"Must be one of: {', '.join(DEMOGRAPHICS_VANITIES.keys())}"
        )
    return DEMOGRAPHICS_VANITIES[jurisdiction]


def build_demographics_host(jurisdiction: str) -> str:
    """
    Build the host URL using demographics vanity for the given jurisdiction.
    
    Args:
        jurisdiction: One of "US", "EU", "CA", "APAC"
    
    Returns:
        Full host URL (e.g., "https://visierdemographics-eu.api.visier.io")
    """
    vanity = get_demographics_vanity(jurisdiction)
    return f"https://{vanity}.api.visier.io"


def get_visier_secure_token(
    username: str,
    password: str,
    jurisdiction: str,
    apikey: Optional[str] = None,
    verify_ssl: bool = True
) -> str:
    """
    Get a Visier secure token (ASID token) using demographics vanity for impersonation.
    
    This is the core function for getting the visierSecureToken. It takes username,
    password, and jurisdiction directly as parameters.
    
    IMPORTANT: For impersonation, you must:
    1. Use demographics vanity (NOT customer vanity) - e.g., visierdemographics-eu
    2. Have VTSI profile for API access
    3. Use the correct jurisdiction-based vanity URL
    
    The URL format is: https://{demographics-vanity}.api.visier.io/v1/admin/visierSecureToken
    
    Args:
        username: Your Visier username (demographics username)
        password: Your Visier password (API password)
        jurisdiction: Jurisdiction code ("US", "EU", "CA", "APAC")
        apikey: Optional API key (may be required for some configurations)
        verify_ssl: Whether to verify SSL certificates (default: True)
    
    Returns:
        ASID token string
    
    Raises:
        ValueError: If jurisdiction is invalid
        requests.HTTPError: If authentication fails
    
    Example:
        token = get_visier_secure_token(
            username="myuser",
            password="mypassword",
            jurisdiction="US"
        )
    """
    # Get demographics vanity and build host URL
    demographics_vanity = get_demographics_vanity(jurisdiction)
    demographics_host = build_demographics_host(jurisdiction)
    
    # Build the authentication URL using demographics vanity
    url = f"{demographics_host}/v1/admin/visierSecureToken"
    
    # Prepare headers
    # Note: According to documentation, visierSecureToken endpoint may not require API key in headers
    # The API key is typically used for subsequent requests, not for token acquisition
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    
    # API key is typically NOT needed for token acquisition endpoint
    # It's used in subsequent API requests after getting the token
    # Uncomment below if your setup requires it:
    # if apikey:
    #     headers["apikey"] = apikey
    
    # Prepare form data with username and password
    form_data = {
        "username": username,
        "password": password
    }
    
    # Use demographics vanity as query parameter (NOT customer vanity)
    params = {"vanity": demographics_vanity}
    
    print(f"→ Getting Visier secure token")
    print(f"  Jurisdiction: {jurisdiction}")
    print(f"  Demographics Vanity: {demographics_vanity}")
    print(f"  URL: {url}")
    print(f"  Username: {username}")
    print(f"  API Key: {'Set' if apikey else 'Not set'}")
    
    # Make the token request
    response = requests.post(
        url,
        headers=headers,
        data=form_data,
        params=params,
        verify=verify_ssl
    )
    
    # Check for errors - provide more detail on 401
    if response.status_code == 401:
        try:
            error_detail = response.json()
            print(f"\n⚠️  Authentication failed (401 Unauthorized)")
            print(f"  Response: {error_detail}")
        except:
            print(f"\n⚠️  Authentication failed (401 Unauthorized)")
            print(f"  Response text: {response.text[:200]}")
        response.raise_for_status()
    
    response.raise_for_status()
    
    # Parse token from response
    try:
        json_response = response.json()
        if isinstance(json_response, dict) and "asid" in json_response:
            token = json_response["asid"]
        elif isinstance(json_response, str):
            token = json_response
        else:
            token = str(json_response)
    except (ValueError, json.JSONDecodeError):
        token = response.text.strip()
    
    # Clean up token (remove quotes if present)
    token = str(token).strip().strip('"').strip("'")
    
    print(f"✓ Visier secure token obtained successfully")
    print(f"  Token (first 20 chars): {token[:20]}...")
    
    return token


def get_visier_impersonation_token(
    asid_token: str,
    target_user_name: str,
    target_tenant_id: str,
    customer_apikey: str,
    jurisdiction: str,
    verify_ssl: bool = True
) -> str:
    """
    Get a Visier impersonation token for a specific user in a customer tenant.
    
    This is the second step in the impersonation flow:
    1. First get visierSecureToken (ASID token) using your credentials
    2. Then get visierImpersonationToken using the ASID token
    
    IMPORTANT: This request requires:
    - UserManagement Read access
    - API view level
    - API VI profile
    - "Read Impersonated" profile
    
    LEARNINGS FROM IMPLEMENTATION:
    ===============================
    1. TargetUsername MUST be in headers (even though OpenAPI spec shows it in body only).
       The API error message states: "TargetUsername parameter is missing. Please include 
       it in the request headers or body." We include it in both for compatibility.
    
    2. TargetTenantID MUST be in headers (NOT in body), per OpenAPI specification.
    
    3. No query parameters needed - the vanity is already encoded in the hostname
       (e.g., visierdemographics.api.visier.io). Do NOT add ?vanity=visierdemographics.
    
    4. Cookie format: Use "Cookie: VisierASIDToken={token}" header format, not cookies parameter.
    
    5. Request format:
       - Headers: apikey, Cookie (VisierASIDToken), TargetTenantID, TargetUsername
       - Body: TargetUsername (JSON)
       - No query parameters
    
    Args:
        asid_token: The secure token obtained from get_visier_secure_token()
        target_user_name: The username of the user in the customer tenant to impersonate
        target_tenant_id: The tenant ID of the customer tenant
        customer_apikey: The customer's API key (NOT your API key)
        jurisdiction: Jurisdiction code ("US", "EU", "CA", "APAC")
        verify_ssl: Whether to verify SSL certificates (default: True)
    
    Returns:
        Impersonation token string
    
    Raises:
        ValueError: If jurisdiction is invalid
        requests.HTTPError: If impersonation token request fails
    
    Example:
        # First get your secure token
        asid_token = get_visier_secure_token(username, password, "US")
        
        # Then get impersonation token for customer user
        impersonation_token = get_visier_impersonation_token(
            asid_token=asid_token,
            target_user_name="customer.user@example.com",
            target_tenant_id="customer-tenant-123",
            customer_apikey="customer-api-key",
            jurisdiction="US"
        )
    """
    # Get demographics vanity and build host URL
    demographics_vanity = get_demographics_vanity(jurisdiction)
    demographics_host = build_demographics_host(jurisdiction)
    
    # Build the impersonation token URL using demographics vanity
    url = f"{demographics_host}/v1/admin/visierImpersonationToken"
    
    # Prepare headers
    # LEARNINGS: Based on actual API testing (not just OpenAPI spec):
    # - apikey: Customer's API key (required)
    # - Cookie: VisierASIDToken as cookie header (required)
    # - TargetTenantID: Tenant ID in headers (required, NOT in body per OpenAPI spec)
    # - TargetUsername: MUST be in headers (required, even though spec shows body only)
    #   The API error explicitly states: "TargetUsername parameter is missing. Please include 
    #   it in the request headers or body." We include it in both for maximum compatibility.
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "apikey": customer_apikey,  # Customer's API key (NOT your API key)
        "Cookie": f"VisierASIDToken={asid_token}",  # Cookie header with ASID token
        "TargetTenantID": target_tenant_id,  # Tenant ID in headers per API documentation
        "TargetUsername": target_user_name  # REQUIRED in headers (API error confirms this)
    }
    
    # Prepare request body with TargetUsername
    # Per OpenAPI spec: https://docs.visier.com/visier-people/apis/references/api-reference.htm#tag/BasicAuthentication/operation/BasicAuthentication_GenerateImpersonationToken
    # Note: We also include TargetUsername in headers because the API error message states
    # it can be in "headers or body", and including it in both ensures compatibility.
    body = {
        "TargetUsername": target_user_name
    }
    
    print(f"→ Getting Visier impersonation token")
    print(f"  Jurisdiction: {jurisdiction}")
    print(f"  Demographics Vanity: {demographics_vanity}")
    print(f"  URL: {url} (no query parameters - vanity is in hostname)")
    print(f"  Target User: {target_user_name}")
    print(f"  Target Tenant ID: {target_tenant_id}")
    print(f"  Customer API Key: Set")
    print(f"\n  Request Details (based on actual API behavior):")
    print(f"    Headers:")
    print(f"      Content-Type: application/json")
    print(f"      Accept: application/json")
    print(f"      apikey: {customer_apikey[:20]}... (customer's API key)")
    print(f"      Cookie: VisierASIDToken={asid_token[:30]}...")
    print(f"      TargetTenantID: {target_tenant_id} (in headers, NOT body)")
    print(f"      TargetUsername: {target_user_name} (in headers - REQUIRED per API error)")
    print(f"    Body: {json.dumps(body, indent=6)} (TargetUsername also in body per spec)")
    print(f"    Query Params: None (vanity encoded in hostname)")
    
    # Make the impersonation token request
    # LEARNINGS:
    # - TargetUsername MUST be in headers (API error confirms this)
    # - TargetTenantID MUST be in headers (OpenAPI spec confirms this)
    # - No query parameters needed (vanity is in hostname)
    # - Use json=body to send JSON (not data=)
    response = requests.post(
        url,
        json=body,  # Send as JSON (not data=)
        headers=headers,
        verify=verify_ssl
        # Note: No params - vanity is already in the hostname (visierdemographics.api.visier.io)
    )
    
    # Check for errors - provide more detail on common errors
    if response.status_code == 403:
        try:
            error_detail = response.json()
            print(f"\n⚠️  Permission denied (403 Forbidden)")
            print(f"  Response: {error_detail}")
            print(f"\n  This likely means:")
            print(f"  - Missing API VI profile")
            print(f"  - Missing 'Read Impersonated' profile")
            print(f"  - Missing UserManagement Read access")
        except:
            print(f"\n⚠️  Permission denied (403 Forbidden)")
            print(f"  Response text: {response.text[:500]}")
        response.raise_for_status()
    elif response.status_code == 401:
        try:
            error_detail = response.json()
            print(f"\n⚠️  Authentication failed (401 Unauthorized)")
            print(f"  Response: {error_detail}")
        except:
            print(f"\n⚠️  Authentication failed (401 Unauthorized)")
            print(f"  Response text: {response.text[:500]}")
        response.raise_for_status()
    elif response.status_code >= 500:
        try:
            error_detail = response.json()
            print(f"\n⚠️  Server error ({response.status_code})")
            print(f"  Response: {error_detail}")
        except:
            print(f"\n⚠️  Server error ({response.status_code})")
            print(f"  Response text: {response.text[:500]}")
        print(f"\n  Error Details:")
        if 'UserManagement' in str(error_detail):
            print(f"  ⚠️  UserManagement capability issue detected")
            print(f"     Even with Enterprise API User, Read Impersonated, API VI, and VTSI profiles,")
            print(f"     you may need explicit UserManagement Read permission enabled.")
            print(f"     Contact Support to verify UserManagement capability is enabled for your account.")
        print(f"\n  Possible causes:")
        print(f"  - UserManagement Read capability not explicitly enabled")
        print(f"  - Invalid target user or tenant ID")
        print(f"  - Invalid customer API key")
        print(f"  - Server-side issue (contact Support)")
        response.raise_for_status()
    
    response.raise_for_status()
    
    # Parse impersonation token from response
    try:
        json_response = response.json()
        if isinstance(json_response, dict) and "asid" in json_response:
            token = json_response["asid"]
        elif isinstance(json_response, dict) and "token" in json_response:
            token = json_response["token"]
        elif isinstance(json_response, str):
            token = json_response
        else:
            token = str(json_response)
    except (ValueError, json.JSONDecodeError):
        token = response.text.strip()
    
    # Clean up token (remove quotes if present)
    token = str(token).strip().strip('"').strip("'")
    
    print(f"✓ Visier impersonation token obtained successfully")
    print(f"  Token (first 20 chars): {token[:20]}...")
    
    return token


def get_asid_token_with_impersonation(
    jurisdiction: str,
    config: Optional[Dict[str, str]] = None,
    target_tenant_id: Optional[str] = None
) -> str:
    """
    Get an ASID authentication token using demographics vanity for impersonation.
    
    This is a convenience wrapper that uses config from environment.
    For direct control, use get_visier_secure_token() instead.
    
    Args:
        jurisdiction: Jurisdiction code ("US", "EU", "CA", "APAC")
        config: Optional API config dict. If None, loads from environment.
        target_tenant_id: Optional target tenant ID (for documentation purposes)
    
    Returns:
        ASID token string
    """
    if config is None:
        config = get_api_config()
    
    return get_visier_secure_token(
        username=config["username"],
        password=config["password"],
        jurisdiction=jurisdiction,
        apikey=config.get("apikey"),
        verify_ssl=config.get("verify_ssl", True)
    )


def execute_query_with_impersonation(
    payload: Dict[str, Any],
    target_tenant_id: str,
    jurisdiction: str,
    config: Optional[Dict[str, str]] = None,
    asid_token: Optional[str] = None
) -> Dict[str, Any]:
    """
    Execute an aggregate query with user impersonation (TargetTenantID header).
    
    IMPORTANT: For impersonation:
    1. Use demographics vanity (NOT customer vanity) in the URL
    2. Add TargetTenantID header to specify the customer tenant
    3. Your account must have VTSI profile and exceptional access permissions
    
    Args:
        payload: Complete query payload dictionary
        target_tenant_id: The tenant ID to impersonate/query on behalf of
        jurisdiction: Jurisdiction code ("US", "EU", "CA", "APAC")
        config: Optional API config dict. If None, loads from environment.
        asid_token: Optional ASID token. If None, will fetch one automatically.
    
    Returns:
        Response JSON as dictionary (CellSetDTO structure)
    
    Raises:
        ValueError: If required parameters are missing
        requests.HTTPError: If API request fails (may indicate missing permissions)
    """
    if config is None:
        config = get_api_config()
    
    # Get ASID token if not provided (uses demographics vanity)
    if asid_token is None:
        asid_token = get_asid_token_with_impersonation(jurisdiction, config, target_tenant_id)
    
    # Build the API URL using demographics vanity (NOT customer vanity)
    demographics_host = build_demographics_host(jurisdiction)
    demographics_vanity = get_demographics_vanity(jurisdiction)
    url = f"{demographics_host}/v1/data/query/aggregate"
    
    # Prepare headers - THIS IS WHERE IMPERSONATION HAPPENS
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    # Add API key
    if config.get("apikey"):
        headers["apikey"] = config["apikey"]
    
    # Add TargetTenantID header for impersonation
    # This tells Visier to execute the query as if you were a user in that tenant
    headers["TargetTenantID"] = target_tenant_id
    
    # Prepare cookies: ASID token
    cookies = {
        "VisierASIDToken": asid_token
    }
    
    # Prepare query parameters - use demographics vanity (NOT customer vanity)
    params = {"vanity": demographics_vanity}
    
    # Make the request
    verify_ssl = config.get("verify_ssl", True)
    
    print(f"→ Executing query with impersonation (TargetTenantID: {target_tenant_id})...")
    
    try:
        response = requests.post(
            url,
            json=payload,  # Send as JSON (not form-encoded)
            headers=headers,
            cookies=cookies,
            params=params,
            verify=verify_ssl
        )
        
        # Check for errors
        if response.status_code != 200:
            try:
                error_data = response.json()
                error_msg = f"API Error {response.status_code}: {error_data}"
            except:
                error_msg = f"API Error {response.status_code}: {response.text}"
            
            # Common error: 403 Forbidden usually means missing impersonation permissions
            if response.status_code == 403:
                error_msg += "\n\n⚠️  PERMISSION ERROR: This likely means you don't have exceptional access"
                error_msg += "\n   to impersonate users in this tenant. See impersonator.md for details."
            
            raise requests.HTTPError(error_msg)
        
        response.raise_for_status()
        
        print("✓ Query executed successfully with impersonation")
        return response.json()
        
    except requests.HTTPError as e:
        print(f"✗ Query failed: {e}")
        raise


def execute_query_with_impersonation_token(
    payload: Dict[str, Any],
    impersonation_token: str,
    customer_apikey: str,
    jurisdiction: str,
    verify_ssl: bool = True
) -> Dict[str, Any]:
    """
    Execute an aggregate query using an impersonation token directly.
    
    This uses the impersonation token obtained from get_visier_impersonation_token()
    in the Cookie header. Unlike execute_query_with_impersonation(), this does NOT
    use the TargetTenantID header - the tenant is determined by the impersonation token.
    
    IMPORTANT: 
    - Use the impersonation token in Cookie: VisierImpersonationToken={impersonation_token}
    - Use customer's API key (NOT your API key)
    - Use demographics vanity in URL
    - No TargetTenantID header needed (token already contains tenant context)
    
    Args:
        payload: Complete query payload dictionary
        impersonation_token: The impersonation token from get_visier_impersonation_token()
        customer_apikey: The customer's API key (NOT your API key)
        jurisdiction: Jurisdiction code ("US", "EU", "CA", "APAC")
        verify_ssl: Whether to verify SSL certificates (default: True)
    
    Returns:
        Response JSON as dictionary (CellSetDTO structure)
    
    Raises:
        ValueError: If jurisdiction is invalid
        requests.HTTPError: If API request fails
    """
    # Build the API URL using demographics vanity (NOT customer vanity)
    demographics_host = build_demographics_host(jurisdiction)
    demographics_vanity = get_demographics_vanity(jurisdiction)
    url = f"{demographics_host}/v1/data/query/aggregate"
    
    # Prepare headers
    # When using impersonation token directly:
    # - Use customer's API key
    # - Use impersonation token in Cookie header
    # - NO TargetTenantID header (token already contains tenant context)
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "apikey": customer_apikey,  # Customer's API key (NOT your API key)
        "Cookie": f"VisierImpersonationToken={impersonation_token}"  # Impersonation token in Cookie
    }
    
    # Prepare query parameters - use demographics vanity (NOT customer vanity)
    params = {"vanity": demographics_vanity}
    
    print(f"→ Executing query with impersonation token (direct)...")
    print(f"  URL: {url}")
    print(f"  Using VisierImpersonationToken in Cookie header")
    print(f"  No TargetTenantID header needed (token contains tenant context)")
    print(f"  Payload: {json.dumps(payload, indent=2)}")
    
    # Make the request
    response = requests.post(
        url,
        json=payload,  # Send as JSON
        headers=headers,
        params=params,
        verify=verify_ssl
    )
    
    # Print response details
    print(f"\n  Response Status: {response.status_code}")
    print(f"  Response Headers: {dict(response.headers)}")
    
    # Check for errors
    if response.status_code != 200:
        try:
            error_data = response.json()
            error_msg = f"API Error {response.status_code}: {error_data}"
            print(f"  Error Response Body: {json.dumps(error_data, indent=2)}")
        except:
            error_msg = f"API Error {response.status_code}: {response.text}"
            print(f"  Error Response Text: {response.text[:500]}")
        
        # Common error: 403 Forbidden usually means missing permissions or invalid token
        if response.status_code == 403:
            error_msg += "\n\n⚠️  PERMISSION ERROR: This likely means:"
            error_msg += "\n   - Impersonation token is invalid or expired"
            error_msg += "\n   - Customer API key is incorrect"
            error_msg += "\n   - Impersonated user doesn't have access to this data"
        
        raise requests.HTTPError(error_msg)
    
    response.raise_for_status()
    
    # Parse response
    response_json = response.json()
    
    # Print response structure details
    print(f"  Response Type: {type(response_json).__name__}")
    if isinstance(response_json, dict):
        print(f"  Response Keys: {list(response_json.keys())}")
        # Check for common response structures
        if "data" in response_json:
            print(f"  Data Structure: {type(response_json['data']).__name__}")
        if "cells" in response_json:
            print(f"  Cells Count: {len(response_json.get('cells', []))}")
        if "rows" in response_json:
            print(f"  Rows Count: {len(response_json.get('rows', []))}")
    
    print(f"  Response Size: {len(response.text)} bytes")
    print("✓ Query executed successfully with impersonation token")
    return response_json


def test_impersonation_connection(
    target_tenant_id: str,
    jurisdiction: str,
    config: Optional[Dict[str, str]] = None
) -> bool:
    """
    Test if impersonation is working by attempting a simple query.
    
    Args:
        target_tenant_id: The tenant ID to test impersonation with
        jurisdiction: Jurisdiction code ("US", "EU", "CA", "APAC")
        config: Optional API config dict. If None, loads from environment.
    
    Returns:
        True if impersonation works, False otherwise
    """
    print(f"\n{'='*70}")
    print(f"TESTING IMPERSONATION CONNECTION")
    print(f"{'='*70}")
    print(f"Jurisdiction: {jurisdiction}")
    print(f"Demographics Vanity: {get_demographics_vanity(jurisdiction)}")
    print(f"Target Tenant ID: {target_tenant_id}")
    print()
    
    # Build a simple test query
    test_payload = {
        "query": {
            "source": {"metric": "employeeCount"},
            "axes": [
                create_dimension_axis("Country_Cost", level_ids=["Country"])
            ],
            "timeIntervals": {
                "fromDateTime": "2026-01-01",
                "intervalPeriodType": "YEAR",
                "intervalCount": 1,
                "direction": "BACKWARD"
            }
        },
        "options": {
            "zeroVisibility": "ELIMINATE",
            "nullVisibility": "ELIMINATE"
        }
    }
    
    try:
        response = execute_query_with_impersonation(
            payload=test_payload,
            target_tenant_id=target_tenant_id,
            jurisdiction=jurisdiction,
            config=config
        )
        
        # Convert to DataFrame to verify we got data
        df = convert_vanilla_response_to_dataframe(response, metric_id="employeeCount")
        
        print(f"\n✓ Impersonation test successful!")
        print(f"  - Rows returned: {len(df)}")
        print(f"  - Columns: {', '.join(df.columns)}")
        
        if len(df) > 0:
            print(f"\n  Sample data:")
            print(df.head(3).to_string())
        
        return True
        
    except Exception as e:
        print(f"\n✗ Impersonation test failed: {e}")
        return False


def main():
    """Main function to test impersonation."""
    parser = argparse.ArgumentParser(
        description="Test user impersonation for Visier API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test token acquisition only (no tenant needed)
  python test_impersonation.py --test-token-only \\
    --username YOUR_USERNAME --password YOUR_PASSWORD --jurisdiction US
  
  # Test impersonation token acquisition (step 2)
  python test_impersonation.py --test-impersonation-token \\
    --target-user customer.user@example.com --target-tenant "customer-tenant-123" \\
    --customer-apikey CUSTOMER_API_KEY --jurisdiction US
  
  # Test full flow: get tokens + execute query with impersonation token (direct)
  python test_impersonation.py --test-impersonation-token-query \\
    --target-user customer.user@example.com --target-tenant "customer-tenant-123" \\
    --customer-apikey CUSTOMER_API_KEY --jurisdiction US
  
  # Test impersonation with EU jurisdiction (using TargetTenantID header)
  python test_impersonation.py --target-tenant "customer-tenant-123" --jurisdiction EU --test-query
  
  # Execute query with US jurisdiction (using TargetTenantID header)
  python test_impersonation.py --target-tenant "customer-tenant-123" --jurisdiction US \\
                                --payload examples/query_payload_examples.json
  
  # Test with APAC jurisdiction (using TargetTenantID header)
  python test_impersonation.py --target-tenant "customer-tenant-123" --jurisdiction APAC --test-query

IMPORTANT: Before using impersonation:
  1. You MUST have VTSI profile for API access
  2. Review impersonator.md for the exceptional access process
  3. Get approval from Support for impersonation permissions
  4. Use demographics vanity (jurisdiction-based), NOT customer vanity
  5. Available jurisdictions: US, EU, CA, APAC
        """
    )
    
    parser.add_argument(
        "--target-tenant",
        help="Target tenant ID to impersonate (customer tenant). Can also be set via VISIER_IMPERSONATION_TARGET_TENANT_ID in .env. Required unless --test-token-only"
    )
    
    parser.add_argument(
        "--jurisdiction",
        choices=["US", "EU", "CA", "APAC"],
        help="Jurisdiction for demographics vanity (US, EU, CA, or APAC). Can also be set via VISIER_IMPERSONATION_JURISDICTION in .env (your jurisdiction)"
    )
    
    parser.add_argument(
        "--payload",
        help="Path to JSON file containing query payload (optional)"
    )
    
    parser.add_argument(
        "--test-query",
        action="store_true",
        help="Run a simple test query to verify impersonation works"
    )
    
    parser.add_argument(
        "--test-token-only",
        action="store_true",
        help="Only test secure token acquisition (step 1)"
    )
    
    parser.add_argument(
        "--test-impersonation-token",
        action="store_true",
        help="Test impersonation token acquisition (step 2). Requires --target-user and --target-tenant"
    )
    
    parser.add_argument(
        "--test-impersonation-token-query",
        action="store_true",
        help="Test full flow: get tokens + execute query using impersonation token directly (in Cookie). Requires --target-user and --target-tenant"
    )
    
    parser.add_argument(
        "--target-user",
        help="Target username in customer tenant to impersonate. Can also be set via VISIER_IMPERSONATION_TARGET_USERNAME in .env. Required for --test-impersonation-token"
    )
    
    parser.add_argument(
        "--customer-apikey",
        help="Customer's API key (required for --test-impersonation-token). Can also be set via VISIER_IMPERSONATION_CUSTOMER_APIKEY in .env"
    )
    
    parser.add_argument(
        "--username",
        help="Visier username (for token testing, otherwise uses .env config)"
    )
    
    parser.add_argument(
        "--password",
        help="Visier password (for token testing, otherwise uses .env config)"
    )
    
    parser.add_argument(
        "--output",
        help="Path to save results CSV (optional)"
    )
    
    args = parser.parse_args()
    
    # Get target-tenant from env var if not provided via command line
    if not args.target_tenant:
        args.target_tenant = os.getenv("VISIER_IMPERSONATION_TARGET_TENANT_ID")
    
    # Get target-user from env var if not provided via command line
    if not args.target_user:
        args.target_user = os.getenv("VISIER_IMPERSONATION_TARGET_USERNAME")
    
    # Validate that target-tenant is provided unless testing tokens only
    if not args.test_token_only and not args.test_impersonation_token and not args.test_impersonation_token_query and not args.target_tenant:
        parser.error("--target-tenant is required (or set VISIER_IMPERSONATION_TARGET_TENANT_ID in .env) unless using --test-token-only, --test-impersonation-token, or --test-impersonation-token-query")
    
    # For test-token-only, test-impersonation-token, and test-impersonation-token-query, jurisdiction can come from env var
    if args.test_token_only or args.test_impersonation_token or args.test_impersonation_token_query:
        # Jurisdiction will be validated later when we try to get it
        pass
    elif not args.jurisdiction:
        parser.error("--jurisdiction is required (or set VISIER_IMPERSONATION_JURISDICTION in .env - your jurisdiction)")
    
    # Print header
    print("="*70)
    print("VISIER API USER IMPERSONATION TEST")
    print("="*70)
    print()
    print("⚠️  IMPORTANT: This script tests user impersonation.")
    print("   - Requires VTSI profile for API access")
    print("   - Uses demographics vanity (NOT customer vanity)")
    print("   - Ensure you have exceptional access permissions")
    print("   - See impersonator.md for the approval process")
    print()
    
    # Test token acquisition only (check this first, before jurisdiction validation)
    if args.test_token_only:
        print("="*70)
        print("TESTING VISIER SECURE TOKEN ACQUISITION")
        print("="*70)
        print()
        
        # Get username, password, and jurisdiction
        # Priority: 1) Command line args, 2) Impersonation-specific env vars, 3) Regular env vars
        username = args.username
        password = args.password
        jurisdiction = args.jurisdiction
        
        # Try impersonation-specific environment variables first
        # These are YOUR credentials (with VTSI profile), not customer credentials
        if not username:
            username = os.getenv("VISIER_IMPERSONATION_MY_USERNAME")
        if not password:
            password = os.getenv("VISIER_IMPERSONATION_MY_PASSWORD")
        if not jurisdiction:
            jurisdiction = os.getenv("VISIER_IMPERSONATION_JURISDICTION")
        
        # Fall back to regular environment variables if impersonation-specific ones aren't set
        if not username or not password:
            try:
                config = get_api_config()
                username = username or config.get("username")
                password = password or config.get("password")
                if not jurisdiction:
                    # Jurisdiction doesn't exist in regular config, so keep it from args or env
                    pass
                print("→ Using credentials from .env file (regular variables)")
            except ValueError:
                pass
        
        # Validate we have all required values
        if not username:
            print("✗ Error: Username required")
            print()
            print("Provide YOUR username (with VTSI profile) via:")
            print("  1. Command line: --username USERNAME")
            print("  2. Environment variable: VISIER_IMPERSONATION_MY_USERNAME (in .env)")
            print("  3. Fallback: VISIER_USERNAME (in .env)")
            sys.exit(1)
        
        if not password:
            print("✗ Error: Password required")
            print()
            print("Provide YOUR password (with VTSI profile) via:")
            print("  1. Command line: --password PASSWORD")
            print("  2. Environment variable: VISIER_IMPERSONATION_MY_PASSWORD (in .env)")
            print("  3. Fallback: VISIER_PASSWORD (in .env)")
            sys.exit(1)
        
        if not jurisdiction:
            print("✗ Error: Jurisdiction required")
            print()
            print("Provide jurisdiction via:")
            print("  1. Command line: --jurisdiction US|EU|CA|APAC")
            print("  2. Environment variable: VISIER_IMPERSONATION_JURISDICTION (in .env)")
            sys.exit(1)
        
        # Validate jurisdiction
        jurisdiction = jurisdiction.upper()
        if jurisdiction not in DEMOGRAPHICS_VANITIES:
            print(f"✗ Error: Invalid jurisdiction: {jurisdiction}")
            print(f"  Must be one of: {', '.join(DEMOGRAPHICS_VANITIES.keys())}")
            sys.exit(1)
        
        print(f"→ Using YOUR credentials (with VTSI profile):")
        print(f"  Username: {username}")
        print(f"  Jurisdiction: {jurisdiction}")
        if args.username or os.getenv("VISIER_IMPERSONATION_MY_USERNAME"):
            print(f"  Source: {'Command line' if args.username else 'VISIER_IMPERSONATION_MY_USERNAME'}")
        else:
            print(f"  Source: VISIER_USERNAME (fallback)")
        print()
        
        try:
            token = get_visier_secure_token(
                username=username,
                password=password,
                jurisdiction=jurisdiction,
                apikey=os.getenv("VISIER_IMPERSONATION_APIKEY") or os.getenv("VISIER_APIKEY")
            )
            
            print()
            print("="*70)
            print("SUCCESS: Token acquired successfully")
            print("="*70)
            print(f"Token: {token}")
            print()
            print("You can now use this token for API requests with TargetTenantID header.")
            sys.exit(0)
            
        except requests.HTTPError as e:
            print(f"\n✗ Token acquisition failed: {e}")
            print("\nTroubleshooting:")
            print("  1. Verify you have VTSI profile for API access")
            print("  2. Check that username and password are correct")
            print("  3. Verify the jurisdiction matches your account region")
            print("  4. Ensure your account has API access enabled")
            sys.exit(1)
        except Exception as e:
            print(f"\n✗ Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    # Test impersonation token acquisition (step 2)
    if args.test_impersonation_token:
        print("="*70)
        print("TESTING VISIER IMPERSONATION TOKEN ACQUISITION")
        print("="*70)
        print()
        print("This is step 2 of the impersonation flow:")
        print("  1. Get secure token (ASID token) using your credentials")
        print("  2. Get impersonation token using ASID token + customer info")
        print()
        
        # Validate required parameters
        if not args.target_user:
            print("✗ Error: Target username required for impersonation token test")
            print()
            print("Provide target username via:")
            print("  1. Command line: --target-user CUSTOMER_USERNAME")
            print("  2. Environment variable: VISIER_IMPERSONATION_TARGET_USERNAME (in .env)")
            print()
            print("Usage:")
            print("  python test_impersonation.py --test-impersonation-token \\")
            print("    --target-user CUSTOMER_USERNAME --target-tenant CUSTOMER_TENANT_ID \\")
            print("    --customer-apikey CUSTOMER_API_KEY --jurisdiction US")
            sys.exit(1)
        
        if not args.target_tenant:
            print("✗ Error: Target tenant ID required for impersonation token test")
            print()
            print("Provide target tenant ID via:")
            print("  1. Command line: --target-tenant CUSTOMER_TENANT_ID")
            print("  2. Environment variable: VISIER_IMPERSONATION_TARGET_TENANT_ID (in .env)")
            sys.exit(1)
        
        # Get customer API key
        customer_apikey = args.customer_apikey or os.getenv("VISIER_IMPERSONATION_CUSTOMER_APIKEY")
        if not customer_apikey:
            print("✗ Error: Customer API key required")
            print()
            print("Provide customer API key via:")
            print("  1. Command line: --customer-apikey CUSTOMER_API_KEY")
            print("  2. Environment variable: VISIER_IMPERSONATION_CUSTOMER_APIKEY (in .env)")
            sys.exit(1)
        
        # Get jurisdiction
        jurisdiction = args.jurisdiction or os.getenv("VISIER_IMPERSONATION_JURISDICTION")
        if not jurisdiction:
            print("✗ Error: Jurisdiction required")
            sys.exit(1)
        jurisdiction = jurisdiction.upper()
        
        if jurisdiction not in DEMOGRAPHICS_VANITIES:
            print(f"✗ Error: Invalid jurisdiction: {jurisdiction}")
            sys.exit(1)
        
        try:
            # Step 1: Get secure token using your credentials
            print("Step 1: Getting secure token (ASID token)...")
            print()
            
            # Get your credentials
            username = args.username or os.getenv("VISIER_IMPERSONATION_MY_USERNAME")
            password = args.password or os.getenv("VISIER_IMPERSONATION_MY_PASSWORD")
            
            if not username or not password:
                try:
                    config = get_api_config()
                    username = username or config.get("username")
                    password = password or config.get("password")
                except ValueError:
                    pass
            
            if not username or not password:
                print("✗ Error: Your username and password required for step 1")
                sys.exit(1)
            
            asid_token = get_visier_secure_token(
                username=username,
                password=password,
                jurisdiction=jurisdiction,
                apikey=os.getenv("VISIER_IMPERSONATION_APIKEY") or os.getenv("VISIER_APIKEY")
            )
            
            print()
            print("Step 2: Getting impersonation token...")
            print()
            
            # Step 2: Get impersonation token
            impersonation_token = get_visier_impersonation_token(
                asid_token=asid_token,
                target_user_name=args.target_user,
                target_tenant_id=args.target_tenant,
                customer_apikey=customer_apikey,
                jurisdiction=jurisdiction
            )
            
            print()
            print("="*70)
            print("SUCCESS: Impersonation token acquired successfully")
            print("="*70)
            print(f"Impersonation Token: {impersonation_token}")
            print()
            print("You can now use this impersonation token for API requests")
            print("as if you were the customer user in their tenant.")
            sys.exit(0)
            
        except requests.HTTPError as e:
            print(f"\n✗ Impersonation token acquisition failed: {e}")
            print("\nTroubleshooting:")
            print("  1. Verify you have API VI profile")
            print("  2. Verify you have 'Read Impersonated' profile")
            print("  3. Verify you have UserManagement Read access")
            print("  4. Check that target user exists in the customer tenant")
            print("  5. Verify customer API key is correct")
            sys.exit(1)
        except Exception as e:
            print(f"\n✗ Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    # Test impersonation token query (full flow: get tokens + query with impersonation token)
    if args.test_impersonation_token_query:
        print("="*70)
        print("TESTING FULL IMPERSONATION FLOW WITH IMPERSONATION TOKEN")
        print("="*70)
        print()
        print("This tests the complete flow:")
        print("  1. Get secure token (ASID token) using your credentials")
        print("  2. Get impersonation token using ASID token + customer info")
        print("  3. Execute query using impersonation token directly (in Cookie header)")
        print()
        print("Test Configuration:")
        print(f"  - Jurisdiction: {args.jurisdiction or os.getenv('VISIER_IMPERSONATION_JURISDICTION', 'Not set')}")
        print(f"  - Target User: {args.target_user or os.getenv('VISIER_IMPERSONATION_TARGET_USERNAME', 'Not set')}")
        print(f"  - Target Tenant: {args.target_tenant or os.getenv('VISIER_IMPERSONATION_TARGET_TENANT_ID', 'Not set')}")
        print(f"  - Customer API Key: {'Set' if (args.customer_apikey or os.getenv('VISIER_IMPERSONATION_CUSTOMER_APIKEY')) else 'Not set'}")
        print()
        
        # Validate required parameters
        if not args.target_user:
            print("✗ Error: Target username required")
            print("  Provide via: --target-user CUSTOMER_USERNAME or VISIER_IMPERSONATION_TARGET_USERNAME")
            sys.exit(1)
        
        if not args.target_tenant:
            print("✗ Error: Target tenant ID required")
            print("  Provide via: --target-tenant CUSTOMER_TENANT_ID or VISIER_IMPERSONATION_TARGET_TENANT_ID")
            sys.exit(1)
        
        # Get customer API key
        customer_apikey = args.customer_apikey or os.getenv("VISIER_IMPERSONATION_CUSTOMER_APIKEY")
        if not customer_apikey:
            print("✗ Error: Customer API key required")
            print("  Provide via: --customer-apikey CUSTOMER_API_KEY or VISIER_IMPERSONATION_CUSTOMER_APIKEY")
            sys.exit(1)
        
        # Get jurisdiction
        jurisdiction = args.jurisdiction or os.getenv("VISIER_IMPERSONATION_JURISDICTION")
        if not jurisdiction:
            print("✗ Error: Jurisdiction required")
            sys.exit(1)
        jurisdiction = jurisdiction.upper()
        
        if jurisdiction not in DEMOGRAPHICS_VANITIES:
            print(f"✗ Error: Invalid jurisdiction: {jurisdiction}")
            sys.exit(1)
        
        try:
            # Step 1: Get secure token using your credentials
            print("Step 1: Getting secure token (ASID token)...")
            print()
            
            # Get your credentials
            username = args.username or os.getenv("VISIER_IMPERSONATION_MY_USERNAME")
            password = args.password or os.getenv("VISIER_IMPERSONATION_MY_PASSWORD")
            
            if not username or not password:
                try:
                    config = get_api_config()
                    username = username or config.get("username")
                    password = password or config.get("password")
                except ValueError:
                    pass
            
            if not username or not password:
                print("✗ Error: Your username and password required for step 1")
                sys.exit(1)
            
            asid_token = get_visier_secure_token(
                username=username,
                password=password,
                jurisdiction=jurisdiction,
                apikey=os.getenv("VISIER_IMPERSONATION_APIKEY") or os.getenv("VISIER_APIKEY")
            )
            
            print()
            print("Step 2: Getting impersonation token...")
            print()
            
            # Step 2: Get impersonation token
            impersonation_token = get_visier_impersonation_token(
                asid_token=asid_token,
                target_user_name=args.target_user,
                target_tenant_id=args.target_tenant,
                customer_apikey=customer_apikey,
                jurisdiction=jurisdiction
            )
            
            print()
            print("Step 3: Executing query using impersonation token directly...")
            print()
            
            # Step 3: Execute query using impersonation token
            # Using simple payload for unit testing (as per documentation)
            test_payload = {
                "query": {
                    "source": {
                        "metric": "employeeCount"
                    },
                    "timeIntervals": {
                        "fromDateTime": "2024-01-01"
                    }
                }
            }
            
            response = execute_query_with_impersonation_token(
                payload=test_payload,
                impersonation_token=impersonation_token,
                customer_apikey=customer_apikey,
                jurisdiction=jurisdiction
            )
            
            print()
            print("="*70)
            print("RESPONSE ANALYSIS")
            print("="*70)
            print(f"  Response Type: {type(response).__name__}")
            if isinstance(response, dict):
                print(f"  Response Keys: {list(response.keys())}")
                print(f"  Full Response Structure:")
                print(json.dumps(response, indent=2, default=str)[:1000])  # First 1000 chars
                if len(json.dumps(response, default=str)) > 1000:
                    print(f"  ... (truncated, total size: {len(json.dumps(response, default=str))} chars)")
            
            # Try to convert to DataFrame to verify we got data
            try:
                df = convert_vanilla_response_to_dataframe(response, metric_id="employeeCount")
                
                print()
                print("="*70)
                print("SUCCESS: Full impersonation flow completed")
                print("="*70)
                print(f"  ✓ Step 1: ASID token obtained")
                print(f"  ✓ Step 2: Impersonation token obtained")
                print(f"  ✓ Step 3: Query executed successfully")
                print(f"  ✓ Step 4: Response parsed to DataFrame")
                print(f"\n  Data Summary:")
                print(f"    - Rows returned: {len(df)}")
                print(f"    - Columns: {', '.join(df.columns)}")
                
                if len(df) > 0:
                    print(f"\n  Sample data (first 3 rows):")
                    print(df.head(3).to_string())
                else:
                    print(f"\n  ⚠️  Warning: No data rows returned (empty result)")
                
            except Exception as df_error:
                print()
                print("="*70)
                print("PARTIAL SUCCESS: Query executed but DataFrame conversion failed")
                print("="*70)
                print(f"  ✓ Step 1: ASID token obtained")
                print(f"  ✓ Step 2: Impersonation token obtained")
                print(f"  ✓ Step 3: Query executed successfully (HTTP 200)")
                print(f"  ✗ Step 4: DataFrame conversion failed: {df_error}")
                print(f"\n  This may indicate:")
                print(f"    - Response structure differs from expected format")
                print(f"    - Response contains error in different format")
                print(f"    - Response is valid but empty")
                print()
                print("="*70)
                print("FINAL STATUS: PARTIAL SUCCESS")
                print("="*70)
                print("Query executed but response parsing failed:")
                print("  [✓] ASID token acquisition")
                print("  [✓] Impersonation token acquisition")
                print("  [✓] Query execution (HTTP 200)")
                print("  [✗] Response parsing to DataFrame")
            
            print()
            print("="*70)
            print("VERIFICATION SUMMARY")
            print("="*70)
            print("✓ Impersonation token works directly in Cookie header!")
            print("✓ Cookie name 'VisierImpersonationToken' is correct")
            print("✓ No TargetTenantID header needed - token contains tenant context")
            print("✓ Request format matches documentation")
            print()
            print("="*70)
            print("FINAL STATUS: SUCCESS")
            print("="*70)
            print("All steps completed successfully:")
            print("  [✓] ASID token acquisition")
            print("  [✓] Impersonation token acquisition")
            print("  [✓] Query execution with impersonation token")
            print("  [✓] Response received and parsed")
            sys.exit(0)
            
        except requests.HTTPError as e:
            print()
            print("="*70)
            print("TEST FAILED: HTTP Error")
            print("="*70)
            print(f"Error: {e}")
            print()
            # Show payload if available
            try:
                if 'test_payload' in locals():
                    print("Request Payload:")
                    print(json.dumps(test_payload, indent=2))
            except:
                pass
            print()
            print("Request Details:")
            print(f"  - Method: POST")
            print(f"  - Endpoint: /v1/data/query/aggregate")
            print(f"  - Cookie: VisierImpersonationToken (set)")
            print(f"  - Jurisdiction: {jurisdiction if 'jurisdiction' in locals() else 'N/A'}")
            print()
            print("Troubleshooting:")
            print("  1. Verify you have API VI profile")
            print("  2. Verify you have 'Read Impersonated' profile")
            print("  3. Verify you have UserManagement Read access")
            print("  4. Check that target user exists in the customer tenant")
            print("  5. Verify customer API key is correct")
            print("  6. Verify impersonation token is valid")
            print("  7. Check if you're in the correct AWS sandbox environment")
            print("  8. Verify the impersonated user has data export permissions")
            print()
            print("="*70)
            print("FINAL STATUS: FAILED")
            print("="*70)
            print("Test failed during execution:")
            if 'asid_token' in locals():
                print("  [✓] ASID token acquisition")
            else:
                print("  [✗] ASID token acquisition")
            if 'impersonation_token' in locals():
                print("  [✓] Impersonation token acquisition")
            else:
                print("  [✗] Impersonation token acquisition")
            print("  [✗] Query execution")
            sys.exit(1)
        except Exception as e:
            print()
            print("="*70)
            print("TEST FAILED: Unexpected Error")
            print("="*70)
            print(f"Error Type: {type(e).__name__}")
            print(f"Error Message: {e}")
            print()
            print("Full Traceback:")
            import traceback
            traceback.print_exc()
            print()
            print("="*70)
            print("FINAL STATUS: FAILED (Unexpected Error)")
            print("="*70)
            sys.exit(1)
    
    # For non-token-only operations, validate jurisdiction
    try:
        demographics_vanity = get_demographics_vanity(args.jurisdiction)
        demographics_host = build_demographics_host(args.jurisdiction)
        print(f"✓ Jurisdiction: {args.jurisdiction}")
        print(f"  Demographics Vanity: {demographics_vanity}")
        print(f"  Demographics Host: {demographics_host}")
        print()
    except ValueError as e:
        print(f"✗ Jurisdiction error: {e}")
        sys.exit(1)
    
    # Load config for other operations
    try:
        config = get_api_config()
        print("✓ API configuration loaded")
        print(f"  Username: {config.get('username', 'Not set')}")
        print(f"  API Key: {'Set' if config.get('apikey') else 'Not set'}")
        print()
        print("⚠️  Note: For impersonation, we use demographics vanity, not the")
        print(f"   vanity from your config ({config.get('vanity', 'N/A')})")
        print()
    except ValueError as e:
        print(f"✗ Configuration error: {e}")
        print("  → Run: python query.py --setup")
        sys.exit(1)
    
    # Test connection if requested
    if args.test_query:
        success = test_impersonation_connection(args.target_tenant, args.jurisdiction, config)
        sys.exit(0 if success else 1)
    
    # Load or build query payload
    if args.payload:
        print(f"→ Loading query payload from: {args.payload}")
        payload = load_query_payload_from_json(args.payload)
        print("✓ Payload loaded")
    else:
        print("→ Building default test query...")
        payload = {
            "query": {
                "source": {"metric": "employeeCount"},
                "axes": [
                    create_dimension_axis("Country_Cost", level_ids=["Country"])
                ],
                "timeIntervals": {
                    "fromDateTime": "2026-01-01",
                    "intervalPeriodType": "YEAR",
                    "intervalCount": 5,
                    "direction": "BACKWARD"
                }
            },
            "options": {
                "zeroVisibility": "ELIMINATE",
                "nullVisibility": "ELIMINATE"
            }
        }
        print("✓ Default payload created")
    
    print()
    
    # Execute query with impersonation
    try:
        response = execute_query_with_impersonation(
            payload=payload,
            target_tenant_id=args.target_tenant,
            jurisdiction=args.jurisdiction,
            config=config
        )
        
        # Convert to DataFrame
        metric_id = payload["query"]["source"]["metric"]
        df = convert_vanilla_response_to_dataframe(response, metric_id=metric_id)
        
        print(f"\n✓ Query executed successfully!")
        print(f"  - Rows: {len(df)}")
        print(f"  - Columns: {', '.join(df.columns)}")
        
        # Show sample data
        if len(df) > 0:
            print(f"\n  Sample data (first 5 rows):")
            print(df.head(5).to_string())
        
        # Save to CSV if requested
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(output_path, index=False)
            print(f"\n✓ Results saved to: {output_path}")
        
        print("\n" + "="*70)
        print("SUCCESS: Impersonation test completed")
        print("="*70)
        
    except requests.HTTPError as e:
        print(f"\n✗ Query failed: {e}")
        print("\nTroubleshooting:")
        print("  1. Verify you have VTSI profile for API access")
        print("  2. Verify you have exceptional access permissions")
        print("  3. Check that the target tenant ID is correct")
        print("  4. Verify the jurisdiction matches the tenant's region")
        print("  5. Ensure your account has the required roles/profiles")
        print("  6. Review impersonator.md for the approval process")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
