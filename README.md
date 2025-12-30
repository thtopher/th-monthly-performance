# TH Monthly Performance

**Monthly performance analysis platform for Third Horizon**

Automated financial analysis tool that processes operational data to generate detailed project-level profitability reports with full cost allocation.

---

## Overview

Third Horizon operates across multiple practice areas (Advisory, Data, Wellness) with complex overhead allocation requirements. This application transforms five monthly data files into actionable financial insights:

- **Revenue Centers:** Client projects with detailed cost waterfalls and margin analysis
- **Cost Centers:** Internal overhead investments (business development, administration, etc.)
- **Non-Revenue Clients:** Client work performed without current revenue recognition

### Key Features

✅ **Automated cost allocation** - Pro-rata distribution of SG&A, data infrastructure, and wellbeing costs
✅ **Project-level profitability** - Complete cost waterfall showing true margins
✅ **Config-driven** - Team can update cost center definitions without code changes
✅ **Flexible validation** - Warns on data issues without blocking analysis
✅ **Professional reports** - Publication-ready tables and dashboards
✅ **Web interface** - Simple upload page for team members

---

## How It Works

### Monthly Process

Each month (around the 3rd week), the team uploads 5 data files:

1. **Pro Forma** - Project revenue data with category tags (Data/Wellness/Advisory)
2. **Compensation** - Staff hourly rates (updated monthly by Aisha)
3. **Harvest Hours** - Time tracking data exported from Harvest
4. **Harvest Expenses** - Project expense data exported from Harvest
5. **P&L** - Organizational overhead costs (Data Services, Wellbeing Coaches)

The application processes these files through a 10-step analysis:

```
1. Load & validate files
2. Extract revenue from Pro Forma (filter revenue > $0)
3. Calculate labor costs (hours × rates)
4. Calculate expense costs
5. Classify projects (Revenue/Cost/Non-Revenue)
6. Calculate SG&A Override (Cost Centers - Starset Dev)
7. Allocate SG&A to all revenue projects (pro-rata)
8. Allocate Data Infrastructure to Data projects (pro-rata)
9. Allocate Wellbeing to Wellness projects (pro-rata)
10. Calculate final margins
```

### Outputs

The application generates three CSV reports:

- **`revenue_centers.csv`** - All revenue-bearing projects with complete cost waterfall
  - Columns: Project Name, Revenue, Labor, Expenses, SG&A, Data, Wellbeing, Margin, Margin %
- **`cost_centers.csv`** - Internal overhead breakdown
  - Columns: Cost Center, Hours, Labor Cost, % of Total
- **`non_revenue_clients.csv`** - Client work without revenue in current month
  - Columns: Project Name, Hours, Labor Cost, Expense Cost, Total Cost

Plus a web dashboard showing:
- Overall performance metrics (Total Revenue, Final Margin, Margin %)
- Cost breakdown by category
- Activity summary (counts by category)

---

## Installation

### Prerequisites

- Python 3.13 or higher
- Git

### Local Setup

```bash
# Clone the repository
git clone git@github.com:thtopher/th-monthly-performance.git
cd th-monthly-performance

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

The application will start on `http://localhost:5000`

### Docker Setup

```bash
# Build the image
docker build -t th-monthly-performance .

# Run the container
docker run -p 5000:5000 -v $(pwd)/uploads:/app/uploads -v $(pwd)/outputs:/app/outputs th-monthly-performance
```

---

## Usage

### Web Interface

1. **Navigate to** `http://localhost:5000`
2. **Upload 5 files** using the upload form
3. **Click "Process"** to run the analysis
4. **View dashboard** with summary metrics
5. **Download reports** as CSV files

### Command Line (Alternative)

```bash
python run_analysis.py \
  --month "December2025" \
  --proforma "path/to/(Proforma)December2025.xlsx" \
  --compensation "path/to/(Compensation)December2025.xlsx" \
  --hours "path/to/(HarvestHours)December2025.xlsx" \
  --expenses "path/to/(HarvestExpenses)December2025.xlsx" \
  --pl "path/to/(P&L)December2025.xlsx"
```

Outputs saved to: `outputs/December2025/`

---

## Configuration

### Cost Centers

The application reads cost center definitions from `config/cost_centers.csv`:

```csv
code,description
THS-25-01-DEV,Business Development
THS-25-01-BAD,Business Administration
THS-25-01-MTG,Internal Meetings
THS-25-01-SAD,Starset Dev Cost
...
```

**To update cost centers:**
1. Open `config/cost_centers.csv`
2. Add/remove/edit rows
3. Save the file
4. Restart the application

### Application Settings

Edit `config/settings.json` to change:

```json
{
  "starset_dev_code": "THS-25-01-SAD",
  "expected_work_weeks": 50,
  "hours_per_week": 52,
  "months_per_year": 12
}
```

---

## File Preparation Guide

### Pro Forma File

