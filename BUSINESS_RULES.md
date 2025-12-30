# Business Rules: Monthly Performance Analysis System

**Version:** 3.0  
**Date:** December 30, 2025  
**Owner:** Third Horizon  
**Primary author:** Topher (based on David’s tracker + walkthrough)

---

## 1. Overview

### 1.1 Purpose

This system produces a repeatable **monthly performance package** by:
- ingesting five monthly source files (Pro Forma, Compensation, Harvest Hours, Harvest Expenses, P&L),
- normalizing them to a shared **contract code** key, and
- generating a project-level “cost waterfall” (revenue → direct costs → allocated overhead → margin).

### 1.2 Core principle

This is a **deterministic rules engine**. Given the same inputs and settings, it must always produce the same outputs, with a validation trail that makes results auditable.

### 1.3 What the system must answer

For each **revenue-bearing contract code** in the month:
- How much revenue (accrual basis) did we recognize?
- How much labor cost did we incur (hours × fully-loaded hourly rates)?
- How much **non-reimbursable** expense did we incur?
- How much overhead should we allocate:
  - **SG&A** (broad overhead allocated across all revenue),
  - **Data Infrastructure** (allocated only to “Data” projects),
  - **Workplace Well-being** (allocated only to “Wellness” projects)?
- What are the resulting margin dollars and margin %?

In addition, the system reports:
- **Cost center activity** (internal overhead time and expenses tracked in Harvest), and
- **Non-revenue client activity** (codes with work but no revenue in the month).

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
- Normalize repeated spaces and invisible characters (e.g., non‑breaking spaces)
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

The engine must support this “Column A tag” behavior (it is NOT always blank).

#### 3.1.3 Category sections (BEH / PAD / MAR / WWB / CMH)

The Pro Forma also groups rows under section headers such as:
- BEH (Behavioral Health)
- PAD (Payment Design & Analytics)
- MAR (Market Analytics)
- WWB (Workplace Well-Being)
- CMH (Community Health)

These section headers are used to assign an **analysis category** (Data / Wellness / Next Gen Advisory) via mapping.

> Important: “Analysis category” is used for reporting; “Allocation tag” determines which overhead pools apply.
> They usually align (PAD+MAR → Data, WWB → Wellness), but the system should not assume they are identical.

#### 3.1.4 Duplicate contract codes in Pro Forma

The Pro Forma can contain **multiple rows with the same contract code** (e.g., split by sub-workstream).
The engine must:
- aggregate revenue by contract code for the month,
- carry project name as “first non-empty” (or concatenate names in a separate field),
- carry allocation tag using priority rules:
  1. If any row for the code is tagged `Data`, allocation_tag = Data (unless any row is tagged Wellness → conflict)
  2. Else if any row is tagged `Wellness`, allocation_tag = Wellness
  3. Else allocation_tag = blank/None

If a code has both `Data` and `Wellness` tags across rows: **FAIL** (human must fix the Pro Forma).

#### 3.1.5 Revenue center rules

For the selected month:
- **Revenue Center** = contract code with aggregated revenue > 0
- **Zero-revenue Pro Forma code** = contract code present but revenue = 0 (tracked for integrity checks)

Zero-revenue codes are “parked” (not included in the revenue-center table), but:
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

**Strategy A (Preferred): Read “Base Cost Per Hour” directly**
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

**Export:** Harvest “Detailed Time Report”  
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

**Export:** Harvest “Detailed Expenses Report”  
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
3. **P&L Payroll / “Nil” bucket** (for reconciliation only; not allocated)  
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
   - In `config/cost_centers.csv`
3. **Non-Revenue Clients**
   - Has hours/expenses in month
   - Not a Revenue Center
   - Not a Cost Center

### 4.2 Conflict rule (critical)

If a Project Code is both:
- a Revenue Center for the month **and**
- listed as a Cost Center

→ **FAIL** (business must decide which it is).

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
   - plus optional “Harvest Cost Center Overhead” if configured to be included
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
- non_reimbursable_expense
- sga_allocation
- data_infrastructure_allocation
- workplace_wellbeing_allocation
- margin_dollars
- margin_percent

### 7.2 cost_centers.csv

One row per cost center code:

- cost_center_code
- description
- labor_cost
- non_reimbursable_expense
- total_cost
- notes (optional)

### 7.3 non_revenue_clients.csv

One row per non-revenue client code:

- project_code
- project_name (from Harvest if present)
- labor_cost
- non_reimbursable_expense
- total_cost

### 7.4 validation_report.md (or .txt)

A human-readable validation summary:
- PASS / WARN / FAIL entries
- key totals and reconciliation checks
- list of unmapped P&L accounts and unmapped Harvest codes

---

## 8. Validation Rules

### 8.1 Critical (FAIL)

- Pro Forma sheet missing
- Month column not found
- No project codes found
- Allocation-tag conflict (both Data and Wellness for same code)
- Any Harvest Hours staff missing compensation rate
- Code is both Revenue Center and Cost Center
- P&L Total column not found and cannot infer numeric total column
- Required columns missing in Harvest exports

### 8.2 Warnings (WARN)

- Harvest rows outside month (excluded)
- Unknown / blank Billable values in expenses (included conservatively)
- Pro Forma code has revenue but no Harvest hours (valid but flagged)
- Harvest code appears but not in Pro Forma and not in cost centers (treated as Non-Revenue Client)
- Pro Forma project names missing
- P&L account not matched by tagging rules (defaults to SGA)

### 8.3 Reconciliation checks

- Sum(project revenues) == Pro Forma base revenue (±$0.01)
- Σ SG&A allocations == SG&A pool (±$0.01)
- Σ Data allocations == Data pool (±$0.01)
- Σ Workplace allocations == Workplace pool (±$0.01)

---

## 9. Configuration

### 9.1 config/cost_centers.csv

Minimum:
```csv
code,description
THS-25-01-DEV,Business Development
THS-25-01-BAD,Business Administration
THS-25-01-MTG,Internal Meetings
...
```

Recommended extension (optional):
```csv
code,description,pool
THS-25-01-SAD,Starset Dev Cost,DATA
THS-25-01-DEV,Business Development,SGA
...
```

### 9.2 config/category_mapping.csv

Maps Pro Forma section headers → analysis categories:
```csv
pro_forma_category,analysis_category
BEH - Behavioral Health,Next Gen Advisory
PAD - Payment Design & Analytics,Data
MAR - Market Analytics,Data
WWB - Workplace Well-Being,Wellness
CMH - Community Health,Next Gen Advisory
```

### 9.3 config/settings.json

Minimum recommended:
```json
{
  "hours_per_week": 50,
  "weeks_per_year": 52,
  "months_per_year": 12,
  "rounding": 2,
  "include_cost_center_overhead_in_sga_pool": true
}
```

---

## Appendix A: Change Log

### v3.0 (December 30, 2025)
- Updated Pro Forma rules: Column A can contain `Data` / `Wellness` allocation tags; it is not always blank.
- Added explicit support for duplicate contract codes in Pro Forma via aggregation.
- Clarified compensation ingestion: support reading `Base Cost Per Hour` directly (preferred) or computing it (fallback).
- Expanded P&L logic from “two-row extraction” to a config-driven account tagging approach for SG&A / Data / Workplace / Nil buckets.
- Elevated missing compensation rates from WARN to FAIL.

