# Visier Aggregate Query Tool

A simple, client-friendly tool to run Visier aggregate queries via REST API. Query employee metrics, organizational data, and more without needing the full Visier SDK.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Or using `uv`:
```bash
uv pip install -r requirements.txt
```

### 2. Setup Credentials

**Option A: Interactive setup**

```bash
python query.py --setup
```

**Option B: Manual setup**

```bash
cp .env.example .env
# Edit .env with your credentials
```

You'll need:
- **API Host URL** (e.g., `https://your-tenant.api.visier.io`)
- **API Key** (from your Visier administrator)
- **Vanity name** (your organization's vanity)
- **Username** and **Password**

The `.env` file is automatically ignored by git (never committed).

### 3. Run Your First Query

```bash
python query.py --payload examples/query_payload_examples.json
```

Results are saved to `output/query_payload_examples_results.csv`

## 📖 Usage

### Basic Commands

```bash
# Validate a payload without executing (great for testing)
python query.py --payload my_query.json --validate-only

# Run a query
python query.py --payload examples/query_payload_examples.json

# Save to a custom output file
python query.py --payload examples/query_payload_examples.json --output my_results.csv

# Show detailed execution info
python query.py --payload examples/query_payload_examples.json --verbose
```

### Understanding Query Payloads

A query payload is a JSON file that defines:
- **Metric**: What you're measuring (e.g., `employeeCount`, `headcount`, `turnover`)
- **Axes (Dimensions)**: How to group the data (e.g., by Country, Function, Organization)
- **Filters**: Optional constraints (e.g., only Full-time employees, only Managers)
- **Time Period**: What time range to query

**💡 Tip**: Start with `examples/query_payload_template.json` - it has extensive inline comments explaining every field. Copy it and remove the `_comment` fields before running.

## 📁 Project Structure

```
.
├── query.py                  # Main script - run single queries from JSON payloads
├── run_multi_metric.py       # Run multiple metrics (different filters) → one CSV
├── client.py                 # Visier API client (use programmatically)
├── setup.py                  # Interactive credential setup
├── .env.example              # Template for environment variables (copy to .env)
├── examples/                 # Example payload files
│   ├── query_payload_examples.json              # Basic example (Employee metrics)
│   ├── query_payload_examples_org_hierarchy.json # Organization hierarchy example
│   ├── query_payload_client.json                # Client example (event metrics, filters)
│   ├── query_multi_metric_config.json           # Multi-metric config example
│   ├── query_payload_template.json              # Template with extensive comments
│   └── example_usage.py                         # Programmatic usage examples
├── output/                   # Query results (CSV files)
├── QUICK_REFERENCE.md        # Quick reference guide
├── WORKING_NOTES.md          # Working notes (event metrics, ranged dimensions, Postman)
├── API_REFERENCE.md          # Complete API reference (based on OpenAPI spec)
└── openapi.json              # Official Visier API OpenAPI specification
```

## 🔄 Multi-Metric Queries

Run multiple metrics with **different filters** per metric and merge results into **one CSV**:

```bash
# Run with default config
python run_multi_metric.py --config examples/query_multi_metric_config.json

# Custom output path
python run_multi_metric.py --config examples/query_multi_metric_config.json --output output/my_results.csv
```

The config file (`examples/query_multi_metric_config.json`) defines:
- **shared**: axes, timeIntervals, options (same for all metrics)
- **metrics**: array of `{ "metric": "...", "label": "...", "filters": [...] }`

Each metric can have different filters. The output CSV has columns: `metric` (display label), `metric_id`, dimensions, `value`, `support`.

See `WORKING_NOTES.md` §9 for details.

## 💻 Programmatic Usage

You can also use the client directly in your Python code:

```python
from client import (
    execute_vanilla_aggregate_query,
    convert_vanilla_response_to_dataframe,
    create_dimension_axis
)

# Load a payload from JSON
from client import load_query_payload_from_json
payload = load_query_payload_from_json("examples/query_payload_examples.json")

# Execute the query
response = execute_vanilla_aggregate_query(payload=payload)

# Convert to pandas DataFrame
metric_id = payload["query"]["source"]["metric"]
df = convert_vanilla_response_to_dataframe(response, metric_id=metric_id)

# Work with the data
print(df.head())
```

## 🎯 Common Use Cases

### 1. Employee Count by Country
Use `Country_Cost` dimension with `Country` level:
```json
{
  "query": {
    "source": {"metric": "employeeCount"},
    "axes": [{
      "dimensionLevelSelection": {
        "dimension": {"name": "Country_Cost", "qualifyingPath": "Employee"},
        "levelIds": ["Country"]
      }
    }]
  }
}
```

### 2. Headcount by Organization
Use `Organization_Hierarchy` dimension (see `examples/query_payload_examples_org_hierarchy.json`)

### 3. Filtered Queries
Add filters to restrict data:
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

## 🔧 Troubleshooting

### "Credentials not configured"
Run `python query.py --setup` to configure your credentials.

### "Payload validation failed"
- Check that your JSON is valid (use a JSON validator)
- Ensure required fields are present: `query.source.metric`, `query.axes`
- See `examples/query_payload_template.json` for the correct structure

### "Query returned no data"
- Verify the metric exists in your tenant
- Check the time period has data
- Verify dimension names and level IDs are correct
- Check filters aren't excluding all data

### "API 400 error"
- Metric ID might not exist in your tenant
- Dimension names or level IDs might be incorrect
- Use `--verbose` to see the exact request being sent

### "API 401 error"
- Re-run `python query.py --setup` to update credentials
- Verify your API key and credentials are correct

### "SSL: CERTIFICATE_VERIFY_FAILED" or "self-signed certificate in certificate chain"
This error occurs when you're behind a corporate proxy/firewall that intercepts HTTPS connections with a self-signed certificate.

**Solution**: Add this to your `.env` file:
```
VISIER_VERIFY_SSL=false
```

**Note**: Disabling SSL verification reduces security. Only use this in trusted corporate environments. You can also set this during setup by running `python query.py --setup` and answering "false" when asked about SSL verification.

## 📝 Creating Your Own Queries

1. **Start with a template**: Copy `examples/query_payload_template.json` (it has detailed comments)
2. **Remove comment fields**: Delete all `_comment` and `_instructions` fields before running
3. **Change the metric**: Update `query.source.metric` (e.g., `"employeeCount"`, `"headcount"`)
4. **Set dimensions**: Modify `query.axes` to group by what you need
5. **Add filters** (optional): Restrict to specific employees, locations, etc.
6. **Set time period**: Update `query.timeIntervals`
7. **Validate first**: Run with `--validate-only` before executing
8. **Execute**: Run the query and check results

**See also**: `QUICK_REFERENCE.md` for common patterns and quick examples.

## 🔍 Discovering Available Metrics and Dimensions

Contact your Visier administrator for:
- Available metrics in your tenant
- Dimension names and level IDs
- API Schema URL (for exploring available objects)

Common dimensions:
- `Country_Cost` - Geographic breakdown
- `Organization_Hierarchy` - Organizational structure
- `Function` - Job functions
- `Location` - Office locations
- `Employment_Type` - Full-time, Part-time, etc.

## 📚 Files Explained

- **`query.py`**: Main entry point. Run single queries from JSON payload files.
- **`run_multi_metric.py`**: Run multiple metrics (different filters each) → one merged CSV.
- **`client.py`**: Low-level API client. Use this if you want to build queries programmatically.
- **`setup.py`**: Interactive credential configuration.
- **`.env.example`**: Template for environment variables (copy to `.env`).
- **`examples/`**: Example payloads showing different query patterns.

## 📚 Documentation

- **QUICK_REFERENCE.md** - Quick reference guide with common patterns
- **WORKING_NOTES.md** - Working notes and learnings (event metrics, ranged dimensions, multi-metric, Postman)
- **API_REFERENCE.md** - Complete API reference based on official OpenAPI specification
- **openapi.json** - Full OpenAPI 3.0 specification for all Visier APIs

## 🤝 Getting Help

1. Check the examples in `examples/` directory
2. Use `--validate-only` to test payloads without executing
3. Use `--verbose` to see detailed execution information
4. See `API_REFERENCE.md` for complete API documentation
5. Contact your Visier administrator for metric/dimension availability

## 📄 License

[Add your license here]
