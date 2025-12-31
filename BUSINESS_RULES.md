# Business Rules: Monthly Performance Analysis System

**Version:** 3.0 (Complete)
**Date:** December 31, 2025
**Owner:** Third Horizon
**Primary author:** Topher Rasmussen (based on David's tracker + walkthrough)

---

## 1. Overview

### 1.1 Purpose

This system produces a repeatable **monthly performance package** by:
- ingesting five monthly source files (Pro Forma, Compensation, Harvest Hours, Harvest Expenses, P&L),
- normalizing them to a shared **contract code** key, and
- generating a project-level "cost waterfall" (revenue → direct costs → allocated overhead → margin).

### 1.2 Core principle

This is a **deterministic rules engine**. Given the same inputs and settings, it must always produce the same outputs, with a validation trail that makes results auditable.

### 1.3 What the system must answer

For each **revenue-bearing contract code** in the month:
- How much revenue (accrual basis) did we recognize?
- How much labor cost did we incur (hours × fully-loaded hourly rates)?
- How much **non-reimbursable** expense did we incur?
- How much overhead should we allocate:
  - **SG&A** (broad overhead allocated across all revenue),
  - **Data Infrastructure** (allocated only to "Data" projects),
  - **Workplace Well-being** (allocated only to "Wellness" projects)?
- What are the resulting margin dollars and margin %?

In addition, the system reports:
- **Cost center activity** (internal overhead time and expenses tracked in Harvest), and
- **Non-revenue client activity** (codes with work but no revenue in the month).

### 1.4 Delivery mechanisms (v3.0)

The system provides results through:
- **CSV files** (revenue_centers.csv, cost_centers.csv, non_revenue_clients.csv, validation_report.md)
- **Interactive web dashboard** with drill-down, filtering, sorting, and visualization
- **API endpoints** for programmatic access to project details

---

## 2. Shared Key: Contract Code

### 2.1 Source of truth

The contract code (aka **Project Code**) is the **primary join key** across:
- Pro Forma (revenue),
- Harvest Hours (time),
- Harvest Expenses (expenses),
- outputs and dashboards.

### 2.2 Normalization rules

Before any joins:
- Trim whitespace
- Normalize repeated spaces and invisible characters (e.g., non-breaking spaces)
- Preserve case (codes are treated as case-sensitive identifiers)
- Treat empty / missing codes as invalid rows (drop + log)

---

## 3. Required Monthly Inputs

### 3.1 Pro Forma (Revenue)

**File name:** `(Proforma) {Month} {Year}.xlsx` (exact naming not required, but month/year must be known by the runner)
**Sheet:** `PRO FORMA 2025`

#### 3.1.1 Structure (as seen in example files)

- Row with month headers (contains `Jan … Dec`)
- Rows underneath contain:
  - section headers (e.g., `BEH - Behavioral Health`) where Project Code is blank
  - project rows with:
    - Column **B** = project name
    - Column **C** = contract code / project code
    - Month column = revenue for that code for that month

#### 3.1.2 Allocation tag (Data vs Wellness)

In the provided examples, Column **A** is used as an **allocation tag** on some project rows:
- `Data` → eligible for Data Infrastructure allocation
- `Wellness` → eligible for Workplace Well-being allocation
- blank → no explicit allocation tag

The engine must support this "Column A tag" behavior (it is NOT always blank).

#### 3.1.3 Category sections (BEH / PAD / MAR / WWB / CMH)

The Pro Forma also groups rows under section headers such as:
- BEH (Behavioral Health)
- PAD (Payment Design & Analytics)
- MAR (Market Analytics)
- WWB (Workplace Well-Being)
- CMH (Community Health)

These section headers are used to assign an **analysis category** (Data / Wellness / Next Gen Advisory) via mapping.

> Important: "Analysis category" is used for reporting; "Allocation tag" determines which overhead pools apply.
> They usually align (PAD+MAR → Data, WWB → Wellness), but the system should not assume they are identical.

#### 3.1.4 Duplicate contract codes in Pro Forma

The Pro Forma can contain **multiple rows with the same contract code** (e.g., split by sub-workstream).
The engine must:
- aggregate revenue by contract code for the month,
- carry project name as "first non-empty" (or concatenate names in a separate field),
- carry allocation tag using priority rules:
  1. If any row for the code is tagged `Data`, allocation_tag = Data (unless any row is tagged Wellness → conflict)
  2. Else if any row is tagged `Wellness`, allocation_tag = Wellness
  3. Else allocation_tag = blank/None

If a code has both `Data` and `Wellness` tags across rows: **FAIL** (human must fix the Pro Forma).

#### 3.1.5 Revenue center rules

For the selected month:
- **Revenue Center** = contract code with aggregated revenue > 0
- **Zero-revenue Pro Forma code** = contract code present but revenue = 0 (tracked for integrity checks)

Zero-revenue codes are "parked" (not included in the revenue-center table), but:
- if Harvest shows hours/expenses against them for the month, they appear as **Non-Revenue Clients** (unless they are Cost Centers).

#### 3.1.6 Total revenue validation

The Pro Forma contains totals (e.g., `Base Revenue`, `Forecasted Revenue`).
Rules:
- Primary total = the row containing `Base Revenue` (case-insensitive match)
- Fallback = `Forecasted Revenue` if `Base Revenue` missing

Validation:
- Sum of project revenues (after aggregation) must match the chosen total within tolerance (±$0.01).

---

### 3.2 Compensation (Fully-loaded hourly rates)

**File name:** `Stylized - (Compensation) {Month} {Year}.xlsx` (name flexible)
**Sheet:** first sheet

#### 3.2.1 Supported strategies (deterministic)

The system must support both:

**Strategy A (Preferred): Read "Base Cost Per Hour" directly**
- Required columns:
  - `Last Name`
  - `Base Cost Per Hour`
- Use the values as the hourly cost rate.

**Strategy B (Fallback): Compute hourly cost**
- If `Base Cost Per Hour` is missing, compute from:
  - either `Total`, or the sum of components:
    - Base Compensation
    - Company Taxes Paid
    - ICHRA Contribution
    - 401k Match
    - Executive Assistant
    - Well Being Card
    - Travel & Expenses

**Expected hours per month**:
- 50 hours/week × 52 weeks/year ÷ 12 months/year = **216.6667 hours/month** (configurable)

`Hourly Cost = Fully-Loaded Monthly Cost / ExpectedHoursPerMonth`

#### 3.2.2 Join key for labor costing

Default join key is `Last Name`.

Validation:
- `Last Name` must be unique in Compensation; if not unique, **FAIL** and require a stronger key (e.g., Employee Id).
- All staff appearing in Harvest Hours for the month must have a matching compensation record.
  - This is **CRITICAL** because missing rates invalidate labor cost.

---

### 3.3 Harvest Hours (Time)

**Export:** Harvest "Detailed Time Report"
**Sheet:** typically `Harvest`

Required fields (column names vary; match case-insensitive with known synonyms):
- Date (or Spent Date)
- Project Code
- Hours
- Last Name (and optionally First Name)

Rules:
- Only include rows where Date falls inside the selected month (outside-month rows: warn + exclude by default).
- Hours must be numeric and ≥ 0 (0-hour rows are allowed but ignored in sums).

---

### 3.4 Harvest Expenses (Expenses)

**Export:** Harvest "Detailed Expenses Report"
Required fields:
- Project Code
- Amount
- Billable (or Billable?, Reimbursable)

#### 3.4.1 Reimbursable vs non-reimbursable

- If **Billable = Yes/True** → reimbursable → **EXCLUDE** from cost
- If **Billable = No/False** → non-reimbursable → **INCLUDE** in cost
- If Billable is blank/unrecognized → warn; default to **INCLUDE** (conservative)

---

### 3.5 P&L (Expense substrate and overhead pools)

**Sheet:** `IncomeStatement` (expected in the example file)

The P&L is multi-column by business line with a rightmost **Total** column.

#### 3.5.1 What must be extracted from P&L

The engine must compute these amounts for the month:

1. **P&L Data Infrastructure spend**
   - baseline: the row labeled `Data Services` (case/punctuation-insensitive)
2. **P&L Workplace Well-being spend**
   - baseline: the row labeled `Well-being Coaches` / `Wellbeing Coaches`
   - may also include other well-being vendor lines (e.g., `Mindful Learning`) via tagging config
3. **P&L Payroll / "Nil" bucket** (for reconciliation only; not allocated)
   - payroll lines that are already represented in hourly labor rates (wages, taxes, health insurance/HRA, guaranteed payments, etc.)
4. **P&L SG&A (non-payroll overhead)**
   - the remainder of operating expenses after removing Data + Workplace + Nil, using account tags.

#### 3.5.2 Account tagging

Because account names vary over time, the P&L categorization must be **config-driven**, not hard-coded.

Recommended config file:
- `config/pnl_account_tags.csv`

Columns:
- `match_type` = exact | contains | regex
- `pattern`
- `bucket` = DATA | WORKPLACE | NIL | SGA
- `notes`

Defaults:
- Anything not matched goes to **SGA**.

Required special case:
- `Wellbeing Benefit` must NOT be treated as `Well-being Coaches`.

#### 3.5.3 Total column extraction

Rules:
- Prefer a column header containing `Total` (case-insensitive).
- If missing, use the rightmost numeric column.

---

## 4. Classification of All Activity

### 4.1 Categories (mutually exclusive)

Every Harvest row (hours or expenses) is classified by its Project Code:

1. **Revenue Centers**
   - In Pro Forma and revenue > 0 for the month
2. **Cost Centers**
   - In `config/cost_centers.csv` OR starts with `THS-` prefix (v3.0 auto-classification)
3. **Non-Revenue Clients**
   - Has hours/expenses in month
   - Not a Revenue Center
   - Not a Cost Center

### 4.2 THS Code Auto-Classification (v3.0)

**Rule:** Any contract code starting with `THS-` is automatically classified as a Cost Center, UNLESS it appears in Pro Forma with revenue > 0.

**Logic:**
```
IF code has revenue in Pro Forma THEN
    classification = Revenue Center
ELSE IF code starts with 'THS-' THEN
    classification = Cost Center (auto-detected)
    default_pool = SGA
ELSE IF code in config/cost_centers.csv THEN
    classification = Cost Center (manual config)
    pool = from config
ELSE IF code has activity in Harvest THEN
    classification = Non-Revenue Client
END IF
```

**Benefits:**
- Zero manual configuration for new THS codes
- Self-documenting naming convention
- Revenue always takes precedence
- No maintenance burden

**Pool assignment for auto-classified THS codes:**
- Default to `SGA` pool
- Can be overridden by adding to `config/cost_centers.csv` with explicit pool

**Project names for auto-classified codes:**
- Use project_name from Harvest Hours if available
- Otherwise use contract code as fallback

### 4.3 Conflict rule (critical)

If a Project Code is both:
- a Revenue Center for the month **and**
- explicitly listed in `config/cost_centers.csv`

→ **FAIL** (business must decide which it is).

**Note:** Auto-classified THS codes do NOT conflict with revenue centers - revenue takes precedence automatically.

---

## 5. Computations

### 5.1 Labor cost (direct)

For each Harvest Hours row:
- identify staff
- look up hourly cost
- compute `row_labor_cost = hours × hourly_cost`

Then group by Project Code:
- `labor_cost[code] = Σ row_labor_cost`

### 5.2 Expense cost (direct non-reimbursable)

For each Harvest Expense row:
- apply reimbursable filter
- `non_reimb_expense[code] = Σ amount (included rows)`

### 5.3 Direct cost merge into Revenue Centers

For each revenue center contract code:
- Revenue (from Pro Forma)
- Labor cost (from Harvest Hours)
- Non-reimbursable expenses (from Harvest Expenses)

Missing labor or expenses are treated as 0 (valid scenario).

---

## 6. Overhead Pools and Allocation

### 6.1 Overhead pools to allocate

The system allocates three pools:

1. **SG&A Pool**
   - P&L SG&A (as tagged)
   - plus optional "Harvest Cost Center Overhead" if configured to be included
2. **Data Infrastructure Pool**
   - P&L Data Services (and other DATA-tagged P&L accounts)
   - plus optional Harvest cost center(s) designated as data infrastructure (e.g., Starset dev)
3. **Workplace Well-being Pool**
   - P&L Well-being Coaches (and other WORKPLACE-tagged P&L accounts)

> Important: To avoid double counting, decide whether overhead expenses tracked in Harvest Cost Centers should also be included in P&L SG&A tagging. The system supports either approach, but the configuration must be consistent.

### 6.2 Allocation bases

All allocations are **pro-rata by revenue**, using accrual revenue from Pro Forma:

- SG&A allocated across **all revenue centers**:
  - base = Total Revenue

- Data Infrastructure allocated only across **Data-tagged revenue centers**:
  - base = Total Revenue for projects with `allocation_tag = Data`

- Workplace Well-being allocated only across **Wellness-tagged revenue centers**:
  - base = Total Revenue for projects with `allocation_tag = Wellness`

### 6.3 Allocation formulas

For each revenue center project `p`:

**SG&A allocation**
```
sga_alloc[p] = (revenue[p] / total_revenue) * sga_pool
```

**Data Infrastructure allocation** (only if allocation_tag == Data)
```
data_alloc[p] = (revenue[p] / total_data_revenue) * data_pool
```

**Workplace Well-being allocation** (only if allocation_tag == Wellness)
```
wellness_alloc[p] = (revenue[p] / total_wellness_revenue) * wellness_pool
```

If the relevant base revenue is 0:
- allocation amount is 0 for all projects in that subset
- log a warning

### 6.4 Margin

For each revenue center project:
```
margin_dollars = revenue
               - labor_cost
               - non_reimb_expenses
               - sga_alloc
               - data_alloc
               - wellness_alloc

margin_percent = margin_dollars / revenue
```

---

## 7. Outputs

### 7.1 revenue_centers.csv

One row per revenue center contract code, with at least:

- contract_code
- project_name
- proforma_section
- analysis_category
- allocation_tag
- revenue
- labor_cost
- expense_cost (non-reimbursable)
- sga_allocation
- data_allocation (if Data-tagged)
- workplace_allocation (if Wellness-tagged)
- total_cost
- margin_dollars
- margin_percent

### 7.2 cost_centers.csv

One row per cost center code:

- contract_code
- description
- pool (SGA | DATA | WORKPLACE)
- labor_cost
- expense_cost
- total_cost

### 7.3 non_revenue_clients.csv

One row per non-revenue client code:

- contract_code (or project_code)
- project_name (from Harvest if present)
- labor_cost
- expense_cost
- total_cost

### 7.4 validation_report.md (or .txt)

A human-readable validation summary:
- PASS / WARN / FAIL entries
- key totals and reconciliation checks
- list of unmapped P&L accounts and unmapped Harvest codes
- THS auto-classification summary

### 7.5 _pools.json (v3.0)

Detailed pool calculation data for transparency:
```json
{
  "sga": {
    "pool_total": 200000,
    "revenue_base": 1000000,
    "project_count": 47
  },
  "data": {
    "pool_total": 155000,
    "revenue_base": 500000,
    "project_count": 25
  },
  "wellness": {
    "pool_total": 1600,
    "revenue_base": 50000,
    "project_count": 5
  }
}
```

---

## 8. Web Dashboard (v3.0)

### 8.1 Interface structure

The web dashboard provides six tabs:

1. **Revenue Centers** - Full P&L table
2. **Margin Analysis** - Visual chart
3. **Cost Centers** - Internal overhead
4. **Non-Revenue Clients** - Exceptions
5. **Validation Report** - Audit trail
6. **Methodology** - Documentation

### 8.2 Drill-down functionality

**Revenue Centers and Cost Centers** tables support drill-down:
- Click any row to expand
- Shows hours detail by person (with rates)
- Shows expense detail by line item
- Shows allocation calculations with formulas

**Drill-down data requirements:**
- Hours: staff_key, hours, hourly_cost, labor_cost
- Expenses: date, description/notes, amount
- Allocations: pool_total, revenue_base, project_revenue, share_pct, formula, result

### 8.3 Table interactivity

All main tables must support:
- **Sorting** by any column
- **Searching** across all text fields
- **Pagination** (default: 25 rows per page)
- **CSV Export** in two modes:
  - Full CSV (original analysis output)
  - Current View CSV (respects sorting, filtering, search)

Default sort orders:
- Revenue Centers: Total cost descending
- Cost Centers: Total cost descending
- Non-Revenue Clients: Total cost descending

### 8.4 Active/Inactive project handling

**Revenue Centers:**
- Active = any financial metric > $0.01
- Inactive = all metrics ≤ $0.01
- Show active by default
- "Show Inactive Projects (N)" toggle button

**Cost Centers:**
- Active = labor_cost OR expense_cost > $0.01
- Inactive = both ≤ $0.01
- Show active by default
- "Show Inactive Cost Centers (N)" toggle button

### 8.5 Margin visualization

**Chart requirements:**
- Type: Horizontal bar chart
- Data: All revenue centers
- Sorting: Margin dollars descending (highest to lowest)
- Color coding:
  - Green (#10b981) for positive margins
  - Red (#ef4444) for negative margins
- Labels: Project name + contract code
- X-axis: Currency formatted ($)
- Tooltips: Exact margin value on hover
- Responsive: Scales to available height

### 8.6 Color coding rules

**Margin columns:**
- Positive margin → Green text (#10b981)
- Negative margin → Red text (#ef4444)
- Font weight: 600 (semi-bold)

**Category badges:**
- Revenue Centers → Blue background
- Cost Centers → Orange background
- Non-Revenue Clients → Red background

### 8.7 API endpoints (internal)

**GET /api/project_details/{type}/{code}**
- `type`: revenue | cost_center | non_revenue
- `code`: contract code (URL-encoded)
- Returns JSON with:
  ```json
  {
    "contract_code": "BEH-25-01-NHCF",
    "project_name": "New Hampshire CF",
    "hours_detail": [...],
    "expenses_detail": [...],
    "sga_details": {...},
    "data_details": {...} or null,
    "wellness_details": {...} or null
  }
  ```

---

## 9. Validation Rules

### 9.1 Critical (FAIL)

- Pro Forma sheet missing
- Month column not found
- No project codes found
- Allocation-tag conflict (both Data and Wellness for same code)
- Any Harvest Hours staff missing compensation rate
- Code is both Revenue Center and Cost Center (in config - not auto-classified)
- P&L Total column not found and cannot infer numeric total column
- Required columns missing in Harvest exports

### 9.2 Warnings (WARN)

- Harvest rows outside month (excluded)
- Unknown / blank Billable values in expenses (included conservatively)
- Pro Forma code has revenue but no Harvest hours (valid but flagged)
- Harvest code appears but not in Pro Forma and not in cost centers (treated as Non-Revenue Client)
- Pro Forma project names missing
- P&L account not matched by tagging rules (defaults to SG&A)
- THS codes auto-classified (informational)

### 9.3 Reconciliation checks

- Sum(project revenues) == Pro Forma base revenue (±$0.01)
- Σ SG&A allocations == SG&A pool (±$0.01)
- Σ Data allocations == Data pool (±$0.01)
- Σ Workplace allocations == Workplace pool (±$0.01)

---

## 10. Configuration

### 10.1 config/cost_centers.csv

Minimum:
```csv
contract_code,description
THS-25-01-DEV,Business Development
THS-25-01-BAD,Business Administration
THS-25-01-MTG,Internal Meetings
```

Recommended extension (optional):
```csv
contract_code,description,pool
THS-25-01-SAD,Starset Dev Cost,DATA
THS-25-01-DEV,Business Development,SGA
```

**v3.0 Notes:**
- THS codes are auto-detected; only add to config if you need to:
  - Override default SGA pool assignment
  - Provide custom description
- Non-THS cost centers must be in config

### 10.2 config/category_mapping.csv

Maps Pro Forma section headers → analysis categories:
```csv
pro_forma_category,analysis_category
BEH - Behavioral Health,Next Gen Advisory
PAD - Payment Design & Analytics,Data
MAR - Market Analytics,Data
WWB - Workplace Well-Being,Wellness
CMH - Community Health,Next Gen Advisory
```

### 10.3 config/pnl_account_tags.csv

Maps P&L accounts to pools:
```csv
match_type,pattern,bucket,notes
exact,Data Services,DATA,Primary data infrastructure
exact,Well-being Coaches,WORKPLACE,Wellness coaching
exact,Mindful Learning,WORKPLACE,Wellness vendor
contains,Payroll,NIL,Already in hourly rates
contains,Health Insurance,NIL,Already in hourly rates
```

Match types:
- `exact` - Case-insensitive exact match
- `contains` - Substring match (case-insensitive)
- `regex` - Regular expression

Buckets:
- `DATA` - Data Infrastructure pool
- `WORKPLACE` - Wellness pool
- `NIL` - Excluded from allocation (already reflected)
- `SGA` - Default catch-all

### 10.4 config/settings.json

Minimum recommended:
```json
{
  "hours_per_week": 50,
  "weeks_per_year": 52,
  "months_per_year": 12,
  "expected_hours_per_month": 216.67,
  "rounding": 2,
  "include_cost_center_overhead_in_sga_pool": true
}
```

---

## 11. Error Handling

### 11.1 Missing compensation rates

**Behavior:**
- FAIL processing
- List all staff without rates
- Provide clear error message
- Direct user to add missing staff to compensation file

**Example error:**
```
ERROR: Missing compensation rates for the following staff:
- Smith, John
- Doe, Jane

Please add these staff members to the compensation file with hourly rates.
```

### 11.2 Classification conflicts

**Scenario 1: Revenue + Manual Cost Center**
```
ERROR: Classification conflict for 'THS-25-01-ACH'
Code appears as both:
  - Revenue Center (Pro Forma: $5,000)
  - Cost Center (config/cost_centers.csv)

Please remove from cost_centers.csv if this is a revenue project.
```

**Scenario 2: Allocation tag conflict**
```
ERROR: Allocation tag conflict for 'BEH-24-01-NYS'
Multiple rows in Pro Forma with conflicting tags:
  - Row 15: Data
  - Row 18: Wellness

Please fix Pro Forma - each code should have only one allocation tag.
```

### 11.3 NaN handling

**Hours detail:**
- If staff has no compensation record → hourly_cost = 0.0, labor_cost = 0.0
- Log warning but don't crash

**Expense detail:**
- If notes/description is NaN → convert to None/null for JSON
- Amount must be numeric (fail if not)

---

## Appendix A: Change Log

### v3.0 (December 31, 2025) - Production Release
- **Web Dashboard**: Interactive Flask application with drill-down
- **Margin Visualization**: Chart.js horizontal bar chart
- **THS Auto-Classification**: Automatic cost center detection for THS- prefixed codes
- **Drill-Down**: Hours, expenses, and allocation calculation transparency
- **DataTables**: Sortable, searchable tables with dual CSV export
- **Active/Inactive Toggles**: Cleaner interface hiding zero-activity projects
- **API Endpoints**: JSON endpoints for project detail data
- **Enhanced Validation**: NaN handling, better error messages
- **Methodology Tab**: Transparent documentation of calculations

### v2.0 (December 30, 2025)
- Updated Pro Forma rules: Column A can contain `Data` / `Wellness` allocation tags; it is not always blank.
- Added explicit support for duplicate contract codes in Pro Forma via aggregation.
- Clarified compensation ingestion: support reading `Base Cost Per Hour` directly (preferred) or computing it (fallback).
- Expanded P&L logic from "two-row extraction" to a config-driven account tagging approach for SG&A / Data / Workplace / Nil buckets.
- Elevated missing compensation rates from WARN to FAIL.

### v1.0 (December 2025)
- Initial CLI-only implementation
- Basic five-file ingestion
- Pro-rata overhead allocation
- CSV outputs
- Validation report
