# TH Monthly Performance Analysis System

**Version:** 3.0 (Complete)
**Date:** December 31, 2025
**Status:** Production Ready

A complete monthly analysis system for Third Horizon that ingests financial data from multiple sources (Pro Forma, Harvest, Compensation, P&L) and produces comprehensive project-level performance metrics with an interactive web dashboard.

---

## What's New in v3.0

- **Interactive Web Dashboard** with drill-down capabilities
- **Margin Visualization** - horizontal bar chart showing contribution by project
- **THS Code Auto-Classification** - internal activities automatically identified
- **Live Data Tables** - sortable, searchable, with CSV export
- **Current View Downloads** - export respects your sorting and filtering
- **Active/Inactive Toggles** - clean interface hiding zero-activity projects
- **Allocation Transparency** - see exactly how overhead was calculated
- **Mobile-Responsive Design** - works on tablets and phones

---

## Quick Start

### Installation

```bash
# Clone the repository
cd /path/to/TH\ Monthly\ Performance\ Analysis

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Run the Web Interface

```bash
python app.py
# Open http://localhost:5000 in your browser
```

### Monthly Workflow

1. **Upload Files** (via web interface or place in folder):
   - Pro Forma (`(Proforma)[Month][Year].xlsx`)
   - Compensation (`(Compensation)[Month][Year].xlsx`)
   - Harvest Hours (`(HarvestHours)[Month][Year].xlsx`)
   - Harvest Expenses (`(HarvestExpenses)[Month][Year].xlsx`)
   - P&L (`(P&L)[Month][Year].xlsx`)

2. **Run Analysis** - Click "Analyze" button on web interface

3. **Review Results** - Interactive dashboard with:
   - **Revenue Centers** - Complete P&L with margins
   - **Margin Analysis** - Visual chart (sorted highest to lowest)
   - **Cost Centers** - Internal overhead tracking
   - **Non-Revenue Clients** - Client work without revenue
   - **Validation Report** - Audit trail and reconciliation checks
   - **Methodology** - Transparent calculation documentation

4. **Download CSVs** - Export full data or current filtered view

---

## System Overview

### Core Functionality

The system performs a **complete cost waterfall analysis**:

```
Revenue (Pro Forma)
  - Direct Labor (Harvest Hours × Compensation Rates)
  - Direct Expenses (Non-reimbursable from Harvest)
  - SG&A Allocation (Pro-rata by revenue)
  - Data Infrastructure Allocation (Data-tagged projects only)
  - Wellness Allocation (Wellness-tagged projects only)
  = Final Contribution Margin
