#!/usr/bin/env python3
"""
Easy Runner for Visier Aggregate Queries

Simple CLI tool for running and debugging aggregate queries.

Usage:
    # Run with default payload file
    python aggregate/scripts/run_query.py
    
    # Run with custom payload file
    python aggregate/scripts/run_query.py --file aggregate/examples/query_payload_examples.json
    
    # Debug mode (shows payload, headers, etc.)
    python aggregate/scripts/run_query.py --debug
    
    # Verbose mode (shows detailed execution steps)
    python aggregate/scripts/run_query.py --verbose
    
    # Save payload to file before sending (for inspection)
    python aggregate/scripts/run_query.py --save-payload payload.json
    
    # Validate payload without executing
    python aggregate/scripts/run_query.py --validate-only
"""

import os
import sys
import json
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aggregate.aggregate_query_vanilla import (
    execute_vanilla_aggregate_query,
    convert_vanilla_response_to_dataframe,
    load_query_payload_from_json,
    get_api_config
)


def print_section(title: str, width: int = 70):
    """Print a formatted section header."""
    print("\n" + "=" * width)
    print(title)
    print("=" * width)


def print_payload(payload: dict, title: str = "Query Payload"):
    """Pretty print the payload."""
    print_section(title)
    print(json.dumps(payload, indent=2))
    print()


def validate_payload(payload: dict) -> tuple[bool, list[str]]:
    """
    Validate the payload structure.
    
    Returns:
        (is_valid, list_of_errors)
    """
    errors = []
    
    # Check top-level structure
    if "query" not in payload:
        errors.append("Missing 'query' key in payload")
        return False, errors
    
    query = payload["query"]
    
    # Check source
    if "source" not in query:
        errors.append("Missing 'source' in query")
    else:
        source = query["source"]
        if "metric" not in source:
            errors.append("Missing 'metric' in source")
    
    # Check axes (required)
    if "axes" not in query:
        errors.append("Missing 'axes' in query (at least one axis is required)")
    elif not query["axes"]:
        errors.append("'axes' is empty (at least one axis is required)")
    else:
        # Validate each axis
        for i, axis in enumerate(query["axes"]):
            if "dimensionLevelSelection" not in axis:
                errors.append(f"Axis {i}: Missing 'dimensionLevelSelection'")
            else:
                dls = axis["dimensionLevelSelection"]
                if "dimension" not in dls:
                    errors.append(f"Axis {i}: Missing 'dimension' in dimensionLevelSelection")
                elif "name" not in dls["dimension"]:
                    errors.append(f"Axis {i}: Missing 'name' in dimension")
                if "levelIds" not in dls:
                    errors.append(f"Axis {i}: Missing 'levelIds' in dimensionLevelSelection")
                elif not dls["levelIds"]:
                    errors.append(f"Axis {i}: 'levelIds' is empty (at least one level ID required)")
    
    # Check filters (optional, but validate structure if present)
    if "filters" in query:
        for i, filter_item in enumerate(query["filters"]):
            if "memberSet" not in filter_item and "selectionConcept" not in filter_item:
                errors.append(f"Filter {i}: Must have either 'memberSet' or 'selectionConcept'")
    
    # Check timeIntervals (optional, but validate structure if present)
    if "timeIntervals" in query:
        ti = query["timeIntervals"]
        if "fromDateTime" not in ti and "dynamicDateFrom" not in ti:
            errors.append("timeIntervals: Must have either 'fromDateTime' or 'dynamicDateFrom'")
        if "intervalPeriodType" not in ti:
            errors.append("timeIntervals: Missing 'intervalPeriodType'")
        if "intervalCount" not in ti:
            errors.append("timeIntervals: Missing 'intervalCount'")
    
    return len(errors) == 0, errors