**Format:** Excel (.xlsx)
**Sheet Name:** "PRO FORMA 2025"
**Key Requirements:**
- Row 6, Column M: Must contain SUM formula for total revenue
- Rows 10-164: Project data
- Column A: Category (must be: "Data", "Wellness", or "Next Gen Advisory")
- Column B: Project Name
- Column C: Project Code (unique identifier)
- Column M: Monthly revenue (numeric, no formulas in data rows)

**Example:**
| Category | Project Name | Project Code | Oct Revenue |
|----------|--------------|--------------|-------------|
| Data | Marsh McLennan | PAD-25-01-MMA | 69,027 |
| Wellness | Mindful Learning | GEH-24-01-MFL | 8,500 |

### Compensation File

**Format:** Excel (.xlsx)
**Key Requirements:**
- Column 1: Last Name (must match Harvest Hours exactly)
- Column 2: Base Cost Per Hour (numeric hourly rate)
- No missing values

**Example:**
| Last Name | Base Cost Per Hour |
|-----------|--------------------|
| Smith | 125.50 |
| Johnson | 98.75 |

### Harvest Hours File

**Format:** Excel (.xlsx)
**Export from Harvest:** Detailed Time Report
**Key Requirements:**
- Date column (all dates must be within reporting month)
- Project Code column (must match Pro Forma or Cost Centers)
- Last Name column (must match Compensation file)
- Hours column (numeric)

### Harvest Expenses File

**Format:** Excel (.xlsx)
**Export from Harvest:** Detailed Expenses Report
**Key Requirements:**
- Project Code column
- Expense Amount column (numeric)

### P&L File

**Format:** Excel (.xlsx)
**Key Requirements:**
- Must contain row labeled "Data Services" with monthly value
- Must contain row labeled "Wellbeing Coaches" with monthly value
- Application searches by text, not row number (flexible)

---

## Data Classification

The application automatically classifies all activity into three mutually exclusive categories:

### Revenue Centers
**Criteria:** Project code appears in Pro Forma with revenue > $0

**Treatment:**
- Receive direct labor and expense costs
- Receive pro-rata SG&A allocation (all revenue projects)
- Receive pro-rata Data Infrastructure (Data category only)
- Receive pro-rata Wellbeing Coaches (Wellness category only)
- Appear in final Revenue Adjustment Table with complete cost waterfall

### Cost Centers
**Criteria:** Project code appears in `config/cost_centers.csv`

**Treatment:**
- Labor and expense costs are calculated and summed
- Starset Dev Cost (THS-25-01-SAD) is separated for Data Infrastructure
- Remaining costs become SG&A Override
- Costs are allocated to revenue projects (not shown per-project)
- Reported separately in Cost Center Summary

### Non-Revenue Clients
**Criteria:** Has hours/expenses but NOT in Pro Forma with revenue > $0

**Auto-detected** - no manual list to maintain

**Treatment:**
- Labor and expense costs are calculated
- Tracked separately for visibility
- NOT allocated to revenue projects
- Reported in Non-Revenue Client table

---

## Cost Allocation Logic

### SG&A Override

**Calculation:**
```
SG&A Override = Total Cost Center Costs - Starset Dev Cost
```

**Allocation:**
- Distributed to ALL revenue-bearing projects
- Pro-rata based on project revenue
- Formula: `(Project Revenue / Total Revenue) × SG&A Override`

**Example:**
- Total Revenue: $750,000
- SG&A Override: $200,000
- Project A Revenue: $75,000 (10% of total)
- Project A SG&A Allocation: $20,000 (10% of SG&A Override)

### Data Infrastructure

**Calculation:**
```
Data Infrastructure = Starset Dev Cost + P&L Data Services
```

**Allocation:**
- Distributed ONLY to Data category projects
- Pro-rata based on Data project revenue
- Formula: `(Project Revenue / Total Data Revenue) × Data Infrastructure`

### Wellbeing Coaches

**Source:** P&L "Wellbeing Coaches" line item

**Allocation:**
- Distributed ONLY to Wellness category projects
- Pro-rata based on Wellness project revenue
- Formula: `(Project Revenue / Total Wellness Revenue) × Wellbeing Coaches`

---

## Validation & Quality Control

The application performs automatic validation checks:

### Data Completeness
- ✓ All required files present and readable
- ✓ All staff in Harvest Hours have matching Compensation rates
- ✓ All project codes in Harvest match Pro Forma or Cost Centers
- ✓ No missing critical fields (Project Code, Revenue, Hours, Rates)

### Mathematical Accuracy
- ✓ Revenue table sum equals Pro Forma Cell M6
- ✓ Total hours across all categories equals Harvest Hours total
- ✓ Total expenses across all categories equals Harvest Expenses total
- ✓ SG&A Offset allocations sum to SG&A Override exactly
- ✓ Data Offset allocations sum to Data Infrastructure exactly
- ✓ Wellbeing Offset allocations sum to Wellbeing Coaches exactly

