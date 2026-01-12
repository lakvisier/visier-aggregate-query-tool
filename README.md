# Aggregate Query Module

RESTful API-based aggregate queries for Visier Platform (no SDK dependencies).

## 🚀 For Clients: Getting Started

**New to this tool? Start here:**

1. **[QUICK_START.md](QUICK_START.md)** - Get running in 5 minutes
2. **[CLIENT_WALKTHROUGH.md](CLIENT_WALKTHROUGH.md)** - Complete step-by-step guide
3. **Interactive Walkthrough**: `python walkthrough.py`

### Quick Commands

```bash
# Setup credentials (first time)
python run_aggregate_query.py --setup

# Run your first query
python run_aggregate_query.py --payload examples/query_payload_examples.json

# Interactive walkthrough
python walkthrough.py
```

## Developer Quick Start

```bash
# Run query with default example
python scripts/run_query.py

# Run with custom payload
python scripts/run_query.py --file examples/query_payload_examples.json
```

## Structure

```
.
├── run_aggregate_query.py         # 🎯 Main client script (START HERE)
├── setup_credentials.py           # Interactive credential setup
├── walkthrough.py                 # Interactive first-time guide
├── aggregate_query_vanilla.py     # Core query functions
├── scripts/                       # Advanced CLI tools
│   ├── run_query.py               # Advanced query runner (with debug options)
│   └── discover_dimension_levels.py  # Dimension level discovery
├── examples/                      # Example payloads
│   ├── query_payload_examples.json
│   └── query_payload_examples_org_hierarchy.json
├── docs/                          # Technical documentation
│   ├── README.md                  # Detailed usage guide
│   └── LEARNINGS.md               # Query patterns and best practices
├── CLIENT_WALKTHROUGH.md          # 📖 Complete client guide
├── QUICK_START.md                 # ⚡ Quick reference
├── tests/                         # Test scripts
└── output/                        # Query results (CSV files)
```

## Documentation

### For Clients
- **[QUICK_START.md](QUICK_START.md)** - ⚡ Get started in 5 minutes
- **[CLIENT_WALKTHROUGH.md](CLIENT_WALKTHROUGH.md)** - 📖 Complete step-by-step guide
- **[Examples](examples/README.md)** - Example payload files

### For Developers
- **[Usage Guide](docs/README.md)** - Technical guide with examples
- **[Learnings](docs/LEARNINGS.md)** - Query patterns, time intervals, and best practices

## Features

- ✅ RESTful API queries (no SDK dependencies)
- ✅ Helper functions for building queries
- ✅ Dimension member filtering
- ✅ Time interval support
- ✅ Direct CSV export via CLI tool
- ✅ JSON payload-based queries

## Usage in Python

```python
from aggregate_query_vanilla import (
    execute_vanilla_aggregate_query,
    convert_vanilla_response_to_dataframe,
    create_dimension_axis
)

# Build and execute query
axes = [create_dimension_axis("Function")]
response = execute_vanilla_aggregate_query(metric_id="employeeCount", axes=axes)
df = convert_vanilla_response_to_dataframe(response, metric_id="employeeCount")
```

See [docs/README.md](docs/README.md) for complete documentation.
