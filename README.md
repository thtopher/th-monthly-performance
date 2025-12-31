# Monthly Performance Analysis System

**Version:** 3.0  
**Date:** December 30, 2025  

This repository contains a deterministic monthly analysis engine for Third Horizon that:
- ingests monthly exports (Pro Forma + Harvest (Hours, Expenses) + Compensation + P&L),
- joins everything by **contract code**,
- produces project-level margins and overhead allocations.

---

## What you upload each month

1. Pro Forma (accrual revenue by contract code)
2. Compensation (fully-loaded cost per hour by staff)
3. Harvest Hours (time entries by contract code)
4. Harvest Expenses (expenses by contract code; reimbursable filtering)
5. P&L (overhead buckets: SG&A, Data Infrastructure, Workplace Well-being, Nil)

---

## Core logic (high level)

1. Build the monthly **Revenue Centers** table from Pro Forma (revenue > 0).
2. Compute **direct labor** from Harvest Hours × fully-loaded hourly rates.
3. Compute **direct non-reimbursable expenses** from Harvest Expenses (exclude Billable=Yes).
4. Build overhead pools from P&L (and optional Harvest cost center pools).
5. Allocate overhead pro-rata by revenue:
   - SG&A → across all revenue centers
   - Data Infrastructure → across Data-tagged revenue centers only
   - Workplace Well-being → across Wellness-tagged revenue centers only
6. Compute margin dollars and margin %.

---

## File preparation guide

### Pro Forma

**Sheet:** `PRO FORMA 2025`

**Structure:**
- **Column A**: Allocation tags (`Data`, `Wellness`, or blank)
- **Column B**: Project names or section headers
- **Column C**: Contract codes (blank for section headers)
- **Month columns**: Jan through Dec (engine detects dynamically)

**Allocation Tags (Column A):**
- `Data` → Eligible for Data Infrastructure allocation
- `Wellness` → Eligible for Workplace Well-being allocation
- blank → Receives SG&A only

**Duplicate Contract Codes:**
The same contract code may appear on multiple rows (e.g., split by sub-workstream).

The engine aggregates them using these rules:
1. **Revenue**: Sum all rows for that code
2. **Allocation tag**:
   - If any row tagged `Data` → code is Data-tagged
   - Else if any row tagged `Wellness` → code is Wellness-tagged
   - If both Data AND Wellness appear → **FAIL** (conflict)
3. **Project name**: First non-empty value

**Example:**
| Column A | Column B | Column C | Nov |
|----------|----------|----------|-----|
| | BEH - Behavioral Health | | 324,048 |
| | New Hampshire CF | BEH-25-01-NHCF | 3,125 |
| Data | NYS - OASAS Stream 1 | BEH-24-01-NYS | 50,000 |
| Data | NYS - OASAS Stream 2 | BEH-24-01-NYS | 43,809 |

Result: `BEH-24-01-NYS` has aggregated revenue of $93,809 with allocation_tag = `Data`

### Compensation

**Strategy A (Preferred):** Read hourly cost directly
- Required columns:
  - `Last Name`
  - `Base Cost Per Hour`
- Engine uses the values as-is

**Strategy B (Fallback):** Compute hourly cost from components
- If `Base Cost Per Hour` is missing, engine computes from:
  - `Total` (monthly fully-loaded cost), OR
  - Sum of components: Base Compensation + Company Taxes Paid + ICHRA Contribution + 401k Match + Executive Assistant + Well Being Card + Travel & Expenses

**Computation:**
```
Expected Hours Per Month = (50 hours/week × 52 weeks/year) ÷ 12 months
                         = 216.67 hours/month

Hourly Cost = Fully-Loaded Monthly Cost ÷ 216.67
```

**Example (Strategy B):**
| Last Name | Base | Taxes | ICHRA | 401k | Assistant | Wellbeing | Travel | → Hourly Cost |
|-----------|------|-------|-------|------|-----------|-----------|--------|---------------|
| Smith | $12,500 | $1,875 | $900 | $625 | $500 | $100 | $500 | $81.48/hr |

