# Quick Reference Guide

## Common Commands

```bash
# Setup (first time only)
python query.py --setup

# Validate a payload
python query.py --payload my_query.json --validate-only

# Run a query
python query.py --payload my_query.json

# Run with verbose output
python query.py --payload my_query.json --verbose

# Save to custom file
python query.py --payload my_query.json --output results.csv
```

## Payload Structure (Minimal)

```json
{
  "payload": {
    "query": {
      "source": {"metric": "employeeCount"},
      "axes": [{
        "dimensionLevelSelection": {
          "dimension": {"name": "Country_Cost", "qualifyingPath": "Employee"},
          "levelIds": ["Country"]
        }
      }],
      "timeIntervals": {
        "fromDateTime": "2026-01-01",
        "intervalPeriodType": "YEAR",
        "intervalCount": 5,
        "direction": "BACKWARD"
      }
    }
  }
}
```

## Common Metrics

- `employeeCount` - Employee count
- `headcount` - Headcount
- `turnover` - Turnover rate
- `terminationCount` - Number of terminations

## Common Dimensions

| Dimension | Common Level IDs | Use Case |
|-----------|----------------|----------|
| `Country_Cost` | `["Country"]` | Geographic breakdown |
| `Organization_Hierarchy` | `["Level_2"]`, `["Profit_Center"]` | Organizational structure |
| `Function` | `["Function"]` | Job functions |
| `Location` | `["Location_0"]` | Office locations |
| `Employment_Type` | `["Employment_Type"]` | Full-time, Part-time, etc. |

## Time Interval Patterns

### Year-end Snapshots (2021-2025)
```json
{
  "fromDateTime": "2026-01-01",
  "intervalPeriodType": "YEAR",
  "intervalCount": 5,
  "direction": "BACKWARD"
}
```

### Point-in-Time (Single Date)
```json
{
  "fromDateTime": "2025-01-01",
  "intervalPeriodType": "DAY",
  "intervalCount": 1,
  "direction": "BACKWARD"
}
```

### Monthly Data (Last 12 Months)
```json
{
  "fromDateTime": "2025-12-01",
  "intervalPeriodType": "MONTH",
  "intervalCount": 12,
  "direction": "BACKWARD"
}
```

## Common Filters

### Filter by Employment Type
```json
{
  "filters": [{
    "memberSet": {
      "dimension": {"name": "Employment_Type", "qualifyingPath": "Employee"},
      "values": {"included": [{"path": ["Full-time shifts"]}]}
    }
  }]
}
```

### Filter by Multiple Values
```json
{
  "filters": [{
    "memberSet": {
      "dimension": {"name": "Country_Cost", "qualifyingPath": "Employee"},
      "values": {
        "included": [
          {"path": ["United States"]},
          {"path": ["Canada"]}
        ]
      }
    }
  }]
}
```

## Troubleshooting Quick Fixes

| Error | Quick Fix |
|-------|-----------|
| "Credentials not configured" | Run `python query.py --setup` |
| "Payload validation failed" | Check JSON syntax, ensure required fields exist |
| "Query returned no data" | Check time period, verify metric exists |
| "API 400 error" | Verify metric/dimension names are correct |
| "API 401 error" | Re-run setup, check credentials |

## Output Files

- Default: `output/<payload_name>_results.csv`
- Custom: Use `--output` flag
- Each query creates a unique file (no overwriting)

## Next Steps

1. Start with `examples/query_payload_template.json`
2. Modify for your needs
3. Validate with `--validate-only`
4. Execute and review results
5. Iterate and refine

## Full Documentation

- **API_REFERENCE.md** - Complete API reference based on official OpenAPI specification
- **openapi.json** - Full OpenAPI 3.0 specification for all Visier APIs
- **README.md** - Getting started guide and full documentation
- **examples/org_hierarchy_query.ipynb** - Interactive tutorial
