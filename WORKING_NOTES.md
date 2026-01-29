# Working Notes: Aggregate Query Payloads

Practical learnings from building and validating payloads with the Visier Aggregate Query API. Use this alongside `REFERENCE.md`.

---

## 1. Convergent analytic object and qualifying paths

**Rule:** Axes (dimensions) must be defined on or reachable from the **convergent analytic object** of the metric.

- **Employee-based metrics** (e.g. `employeeCount`, `headcount`) converge on **Employee**. Use `qualifyingPath: "Employee"` for axes.
- **Event-based metrics** (e.g. `resignationRate`, `terminationCount`) converge on the **event object** (e.g. **Employee_Exit**). Axes cannot use `qualifyingPath: "Employee"` directly or the API returns: *"Object must be defined on the convergent analytic object [Employee_Exit], but is defined on [Employee]."*

**Fix for event-based metrics:** Traverse from the event to the subject. Use **`Employee_Exit.Employee`** so the axis is “the employee who exited.” Then Employee dimensions (Function, tenure, etc.) are valid.

```json
"dimension": {
  "name": "Function",
  "qualifyingPath": "Employee_Exit.Employee"
}
```

---

## 2. Event-based metrics (e.g. resignationRate)

| Metric             | Convergent object | Use this qualifying path for Employee axes |
|--------------------|-------------------|--------------------------------------------|
| `resignationRate`  | Employee_Exit     | `Employee_Exit.Employee`                   |
| `terminationCount` | Employee_Exit     | `Employee_Exit.Employee`                   |

- **Do not** use `qualifyingPath: "Employee"` alone for these metrics.
- **Do not** use `qualifyingPath: "Employee_Exit"` for Employee dimensions (Function, tenure, etc.) — they don’t exist on the event; they exist on the subject. Use `Employee_Exit.Employee`.

---

## 3. Ranged dimensions (e.g. tenure)

**Employe_Tenure_Year** (note: object name is spelled with one `e` in this tenant) is a **ranged dimension** on the Employee object.

- **Do not** use **dimensionLevelSelection** with a level ID for this dimension. The API returns: *"Unable to resolve the levels [ Employe_Tenure_Year ] of the dimension Employe_Tenure_Year."* Ranged dimensions don’t use level IDs the same way.
- **Do** use **dimensionLeafMemberSelection** so the API returns all tenure bands (leaf members) without specifying a level.

```json
{
  "dimensionLeafMemberSelection": {
    "dimension": {
      "name": "Employe_Tenure_Year",
      "qualifyingPath": "Employee_Exit.Employee"
    }
  }
}
```

For event-based metrics, keep the same path: `Employee_Exit.Employee`.

**Alternative:** If your tenant exposes tenure as a **numeric property** (not a dimension), you would use the **numericRanges** axis with a `property` reference and a `ranges` string (e.g. `"0 1 3 5 10 15 20"`). That did not resolve in our tenant; the dimension approach did.

---

## 4. Axis types cheat sheet

| Axis type                      | When to use |
|--------------------------------|-------------|
| **dimensionLevelSelection**     | Levelled dimensions (Function, Country_Cost, Organization_Hierarchy). Requires `levelIds` (e.g. `["Function"]`, `["Country"]`). |
| **dimensionLeafMemberSelection**| Ranged dimensions or when you want all leaf members of a dimension (e.g. Employe_Tenure_Year). No `levelIds`. |
| **numericRanges**              | Group by a numeric property with custom buckets. Requires `property` (name + qualifyingPath) and `ranges` (space-separated bounds). |
| **dimensionMemberSelection**    | Explicit list of dimension members. |

---

## 5. Working client payload reference

A validated payload that runs successfully:

- **File:** `examples/query_payload_client.json`
- **Metric:** `resignationRate`
- **Axes:** Function (dimensionLevelSelection), Employe_Tenure_Year (dimensionLeafMemberSelection)
- **Path for both:** `Employee_Exit.Employee`

Run it:

```bash
uv run python query.py --payload examples/query_payload_client.json
```

