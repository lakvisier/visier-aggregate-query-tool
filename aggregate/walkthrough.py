#!/usr/bin/env python3
"""
Interactive Walkthrough for First-Time Users

This script provides a step-by-step guide for first-time users to:
1. Set up credentials
2. Understand the query payload structure
3. Run their first query
4. Understand the results

Usage:
    python aggregate/walkthrough.py
"""

import os
import sys
from pathlib import Path


def print_header(text: str, char: str = "="):
    """Print a formatted header."""
    width = 70
    print("\n" + char * width)
    print(f"  {text}")
    print(char * width)


def print_success(text: str):
    """Print success message."""
    print(f"✓ {text}")


def print_info(text: str):
    """Print info message."""
    print(f"ℹ {text}")


def print_step(number: int, text: str):
    """Print a step number."""
    print(f"\n[Step {number}] {text}")
    print("-" * 70)


def wait_for_user(prompt: str = "Press Enter to continue..."):
    """Wait for user to press Enter."""
    input(f"\n{prompt}")


def check_credentials() -> bool:
    """Check if credentials are configured."""
    try:
        # Add current directory to path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        from aggregate_query_vanilla import get_api_config
        config = get_api_config()
        required = ["host", "apikey", "vanity", "username", "password"]
        missing = [key for key in required if not config.get(key)]
        return len(missing) == 0
    except:
        return False