```

### Key Features

#### 1. Intelligent Classification

Every project code is automatically classified into exactly one category:

- **Revenue Centers**: Projects with revenue in Pro Forma
- **Cost Centers**: Internal overhead activities (from config + THS- auto-detection)
- **Non-Revenue Clients**: Activity logged but no revenue (e.g., proposals, pro bono)

**NEW in v3.0:** Any code starting with `THS-` is automatically classified as a cost center (unless it has revenue, then it's a revenue center). No manual configuration needed.

#### 2. Overhead Pool Allocation

Three pools allocated proportionally by revenue:

- **SG&A**: Allocated to ALL revenue centers
- **Data Infrastructure**: Allocated only to Data-tagged projects
- **Wellness**: Allocated only to Wellness-tagged projects

All allocations reconcile to pool totals (±$0.01 tolerance).

#### 3. Interactive Dashboard Features

**Drill-Down Tables:**
- Click any project to see:
  - Hours detail by person (with rates and costs)
  - Expense detail by line item
  - Allocation calculation walkthrough (shows exact formula)

**Smart Sorting:**
- All tables sortable by any column
- Default sorts optimized for analysis
- "Download Current View" preserves your sorting

**Active/Inactive Projects:**
- Zero-activity projects hidden by default
- Toggle button to show/hide inactive items
- Keeps dashboard focused on what matters

**Margin Visualization:**
- Horizontal bar chart sorted by margin contribution
- Green bars = positive margin
- Red bars = negative margin
- Hover for exact values

#### 4. Validation & Audit Trail

Every analysis includes comprehensive checks:
- Revenue totals reconcile to Pro Forma
- All staff have compensation rates
- Pool allocations sum correctly
- No classification conflicts
- P&L account bucketing transparency

**validation_report.md** provides complete audit trail.

---

## File Preparation Guide

### Pro Forma

**Sheet:** `PRO FORMA 2025`

**Structure:**
- **Column A**: Allocation tags (`Data`, `Wellness`, or blank)
- **Column B**: Project names
- **Column C**: Contract codes
- **Month columns**: Jan through Dec

**Allocation Tags (Column A):**
- `Data` → Receives Data Infrastructure allocation
- `Wellness` → Receives Wellness allocation
- blank → Receives SG&A only

**Duplicate Contract Codes:**
The same code may appear on multiple rows (e.g., split by sub-workstream). The engine aggregates by:
1. **Revenue**: Sum all rows
2. **Allocation tag**: If any row = `Data` → code is Data-tagged (conflict if both Data AND Wellness)
3. **Project name**: First non-empty value

### Compensation

**Strategies:**

**Strategy A (Preferred):** Direct hourly cost
- Required: `Last Name`, `Base Cost Per Hour`

**Strategy B (Fallback):** Computed from components
- Sums: Base + Taxes + ICHRA + 401k + Assistant + Wellbeing + Travel
- Divides by 216.67 hours/month (50 hrs/week × 52 weeks / 12 months)

**Validation:**
- `Last Name` must be unique
- All Harvest staff must have compensation record (CRITICAL)

### Harvest Hours

**Export:** Detailed Time Report

**Required fields:**
- Date (or Spent Date)
- Project Code
- Hours
- Last Name

### Harvest Expenses

**Export:** Detailed Expenses Report

**Required fields:**
- Project Code
- Amount
- Billable

**Filtering:**
- `Billable = Yes` → Reimbursable → EXCLUDED
- `Billable = No` → Non-reimbursable → INCLUDED
- blank/unknown → WARN + INCLUDED (conservative)

### P&L

**Sheet:** `IncomeStatement`

The system reads the **Total Amount** column and buckets accounts into pools:
- **DATA**: Data Services
- **WORKPLACE**: Well-being Coaches, Mindful Learning
- **NIL**: Payroll expenses (already in hourly rates)
- **SG&A**: Everything else (default)

Account bucketing configured in `config/pnl_account_tags.csv`.

---

## Dashboard Interface

### Navigation Tabs

1. **Revenue Centers** - Full P&L by project
   - Revenue, labor, expenses, allocations, margins
   - Drill down for hours/expense detail
   - See allocation calculations
   - Sort and filter as needed
   - Download full CSV or current view

2. **Margin Analysis** - Visual chart
   - Horizontal bars sorted highest to lowest
   - Green = positive margin
   - Red = negative margin
   - Shows project name + code
   - Hover for exact values

3. **Cost Centers** - Internal overhead
   - Labor and expense costs by center
   - Organized by pool (SG&A, Data, Wellness)
   - Active/inactive toggle
   - Drill down for detail

4. **Non-Revenue Clients** - Exceptions
   - Client work without revenue
   - Proposals, pro bono, development
   - Helps identify missing Pro Forma entries

5. **Validation Report** - Audit trail
   - All reconciliation checks
   - Warnings and notices
   - Unmatched P&L accounts
   - Data quality issues

6. **Methodology** - Transparency
   - ETL process documentation
   - Classification logic explained
   - Pool calculation walkthrough
   - Allocation formulas with examples

### Key Metrics (Top of Dashboard)

- **Total Revenue** - Sum from Pro Forma
- **Final Contribution Margin** - After all allocations
- **Overall Margin %** - Company-wide margin rate

Plus detailed cost breakdown showing percentages of revenue.

---

## Project Structure

```
TH Monthly Performance Analysis/
├── app.py                      # Flask web application
├── run_analysis.py             # CLI entry point (legacy)
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── BUSINESS_RULES.md          # Technical specification
├── PROJECT_PLAN.md            # Implementation plan
├── config/                     # Configuration files
│   ├── cost_centers.csv       # Cost center definitions
│   ├── category_mapping.csv   # Pro Forma → category mapping
│   ├── pnl_account_tags.csv   # P&L account → pool bucketing
│   └── settings.json          # App settings
├── analysis/                   # Core business logic
│   ├── loaders.py             # File loading
│   ├── computations.py        # Cost calculations
│   ├── allocations.py         # Overhead allocation
│   ├── classification.py      # Project classification
│   ├── validators.py          # Validation checks
│   └── outputs.py             # CSV generation
├── templates/                  # Flask templates
│   ├── base.html              # Base layout
│   ├── index.html             # Upload form
│   └── results.html           # Interactive dashboard
├── static/                     # CSS and assets
│   └── style.css              # Dashboard styling
├── outputs/                    # Generated reports
│   └── [Month][Year]/
│       ├── revenue_centers.csv
│       ├── cost_centers.csv
│       ├── non_revenue_clients.csv
│       ├── validation_report.md
│       └── _pools.json        # Allocation detail
└── tests/                      # Test suite
    ├── fixtures/
    ├── test_loaders.py
    ├── test_computations.py
    └── test_integration.py
