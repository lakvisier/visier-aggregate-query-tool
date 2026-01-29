# Visier Aggregate Query Reference

Quick reference for the Visier Aggregate Query API. For getting started, see `README.md`. For advanced patterns (event metrics, ranged dimensions), see `WORKING_NOTES.md`.

---

## Commands

```bash
# Setup credentials (first time)
python query.py --setup

# Validate payload (no execution)
python query.py --payload my_query.json --validate-only

# Run query
python query.py --payload my_query.json

# Run with verbose output
python query.py --payload my_query.json --verbose

# Custom output file
python query.py --payload my_query.json --output results.csv

# Multi-metric (different filters per metric)
python run_multi_metric.py --config examples/query_multi_metric_config.json
```

---

## API Endpoint

```
POST /v1/data/query/aggregate
```

### Headers

| Header | Required | Description |
|--------|----------|-------------|
| `Content-Type` | Yes | `application/json` |
| `apikey` | Yes | Your API key |
| `Accept` | No | `application/json` (default), `text/csv`, `application/jsonlines` |
| `TargetTenantID` | No | Target tenant (if different from auth tenant) |

---

## Request Body Structure

```json
{
  "query": {
    "source": { "metric": "employeeCount" },
    "axes": [ ... ],
    "filters": [ ... ],
    "timeIntervals": { ... }
  },
  "options": { ... }
}
```

**Required:** `source`, `axes` (at least one), `timeIntervals`

---

## Source

```json
"source": { "metric": "employeeCount" }
```

Or for formulas:
```json
"source": { "formula": "count(Employee)" }
```

Common metrics: `employeeCount`, `headcount`, `turnover`, `terminationCount`, `resignationRate`

---

## Axes (Dimensions)

### dimensionLevelSelection (most common)

For levelled dimensions (Country, Function, Organization):

```json
{
  "dimensionLevelSelection": {
    "dimension": { "name": "Country_Cost", "qualifyingPath": "Employee" },
    "levelIds": ["Country"]
  }
}
```

### dimensionLeafMemberSelection

For ranged dimensions or all leaf members (e.g., tenure bands):

```json
{
  "dimensionLeafMemberSelection": {
    "dimension": { "name": "Employe_Tenure_Year", "qualifyingPath": "Employee" }
  }
}
```

### Common Dimensions

| Dimension | Level IDs | Use Case |
|-----------|-----------|----------|
| `Country_Cost` | `["Country"]` | Geographic breakdown |
| `Organization_Hierarchy` | `["Level_2"]`, `["Profit_Center"]` | Org structure |
| `Function` | `["Function"]` | Job functions |
| `Location` | `["Location_0"]` | Office locations |
| `Employment_Type` | `["Employment_Type"]` | Full-time, Part-time |

**Note:** For event-based metrics (resignationRate, terminationCount), use `qualifyingPath: "Employee_Exit.Employee"`. See `WORKING_NOTES.md`.

---

## Filters

Filter by dimension members:

```json
"filters": [{
  "memberSet": {
    "dimension": { "name": "Employment_Type", "qualifyingPath": "Employee" },
    "values": { "included": [{ "path": ["Full-time shifts"] }] }
  }
}]
```

Multiple values:
```json
"values": {
  "included": [
    { "path": ["United States"] },
    { "path": ["Canada"] }
  ]
}
```

---

## Time Intervals

### Year-end snapshots (2021-2025)
```json
{
  "fromDateTime": "2026-01-01",
  "intervalPeriodType": "YEAR",
  "intervalCount": 5,
  "direction": "BACKWARD"
}
```

### Monthly (last 12 months)
```json
{
  "fromDateTime": "2026-01-01",
  "intervalPeriodType": "MONTH",
  "intervalCount": 12,
  "direction": "BACKWARD"
}
```

### Single point-in-time
```json
{
  "fromDateTime": "2025-01-01",
  "intervalPeriodType": "DAY",
  "intervalCount": 1,
  "direction": "BACKWARD"
}
```

**Period types:** `YEAR`, `MONTH`, `WEEK`, `DAY`

---

## Options

```json
"options": {
  "calendarType": "TENANT_CALENDAR",
  "zeroVisibility": "ELIMINATE",
  "nullVisibility": "ELIMINATE",
  "internal": { "alignTimeAxisToPeriodEnd": true }
}
```

| Option | Values | Default | Description |
|--------|--------|---------|-------------|
| `calendarType` | `TENANT_CALENDAR`, `GREGORIAN_CALENDAR` | `TENANT_CALENDAR` | Calendar for time calculations |
| `zeroVisibility` | `SHOW`, `HIDE`, `ELIMINATE` | `SHOW` | How to handle zeros |
| `nullVisibility` | `SHOW`, `HIDE`, `ELIMINATE` | `SHOW` | How to handle nulls |
| `memberDisplayMode` | `DEFAULT`, `COMPACT`, `DISPLAY` | `DEFAULT` | Member value format |
| `internal.alignTimeAxisToPeriodEnd` | `true`, `false` | `false` | Align to period end (match Visier UI) |

---

## Response

### Success (200)

JSON with `cells`, `axes`, `measures`. Each cell contains dimension coordinates and the metric value.

### Errors

| Code | Meaning |
|------|---------|
| 400 | Invalid payload (bad metric/dimension name, missing fields) |
| 401 | Unauthorized (bad credentials) |
| 404 | Metric/dimension not found |

---

## Troubleshooting

| Error | Fix |
|-------|-----|
| "Credentials not configured" | Run `python query.py --setup` |
| "Payload validation failed" | Check JSON syntax, ensure required fields |
| "Query returned no data" | Check time period, verify metric exists |
| "API 400 error" | Verify metric/dimension names are correct |
| "API 401 error" | Re-run setup, check credentials |
| "must be defined on [Employee_Exit]" | Use `qualifyingPath: "Employee_Exit.Employee"` for event metrics |

---

## Complete Example

```json
{
  "query": {
    "source": { "metric": "employeeCount" },
    "axes": [{
      "dimensionLevelSelection": {
        "dimension": { "name": "Country_Cost", "qualifyingPath": "Employee" },
        "levelIds": ["Country"]
      }
    }],
    "filters": [{
      "memberSet": {
        "dimension": { "name": "Employment_Type", "qualifyingPath": "Employee" },
        "values": { "included": [{ "path": ["Full-time shifts"] }] }
      }
    }],
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
```

---

## Related Resources

- `README.md` — Getting started, installation, usage
- `WORKING_NOTES.md` — Advanced patterns (event metrics, ranged dimensions, Postman)
- `openapi.json` — Full OpenAPI 3.0 specification
- `examples/` — Working payload examples
