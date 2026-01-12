# Migration Guide: Extracting to Standalone Repository

> **Note:** This migration has been completed. Files are now at the repository root level (not in an `aggregate/` folder). This guide is kept for historical reference.

This guide helps you extract the aggregate folder into a standalone repository.

## Benefits of Separation

✅ **Cleaner distribution** - Clients only get what they need  
✅ **Independent versioning** - Version aggregate tool separately  
✅ **Focused repository** - Easier to navigate and maintain  
✅ **Simpler setup** - No confusion about dependencies  

## What to Include

The aggregate folder is **fully self-contained**. Include everything in the `aggregate/` directory:

```
aggregate/
├── __init__.py
├── aggregate_query_vanilla.py
├── run_aggregate_query.py
├── setup_credentials.py
├── walkthrough.py
├── README.md (or use STANDALONE_README.md)
├── CLIENT_WALKTHROUGH.md
├── QUICK_START.md
├── requirements.txt (NEW - minimal dependencies)
├── .env.example (NEW - credential template)
├── scripts/
│   ├── __init__.py
│   ├── run_query.py
│   └── discover_dimension_levels.py
├── examples/
│   ├── README.md
│   ├── query_payload_template.json
│   ├── query_payload_examples.json
│   └── query_payload_examples_org_hierarchy.json
├── docs/
│   ├── README.md
│   └── LEARNINGS.md
├── tests/
│   ├── __init__.py
│   └── test_org_hierarchy_levels.py
└── output/ (can be empty or .gitignored)
```

## Steps to Create Standalone Repo

### 1. Create New Repository

```bash
# Create new directory
mkdir visier-aggregate-query-tool
cd visier-aggregate-query-tool
git init
```

### 2. Copy Files

Copy the entire `aggregate/` folder contents to the new repo root:

```bash
# From PythonSDK directory
cp -r aggregate/* visier-aggregate-query-tool/
```

### 3. Update Files

#### Update README.md

Replace `aggregate/README.md` with `STANDALONE_README.md` or update paths:

```bash
cp aggregate/STANDALONE_README.md visier-aggregate-query-tool/README.md
```

#### Update setup_credentials.py

The `get_project_root()` function should work as-is since it looks for `.env.example` or `requirements.txt` in parent directories.

#### Update Script Paths

All scripts use relative paths, so they should work as-is. The imports are already fixed to work standalone.

### 4. Create .gitignore

```bash
cat > .gitignore << EOF
# Environment
.env

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/

# Output
output/*.csv
!output/.gitkeep

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
EOF
```

### 5. Create Initial Commit

```bash
git add .
git commit -m "Initial commit: Standalone Visier Aggregate Query Tool"
```

## Dependencies

The standalone repo only needs:

- `requests` - HTTP requests
- `python-dotenv` - Environment variable loading
- `pandas` - DataFrame conversion (optional, but recommended)

**No SDK dependency** - The tool uses REST API directly.

## Testing the Standalone Repo

1. **Test credential setup:**
   ```bash
   python run_aggregate_query.py --setup
   ```

2. **Test query execution:**
   ```bash
   python run_aggregate_query.py --payload examples/query_payload_examples.json --validate-only
   ```

3. **Test walkthrough:**
   ```bash
   python walkthrough.py
   ```

## What Changes in Parent Repo

After extraction, you can:

1. **Remove aggregate folder** from PythonSDK (if no longer needed)
2. **Add reference** in PythonSDK README pointing to new repo
3. **Keep aggregate folder** but mark as deprecated/redirect

## Notes

- All imports are already fixed to work standalone
- Scripts use relative paths
- No hard dependencies on parent repo
- `.env` file location is auto-detected

## Next Steps

1. Create the new repository
2. Copy files
3. Test in the new location
4. Update documentation links if needed
5. Share with clients!