def run_walkthrough():
    """Main walkthrough function."""
    print_header("Welcome to Visier Aggregate Query Tool")
    
    print("This walkthrough will guide you through:")
    print("  1. Setting up your API credentials")
    print("  2. Understanding query payloads")
    print("  3. Running your first query")
    print("  4. Understanding the results")
    
    wait_for_user()
    
    # Step 1: Credentials
    print_step(1, "Setting Up Credentials")
    
    if check_credentials():
        print_success("Credentials are already configured!")
        print_info("You can skip this step or update your credentials if needed.")
        response = input("\nDo you want to update credentials? (yes/no) [no]: ").strip().lower()
        if response in ["yes", "y"]:
            try:
                # Add current directory to path
                current_dir = os.path.dirname(os.path.abspath(__file__))
                if current_dir not in sys.path:
                    sys.path.insert(0, current_dir)
                from setup_credentials import setup_credentials_interactive
                setup_credentials_interactive()
            except ImportError:
                print_info("Run: python aggregate/setup_credentials.py")
    else:
        print_info("Credentials are not configured yet.")
        print_info("You'll need:")
        print("  • Visier API Host URL")
        print("  • API Key")
        print("  • Vanity name")
        print("  • Username")
        print("  • Password")
        
        response = input("\nDo you want to set up credentials now? (yes/no) [yes]: ").strip().lower()
        if response not in ["no", "n"]:
            try:
                # Add current directory to path
                current_dir = os.path.dirname(os.path.abspath(__file__))
                if current_dir not in sys.path:
                    sys.path.insert(0, current_dir)
                from setup_credentials import setup_credentials_interactive
                setup_credentials_interactive()
            except ImportError:
                print_info("Run: python aggregate/setup_credentials.py")
                wait_for_user()
    
    # Step 2: Understanding Payloads
    print_step(2, "Understanding Query Payloads")
    
    print("A query payload is a JSON file that defines:")
    print("  • Which metric to query (e.g., employeeCount)")
    print("  • Which dimensions to group by (axes)")
    print("  • Any filters to apply")
    print("  • Time period to query")
    
    print("\nExample payload structure:")
    print("""
{
  "payload": {
    "query": {
      "source": {
        "metric": "employeeCount"    ← The metric you want
      },
      "axes": [                       ← Dimensions to group by
        {
          "dimensionLevelSelection": {
            "dimension": {
              "name": "Country_Cost",
              "qualifyingPath": "Employee"
            },
            "levelIds": ["Country"]
          }
        }
      ],
      "filters": [...],               ← Optional filters
      "timeIntervals": {...}          ← Time period
    }
  }
}
    """)
    
    print_info("See examples/query_payload_examples.json for a complete example")
    wait_for_user()
    
    # Step 3: Running a Query
    print_step(3, "Running Your First Query")
    
    aggregate_dir = Path(__file__).parent
    example_file = aggregate_dir / "examples" / "query_payload_examples.json"
    
    if example_file.exists():
        print_success(f"Found example file: {example_file}")
        print_info("This example queries employeeCount by Country_Cost")
        
        response = input("\nDo you want to run this example query? (yes/no) [yes]: ").strip().lower()
        if response not in ["no", "n"]:
            print("\nRunning query...")
            print("=" * 70)
            
            try:
                # Add current directory to path
                current_dir = os.path.dirname(os.path.abspath(__file__))
                if current_dir not in sys.path:
                    sys.path.insert(0, current_dir)
                
                # Import and run
                from run_aggregate_query import main as run_query_main
                import sys as sys_module
                
                # Temporarily set sys.argv for the run_query script
                original_argv = sys_module.argv
                sys_module.argv = [
                    "run_aggregate_query.py",
                    "--payload",
                    str(example_file)
                ]
                
                result = run_query_main()
                
                # Restore original argv
                sys_module.argv = original_argv
                
                if result == 0:
                    print_success("Query completed successfully!")
                else:
                    print_info("Query had some issues. Check the output above.")
                    
            except Exception as e:
                print(f"Error running query: {e}")
                print_info("You can run it manually with:")
                print(f"  python aggregate/run_aggregate_query.py --payload {example_file}")
        else:
            print_info("You can run queries manually with:")
            print("  python aggregate/run_aggregate_query.py --payload <your-payload.json>")
    else:
        print_info("Example file not found. You can create your own payload file.")
        print_info("See CLIENT_WALKTHROUGH.md for detailed instructions.")
    
    wait_for_user()
    
    # Step 4: Understanding Results
    print_step(4, "Understanding Query Results")
    
    print("Query results are saved as CSV files with:")
    print("  • One row per combination of dimension values")
    print("  • Columns for each dimension")
    print("  • A 'value' column with the metric value")
    print("  • Optional 'support' column (sample size)")
    
    print("\nExample output:")
    print("""
Country,value
United States,1500
Canada,200
United Kingdom,300
    """)
    
    print_info("Results are saved to: output/query_results.csv")
    print_info("You can open this file in Excel, Python, or any CSV viewer")
    
    wait_for_user()
    
    # Step 5: Next Steps
    print_step(5, "Next Steps")
    
    print("You're ready to start querying! Here's what to do next:")
    print()
    print("1. Customize your queries:")
    print("   • Edit examples/query_payload_examples.json")
    print("   • Change the metric, dimensions, filters, or time period")
    print()
    print("2. Create your own payload files:")
    print("   • Copy an example file")
    print("   • Modify it for your needs")
    print("   • Run: python aggregate/run_aggregate_query.py --payload <your-file.json>")
    print()
    print("3. Learn more:")
    print("   • Read CLIENT_WALKTHROUGH.md for detailed guide")
    print("   • Read QUICK_START.md for quick reference")
    print("   • Check examples/ directory for more examples")
    print()
    print("4. Get help:")
    print("   • Use --validate-only to check payloads before running")
    print("   • Use --verbose for detailed output")
    print("   • Check the API schema URL for available metrics and dimensions")
    
    print_header("Walkthrough Complete!", "=")
    print_success("You're all set to start querying Visier data!")
    print()
    print("Quick command reference:")
    print("  Setup:     python aggregate/run_aggregate_query.py --setup")
    print("  Run query: python aggregate/run_aggregate_query.py --payload <file.json>")
    print("  Validate:  python aggregate/run_aggregate_query.py --payload <file.json> --validate-only")


if __name__ == "__main__":
    try:
        run_walkthrough()
    except KeyboardInterrupt:
        print("\n\nWalkthrough cancelled by user.")
        sys.exit(1)
