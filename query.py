#!/usr/bin/env python3
"""
Visier Aggregate Query Runner - Client-Friendly Script

This is the main entry point for clients to run aggregate queries.

Usage:
    # First time setup (creates .env file)
    python query.py --setup

    # Run a query with a JSON payload file
    python query.py --payload examples/query_payload_examples.json

    # Run with custom output file
    python query.py --payload examples/query_payload_examples.json --output results.csv

    # Validate payload without executing
    python query.py --payload examples/query_payload_examples.json --validate-only

For more help, see CLIENT_WALKTHROUGH.md
"""

import os
import sys
import json
import argparse
from pathlib import Path

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import from the same directory
from client import (
    execute_vanilla_aggregate_query,
    convert_vanilla_response_to_dataframe,
    load_query_payload_from_json,
    get_api_config
)


def print_header(text: str, char: str = "="):
    """Print a formatted header."""
    width = 70
    print("\n" + char * width)
    print(f"  {text}")
    print(char * width)


def print_success(text: str):
    """Print success message."""
    print(f"✓ {text}")


def print_error(text: str):
    """Print error message."""
    print(f"✗ {text}")


def print_info(text: str):
    """Print info message."""
    print(f"ℹ {text}")


def validate_credentials() -> bool:
    """
    Check if credentials are configured.
    
    Returns:
        True if credentials are present, False otherwise
    """
    try:
        config = get_api_config()
        # Check if all required fields are present
        required = ["host", "apikey", "vanity", "username", "password"]
        missing = [key for key in required if not config.get(key)]
        if missing:
            print_error(f"Missing credentials: {', '.join(missing)}")
            print_info("Run with --setup to configure credentials")
            return False
        return True
    except ValueError as e:
        print_error(str(e))
        print_info("Run with --setup to configure credentials")
        return False


def validate_payload_structure(payload: dict) -> tuple[bool, list[str]]:
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
        if "metric" not in source and "metrics" not in source:
            errors.append("Missing 'metric' or 'metrics' in source")
        elif "metrics" in source:
            cols = source.get("metrics", {}).get("columns", [])
            if not cols:
                errors.append("'source.metrics.columns' is empty")
    
    # Check axes (required)
    if "axes" not in query:
        errors.append("Missing 'axes' in query (at least one axis is required)")
    elif not query["axes"]:
        errors.append("'axes' is empty (at least one axis is required)")
    else:
        # Valid axis types (per OpenAPI): dimensionLevelSelection, numericRanges, dimensionMemberSelection, etc.
        VALID_AXIS_KEYS = (
            "dimensionLevelSelection",
            "numericRanges",
            "dimensionMemberSelection",
            "memberMapSelection",
            "formula",
            "selectionConcept",
            "dimensionLeafMemberSelection",
            "dimensionDataMemberSelection",
            "dimensionLevelWithUncategorizedValueSelection",
        )
        for i, axis in enumerate(query["axes"]):
            if not any(k in axis for k in VALID_AXIS_KEYS):
                errors.append(
                    f"Axis {i+1}: Must have one of {', '.join(VALID_AXIS_KEYS)}"
                )
            elif "dimensionLevelSelection" in axis:
                dls = axis["dimensionLevelSelection"]
                if "dimension" not in dls:
                    errors.append(f"Axis {i+1}: Missing 'dimension' in dimensionLevelSelection")
                elif "name" not in dls["dimension"]:
                    errors.append(f"Axis {i+1}: Missing 'name' in dimension")
                if "levelIds" not in dls:
                    errors.append(f"Axis {i+1}: Missing 'levelIds' in dimensionLevelSelection")
                elif not dls["levelIds"]:
                    errors.append(f"Axis {i+1}: 'levelIds' is empty (at least one level ID required)")
            elif "numericRanges" in axis:
                nr = axis["numericRanges"]
                if "property" not in nr:
                    errors.append(f"Axis {i+1}: Missing 'property' in numericRanges")
                if "ranges" not in nr:
                    errors.append(f"Axis {i+1}: Missing 'ranges' in numericRanges (space-separated bounds)")
    
    return len(errors) == 0, errors


