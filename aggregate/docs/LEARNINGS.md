# Visier Aggregate Query Learnings

This document captures key learnings and patterns discovered during development and debugging of Visier aggregate queries. Use this as a reference to avoid common pitfalls and ensure correct query construction.

## Table of Contents
1. [Time Interval Patterns](#time-interval-patterns)
2. [Point-in-Time Queries](#point-in-time-queries)
3. [Multi-Year Queries](#multi-year-queries)
4. [Time Dimension as Axis](#time-dimension-as-axis)
5. [Query Options](#query-options)
6. [Common Pitfalls](#common-pitfalls)
7. [Validated Patterns](#validated-patterns)

---

## Time Interval Patterns

### Key Principle
**For point-in-time queries, use the start of the NEXT period with BACKWARD direction.**

### Point-in-Time Query Pattern
To get a snapshot at a specific date (e.g., Dec 31, 2024):

```json
{
  "timeIntervals": {
    "fromDateTime": "2025-01-01",  // Start of NEXT day
    "intervalPeriodType": "DAY",
    "intervalCount": 1,
    "direction": "BACKWARD"        // Gets the day ending at that point
  }
}
```

**Why this works:** The `fromDateTime` is exclusive - it represents the start of the next period. Using `BACKWARD` direction gets the period ending at that point.

### Multi-Year Query Pattern
To get year-end snapshots for multiple years (e.g., 2021-2025):

```json
{
  "timeIntervals": {
    "fromDateTime": "2025-11-28",  // Or "2026-01-01" - after last data point
    "intervalPeriodType": "YEAR",
    "intervalCount": 5,             // Number of years
    "direction": "BACKWARD"          // Gets years ending at that point
  }
}
```

**Note:** If 2025 data only goes up to Nov 27, 2025, use a date after that (e.g., "2025-11-28" or "2026-01-01").

---

## Point-in-Time Queries

### Correct Pattern (VALIDATED)
```json
{
  "timeIntervals": {
    "fromDateTime": "2025-01-01",
    "intervalPeriodType": "DAY",
    "intervalCount": 1,
    "direction": "BACKWARD"
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

**Result:** Returns data for Dec 31, 2024 with `DateInRange: "2024-12-31T23:59:59.999Z - [0]"`

### What DOESN'T Work
- ❌ `fromDateTime: "2024-12-31"` with `direction: "BACKWARD"` - Returns wrong values
- ❌ `fromDateTime: "2024-12-31"` with `direction: "FORWARD"` - Returns 2025 data
- ❌ `fromDateTime: "2024-12-01"` with `direction: "FORWARD"` and `intervalPeriodType: "MONTH"` - Close but not exact

---

## Multi-Year Queries

### Correct Pattern (VALIDATED)
```json
{
  "timeIntervals": {
    "fromDateTime": "2025-11-28",  // After last data point in 2025
    "intervalPeriodType": "YEAR",
    "intervalCount": 5,
    "direction": "BACKWARD"
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

**Result:** Returns 50 rows (10 countries × 5 years) with `DateInRange` values:
- `2021-12-31T23:59:59.999Z - [0]`
- `2022-12-31T23:59:59.999Z - [1]`
- `2023-12-31T23:59:59.999Z - [2]`
- `2024-12-31T23:59:59.999Z - [3]`
- `2025-12-31T23:59:59.999Z - [4]`

**Note:** Even though 2025 data only goes to Nov 27, the query still returns 2025 with the year-end date label.

---

## Time Dimension as Axis

### Important Discovery
**DO NOT add Time as an explicit axis when using `timeIntervals`.**

### What Happens
- When you use `timeIntervals`, the API automatically creates a Time dimension
- This appears as `DateInRange` in the response
- Adding Time as an explicit axis causes: `"Unable to resolve dimension Time with qualifying path Employee"`

### Correct Approach
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
    // DO NOT add Time axis here - it's created automatically by timeIntervals
  ],
  "timeIntervals": {
    "fromDateTime": "2025-11-28",
    "intervalPeriodType": "YEAR",
    "intervalCount": 5,
    "direction": "BACKWARD"
  }
}
```

### Why This Happens
The API tries to infer a `qualifyingPath` for Time from other axes (like "Employee" from Country_Cost), but Time dimension doesn't support qualifying paths.

---

## Query Options

### Essential Options for Accurate Results

```json
{
  "options": {
    "calendarType": "TENANT_CALENDAR",  // Use tenant's fiscal calendar
    "zeroVisibility": "ELIMINATE",       // Remove zero-value rows
    "nullVisibility": "ELIMINATE",       // Remove null-value rows
    "internal": {
      "alignTimeAxisToPeriodEnd": true   // Aligns timestamps to period end
    }
  }
}
```

### What Each Option Does

1. **`calendarType: "TENANT_CALENDAR"`**
   - Uses the tenant's fiscal calendar
   - Alternative: `"GREGORIAN_CALENDAR"` (but TENANT_CALENDAR is usually correct)

2. **`zeroVisibility: "ELIMINATE"`**
   - Removes rows where the metric value is 0
   - Prevents empty country rows from appearing
   - Alternative: `"SHOW"` or `"HIDE"`

3. **`nullVisibility: "ELIMINATE"`**
   - Removes rows where the metric value is null
   - Alternative: `"SHOW"` or `"HIDE"`

4. **`alignTimeAxisToPeriodEnd: true`**
   - Shifts timestamps to the end of the period
   - Example: `2024-12-31T00:00:00.000Z` becomes `2024-12-31T23:59:59.999Z`
   - **CRITICAL:** This ensures timestamps match dashboard displays

---

## Common Pitfalls

### 1. Wrong Time Interval Direction
**Problem:** Using `fromDateTime: "2024-12-31"` with `direction: "BACKWARD"`  
**Solution:** Use `fromDateTime: "2025-01-01"` (next period) with `direction: "BACKWARD"`

### 2. Adding Time as Explicit Axis
**Problem:** Adding Time dimension to axes array causes qualifying path errors  
**Solution:** Let `timeIntervals` automatically create the Time dimension

### 3. Wrong Calendar Type
**Problem:** Using `GREGORIAN_CALENDAR` when tenant uses fiscal calendar  
**Solution:** Use `TENANT_CALENDAR` (validated to work correctly)

### 4. Missing `alignTimeAxisToPeriodEnd`
**Problem:** Timestamps show period start instead of period end  
**Solution:** Always include `"internal": {"alignTimeAxisToPeriodEnd": true}`

### 5. Not Eliminating Zero/Null Values
**Problem:** Empty country rows appear in results  
**Solution:** Use `"zeroVisibility": "ELIMINATE"` and `"nullVisibility": "ELIMINATE"`

### 6. Wrong Date for Multi-Year Queries
**Problem:** Using a date before the last data point  
**Solution:** Use a date after the last data point (e.g., if data goes to Nov 27, 2025, use Nov 28, 2025 or later)

---

## Validated Patterns

### Pattern 1: Single Point-in-Time (Dec 31, 2024)
```json
{
  "timeIntervals": {
    "fromDateTime": "2025-01-01",
    "intervalPeriodType": "DAY",
    "intervalCount": 1,
    "direction": "BACKWARD"
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
**Validated:** Returns correct values matching dashboard (3,963 total)

### Pattern 2: Multi-Year Year-End Snapshots (2021-2025)
```json
{
  "timeIntervals": {
    "fromDateTime": "2025-11-28",
    "intervalPeriodType": "YEAR",
    "intervalCount": 5,
    "direction": "BACKWARD"
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
**Validated:** Returns correct values for all 5 years (50 rows: 10 countries × 5 years)

---

## Key Insights

1. **Time Intervals Create Time Dimension Automatically**
   - No need to add Time as an explicit axis
   - Time appears as `DateInRange` in the response

2. **Point-in-Time = Next Period Start + BACKWARD**
   - Always use the start of the next period
   - BACKWARD direction gets the period ending at that point

3. **Year-End Snapshots Need Year Interval Type**
   - Use `intervalPeriodType: "YEAR"` for yearly data
   - Use `intervalCount` to specify number of years

4. **Options Are Critical**
   - `alignTimeAxisToPeriodEnd` ensures correct timestamp display
   - `zeroVisibility` and `nullVisibility` clean up results
   - `calendarType` must match tenant configuration

5. **DateInRange Format**
   - Format: `"YYYY-MM-DDT23:59:59.999Z - [N]"`
   - The `[N]` is the interval index (0-based)
   - With `alignTimeAxisToPeriodEnd`, timestamps are at period end

---

## Tenant-Specific Considerations

1. **Data Availability**
   - Check when data ends (e.g., Nov 27, 2025)
   - Use dates after the last data point for queries

2. **Calendar Type**
   - Most tenants use `TENANT_CALENDAR`
   - Verify if fiscal year differs from calendar year

3. **Dimension Names**
   - `Country_Cost` is tenant-specific
   - Level IDs like `["Country"]` may vary
   - Always validate dimension names and level IDs

4. **Metric IDs**
   - `employeeCount` works for this tenant
   - Other metrics may have different IDs
   - Validate metric IDs exist in tenant

5. **Parent-Child Hierarchies (Organization_Hierarchy)**
   - **CRITICAL:** Level IDs are tenant-specific and MUST be discovered
   - Cannot use generic level IDs like `["Country"]` that work for levelled dimensions
   - Common level IDs: `["Profit_Center"]`, `["Business_Unit"]`, `["Department"]`, `["Level_1"]`
   - **Discovery Method:** Use Dimensions API: `GET /v1/data/model/dimensions/Organization_Hierarchy/levels`
   - May need to try multiple level IDs to find the correct one
   - Qualifying path usually stays `"Employee"` (same as levelled dimensions)

---

## Response Structure

### With timeIntervals (No Explicit Time Axis)
```
Columns: Measures, DateInRange, Country_Cost, value, support
```

### DateInRange Values
- Single year: `["2024-12-31T23:59:59.999Z - [0]"]`
- Multiple years: `["2021-12-31T23:59:59.999Z - [0]", "2022-12-31T23:59:59.999Z - [1]", ...]`

### Row Count
- Single year: `number_of_countries` rows
- Multiple years: `number_of_countries × number_of_years` rows

---

## Debugging Tips

1. **Always validate payload structure** before sending
2. **Use `--debug` flag** to see exact payload and response
3. **Check DateInRange values** to verify time intervals are correct
4. **Compare totals** with known dashboard values
5. **Test with single year first**, then expand to multiple years

---

## Remember

- ✅ Use next period start + BACKWARD for point-in-time
- ✅ Let timeIntervals create Time dimension automatically
- ✅ Always include `alignTimeAxisToPeriodEnd: true`
- ✅ Use `TENANT_CALENDAR` unless specifically needed otherwise
- ✅ Eliminate zero/null values for cleaner results
- ❌ Don't add Time as explicit axis
- ❌ Don't use target date directly in fromDateTime
- ❌ Don't forget to account for data availability dates

---

## Switching Dimensions: Country_Cost to Organization_Hierarchy

### Key Differences

| Aspect | Country_Cost (Levelled) | Organization_Hierarchy (Parent-Child) |
|--------|------------------------|--------------------------------------|
| Dimension Type | Levelled dimension | Parent-child hierarchy |
| Level IDs | Simple, predictable: `["Country"]` | Tenant-specific, must discover |
| Discovery | Usually obvious from dimension name | Requires API call or documentation |
| Common Level IDs | `["Country"]`, `["Cost"]` | `["Profit_Center"]`, `["Business_Unit"]`, `["Level_1"]` |
| Qualifying Path | Usually `"Employee"` | Usually `"Employee"` (same) |

### Switching Steps

1. **Replace dimension name:**
   ```json
   "name": "Country_Cost"  →  "name": "Organization_Hierarchy"
   ```

2. **Replace levelIds (CRITICAL - must discover):**
   ```json
   "levelIds": ["Country"]  →  "levelIds": ["Profit_Center"]
   ```
   ⚠️ **You MUST verify the level ID exists in your tenant!**

3. **Keep qualifyingPath:**
   ```json
   "qualifyingPath": "Employee"  // Usually same for both
   ```

### How to Discover Level IDs

**Method 1: Use the Discovery Script (RECOMMENDED)**
```bash
# Discover levels for Organization_Hierarchy
python aggregate/scripts/discover_dimension_levels.py Organization_Hierarchy

# Get only level IDs (for scripting)
python aggregate/scripts/discover_dimension_levels.py Organization_Hierarchy --level-ids-only

# Use v2alpha API (includes more details)
python aggregate/scripts/discover_dimension_levels.py Organization_Hierarchy --api-version v2alpha
```

**Method 2: Dimensions API (Manual)**
```bash
# v2alpha API (recommended - includes levels)
GET /v2alpha/data/model/dimensions/Organization_Hierarchy?with=details

# v1 API (requires object ID)
GET /v1/data/model/analytic-objects/Employee/dimensions/Organization_Hierarchy
```

**Method 3: Try Common Patterns**
- `["Profit_Center"]` - Most common top level
- `["Business_Unit"]` - Second level
- `["Department"]` - Third level
- `["Level_1"]`, `["Level_2"]`, `["Level_3"]` - Generic levels
- `["Organization_Hierarchy"]` - Sometimes the dimension name itself

**Method 3: Check Tenant Documentation**
- Review data model documentation
- Check Visier Studio for dimension structure

### Example: Complete Switch

**Before (Country_Cost):**
```json
{
  "dimensionLevelSelection": {
    "dimension": {
      "name": "Country_Cost",
      "qualifyingPath": "Employee"
    },
    "levelIds": ["Country"]
  }
}
```

**After (Organization_Hierarchy):**
```json
{
  "dimensionLevelSelection": {
    "dimension": {
      "name": "Organization_Hierarchy",
      "qualifyingPath": "Employee"
    },
    "levelIds": ["Profit_Center"]  // ⚠️ Verify this exists in your tenant!
  }
}
```

### Common Pitfalls When Switching

1. **Using Wrong Level ID**
   - ❌ Assuming `["Country"]` works for Organization_Hierarchy
   - ✅ Must discover tenant-specific level IDs

2. **Not Verifying Level ID**
   - ❌ Using a level ID without checking if it exists
   - ✅ Always verify with Dimensions API or test query

3. **Using Multiple Levels**
   - Can specify multiple levels: `["Level_1", "Level_2"]`
   - But usually start with single level first: `["Profit_Center"]`

4. **Wrong Qualifying Path**
   - Usually stays `"Employee"` but verify if query fails
   - May need to try `null` or different path

### Template File

See `query_payload_examples_org_hierarchy.json` for a complete example with Organization_Hierarchy.

---

*Last updated: Based on validated queries returning correct values matching dashboard data*
