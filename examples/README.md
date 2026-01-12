# Query Payload Examples

This directory contains example JSON payloads for Visier aggregate queries.

## Files

- **query_payload_template.json** - 📝 Template with detailed comments and customization guide (START HERE)
- **query_payload_examples.json** - Basic example with Country_Cost dimension
- **query_payload_examples_org_hierarchy.json** - Example with Organization_Hierarchy, Location, and Country_Cost dimensions

## Usage

### For Clients

Use these examples with the main client script:

```bash
# Run with basic example
python run_aggregate_query.py --payload examples/query_payload_examples.json

# Run with organization hierarchy example
python run_aggregate_query.py --payload examples/query_payload_examples_org_hierarchy.json

# Validate before running
python run_aggregate_query.py --payload examples/query_payload_examples.json --validate-only
```

### For Developers

Use with the advanced script:

```bash
# Run with basic example
python scripts/run_query.py --file examples/query_payload_examples.json
```

## Creating Your Own Payload

1. **Start with the template**: Copy `query_payload_template.json` to create your own
2. **Modify the fields**: Edit metric, dimensions, filters, and time intervals
3. **Validate**: Use `--validate-only` to check your payload before running
4. **Run**: Execute your query with `--payload <your-file.json>`

## Customizing

Edit the JSON files to customize:
- **Metrics** (`query.source.metric`) - What you're measuring
- **Dimensions/axes** (`query.axes`) - How to group the data
- **Filters** (`query.filters`) - Optional constraints
- **Time intervals** (`query.timeIntervals`) - Time period
- **Options** (`options`) - Display and formatting options

## Getting Help

- **Template Guide**: See `query_payload_template.json` for detailed customization instructions
- **Complete Guide**: See `CLIENT_WALKTHROUGH.md` for step-by-step instructions
- **Quick Reference**: See `QUICK_START.md` for common commands
- **Patterns**: See `docs/LEARNINGS.md` for detailed patterns and examples