def main():
    parser = argparse.ArgumentParser(
        description="Run Visier aggregate queries from JSON payload files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "--payload", "-p",
        type=str,
        default=None,
        help="Path to JSON file containing the query payload (required unless using --setup)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="CSV file path to save results (default: output/<payload_name>_results.csv)"
    )
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Interactive setup to configure API credentials"
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate the payload structure, don't execute the query"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed execution information"
    )
    
    args = parser.parse_args()
    
    # Handle setup mode
    if args.setup:
        try:
            from setup import setup_credentials_interactive
            setup_credentials_interactive()
            return 0
        except ImportError:
            print_error("Setup script not found. Please create .env file manually.")
            print_info("See visier.env.example for the required format")
            return 1
    
    # Require payload file
    if not args.payload:
        print_error("Payload file is required. Use --payload <file> to specify a JSON payload file.")
        print_info("Example: python query.py --payload examples/query_payload_examples.json")
        parser.print_help()
        return 1
    
    # Check if payload file exists
    payload_path = Path(args.payload)
    if not payload_path.is_absolute():
        # Make relative to aggregate directory
        aggregate_dir = Path(__file__).parent
        payload_path = aggregate_dir / payload_path
    
    if not payload_path.exists():
        print_error(f"Payload file not found: {payload_path}")
        print_info("Please check the file path and try again")
        return 1
    
    # Load payload
    print_header("Loading Query Payload")
    try:
        payload = load_query_payload_from_json(str(payload_path))
        print_success(f"Payload loaded from: {payload_path}")
    except Exception as e:
        print_error(f"Failed to load payload file: {e}")
        return 1
    
    # Validate payload structure
    print_header("Validating Payload")
    is_valid, errors = validate_payload_structure(payload)
    if not is_valid:
        print_error("Payload validation failed:")
        for error in errors:
            print(f"  • {error}")
        print_info("\nPlease check your payload file structure.")
        print_info("See examples/query_payload_examples.json for a valid format")
        return 1
    print_success("Payload structure is valid")
    
    # If validate-only, stop here
    if args.validate_only:
        print_header("Validation Complete")
        print_success("Payload is valid and ready to use")
        return 0
    
    # Check credentials
    print_header("Checking Credentials")
    if not validate_credentials():
        return 1
    print_success("Credentials configured")
    
    # Execute query
    print_header("Executing Query")
    if args.verbose:
        print_info("Sending request to Visier API...")
        source = payload.get("query", {}).get("source", {})
        metric_id = source.get("metric") or (source.get("metrics", {}).get("columns") or [{}])[0].get("id", "unknown")
        print_info(f"Metric: {metric_id}")
        axes_count = len(payload.get("query", {}).get("axes", []))
        print_info(f"Dimensions: {axes_count}")
    
    try:
        response = execute_vanilla_aggregate_query(payload=payload)
        print_success("Query executed successfully")
        
        if args.verbose:
            if "cells" in response:
                print_info(f"Cells returned: {len(response['cells'])}")
            if "axes" in response:
                print_info(f"Axes (dimensions): {len(response['axes'])}")
    
    except Exception as e:
        print_error(f"Query execution failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        print_info("\nTroubleshooting tips:")
        print_info("  • Check your credentials with --setup")
        print_info("  • Verify the metric ID exists in your tenant")
        print_info("  • Check dimension names and level IDs are correct")
        print_info("  • Use --verbose for more details")
        return 1
    
    # Convert to DataFrame
    print_header("Processing Results")
    try:
        source = payload.get("query", {}).get("source", {})
        metric_id = source.get("metric") or (source.get("metrics", {}).get("columns") or [{}])[0].get("id")
        df = convert_vanilla_response_to_dataframe(response, metric_id=metric_id)
        
        if df.empty:
            print_error("Query returned no data")
            print_info("\nPossible reasons:")
            print_info("  • No data matches the query criteria")
            print_info("  • Time period has no data")
            print_info("  • Filters exclude all data")
            return 1
        
        print_success(f"Converted to DataFrame: {len(df)} rows, {len(df.columns)} columns")
        
    except Exception as e:
        print_error(f"Failed to process results: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1
    
    # Save results
    print_header("Saving Results")
    if args.output:
        output_path = Path(args.output)
    else:
        # Default to output directory with filename based on payload
        aggregate_dir = Path(__file__).parent
        output_dir = aggregate_dir / "output"
        output_dir.mkdir(exist_ok=True)
        
        # Generate output filename from payload filename
        payload_name = payload_path.stem  # Get filename without extension
        output_filename = f"{payload_name}_results.csv"
        output_path = output_dir / output_filename
    
    try:
        df.to_csv(output_path, index=False)
        print_success(f"Results saved to: {output_path}")
    except Exception as e:
        print_error(f"Failed to save results: {e}")
        return 1
    
    # Display summary
    print_header("Query Summary")
    print(f"Rows: {len(df)}")
    print(f"Columns: {', '.join(df.columns)}")
    
    if "value" in df.columns:
        non_null = df["value"].notna().sum()
        if non_null > 0:
            print(f"\nValue Statistics:")
            print(f"  Non-null values: {non_null} / {len(df)}")
            print(f"  Min: {df['value'].min():.2f}")
            print(f"  Max: {df['value'].max():.2f}")
            print(f"  Sum: {df['value'].sum():.2f}")
            print(f"  Mean: {df['value'].mean():.2f}")
    
    print_header("✓ Query Completed Successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