```

---

## Configuration

### Cost Centers

Edit `config/cost_centers.csv`:

```csv
contract_code,description,pool
THS-25-01-DEV,Business Development,SGA
THS-25-01-BAD,Business Administration,SGA
THS-25-01-MTG,Internal Meetings,SGA
THS-25-01-SAD,Starset Dev Cost,DATA
THS-25-01-OOO,Out of Office,SGA
```

**Note:** THS- prefixed codes are auto-detected. You only need to add them to config if you want to specify a non-SGA pool or custom description.

### Pro Forma Category Mapping

Edit `config/category_mapping.csv`:

```csv
pro_forma_category,analysis_category
BEH - Behavioral Health,Next Gen Advisory
PAD - Payment Design & Analytics,Data
MAR - Market Analytics,Data
WWB - Workplace Well-Being,Wellness
CMH - Community Health,Next Gen Advisory
```

### P&L Account Bucketing

Edit `config/pnl_account_tags.csv` to control which P&L accounts go to which pool:

```csv
match_type,pattern,bucket,notes
exact,Data Services,DATA,Primary data infrastructure
exact,Well-being Coaches,WORKPLACE,Wellness coaching
exact,Mindful Learning,WORKPLACE,Wellness vendor
contains,Payroll,NIL,Already in hourly rates
contains,Health Insurance,NIL,Already in hourly rates
```

Match types:
- `exact` - Exact string match (case-insensitive)
- `contains` - Substring match
- `regex` - Regular expression pattern

Buckets:
- `DATA` - Data Infrastructure pool
- `WORKPLACE` - Wellness pool
- `NIL` - Excluded (already reflected in costs)
- `SGA` - Default (anything unmatched goes here)

---

## API Endpoints

### Flask Routes

**GET /**
- Upload form

**POST /upload**
- Upload 5 files
- Run analysis
- Redirect to results

**GET /results**
- Show last analysis results

**POST /analyze**
- Re-run analysis on uploaded files
- Useful for config changes

**GET /download/{month}/{filename}**
- Download CSV outputs

**GET /api/project_details/{type}/{code}**
- Get drill-down data (hours, expenses, allocations)
- Used by JavaScript for expandable rows

---

## Validation Rules

### Critical Failures (Processing Stops)

- Pro Forma sheet missing
- Month column not found
- Allocation tag conflict (code has both Data AND Wellness)
- Harvest staff missing compensation rate
- Code is both Revenue Center AND Cost Center (in config)
- P&L Total column missing
- Required columns missing

### Warnings (Logged but Processing Continues)

- Harvest rows outside selected month (excluded)
- Unknown Billable values (conservatively included)
- Pro Forma code with revenue but no hours
- Harvest code not in Pro Forma (becomes Non-Revenue Client)
- P&L account unmatched (defaults to SG&A)
- Missing project names

### Reconciliation Checks

All checks must pass within ±$0.01:
- Sum(project revenues) = Pro Forma base revenue
- Sum(SG&A allocations) = SG&A pool
- Sum(Data allocations) = Data pool
- Sum(Wellness allocations) = Wellness pool

---

## Advanced Features

### THS Code Auto-Classification

Any contract code starting with `THS-` is automatically treated as internal overhead:

**Logic:**
1. If code has revenue in Pro Forma → Revenue Center (THS projects CAN be revenue-generating)
2. Else if code starts with `THS-` → Cost Center (auto-classified)
3. Else if code in cost_centers.csv → Cost Center (manual config)
4. Else if code has activity → Non-Revenue Client

**Benefits:**
- Zero manual maintenance for new internal codes
- Self-documenting (THS = Third Horizon internal)
- Revenue always takes precedence (correct treatment)

**Default Pool:** Auto-classified THS codes default to SG&A pool unless specified in config.

### Drill-Down Details

Click any expandable row (▶) to see:

**Hours Detail:**
- Staff person
- Hours worked
- Hourly rate
- Total cost
- Sortable by any column

**Expense Detail:**
- Date
- Description
- Amount
- Sortable by amount (default)

**Allocation Calculations:**
Side-by-side boxes showing:

- **SG&A**: Total pool, total revenue, project share %, formula, result
- **Data**: (If tagged) Data pool, Data revenue, project share %, formula, result
- **Wellness**: (If tagged) Wellness pool, Wellness revenue, project share %, formula, result

All formulas shown with actual numbers for transparency.

### Download Options

Two download buttons on each table:

1. **Download Full CSV** - Complete analysis output
   - Original file from analysis run
   - All projects, original sort order

2. **Download Current View CSV** - Filtered/sorted view
   - Respects your current sorting
   - Respects your search filters
   - Respects pagination (exports all pages matching filter)

---

## Technical Design

### Design Principles

1. **Deterministic** - Same inputs always produce same outputs
2. **Auditable** - Complete validation trail
3. **Config-Driven** - No code changes for new cost centers or P&L accounts
4. **Fail-Fast** - Critical validation errors stop processing
5. **Transparent** - Show all calculations and formulas

### Technology Stack

**Backend:**
- Python 3.13
- Flask (web framework)
- Pandas (data processing)
- OpenPyXL (Excel reading)

**Frontend:**
- Jinja2 templates
- jQuery
- DataTables.js (interactive tables)
- Chart.js (margin visualization)
- Vanilla JavaScript (drill-down functionality)

**Data Flow:**

```
Upload Files
    ↓
