# AWS Workspace Setup Guide

This guide helps you set up the Visier impersonation test script in an AWS workspace where you can only copy files in (no GitHub, no AI tools).

## Files to Copy

Copy these files to your AWS workspace:

### Required Files:
1. **test_impersonation.py** - The main impersonation test script
2. **client.py** - Core client functions (required dependency)
3. **requirements.txt** - Python dependencies

### Optional Files (for reference):
- `impersonator.md` - Documentation about exceptional access process
- `API_REFERENCE.md` - API reference documentation
- `examples/query_payload_examples.json` - Example query payloads (if you want to test queries)

## Setup Steps

### 1. Copy Files
Copy the required files to your AWS workspace in the same directory.

### 2. Install Dependencies
In your AWS workspace terminal, run:

```bash
# If using pip
pip install -r requirements.txt

# If using uv (if available)
uv pip install -r requirements.txt
```

### 3. Create .env File
Create a `.env` file in the same directory with your credentials:

```bash
# YOUR credentials (with VTSI profile) - for step 1
VISIER_IMPERSONATION_MY_USERNAME=your_username
VISIER_IMPERSONATION_MY_PASSWORD=your_password
VISIER_IMPERSONATION_JURISDICTION=US
VISIER_IMPERSONATION_APIKEY=your_apikey

# Customer information (for step 2 - impersonation token)
VISIER_IMPERSONATION_TARGET_USERNAME=customer.user@example.com
VISIER_IMPERSONATION_TARGET_TENANT_ID=customer-tenant-123
VISIER_IMPERSONATION_CUSTOMER_APIKEY=customer_api_key
```

### 4. Test Step 1 (Secure Token)
```bash
python3 test_impersonation.py --test-token-only
```

### 5. Test Step 2 (Impersonation Token)
```bash
python3 test_impersonation.py --test-impersonation-token
```

## Minimal File List

If you need the absolute minimum, copy only:
- `test_impersonation.py`
- `client.py`
- `requirements.txt`

The script will work with just these three files.

## Dependencies

The script requires these Python packages (from requirements.txt):
- `requests>=2.31.0`
- `python-dotenv>=1.0.0`
- `pandas>=2.0.0` (for DataFrame conversion)

## Troubleshooting

If you get import errors:
1. Make sure `test_impersonation.py` and `client.py` are in the same directory
2. Check that all dependencies are installed: `pip list | grep requests`
3. Verify Python version is 3.9+

If you get permission errors:
- See `impersonator.md` for the exceptional access process
- Verify you have VTSI profile and API VI profile
- Check that UserManagement Read access is enabled

## Quick Reference

**Test secure token (step 1):**
```bash
python3 test_impersonation.py --test-token-only
```

**Test impersonation token (step 2):**
```bash
python3 test_impersonation.py --test-impersonation-token
```

**Test a query with impersonation:**
```bash
python3 test_impersonation.py --target-tenant "TENANT_ID" --jurisdiction US --test-query
```

All parameters can be set in `.env` file - no command line arguments needed if everything is configured.