**Validation:**
- `Last Name` must be unique (otherwise engine fails)
- All staff in Harvest Hours must have a matching compensation record (critical validation)

### Harvest Hours

Export from Harvest: **Detailed Time Report**

Required fields (header names vary):
- Date
- Project Code
- Hours
- Last Name (and optionally First Name)

### Harvest Expenses

Export from Harvest: **Detailed Expenses Report**

Required fields:
- Project Code
- Amount
- Billable

Filtering rule:
- Billable = Yes → reimbursable (excluded)
- Billable = No → included
- blank/unrecognized → warn + included (conservative)

### P&L

Sheet: `IncomeStatement`

The engine reads the **Total** column and buckets accounts into:
- DATA (e.g., Data Services)
- WORKPLACE (e.g., Well-being Coaches, Mindful Learning)
- NIL (payroll-related, already reflected in hourly labor rates)
- SGA (everything else not matched; default)

Account bucketing is configured in `config/pnl_account_tags.csv`.

---

## Outputs

After a successful run, the system writes:

- `outputs/YYYY-MM/revenue_centers.csv`
- `outputs/YYYY-MM/cost_centers.csv`
- `outputs/YYYY-MM/non_revenue_clients.csv`
- `outputs/YYYY-MM/validation_report.md`

---

## Project Structure

```
th-monthly-performance/
├── run_analysis.py             # CLI entry point
├── requirements.txt            # Python dependencies
├── .gitignore                  # Exclude outputs, *.xlsx
├── README.md                   # This file
├── PROJECT_PLAN.md            # Implementation plan
├── BUSINESS_RULES.md          # Technical specification
├── config/                     # Configuration files (editable by team)
│   ├── cost_centers.csv       # Cost center definitions
│   ├── category_mapping.csv   # Pro Forma section → analysis category
│   ├── pnl_account_tags.csv   # P&L account → pool bucketing
│   └── settings.json          # App settings (216.67 hours, etc.)
├── analysis/                   # Core business logic
│   ├── __init__.py
│   ├── loaders.py             # File loading (Pro Forma, Comp, Hours, Expenses, P&L)
│   ├── computations.py        # Labor cost, expense cost calculations
│   ├── allocations.py         # SG&A, Data, Wellbeing pro-rata allocation
│   ├── classification.py      # Revenue/Cost/Non-Revenue classification
│   ├── validators.py          # All validation checks
│   └── outputs.py             # CSV generation + validation report
├── tests/                      # Test suite
│   ├── fixtures/              # Demo files (November 2025)
│   ├── test_loaders.py
│   ├── test_computations.py
│   └── test_integration.py
├── outputs/                    # Generated reports (gitignored)
│   └── [Month][Year]/
│       ├── revenue_centers.csv
│       ├── cost_centers.csv
│       ├── non_revenue_clients.csv
│       └── validation_report.md
└── demo_files/                 # Sample data for testing
    ├── (Proforma)November2025.xlsx
    ├── (Compensation)November2025.xlsx
    ├── (HarvestHours)November2025.xlsx
    ├── (HarvestExpenses)November2025.xlsx
    └── (P&L)November2025.xlsx
```

**Future phases:** Add `app.py` and `web/` directory for Flask interface

---

## Configuration

### Cost centers

Edit `config/cost_centers.csv`:
```csv
code,description
THS-25-01-DEV,Business Development
THS-25-01-BAD,Business Administration
THS-25-01-MTG,Internal Meetings
...
```

### Pro Forma category mapping (for reporting)

Edit `config/category_mapping.csv`:
```csv
pro_forma_category,analysis_category
BEH - Behavioral Health,Next Gen Advisory
PAD - Payment Design & Analytics,Data
MAR - Market Analytics,Data
WWB - Workplace Well-Being,Wellness
CMH - Community Health,Next Gen Advisory
```

### P&L account tags

