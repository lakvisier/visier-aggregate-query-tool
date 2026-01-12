# Visier Aggregate Query Tool

Simple tool to run Visier aggregate queries via REST API.

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Setup credentials:**
   ```bash
   python run_aggregate_query.py --setup
   ```

3. **Run a query:**
   ```bash
   python run_aggregate_query.py --payload examples/query_payload_examples.json
   ```

## Usage

```bash
# Setup credentials (first time)
python run_aggregate_query.py --setup

# Run query
python run_aggregate_query.py --payload examples/query_payload_examples.json

# Validate payload without running
python run_aggregate_query.py --payload examples/query_payload_examples.json --validate-only

# Save results to custom file
python run_aggregate_query.py --payload examples/query_payload_examples.json --output results.csv
```

## Files

- `run_aggregate_query.py` - Main script
- `aggregate_query_vanilla.py` - Core query functions
- `setup_credentials.py` - Credential setup
- `examples/` - Example payload files
