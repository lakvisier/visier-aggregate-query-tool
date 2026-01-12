#!/usr/bin/env python3
"""
Discover Dimension Levels for Visier Dimensions

This script queries the Visier Dimensions API to discover available level IDs
for a given dimension. This is especially useful for parent-child hierarchies
like Organization_Hierarchy where level IDs are tenant-specific.

Usage:
    # Discover levels for Organization_Hierarchy
    python scripts/discover_dimension_levels.py Organization_Hierarchy
    
    # Discover levels for Country_Cost
    python scripts/discover_dimension_levels.py Country_Cost
    
    # Use v2alpha API (includes more details)
    python scripts/discover_dimension_levels.py Organization_Hierarchy --api-version v2alpha
    
    # Get details for a specific analytic object
    python scripts/discover_dimension_levels.py Organization_Hierarchy --object-id Employee
"""

import os
import sys
import json
import argparse
import requests
from typing import Dict, List, Optional

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Import - works both as standalone and as part of package
try:
    from aggregate_query_vanilla import get_api_config, get_asid_token
except ImportError:
    # Fallback for package structure
    from aggregate_query_vanilla import get_api_config, get_asid_token


def get_dimension_details_v1(
    dimension_id: str,
    object_id: Optional[str] = None,
    config: Optional[Dict[str, str]] = None,
    asid_token: Optional[str] = None
) -> Dict:
    """
    Get dimension details using v1 API.
    
    If object_id is provided, uses: GET /v1/data/model/analytic-objects/{objectId}/dimensions/{dimensionId}
    Otherwise, tries to find dimension in all analytic objects.
    
    Args:
        dimension_id: The dimension ID (e.g., "Organization_Hierarchy")
        object_id: Optional analytic object ID (e.g., "Employee")
        config: Optional API config dict
        asid_token: Optional ASID token
    
    Returns:
        Dimension details dictionary
    """
    if config is None:
        config = get_api_config()
    
    if asid_token is None:
        asid_token = get_asid_token(config)
    
    host = config["host"].rstrip('/')
    vanity = config["vanity"]
    
    # Try with object_id first if provided
    if object_id:
        url = f"{host}/v1/data/model/analytic-objects/{object_id}/dimensions"
        params = {"id": [dimension_id]}
    else:
        # Try to get from dimensions endpoint (may not exist in v1)
        # For now, we'll need object_id - most dimensions are under "Employee"
        url = f"{host}/v1/data/model/analytic-objects/Employee/dimensions"
        params = {"id": [dimension_id]}
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    if config.get("apikey"):
        headers["apikey"] = config["apikey"]
    
    cookies = {"VisierASIDToken": asid_token}
    
    if vanity:
        params["vanity"] = vanity
    
    response = requests.get(url, headers=headers, cookies=cookies, params=params)
    response.raise_for_status()
    
    data = response.json()
    
    # Response is usually a list of dimensions
    if isinstance(data, list) and len(data) > 0:
        return data[0]  # Return first match
    elif isinstance(data, dict):
        return data
    
    raise ValueError(f"Dimension {dimension_id} not found")


def get_dimension_details_v2alpha(
    dimension_id: str,
    config: Optional[Dict[str, str]] = None,
    asid_token: Optional[str] = None,
    with_details: bool = True
) -> Dict:
    """
    Get dimension details using v2alpha API.
    
    Endpoint: GET /v2alpha/data/model/dimensions/{dimensionId}
    
    Args:
        dimension_id: The dimension ID (e.g., "Organization_Hierarchy")
        config: Optional API config dict
        asid_token: Optional ASID token
        with_details: If True, includes levels and settings (default: True)
    
    Returns:
        Dimension details dictionary with levels
    """
    if config is None:
        config = get_api_config()
    
    if asid_token is None:
        asid_token = get_asid_token(config)
    
    host = config["host"].rstrip('/')
    vanity = config["vanity"]
    
    url = f"{host}/v2alpha/data/model/dimensions/{dimension_id}"
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    if config.get("apikey"):
        headers["apikey"] = config["apikey"]
    
    cookies = {"VisierASIDToken": asid_token}
    
    params = {}
    if vanity:
        params["vanity"] = vanity
    
    if with_details:
        params["with"] = ["details"]  # Get levels and settings
    
    response = requests.get(url, headers=headers, cookies=cookies, params=params)
    response.raise_for_status()
    
    return response.json()


def extract_level_ids(dimension_details: Dict) -> List[str]:
    """
    Extract level IDs from dimension details.
    
    For parent-child hierarchies, level IDs are often not directly in the response.
    We need to infer them or try common patterns.
    
    Args:
        dimension_details: Dimension details dictionary from API
    
    Returns:
        List of level IDs
    """
    level_ids = []
    
    # Handle v2alpha response structure
    if "dimension" in dimension_details:
        dim = dimension_details["dimension"]
        
        # Check if it's a parent-child hierarchy
        if "details" in dim and "parentChild" in dim["details"]:
            # For parent-child, levels are dynamically generated
            # Common level IDs to try:
            level_ids = [
                "Profit_Center",
                "Business_Unit", 
                "Department",
                "Level_1",
                "Level_2",
                "Level_3",
                dim.get("objectName", "")  # Try dimension name itself
            ]
            # Remove empty strings
            level_ids = [lid for lid in level_ids if lid]
        
        # Check for explicit levels
        if "details" in dim and "levels" in dim["details"]:
            levels = dim["details"]["levels"]
            if isinstance(levels, list):
                for level in levels:
                    if isinstance(level, dict):
                        level_id = (
                            level.get("id") or
                            level.get("levelId") or
                            level.get("name") or
                            level.get("objectName")
                        )
                        if level_id:
                            level_ids.append(level_id)
                    elif isinstance(level, str):
                        level_ids.append(level)
    
    # Check for levels at top level (v1 API structure)
    elif "levels" in dimension_details:
        levels = dimension_details["levels"]
        if isinstance(levels, list):
            for level in levels:
                if isinstance(level, dict):
                    level_id = (
                        level.get("id") or
                        level.get("levelId") or
                        level.get("name") or
                        level.get("objectName")
                    )
                    if level_id:
                        level_ids.append(level_id)
                elif isinstance(level, str):
                    level_ids.append(level)
    
    return level_ids