Load & Normalize (analysis/loaders.py)
    ↓
Classify Projects (analysis/classification.py)
    ↓
Calculate Direct Costs (analysis/computations.py)
    ↓
Allocate Overhead Pools (analysis/allocations.py)
    ↓
Validate & Generate Outputs (analysis/outputs.py)
    ↓
Render Interactive Dashboard (templates/results.html)
```

### Error Handling

- Missing files → User-friendly error message
- Invalid Excel format → Detailed error with file/sheet name
- Missing compensation → Lists all staff without rates
- Validation failures → Comprehensive report with line numbers
- Classification conflicts → Exact code and conflict type

---

## Troubleshooting

### Common Issues

**"Missing compensation rate for staff: [names]"**
- **Cause**: Staff worked hours but not in compensation file
- **Fix**: Add staff to compensation file or remove their hours

**"Classification conflict for code X"**
- **Cause**: Code appears in Pro Forma (revenue) AND cost_centers.csv
- **Fix**: Decide if it's a revenue project or cost center, update config accordingly

**"Allocation tag conflict for code Y"**
- **Cause**: Same code has rows tagged both Data AND Wellness
- **Fix**: Fix Pro Forma - code should have only one allocation tag

**"Pool allocation doesn't reconcile"**
- **Cause**: Rounding error exceeded ±$0.01 tolerance
- **Fix**: This should never happen - report as bug

**"P&L Total column not found"**
- **Cause**: P&L sheet structure changed
- **Fix**: Ensure sheet has "Total" column header or rightmost column is numeric

### Debug Mode

Set Flask to debug mode for detailed error traces:

```bash
export FLASK_ENV=development
python app.py
```

### Validation Report

Always check `outputs/[Month]/validation_report.md` for:
- Warnings about data quality
- Unmatched P&L accounts
- Excluded Harvest rows
- Revenue reconciliation details

---

## Version History

### v3.0 (December 31, 2025) - Production Release
- Interactive web dashboard with Flask
- Margin visualization chart (Chart.js)
- THS code auto-classification
- Drill-down functionality for hours and expenses
- Allocation calculation transparency
- DataTables integration with sorting and filtering
- Download current view CSV
- Active/inactive project toggles
- Mobile-responsive design
- Comprehensive methodology documentation

### v2.0 (December 30, 2025) - Enhanced CLI
- P&L account tagging system
- Duplicate contract code aggregation
- Column A allocation tags support
- Compensation Strategy A/B support
- Enhanced validation engine
- Cost center pool classification

### v1.0 (December 2025) - Initial CLI
- Basic CLI interface
- Five-file ingestion
- Pro-rata overhead allocation
- CSV outputs
- Validation report

---

## Support & Maintenance

**Configuration Updates:**
- Cost centers: Edit `config/cost_centers.csv`
- P&L accounts: Edit `config/pnl_account_tags.csv`
- Category mappings: Edit `config/category_mapping.csv`

**Monthly Process:**
1. Upload files via web interface
2. Run analysis
3. Review validation report for warnings
4. Check margin analysis for surprises
5. Download CSVs for further analysis/reporting

**First-Time Setup:**
1. Run analysis with current month
2. Compare results to existing Excel tracker
3. Adjust configs as needed
4. Re-run until results match
5. Use going forward

---

## License & Attribution

**Owner:** Third Horizon
**Primary Author:** Topher Rasmussen
**Based on:** David's monthly performance tracker

Internal use only. Not for redistribution.

---

## Next Steps

v3.0 is considered **feature complete** for current needs.

**Potential Future Enhancements:**
- Multi-month trend analysis
- Budget vs actual comparisons
- Project forecasting
- Team utilization metrics
- Custom report builder

For questions or issues, contact the development team.
