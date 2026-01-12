#!/usr/bin/env python3
"""
Example: Using the Visier client programmatically

This script shows how to use the client.py module directly in your own code.
"""

from client import (
    execute_vanilla_aggregate_query,
    convert_vanilla_response_to_dataframe,
    create_dimension_axis,
    load_query_payload_from_json
)

# Example 1: Load and execute a query from a JSON file
print("Example 1: Loading query from JSON file")
print("-" * 50)
payload = load_query_payload_from_json("examples/query_payload_examples.json")
response = execute_vanilla_aggregate_query(payload=payload)
metric_id = payload["query"]["source"]["metric"]
df = convert_vanilla_response_to_dataframe(response, metric_id=metric_id)
print(f"✓ Query executed: {len(df)} rows returned")
print(f"  Columns: {', '.join(df.columns)}")
print()

# Example 2: Build a query programmatically
print("Example 2: Building a query programmatically")
print("-" * 50)

# Create axes (dimensions to group by)
axes = [
    create_dimension_axis("Country_Cost", level_ids=["Country"])
]

# Build the payload
query_payload = {
    "query": {
        "source": {"metric": "employeeCount"},
        "axes": axes,
        "timeIntervals": {
            "fromDateTime": "2026-01-01",
            "intervalPeriodType": "YEAR",
            "intervalCount": 5,
            "direction": "BACKWARD"
        }
    },
    "options": {
        "calendarType": "TENANT_CALENDAR",
        "zeroVisibility": "ELIMINATE",
        "nullVisibility": "ELIMINATE"
    }
}

# Execute
response = execute_vanilla_aggregate_query(payload=query_payload)
df = convert_vanilla_response_to_dataframe(response, metric_id="employeeCount")
print(f"✓ Query executed: {len(df)} rows returned")
print(f"  Sample data:")
print(df.head(3).to_string())
print()

# Example 3: Multiple dimensions
print("Example 3: Query with multiple dimensions")
print("-" * 50)

axes = [
    create_dimension_axis("Country_Cost", level_ids=["Country"]),
    create_dimension_axis("Function")
]

query_payload = {
    "query": {
        "source": {"metric": "employeeCount"},
        "axes": axes,
        "timeIntervals": {
            "fromDateTime": "2025-01-01",
            "intervalPeriodType": "YEAR",
            "intervalCount": 1,
            "direction": "BACKWARD"
        }
    },
    "options": {
        "calendarType": "TENANT_CALENDAR",
        "zeroVisibility": "ELIMINATE",
        "nullVisibility": "ELIMINATE"
    }
}

response = execute_vanilla_aggregate_query(payload=query_payload)
df = convert_vanilla_response_to_dataframe(response, metric_id="employeeCount")
print(f"✓ Query executed: {len(df)} rows returned")
print(f"  Dimensions: Country, Function")
print()

print("All examples completed successfully!")
print("\nTip: See README.md for more usage patterns and examples.")