def print_dimension_info(dimension_details: Dict, dimension_id: str):
    """Pretty print dimension information."""
    print(f"\n{'='*70}")
    print(f"Dimension: {dimension_id}")
    print(f"{'='*70}")
    
    # Basic info
    if "objectName" in dimension_details:
        print(f"Object Name: {dimension_details['objectName']}")
    if "displayName" in dimension_details:
        print(f"Display Name: {dimension_details.get('displayName')}")
    if "description" in dimension_details:
        print(f"Description: {dimension_details.get('description')}")
    
    # Dimension type
    if "dimensionType" in dimension_details:
        dim_type = dimension_details["dimensionType"]
        print(f"Dimension Type: {dim_type}")
        if dim_type == "PARENT_CHILD":
            print("  ⚠️  This is a PARENT-CHILD hierarchy - level IDs are tenant-specific!")
    
    # Levels
    level_ids = extract_level_ids(dimension_details)
    
    # Check if it's parent-child
    is_parent_child = False
    if "dimension" in dimension_details:
        dim = dimension_details["dimension"]
        if "details" in dim and "parentChild" in dim["details"]:
            is_parent_child = True
    
    if level_ids:
        print(f"\n{'⚠️  SUGGESTED Level IDs to Try' if is_parent_child else 'Available Level IDs'} ({len(level_ids)}):")
        for i, level_id in enumerate(level_ids, 1):
            print(f"  {i}. {level_id}")
        
        if is_parent_child:
            print(f"\n⚠️  NOTE: This is a PARENT-CHILD hierarchy.")
            print(f"   Level IDs are tenant-specific and may not be in the API response.")
            print(f"   Try these common level IDs in order:")
            print(f"   1. Start with: {json.dumps([level_ids[0]])}")
            print(f"   2. If that fails, try others from the list above")
            print(f"   3. Test each level ID with a query to see which works")
        else:
            print(f"\n✅ Use these level IDs in your query:")
            print(f"   \"levelIds\": {json.dumps(level_ids[:1])}  # Use first level, or specify multiple")
            if len(level_ids) > 1:
                print(f"   \"levelIds\": {json.dumps(level_ids)}  # Use all levels")
    else:
        print("\n⚠️  No level IDs found in response")
        if is_parent_child:
            print("   This is a parent-child hierarchy - level IDs are tenant-specific.")
            print("   Try common level IDs: ['Profit_Center'], ['Business_Unit'], ['Level_1']")
        else:
            print("   This might be a regular dimension (not parent-child)")
            print("   Try using the dimension name itself as the level ID")
    
    # Raw response (for debugging)
    print(f"\n{'='*70}")
    print("Raw Response (first 500 chars):")
    print(json.dumps(dimension_details, indent=2)[:500] + "...")


def main():
    parser = argparse.ArgumentParser(
        description="Discover dimension level IDs using Visier Dimensions API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "dimension_id",
        help="Dimension ID to query (e.g., 'Organization_Hierarchy', 'Country_Cost')"
    )
    parser.add_argument(
        "--api-version",
        choices=["v1", "v2alpha"],
        default="v2alpha",
        help="API version to use (default: v2alpha - includes more details)"
    )
    parser.add_argument(
        "--object-id",
        help="Analytic object ID (e.g., 'Employee'). Required for v1 API if dimension not found globally"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw JSON response"
    )
    parser.add_argument(
        "--level-ids-only",
        action="store_true",
        help="Output only the level IDs (one per line, for scripting)"
    )
    
    args = parser.parse_args()
    
    try:
        config = get_api_config()
        asid_token = get_asid_token(config)
        
        if args.api_version == "v2alpha":
            dimension_details = get_dimension_details_v2alpha(
                args.dimension_id,
                config=config,
                asid_token=asid_token
            )
        else:
            dimension_details = get_dimension_details_v1(
                args.dimension_id,
                object_id=args.object_id or "Employee",
                config=config,
                asid_token=asid_token
            )
        
        if args.json:
            print(json.dumps(dimension_details, indent=2))
        elif args.level_ids_only:
            level_ids = extract_level_ids(dimension_details)
            for level_id in level_ids:
                print(level_id)
        else:
            print_dimension_info(dimension_details, args.dimension_id)
        
        return 0
        
    except requests.HTTPError as e:
        print(f"✗ API Error: {e}")
        if hasattr(e.response, 'text'):
            try:
                error_data = e.response.json()
                print(f"  Details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"  Response: {e.response.text[:500]}")
        return 1
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
