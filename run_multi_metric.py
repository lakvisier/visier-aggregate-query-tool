#!/usr/bin/env python3
"""
Run multiple aggregate queries (same axes and time, different filters per metric)
and merge results into one CSV with a 'metric' column.

The Visier API applies one filters array per request, so "each metric filtered
differently" requires one query per metric; this script runs them and merges.

Usage:
    uv run python run_multi_metric.py --config examples/query_multi_metric_config.json
    uv run python run_multi_metric.py --config examples/query_multi_metric_config.json --output output/multi_metric_results.csv
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root for imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

from client import (
    execute_vanilla_aggregate_query,
    convert_vanilla_response_to_dataframe,
    get_api_config,
)
from query import validate_credentials


def load_config(config_path: Path) -> dict:
    with open(config_path, "r") as f:
        return json.load(f)


def build_payload(shared: dict, metric: str, filters: list) -> dict:
    """Build full payload for one metric + its filters."""
    return {
        "query": {
            "source": {"metric": metric},
            "axes": shared["axes"],
            "filters": filters,
            "timeIntervals": shared["timeIntervals"],
        },
        "options": shared.get("options", {}),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Run multiple metrics (different filters each) and merge to one CSV"
    )
    parser.add_argument(
        "--config", "-c",
        type=Path,
        default=Path(__file__).parent / "examples" / "query_multi_metric_config.json",
        help="Path to multi-metric config JSON",
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=None,
        help="Output CSV path (default: output/multi_metric_results.csv)",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    config_path = args.config
    if not config_path.is_absolute():
        config_path = Path(__file__).resolve().parent / config_path
    if not config_path.exists():
        print(f"Error: Config file not found: {config_path}")
        sys.exit(1)

    if not validate_credentials():
        print("Error: Credentials not configured. Run: python query.py --setup")
        sys.exit(1)

    config = load_config(config_path)
    shared = config["shared"]
    metrics = config["metrics"]

    if not metrics:
        print("Error: No metrics defined in config")
        sys.exit(1)

    dataframes = []
    for i, entry in enumerate(metrics):
        metric_id = entry["metric"]
        filters = entry.get("filters", [])
        if args.verbose:
            print(f"Query {i + 1}/{len(metrics)}: {metric_id} (filters: {len(filters)})")
        payload = build_payload(shared, metric_id, filters)
        try:
            response = execute_vanilla_aggregate_query(payload=payload)
            df = convert_vanilla_response_to_dataframe(response, metric_id=metric_id)
            if df.empty:
                if args.verbose:
                    print(f"  No data for {metric_id}")
                continue
            # Label: use optional "label" from config for display, else metric id
            metric_label = entry.get("label", metric_id)
            df.insert(0, "metric_id", metric_id)
            df.insert(0, "metric", metric_label)
            dataframes.append(df)
        except Exception as e:
            print(f"Error querying {metric_id}: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            sys.exit(1)

    if not dataframes:
        print("Error: No data returned from any query")
        sys.exit(1)

    import pandas as pd
    merged = pd.concat(dataframes, ignore_index=True)

    out_path = args.output
    if out_path is None:
        out_path = Path(__file__).resolve().parent / "output" / "multi_metric_results.csv"
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(out_path, index=False)
    print(f"Merged {len(merged)} rows from {len(dataframes)} metric(s) -> {out_path}")


if __name__ == "__main__":
    main()