def main():
    parser = argparse.ArgumentParser(
        description="Run and debug Visier aggregate queries from JSON payload files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--file", "-f",
        type=str,
        default=None,
        help="Path to JSON file containing the query payload (default: aggregate/examples/query_payload_examples.json)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="CSV file path to save results (default: auto-saves to output/query_results.csv)"
    )
    parser.add_argument(
        "--debug", "-d",
        action="store_true",
        help="Debug mode: show payload, headers, and detailed execution info"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose mode: show detailed execution steps"
    )
    parser.add_argument(
        "--save-payload",
        type=str,
        default=None,
        help="Save the loaded payload to a file (useful for inspection/debugging)"
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate the payload structure, don't execute the query"
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't auto-save results to CSV"
    )
    
    args = parser.parse_args()
    
    # Set default file if not provided
    if args.file is None:
        # Default to examples directory relative to aggregate root
        script_dir = os.path.dirname(os.path.abspath(__file__))
        aggregate_dir = os.path.dirname(script_dir)
        default_file = os.path.join(aggregate_dir, "examples", "query_payload_examples.json")
        args.file = default_file
    
    # Check if payload file exists
    if not os.path.exists(args.file):
        print(f"✗ Error: Payload file not found: {args.file}")
        print(f"\nPlease ensure the file exists or specify a different file with --file")
        return 1
    
    # Load payload
    try:
        if args.debug or args.verbose:
            print_section("Loading Payload")
            print(f"File: {args.file}")
        
        payload = load_query_payload_from_json(args.file)
        
        if args.debug or args.verbose:
            print("✓ Payload loaded successfully")
        
    except Exception as e:
        print(f"✗ Error loading payload file: {e}")
        return 1
    
    # Save payload if requested
    if args.save_payload:
        try:
            with open(args.save_payload, 'w') as f:
                json.dump(payload, f, indent=2)
            print(f"✓ Payload saved to: {args.save_payload}")
        except Exception as e:
            print(f"✗ Error saving payload: {e}")
            return 1
    
    # Validate payload
    if args.debug or args.verbose or args.validate_only:
        print_section("Validating Payload")
        is_valid, errors = validate_payload(payload)
        
        if is_valid:
            print("✓ Payload is valid")
        else:
            print("✗ Payload validation failed:")
            for error in errors:
                print(f"  - {error}")
            return 1
    
    # If validate-only, stop here
    if args.validate_only:
        print("\n✓ Validation complete (--validate-only mode)")
        return 0
    
    # Show payload in debug mode
    if args.debug:
        print_payload(payload, "Payload to be sent")
        
        # Show config info (without sensitive data)
        try:
            config = get_api_config()
            print_section("API Configuration")
            print(f"Host: {config.get('host', 'N/A')}")
            print(f"Vanity: {config.get('vanity', 'N/A')}")
            print(f"API Key: {'***' + config.get('apikey', '')[-4:] if config.get('apikey') else 'N/A'}")
            print(f"Username: {config.get('username', 'N/A')}")
            print(f"Password: {'***' if config.get('password') else 'N/A'}")
        except Exception as e:
            print(f"⚠ Could not load config: {e}")
    
    # Execute query
    try:
        if args.verbose or args.debug:
            print_section("Executing Query")
            print("Sending request to Visier API...")
        
        response = execute_vanilla_aggregate_query(payload=payload)
        
        if args.verbose or args.debug:
            print("✓ Query executed successfully")
            print(f"Response keys: {list(response.keys())}")
            if "cells" in response:
                print(f"Cells returned: {len(response['cells'])}")
            if "axes" in response:
                print(f"Axes (dimensions): {len(response['axes'])}")
        
    except Exception as e:
        print(f"\n✗ Error executing query: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1
    
    # Extract metric ID for DataFrame conversion
    metric_id = None
    if "query" in payload and "source" in payload["query"]:
        metric_id = payload["query"]["source"].get("metric")
    
    # Convert to DataFrame
    try:
        if args.verbose or args.debug:
            print_section("Converting Response")
            print("Converting API response to DataFrame...")
        
        df = convert_vanilla_response_to_dataframe(response, metric_id=metric_id)
        
        # Convert DateInRange to year-end dates
        # DateInRange shows the start of each interval (e.g., 2021-01-01 for 2021 data).
        # We convert the label to year-end (2021-12-31) for clarity.
        if "DateInRange" in df.columns:
            if args.debug:
                print(f"\nDEBUG: Raw DateInRange before conversion: {df['DateInRange'].iloc[0]}")
            
            import re
            from datetime import datetime
            
            def convert_to_year_end(date_str):
                """Convert DateInRange from year-start to year-end."""
                # Format: "2022-01-01T00:00:00.000Z - [0]"
                # Extract date part and interval index
                match = re.match(r'(\d{4}-\d{2}-\d{2})T.*?(\[.*?\])', str(date_str))
                if match:
                    date_part = match.group(1)
                    interval_part = match.group(2)
                    try:
                        # Parse date and convert to year-end
                        date_obj = datetime.strptime(date_part, "%Y-%m-%d")
                        year_end = datetime(date_obj.year, 12, 31)
                        # Reconstruct with year-end date, keeping original time and interval
                        year_end_str = year_end.strftime("%Y-%m-%d")
                        # Keep the time part from original if present
                        time_match = re.search(r'T([\d:\.]+Z)', str(date_str))
                        if time_match:
                            time_part = time_match.group(1)
                            return f"{year_end_str}T{time_part} - {interval_part}"
                        else:
                            return f"{year_end_str}T00:00:00.000Z - {interval_part}"
                    except ValueError:
                        return date_str
                return date_str
            
            df["DateInRange"] = df["DateInRange"].apply(convert_to_year_end)
        
        if args.verbose or args.debug:
            print(f"✓ Converted to DataFrame: {len(df)} rows, {len(df.columns)} columns")
        
    except Exception as e:
        print(f"\n✗ Error converting response: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1
    
    # Display results
    print_section("Query Results")
    print(f"Rows: {len(df)}")
    print(f"Columns: {', '.join(df.columns)}")
    print()
    
    if df.empty:
        print("⚠ No data returned (empty DataFrame)")
        print("\nPossible reasons:")
        print("  - No data matches the query criteria")
        print("  - Metric ID doesn't exist in your tenant")
        print("  - Time period has no data")
        print("  - Filters exclude all data")
    else:
        print("Sample data (first 10 rows):")
        print(df.head(10).to_string(index=False))
        print()
        
        # Show summary statistics
        if "value" in df.columns:
            non_null = df["value"].notna().sum()
            print(f"Value statistics:")
            print(f"  Non-null values: {non_null} / {len(df)}")
            if non_null > 0:
                print(f"  Min: {df['value'].min():.2f}")
                print(f"  Max: {df['value'].max():.2f}")
                print(f"  Sum: {df['value'].sum():.2f}")
                print(f"  Mean: {df['value'].mean():.2f}")
        
        # Show unique values in dimension columns
        dimension_cols = [c for c in df.columns if c not in ["value", "support", "Measures"]]
        for col in dimension_cols[:3]:  # Show first 3 dimensions
            unique_vals = df[col].unique()
            if len(unique_vals) <= 20:
                print(f"\n{col} values ({len(unique_vals)} unique): {list(unique_vals)}")
            else:
                print(f"\n{col} values ({len(unique_vals)} unique): {list(unique_vals[:10])}... (showing first 10)")
    
    # Save to CSV
    if not args.no_save:
        if args.output:
            output_file = args.output
        else:
            # Auto-save to output directory
            output_dir = os.path.join(os.path.dirname(__file__), "output")
            os.makedirs(output_dir, exist_ok=True)
            output_file = os.path.join(output_dir, "query_results.csv")
        
        try:
            df.to_csv(output_file, index=False)
            print(f"\n✓ Results saved to: {output_file}")
        except Exception as e:
            print(f"\n⚠ Could not save results: {e}")
    
    print_section("✓ Query Completed Successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
