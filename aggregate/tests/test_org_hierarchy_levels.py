#!/usr/bin/env python3
"""
Quick test script to try different Organization_Hierarchy level IDs.

Tests each level ID and reports which ones work.
"""

import os
import sys
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aggregate.aggregate_query_vanilla import (
    execute_vanilla_aggregate_query,
    convert_vanilla_response_to_dataframe,
    get_api_config
)

# Level IDs to test
LEVEL_IDS_TO_TEST = [
    ["Level_1"],
    ["Level_2"],
    ["Level_3"],
    ["Organization_Hierarchy"]
]

def test_level_id(level_ids):
    """Test a specific level ID."""
    print(f"\n{'='*70}")
    print(f"Testing levelIds: {level_ids}")
    print(f"{'='*70}")
    
    # Build a simple test query - just get one year to test quickly
    payload = {
        "query": {
            "source": {
                "metric": "employeeCount"
            },
            "axes": [
                {
                    "dimensionLevelSelection": {
                        "dimension": {
                            "name": "Organization_Hierarchy",
                            "qualifyingPath": "Employee"
                        },
                        "levelIds": level_ids
                    }
                }
            ],
            "filters": [
                {
                    "memberSet": {
                        "dimension": {
                            "name": "Employment_Type",
                            "qualifyingPath": "Employee"
                        },
                        "values": {
                            "included": [
                                {
                                    "path": ["Full-time shifts"]
                                }
                            ]
                        }
                    }
                }
            ],
            "timeIntervals": {
                "fromDateTime": "2025-01-01",
                "intervalPeriodType": "DAY",
                "intervalCount": 1,
                "direction": "BACKWARD"
            }
        },
        "options": {
            "calendarType": "TENANT_CALENDAR",
            "zeroVisibility": "ELIMINATE",
            "nullVisibility": "ELIMINATE",
            "internal": {
                "alignTimeAxisToPeriodEnd": True
            }
        }
    }
    
    try:
        response = execute_vanilla_aggregate_query(payload=payload)
        df = convert_vanilla_response_to_dataframe(response, metric_id="employeeCount")
        
        if df.empty:
            print(f"⚠️  Query succeeded but returned no data")
            return False
        
        print(f"✅ SUCCESS! Query returned {len(df)} rows")
        print(f"\nSample data:")
        print(df.head(5).to_string(index=False))
        
        # Show unique organization values
        org_col = None
        for col in df.columns:
            if col not in ["Measures", "DateInRange", "value", "support"]:
                org_col = col
                break
        
        if org_col:
            unique_orgs = df[org_col].unique()
            print(f"\nUnique {org_col} values ({len(unique_orgs)}):")
            if len(unique_orgs) <= 10:
                for org in unique_orgs:
                    print(f"  - {org}")
            else:
                for org in unique_orgs[:10]:
                    print(f"  - {org}")
                print(f"  ... and {len(unique_orgs) - 10} more")
        
        return True
        
    except Exception as e:
        error_msg = str(e)
        if "DSE_INVALID_DATA_MODEL_OBJECT" in error_msg:
            print(f"❌ FAILED: Invalid level ID")
            if "Unable to resolve" in error_msg:
                print(f"   The level ID {level_ids} doesn't exist in your tenant")
        else:
            print(f"❌ FAILED: {error_msg}")
        return False


def main():
    print("Testing Organization_Hierarchy Level IDs")
    print("=" * 70)
    
    working_levels = []
    
    for level_ids in LEVEL_IDS_TO_TEST:
        if test_level_id(level_ids):
            working_levels.append(level_ids)
    
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    
    if working_levels:
        print(f"\n✅ Working Level IDs:")
        for level_ids in working_levels:
            print(f"   {json.dumps(level_ids)}")
        
        print(f"\n💡 Use this in your query:")
        print(f"   \"levelIds\": {json.dumps(working_levels[0])}")
    else:
        print(f"\n❌ None of the tested level IDs worked")
        print(f"   You may need to:")
        print(f"   1. Check your tenant's documentation")
        print(f"   2. Try other common level IDs (Profit_Center, Business_Unit, etc.)")
        print(f"   3. Contact Visier support for your tenant's level IDs")
    
    return 0 if working_levels else 1


if __name__ == "__main__":
    sys.exit(main())