### Reasonableness Checks
- ⚠ Overall margin % between 20-40% (typical range)
- ⚠ Labor as % of revenue between 15-30% per project
- ⚠ No extreme negative margins (< -50%)
- ⚠ Data Infrastructure cost reasonable ($150K-$160K range)

**Warnings vs Errors:**
- **Warnings** allow analysis to continue (logged for review)
- **Errors** block analysis (must be fixed)

---

## Project Structure

```
th-monthly-performance/
├── app.py                      # Flask web application
├── config.py                   # Configuration and paths
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container definition
├── config/                     # Configuration files (editable)
│   ├── cost_centers.csv       # Cost center definitions
│   └── settings.json          # App settings
├── analysis/                   # Core business logic
│   ├── data_loader.py         # Load and validate files
│   ├── classification.py      # Classify projects
│   ├── cost_allocation.py     # Allocate overhead costs
│   ├── calculators.py         # Calculate labor, expenses, margins
│   └── validators.py          # Quality control checks
├── web/                        # Web interface
│   ├── routes.py              # Flask routes
│   ├── templates/             # HTML templates
│   └── static/                # CSS, JS, assets
├── tests/                      # Test suite
├── uploads/                    # Uploaded files (gitignored)
├── outputs/                    # Generated reports (gitignored)
└── docs/                       # Documentation
```

---

## Troubleshooting

### "Revenue mismatch" error

**Problem:** Sum of project revenues doesn't match Pro Forma Cell M6

**Solutions:**
- Verify Cell M6 contains a SUM formula
- Check for duplicate project codes in Pro Forma
- Ensure all revenue values are numeric (no text, no errors)

### "Staff member not found in Compensation" warning

**Problem:** Someone logged hours but isn't in the Compensation file

**Solutions:**
- Add missing staff member to Compensation file
- Verify name spelling matches exactly (case-sensitive)
- Check for extra spaces in names

### "Project code not found" warning

**Problem:** Hours/expenses logged to unknown project code

**Solutions:**
- Add project to Pro Forma if it's a revenue project
- Add to `config/cost_centers.csv` if it's a cost center
- It will auto-classify as Non-Revenue Client if neither

### File structure errors

**Problem:** Application can't find expected columns/rows

**Solutions:**
- Check file format matches expected structure
- Review validation log for specific issues
- Ensure sheet names are correct (e.g., "PRO FORMA 2025")

---

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_data_loader.py

# Run with coverage
pytest --cov=analysis --cov-report=html
```

### Adding a New Cost Center

1. Open `config/cost_centers.csv`
2. Add new row: `CODE,Description`
3. Save and restart application
4. No code changes needed!

### Updating Business Logic

Core analysis logic is in `analysis/` directory:
- `data_loader.py` - Modify to handle new file formats
- `classification.py` - Update classification rules
- `cost_allocation.py` - Change allocation formulas
- `calculators.py` - Adjust calculations

Always update tests when changing business logic.

---

## Deployment

### Heroku

```bash
heroku create th-monthly-performance
git push heroku main
heroku open
```

### Railway

```bash
railway init
railway up
```

### VPS (DigitalOcean, Linode, etc.)

```bash
# SSH to server
ssh user@server

# Clone and setup
git clone git@github.com:thtopher/th-monthly-performance.git
cd th-monthly-performance
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

---

## Technology Stack

- **Backend:** Python 3.13+, Flask
- **Data Processing:** pandas, openpyxl
- **Frontend:** HTML5, CSS3, JavaScript (vanilla)
- **Charts:** Chart.js
- **Testing:** pytest
- **Deployment:** Docker, Gunicorn

---

## Contributing

This is an internal Third Horizon tool. For changes or enhancements:

1. Create feature branch from `main`
2. Make changes with clear commit messages
3. Write/update tests
4. Submit pull request with description
5. Tag David for review

---

## License

Internal use only - Third Horizon proprietary.

---

## Support

For questions or issues:

- **GitHub Issues:** [github.com/thtopher/th-monthly-performance/issues](https://github.com/thtopher/th-monthly-performance/issues)
- **Project Lead:** David (Third Horizon)
- **Developer:** Topher

---

## Release Notes

### Version 1.0.0 (December 2025)

**Initial Release**

✅ Core analysis engine with 10-step process
✅ Web upload interface
✅ Config-driven cost center management
✅ Auto-detection of non-revenue clients
✅ Flexible file validation
✅ Professional dashboard and reports
✅ CSV export functionality
✅ Docker deployment support

**Design Decisions:**
- Removed historical aggregation rules (TKF, HWM, HPA)
- Config-based cost center definitions
- Trust Pro Forma Category column for Data/Wellness tagging
- Warn on validation issues, fail only on critical errors

---

**Current Status:** Production Ready
**Last Updated:** December 30, 2025
