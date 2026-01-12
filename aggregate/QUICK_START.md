# Quick Start Guide

Get up and running with Visier Aggregate Queries in 5 minutes.

## 1. Setup Credentials

```bash
python aggregate/run_aggregate_query.py --setup
```

Enter your API credentials when prompted. This creates a `.env` file.

## 2. Run Your First Query

```bash
python aggregate/run_aggregate_query.py --payload examples/query_payload_examples.json
```

Results are saved to `output/query_results.csv`.

## 3. Customize Your Query

Edit `examples/query_payload_examples.json`:

- **Change metric**: Edit `payload.query.source.metric`
- **Change dimensions**: Edit `payload.query.axes`
- **Add filters**: Add to `payload.query.filters`
- **Change time period**: Edit `payload.query.timeIntervals`

## 4. Validate Before Running

```bash
python aggregate/run_aggregate_query.py --payload my_query.json --validate-only
```

## Common Commands

| Command | Description |
|---------|-------------|
| `--setup` | Configure credentials |
| `--payload <file>` | Run query from JSON file |
| `--output <file>` | Save results to custom file |
| `--validate-only` | Check payload without running |
| `--verbose` | Show detailed output |

## Payload Structure

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
        "intervalCount": 5,
        "direction": "BACKWARD"
      }
    }
  }
}
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Missing credentials | Run `--setup` |
| Validation errors | Check payload structure matches examples |
| API 400 error | Verify metric/dimension names in schema |
| API 401 error | Re-run `--setup` to update credentials |
| No data returned | Check time period, filters, or permissions |

## Next Steps

- **Full Guide**: See `CLIENT_WALKTHROUGH.md`
- **Interactive Help**: Run `python aggregate/walkthrough.py`
- **Examples**: Check `examples/` directory
- **API Schema**: Use URL from your administrator

---

**Need Help?** See `CLIENT_WALKTHROUGH.md` for detailed instructions.
