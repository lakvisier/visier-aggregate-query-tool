# Visier Aggregate Query Tool

A standalone tool for querying Visier aggregate data via REST API. This tool allows you to easily configure credentials and run queries using JSON payload files.

## 🚀 Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Setup credentials:**
   ```bash
   python run_aggregate_query.py --setup
   ```

3. **Run your first query:**
   ```bash
   python run_aggregate_query.py --payload examples/query_payload_examples.json
   ```

## 📚 Documentation

- **[QUICK_START.md](QUICK_START.md)** - Get running in 5 minutes
- **[CLIENT_WALKTHROUGH.md](CLIENT_WALKTHROUGH.md)** - Complete step-by-step guide
- **Interactive Walkthrough**: `python walkthrough.py`

## 📁 Project Structure

```
.
├── run_aggregate_query.py         # 🎯 Main script (START HERE)
├── setup_credentials.py           # Interactive credential setup
├── walkthrough.py                 # Interactive first-time guide
├── aggregate_query_vanilla.py     # Core query functions
├── scripts/                       # Advanced CLI tools
│   ├── run_query.py               # Advanced query runner
│   └── discover_dimension_levels.py  # Dimension level discovery
├── examples/                      # Example payloads
│   ├── query_payload_template.json # Template with guide
│   ├── query_payload_examples.json
│   └── query_payload_examples_org_hierarchy.json
├── docs/                          # Technical documentation
│   ├── README.md                  # Detailed usage guide
│   └── LEARNINGS.md               # Query patterns and best practices
├── CLIENT_WALKTHROUGH.md          # 📖 Complete client guide
├── QUICK_START.md                 # ⚡ Quick reference
├── requirements.txt               # Python dependencies
├── .env.example                   # Credential template
└── output/                        # Query results (CSV files)
```

## 🔧 Requirements

- Python 3.9+
- See `requirements.txt` for package dependencies

## 📖 Usage

### Setup Credentials

```bash
python run_aggregate_query.py --setup
```

### Run a Query

```bash
python run_aggregate_query.py --payload examples/query_payload_examples.json
```

### Validate Payload

```bash
python run_aggregate_query.py --payload my_query.json --validate-only
```

### Interactive Walkthrough

```bash
python walkthrough.py
```

## 🎯 Features

- ✅ RESTful API queries (no SDK dependencies)
- ✅ Interactive credential setup
- ✅ JSON payload-based queries
- ✅ Payload validation
- ✅ CSV export
- ✅ Comprehensive documentation
- ✅ Example templates

## 📝 License

[Add your license here]

## 🤝 Support

For issues or questions, see the documentation files or contact your administrator.