Edit `config/pnl_account_tags.csv` to control which P&L accounts go to which pool.

---

## Installation

```bash
# Clone the repository
git clone git@github.com:thtopher/th-monthly-performance.git
cd th-monthly-performance

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## Usage

### CLI (Primary Interface - MVP)

```bash
python run_analysis.py \
  --month "November2025" \
  --proforma "(Proforma)November2025.xlsx" \
  --compensation "(Compensation)November2025.xlsx" \
  --hours "(HarvestHours)November2025.xlsx" \
  --expenses "(HarvestExpenses)November2025.xlsx" \
  --pl "(P&L)November2025.xlsx" \
  --output-dir "./outputs/November2025"
```

**Arguments:**
- `--month` - Month name and year (e.g., "November2025")
- `--proforma` - Path to Pro Forma file
- `--compensation` - Path to Compensation file
- `--hours` - Path to Harvest Hours file
- `--expenses` - Path to Harvest Expenses file
- `--pl` - Path to P&L file
- `--output-dir` - Output directory (default: `./outputs`)

**Console Output:**

```
[INFO] Loading files...
[INFO] ✓ Pro Forma: 47 projects, 5 categories
[INFO] ✓ Detected allocation tags: 25 Data, 5 Wellness, 17 untagged
[INFO] ✓ Aggregated 3 duplicate contract codes
[INFO] Computing fully-loaded hourly costs...
[INFO] ✓ Strategy A: Read 'Base Cost Per Hour' for 34 staff
[INFO] Filtering non-reimbursable expenses...
[INFO] ✓ Non-reimbursable: $20,000 (Reimbursable: $25,000 excluded)
[INFO] Classifying projects...
[INFO] ✓ Revenue Centers: 47, Cost Centers: 15, Non-Revenue Clients: 3
[INFO] Loading P&L and bucketing accounts...
[INFO] ✓ Matched 45 accounts using config/pnl_account_tags.csv
[WARN] 3 unmatched accounts defaulted to SG&A (see validation report)
[INFO] Allocating overhead...
[INFO] ✓ SG&A: $200,000 allocated across 47 projects
[INFO] ✓ Data Infrastructure: $155,000 allocated to 25 Data-tagged projects
[INFO] ✓ Wellbeing: $1,600 allocated to 5 Wellness-tagged projects
[INFO] Validating allocations...
[INFO] ✓ All pool allocations reconcile (±$0.01)
[INFO] Generating outputs...
[SUCCESS] Processing complete!
[INFO] Outputs saved to: ./outputs/November2025/
[INFO] Review validation_report.md for detailed audit trail
```

### Web Interface (Future - Optional)

```bash
python app.py
# Open http://localhost:5000/upload
```

---

## Monthly Operational Workflow

**Week 3 of each month:**

1. **Aisha uploads:**
   - Compensation file (updated monthly rates)
   - P&L file (organizational overhead)

2. **Jordana uploads:**
   - Harvest Hours (time tracking export)
   - Harvest Expenses (expense export)

3. **Greg uploads:**
   - Pro Forma (revenue projections)

4. **Run analysis:**
   ```bash
   python run_analysis.py --month "[Month][Year]" [file paths]
   ```

5. **Review outputs:**
   - Check `validation_report.md` for warnings and errors
   - Review `revenue_centers.csv` for margin analysis
   - Review `non_revenue_clients.csv` for exceptions
   - Compare against David's spreadsheet (first 2-3 months for validation)

6. **Update configurations (as needed):**
   - New cost center → Edit `config/cost_centers.csv`
   - New category → Edit `config/category_mapping.csv`
   - P&L account changes → Edit `config/pnl_account_tags.csv`

---

## Design constraints

- **CLI-first:** Auditable, reproducible, perfect for automation
- **Deterministic:** No "guessing" - same inputs always produce same outputs
- **Strong validation:** Missing hourly rates is a hard failure
- **Config-driven:** Mappings update without code changes (cost centers, P&L account buckets)

