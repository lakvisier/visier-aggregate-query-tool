# Visier Aggregate Query API Reference

This document provides a reference guide based on the official Visier OpenAPI specification for the Aggregate Query API.

## Endpoint

```
POST /v1/data/query/aggregate
```

**Description**: To retrieve aggregated values from your data in Visier, you can perform an aggregation. Usually, an aggregation retrieves values over a period of time, such as multiple months. You can also group and filter your data in an aggregation query to retrieve detailed information.

## Request Structure

### Headers

- `Content-Type`: `application/json` (required)
- `Accept`: `application/json`, `application/jsonlines`, or `text/csv` (optional)
- `apikey`: Your API key (required)
- `TargetTenantID`: Optional tenant ID (if omitted, uses administrating tenant)

### Authentication

Authentication is done via:
- **API Key**: Passed in the `apikey` header
- **ASID Token**: Passed as a cookie `VisierASIDToken` (obtained via username/password)

### Request Body Schema

```json
{
  "query": {
    "source": {
      "metric": "string" | "formula": "string" | "metrics": {...}
    },
    "axes": [...],
    "filters": [...],
    "timeIntervals": {...},
    "parameterValues": [...]
  },
  "options": {...}
}
```

## Query Components

### 1. Source (`query.source`)

Defines what metric or formula to query.

**Options:**
- `metric`: The ID of an existing metric (e.g., `"employeeCount"`)
- `formula`: An ad-hoc metric formula
- `metrics`: Multiple metrics (only available with CSV response format)

**Example:**
```json
{
  "source": {
    "metric": "employeeCount"
  }
}
```

### 2. Axes (`query.axes`)

Defines how to group the data. **At least one axis is required for aggregate queries.**

Each axis is a `QueryAxisDTO` with:
- `dimensionLevelSelection`: Dimension and level IDs
- `dimension`: Dimension name and qualifying path
- `levelIds`: Array of level IDs to use

**Example:**
```json
{
  "axes": [
    {
      "dimensionLevelSelection": {
        "dimension": {
          "name": "Country_Cost",
          "qualifyingPath": "Employee"
        },
        "levelIds": ["Country"]
      }
    }
  ]
}
```

**Note**: For parent-child hierarchies (like `Organization_Hierarchy`), you MUST use tenant-specific level IDs. The dimension name itself won't work.

### 3. Filters (`query.filters`)

Optional constraints to restrict the data. Omit if no filtering is required.

**Filter Types:**
- `memberSet`: Filter by dimension members
- `selectionConcept`: Filter by boolean concepts (e.g., `isManager`)

**Example:**
```json
{
  "filters": [
    {
      "memberSet": {
        "dimension": {
          "name": "Employment_Type",
          "qualifyingPath": "Employee"
        },
        "values": {
          "included": [
            {"path": ["Full-time shifts"]}
          ]
        }
      }
    }
  ]
}
```

### 4. Time Intervals (`query.timeIntervals`)

**Required** for aggregate queries. Defines the time period to query.

**Properties:**
- `fromDateTime`: Start date (format: `"YYYY-MM-DD"`)
- `fromInstant`: Start instant (milliseconds since epoch as string)
- `dynamicDateFrom`: Dynamic date source (e.g., `"SOURCE"`)
- `intervalPeriodType`: `YEAR`, `MONTH`, `DAY`, etc.
- `intervalCount`: Number of periods
- `intervalPeriodCount`: Alternative to `intervalCount`
- `direction`: `BACKWARD` or `FORWARD`

**Example:**
```json
{
  "timeIntervals": {
    "fromDateTime": "2026-01-01",
    "intervalPeriodType": "YEAR",
    "intervalCount": 5,
    "direction": "BACKWARD"
  }
}
```

### 5. Parameter Values (`query.parameterValues`)

Optional values for parameterized metrics (e.g., Visier Benchmarks metrics).

### 6. Options (`options`)

Additional instructions for query execution.

**Key Options:**

