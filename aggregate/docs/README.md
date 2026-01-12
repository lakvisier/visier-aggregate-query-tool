# Aggregate Query Runner

Easy workflow for running and debugging Visier aggregate queries.

## Quick Start

```bash
# Run with default payload file
python aggregate/scripts/run_query.py

# Run with custom payload file
python aggregate/scripts/run_query.py --file aggregate/examples/query_payload_examples.json
```

## Workflow

### 1. Edit Your Query Payload

Edit `aggregate/examples/query_payload_examples.json` to define your query:

```json
{
  "payload": {
    "query": {
      "source": {"metric": "employeeCount"},
      "axes": [...],
      "filters": [...],
      "timeIntervals": {...}
    }
  }
}
```

### 2. Validate Before Running

```bash
# Check if payload is valid (doesn't execute query)
python aggregate/scripts/run_query.py --validate-only
```

### 3. Run with Debug Info

```bash
# See payload, config, and detailed execution steps
python aggregate/scripts/run_query.py --debug

# Or just verbose output
python aggregate/scripts/run_query.py --verbose
```

### 4. Save Results

```bash
# Auto-saves to output/query_results.csv by default
python aggregate/scripts/run_query.py

# Or specify custom output file
python aggregate/scripts/run_query.py --output my_results.csv
```

## Command Line Options

| Option | Short | Description |
|--------|-------|-------------|
| `--file` | `-f` | Path to JSON payload file (default: `aggregate/examples/query_payload_examples.json`) |
| `--output` | `-o` | CSV file path to save results |
| `--debug` | `-d` | Show payload, headers, and detailed execution info |
| `--verbose` | `-v` | Show detailed execution steps |
| `--save-payload` | | Save the loaded payload to a file (for inspection) |
| `--validate-only` | | Only validate payload structure, don't execute |
| `--no-save` | | Don't auto-save results to CSV |

## Examples

### Basic Usage

```bash
# Run query with default settings
python aggregate/scripts/run_query.py
```

### Debugging

```bash
# Full debug output
python aggregate/scripts/run_query.py --debug

# Validate payload structure
python aggregate/scripts/run_query.py --validate-only

# Save payload for inspection
python aggregate/scripts/run_query.py --save-payload my_payload.json
```

### Custom Files

```bash
# Use different payload file
python aggregate/scripts/run_query.py --file my_query.json

# Save to custom location
python aggregate/scripts/run_query.py --output /path/to/results.csv
```

## Discovering Dimension Levels

For parent-child hierarchies like `Organization_Hierarchy`, you need to discover the correct level IDs.

### Quick Discovery

```bash
# Discover levels for Organization_Hierarchy
python aggregate/scripts/discover_dimension_levels.py Organization_Hierarchy

# Get only level IDs (for scripting)
python aggregate/scripts/discover_dimension_levels.py Organization_Hierarchy --level-ids-only
```

The script will suggest common level IDs to try. For parent-child hierarchies, you may need to test each level ID with a query to find the correct one.

### Common Level IDs for Organization_Hierarchy

- `["Profit_Center"]` - Most common top level
- `["Business_Unit"]` - Second level
- `["Department"]` - Third level
- `["Level_1"]`, `["Level_2"]`, `["Level_3"]` - Generic levels
- `["Organization_Hierarchy"]` - Sometimes the dimension name itself

**Note:** Level IDs are tenant-specific. Always verify with a test query!

## Troubleshooting

### Payload Validation Errors

If you see validation errors, check:
- `query.source.metric` exists
- `query.axes` has at least one axis
- Each axis has `dimensionLevelSelection.dimension.name`
- Each axis has `dimensionLevelSelection.levelIds` (non-empty)

### API Errors

Common issues:
- **400 Bad Request**: Check dimension names and level IDs match your tenant
- **401 Unauthorized**: Check `.env` file has correct credentials
- **404 Not Found**: Check metric ID exists in your tenant

Use `--debug` to see the exact payload being sent.

### No Data Returned

If query succeeds but returns empty DataFrame:
- Check time period has data
- Verify filters aren't too restrictive
- Confirm metric ID is correct
- Check you have permissions for the data

## File Structure

```
aggregate/
├── aggregate_query_vanilla.py    # Core query functions
├── scripts/
│   ├── run_query.py              # CLI runner (this tool)
│   └── discover_dimension_levels.py  # Dimension level discovery
├── examples/
│   └── query_payload_examples.json   # Query payload definitions
├── docs/
│   ├── README.md                 # This file
│   └── LEARNINGS.md              # Query patterns and learnings
└── output/                       # Auto-saved results
    └── query_results.csv
```

## Integration

You can also use the functions directly in Python:

```python
from aggregate.aggregate_query_vanilla import (
    execute_vanilla_aggregate_query,
    convert_vanilla_response_to_dataframe,
    load_query_payload_from_json
)

# Load and execute
payload = load_query_payload_from_json("aggregate/examples/query_payload_examples.json")
response = execute_vanilla_aggregate_query(payload=payload)
df = convert_vanilla_response_to_dataframe(response)
```
