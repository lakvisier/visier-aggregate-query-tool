# Client Walkthrough: Using the Visier Aggregate Query Tool

This guide will walk you through setting up and using the Visier Aggregate Query tool step by step.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [Understanding Query Payloads](#understanding-query-payloads)
4. [Running Your First Query](#running-your-first-query)
5. [Customizing Queries](#customizing-queries)
6. [Understanding Results](#understanding-results)
7. [Common Patterns](#common-patterns)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before you begin, make sure you have:

- **Python 3.9+** installed
- **API Credentials** from your Visier administrator:
  - API Host URL (e.g., `https://your-tenant.api.visier.io`)
  - API Key
  - Vanity name
  - Username and Password
- **Access to the API Schema** (URL provided by your administrator) to discover available metrics and dimensions

---

## Initial Setup

### Step 1: Install Dependencies

If you haven't already, install the required Python packages:

```bash
pip install -r requirements.txt
```

Or using `uv` (if available):

```bash
uv pip install -r requirements.txt
```

### Step 2: Configure Credentials

You have two options for setting up credentials:

#### Option A: Interactive Setup (Recommended)

Run the interactive setup script:

```bash
python aggregate/run_aggregate_query.py --setup
```

This will guide you through entering your credentials and create a `.env` file automatically.

#### Option B: Manual Setup

1. Copy the example environment file:
   ```bash
   cp visier.env.example .env
   ```

2. Edit `.env` and fill in your credentials:
   ```
   VISIER_HOST=https://your-tenant.api.visier.io
   VISIER_APIKEY=your-api-key
   VISIER_VANITY=your-vanity
   VISIER_USERNAME=your-username
   VISIER_PASSWORD=your-password
   ```

**Important:** Never commit the `.env` file to version control. It contains sensitive credentials.

### Step 3: Verify Setup

Test your credentials by running the walkthrough:

```bash
python aggregate/walkthrough.py
```

This interactive guide will help you verify everything is set up correctly.

---

## Understanding Query Payloads

A query payload is a JSON file that defines what data you want to retrieve from Visier. It specifies:

- **Metric**: What you're measuring (e.g., `employeeCount`, `headcount`, `turnover`)
- **Dimensions (Axes)**: How to group the data (e.g., by Country, Function, Organization)
- **Filters**: Optional constraints (e.g., only Full-time employees, only Managers)
- **Time Period**: What time range to query

### Basic Payload Structure

```json
{
  "payload": {
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
      "timeIntervals": {
        "fromDateTime": "2025-01-01",
        "intervalPeriodType": "YEAR",
        "intervalCount": 5,
        "direction": "BACKWARD"
      }
    },
    "options": {
      "zeroVisibility": "ELIMINATE",
      "nullVisibility": "ELIMINATE"
    }
  }
}
```

### Key Components Explained

#### 1. Source (Metric)

The `source.metric` field specifies which metric to query. Common metrics include:
- `employeeCount` - Number of employees
- `headcount` - Headcount metric
- `turnover` - Turnover rate

**Note:** Available metrics depend on your tenant. Check your API schema documentation.

#### 2. Axes (Dimensions)

Axes define how to group your data. Each axis is a dimension like:
- `Country_Cost` - Geographic location
- `Function` - Job function
- `Organization_Hierarchy` - Organizational structure
- `Location` - Physical location

**Important:** For parent-child hierarchies (like `Organization_Hierarchy`), you need to specify the correct `levelIds`. These are tenant-specific. Use the discovery script or check your API schema.

#### 3. Filters (Optional)

Filters let you narrow down the data:
- **Member Set Filters**: Filter by specific dimension members (e.g., only certain countries)
- **Selection Concept Filters**: Filter by boolean concepts (e.g., `isManager`, `isActive`)

#### 4. Time Intervals

Time intervals define the time period:
- `fromDateTime`: Start date (e.g., `"2025-01-01"`)
- `intervalPeriodType`: Period type (`YEAR`, `MONTH`, `QUARTER`, `DAY`)
- `intervalCount`: Number of periods
- `direction`: `FORWARD` or `BACKWARD` from the start date

---

## Running Your First Query

### Step 1: Use an Example Payload

Start with the provided example:

```bash
python aggregate/run_aggregate_query.py --payload examples/query_payload_examples.json
```

This will:
1. Load the payload file
2. Validate the structure
3. Execute the query
4. Save results to `output/query_results.csv`

### Step 2: Validate Before Running

To check if your payload is valid without executing:

```bash
python aggregate/run_aggregate_query.py --payload examples/query_payload_examples.json --validate-only
```

### Step 3: View Results

Results are automatically saved to `output/query_results.csv`. Open this file in Excel, a text editor, or use Python/pandas to analyze it.

---

## Customizing Queries

### Changing the Metric

Edit the `source.metric` field:

```json
"source": {
  "metric": "headcount"  // Changed from employeeCount
}
```

### Adding Dimensions

Add more axes to group by multiple dimensions:

```json
"axes": [
  {
    "dimensionLevelSelection": {
      "dimension": {
        "name": "Country_Cost",
        "qualifyingPath": "Employee"
      },
      "levelIds": ["Country"]
    }
  },
  {
    "dimensionLevelSelection": {
      "dimension": {
        "name": "Function",
        "qualifyingPath": "Employee"
      },
      "levelIds": ["Function"]
    }
  }
]
```

This will group data by both Country and Function.

### Adding Filters

#### Filter by Dimension Members

```json
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
```

#### Filter by Selection Concept

```json
"filters": [
  {
    "selectionConcept": {
      "name": "isManager",
      "qualifyingPath": "Employee"
    }
  }
]
```

### Changing Time Period

For year-end snapshots (2020-2024):

```json
"timeIntervals": {
  "fromDateTime": "2025-01-01",
  "intervalPeriodType": "YEAR",
  "intervalCount": 5,
  "direction": "BACKWARD"
}
```

For monthly data (last 12 months):

```json
"timeIntervals": {
  "fromDateTime": "2025-01-01",
  "intervalPeriodType": "MONTH",
  "intervalCount": 12,
  "direction": "BACKWARD"
}
```

---

## Understanding Results

### Output Format

Results are saved as CSV files with:
- **Dimension columns**: One column per dimension in your axes
- **Value column**: The metric value for that combination
- **Support column** (optional): Sample size or support count

### Example Output

```
Country,Function,value
United States,Engineering,500
United States,Sales,300
Canada,Engineering,100
Canada,Sales,50
```

### Interpreting Results

- Each row represents a unique combination of dimension values
- The `value` column contains the metric value for that combination
- Empty or zero values are typically excluded (due to `zeroVisibility: "ELIMINATE"`)

---

## Common Patterns

### Pattern 1: Employee Count by Country

```json
{
  "payload": {
    "query": {
      "source": {"metric": "employeeCount"},
      "axes": [{
        "dimensionLevelSelection": {
          "dimension": {
            "name": "Country_Cost",
            "qualifyingPath": "Employee"
          },
          "levelIds": ["Country"]
        }
      }],
      "timeIntervals": {
        "fromDateTime": "2025-01-01",
        "intervalPeriodType": "YEAR",
        "intervalCount": 1,
        "direction": "BACKWARD"
      }
    }
  }
}
```

### Pattern 2: Headcount by Organization and Function

```json
{
  "payload": {
    "query": {
      "source": {"metric": "headcount"},
      "axes": [
        {
          "dimensionLevelSelection": {
            "dimension": {
              "name": "Organization_Hierarchy",
              "qualifyingPath": "Employee"
            },
            "levelIds": ["Level_2"]
          }
        },
        {
          "dimensionLevelSelection": {
            "dimension": {
              "name": "Function",
              "qualifyingPath": "Employee"
            },
            "levelIds": ["Function"]
          }
        }
      ],
      "timeIntervals": {
        "fromDateTime": "2025-01-01",
        "intervalPeriodType": "YEAR",
        "intervalCount": 1,
        "direction": "BACKWARD"
      }
    }
  }
}
```

### Pattern 3: Managers Only, by Location

```json
{
  "payload": {
    "query": {
      "source": {"metric": "employeeCount"},
      "axes": [{
        "dimensionLevelSelection": {
          "dimension": {
            "name": "Location",
            "qualifyingPath": "Employee"
          },
          "levelIds": ["Location_0"]
        }
      }],
      "filters": [{
        "selectionConcept": {
          "name": "isManager",
          "qualifyingPath": "Employee"
        }
      }],
      "timeIntervals": {
        "fromDateTime": "2025-01-01",
        "intervalPeriodType": "YEAR",
        "intervalCount": 1,
        "direction": "BACKWARD"
      }
    }
  }
}
```

---

## Troubleshooting

### Issue: "Missing required environment variables"

**Solution:** Run the setup script:
```bash
python aggregate/run_aggregate_query.py --setup
```

### Issue: "Payload validation failed"

**Common causes:**
- Missing `query` key
- Missing `source.metric`
- Empty or missing `axes`
- Invalid axis structure

**Solution:** 
1. Use `--validate-only` to see specific errors
2. Compare your payload with `examples/query_payload_examples.json`
3. Check the API schema for correct dimension names and level IDs

### Issue: "API Error 400: Bad Request"

**Common causes:**
- Invalid metric ID
- Invalid dimension name
- Invalid level IDs (especially for parent-child hierarchies)
- Invalid time interval format

**Solution:**
1. Verify metric ID exists in your tenant
2. Check dimension names match your tenant's schema
3. For parent-child hierarchies, use the discovery script:
   ```bash
   python aggregate/scripts/discover_dimension_levels.py Organization_Hierarchy
   ```

### Issue: "API Error 401: Unauthorized"

**Solution:**
1. Verify credentials in `.env` file
2. Re-run setup: `python aggregate/run_aggregate_query.py --setup`
3. Check with your administrator that credentials are still valid

### Issue: "Query returned no data"

**Possible reasons:**
- Time period has no data
- Filters exclude all data
- Metric doesn't exist for the selected dimensions
- Insufficient permissions

**Solution:**
1. Try a broader time period
2. Remove filters to see if data exists
3. Verify you have permissions for the data
4. Check if the metric exists in your tenant

### Issue: "Invalid levelIds for Organization_Hierarchy"

**Solution:**
Parent-child hierarchies require tenant-specific level IDs. Try:
1. Use the discovery script
2. Try common patterns: `["Level_1"]`, `["Level_2"]`, `["Profit_Center"]`, `["Business_Unit"]`
3. Check your API schema documentation

---

## Getting Help

- **Documentation**: See `QUICK_START.md` for quick reference
- **Examples**: Check `examples/` directory for more examples
- **API Schema**: Use the URL provided by your administrator to discover available metrics and dimensions
- **Validation**: Always use `--validate-only` before running queries to catch errors early

---

## Quick Command Reference

```bash
# Setup credentials
python aggregate/run_aggregate_query.py --setup

# Run interactive walkthrough
python aggregate/walkthrough.py

# Run a query
python aggregate/run_aggregate_query.py --payload examples/query_payload_examples.json

# Validate payload
python aggregate/run_aggregate_query.py --payload my_query.json --validate-only

# Run with verbose output
python aggregate/run_aggregate_query.py --payload my_query.json --verbose

# Custom output file
python aggregate/run_aggregate_query.py --payload my_query.json --output results.csv
```

---

**Happy Querying!** 🎉