| Option | Type | Values | Description |
|--------|------|--------|-------------|
| `calendarType` | enum | `TENANT_CALENDAR`, `GREGORIAN_CALENDAR` | Calendar type for time calculations (default: `TENANT_CALENDAR`) |
| `zeroVisibility` | enum | `SHOW`, `HIDE`, `ELIMINATE` | Show/hide zeros (default: `SHOW`) |
| `nullVisibility` | enum | `SHOW`, `HIDE`, `ELIMINATE` | Show/hide nulls (default: `SHOW`) |
| `axisVisibility` | enum | `SIMPLE`, `VERBOSE` | Amount of axis information (default: `SIMPLE`) |
| `memberDisplayMode` | enum | `DEFAULT`, `COMPACT`, `DISPLAY`, `MDX`, `COMPACT_DISPLAY` | How member values are displayed (default: `DEFAULT`) |
| `axesOverallValueMode` | enum | `NONE`, `AGGREGATE`, `OVERALL` | Type of overall values to return (default: `NONE`) |
| `enableSparseResults` | boolean | `true`, `false` | Retrieve only non-zero/non-null cells |
| `internal.alignTimeAxisToPeriodEnd` | boolean | `true`, `false` | Align timestamps to period end |

**Example:**
```json
{
  "options": {
    "calendarType": "TENANT_CALENDAR",
    "zeroVisibility": "ELIMINATE",
    "nullVisibility": "ELIMINATE",
    "internal": {
      "alignTimeAxisToPeriodEnd": true
    }
  }
}
```

## Response Structure

### Success Response (200)

Returns a `CellSetDTO` containing:
- `cells`: Array of data cells (each cell has dimension values and metric value)
- `axes`: Array of axis information
- `measures`: Array of measure information

**Response Formats:**
- `application/json`: JSON format (default)
- `application/jsonlines`: JSON Lines format
- `text/csv`: CSV format

### Error Response

Returns a `Status` object with error details.

**Common HTTP Status Codes:**
- `200`: Success
- `400`: Bad Request (invalid payload, missing required fields)
- `401`: Unauthorized (invalid credentials)
- `404`: Not Found (metric/dimension doesn't exist)
- `500`: Internal Server Error

## Complete Example

```json
{
  "query": {
    "source": {
      "metric": "employeeCount"
    },
    "axes": [
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
    "filters": [
      {
        "memberSet": {
          "dimension": {
            "name": "Employment_Type",
            "qualifyingPath": "Employee"
          },
          "values": {
            "included": [
              {"path": ["Full-time shifts"]}
            ]
          }
        }
      }
    ],
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
    "nullVisibility": "ELIMINATE",
    "internal": {
      "alignTimeAxisToPeriodEnd": true
    }
  }
}
```

## Important Notes

1. **Axes are Required**: Aggregate queries must have at least one axis (dimension).

2. **Time Intervals are Required**: All aggregate queries must specify `timeIntervals`.

3. **Level IDs for Parent-Child Hierarchies**: For dimensions like `Organization_Hierarchy`, you MUST use tenant-specific level IDs (e.g., `["Level_1"]`, `["Level_2"]`). The dimension name itself won't work.

4. **Metric Names**: Metric IDs are tenant-specific. Contact your Visier administrator or use the Data Model API to discover available metrics.

5. **Member Paths**: Filter member paths must match exact values in your tenant (case-sensitive).

6. **Year-End Snapshots**: For year-end data, use the start of the NEXT year with `BACKWARD` direction. Example: `"2026-01-01"` with 5 years `BACKWARD` returns 2021-2025 year-end snapshots.

## Related Endpoints

- `POST /v1/data/query/list` - List query (detailed records, not aggregated)
- `POST /v1/data/query/snapshot` - Snapshot query (time series of list queries)
- `POST /v1/data/query/sql` - SQL-like query syntax

## Full API Documentation

For complete API documentation, see `openapi.json` in this repository. This file contains the full OpenAPI 3.0 specification with all endpoints, schemas, and examples.

## Resources

- **OpenAPI Spec**: `openapi.json` - Full API specification
- **Examples**: `examples/` - Working query examples
- **Template**: `examples/query_payload_template.json` - Template with comments
- **Quick Reference**: `QUICK_REFERENCE.md` - Quick reference guide
- **Tutorial**: `examples/org_hierarchy_query.ipynb` - Jupyter notebook tutorial