Results: CSV with columns `Measures`, `TimeInInterval`, `Function`, `Employe_Tenure_Year`, `value`, `support`.

---

## 6. Common pitfalls

1. **Wrong qualifying path for event metrics** — Using `Employee` for resignationRate causes “must be defined on [Employee_Exit]”. Use `Employee_Exit.Employee`.
2. **Ranged dimension with level ID** — Using dimensionLevelSelection with a level for Employe_Tenure_Year causes “Unable to resolve the levels”. Use dimensionLeafMemberSelection.
3. **Wrong object name** — Tenant object name may differ (e.g. `Employe_Tenure_Year` vs `Employee_Tenure_Year`). Use the exact name from your data model.
4. **numericRanges for a dimension** — If tenure is a **dimension** (range bands), use dimensionLeafMemberSelection. Use numericRanges only when the backend is a **numeric property** and you define the buckets.

---

## 7. Query options (quick reference)

See `REFERENCE.md` and OpenAPI for full list. Commonly used:

- **calendarType:** `TENANT_CALENDAR` | `GREGORIAN_CALENDAR`
- **zeroVisibility** / **nullVisibility:** `SHOW` | `HIDE` | `ELIMINATE`
- **internal.alignTimeAxisToPeriodEnd:** `true` — aligns time to period end (e.g. year-end) to match Visier UI

---

---

## 8. Using the payload in Postman (or other REST clients)

**The JSON file is not sent 1:1.** The tool unwraps it:

- The file has a top-level **`payload`** key (and optionally **`description`**).
- Only the **contents of `payload`** are sent as the request body — i.e. the object with **`query`** and **`options`**.
- No other transformation: that object is sent as-is (no extra wrapper, no cleanup of fields).

**For Postman:**

1. **Method:** POST  
2. **URL:** `https://{your-tenant}.api.visier.io/v1/data/query/aggregate` (with your vanity and auth).  
3. **Body:** Use the **inner** object only — copy the value of **`payload`** from the JSON file (the whole `{ "query": { ... }, "options": { ... } }` block). Do **not** send the whole file (no outer `"description"` or `"payload"` key).  
4. **Auth:** Use the same auth as the tool (e.g. session cookie / API key as required by your tenant).

So: **Body = contents of `payload`** from `query_payload_client.json`, not the full file.

---

## 9. Multiple metrics, same group-by and time, different filters per metric

**API limitation:** The aggregate API has one **filters** array per request. There is no per-metric filter — so “each metric filtered differently” cannot be done in a single API call.

**Two approaches:**

### A. Same filters for all metrics → one request, one CSV

Use **source.metrics** (plural) with multiple metric columns, same axes and timeIntervals, and the same filters. Request **Accept: text/csv** so the API returns one CSV with one column per metric. All metrics must reference the same analytic object (e.g. all Employee_Exit). The client would need to send `Accept: text/csv` and handle CSV response; the tool does not yet support this path.

### B. Different filters per metric → N requests, one merged CSV (recommended)

Run **one query per metric** (each with its own filters), then merge results into **one CSV** with a **metric** column so you can tell which metric each row is for.

**How:**

1. **Config file:** `examples/query_multi_metric_config.json`  
   - **shared:** `axes`, `timeIntervals`, `options` (same for all).  
   - **metrics:** array of `{ "metric": "<id>", "filters": [ ... ] }` — each entry can have different filters.

2. **Run:**  
   `uv run python run_multi_metric.py --config examples/query_multi_metric_config.json`

3. **Output:** One CSV (default `output/multi_metric_results.csv`) with columns: **metric**, dimension columns, **TimeInInterval**, **value**, **support**, etc. Rows from different metrics are stacked; the **metric** column identifies which metric each row is for.

**Example config:** Two runs of `resignationRate` — one filtered to US + Job_Family “Individual Contributor 2”, one filtered to Canada only — same axes (Function, Employe_Tenure_Year) and time (last 12 months). Edit `metrics` in the config to add more metric+filter combinations.

---

*Last updated from learnings while building `examples/query_payload_client.json` and multi-metric flow.*
