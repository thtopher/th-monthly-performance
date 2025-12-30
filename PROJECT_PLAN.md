# TH Monthly Performance - Project Plan

**Project:** th-monthly-performance
**GitHub:** github.com/thtopher/th-monthly-performance
**Target Completion:** Weekend (Initial Working Prototype)
**Owner:** Topher
**Stakeholder:** David (Third Horizon)

---

## Project Overview

Build a web-based monthly performance analysis application that processes 5 operational data files (Pro Forma, Compensation, Harvest Hours, Harvest Expenses, P&L) to generate detailed project-level profitability reports with automated cost allocation.

---

## Simplified Core Business Rules (FINAL - December 2025)

This is the **durable, repeating logic** that will work month-over-month:

### Core Process (10 Steps):
1. **Load 5 files** → Flexible validation (warn on issues, fail only on critical errors)
2. **Extract revenue** from Pro Forma → Category column tells us Data/Wellness/Advisory
3. **Calculate labor** = hours × rates (grouped by project code)
4. **Calculate expenses** (grouped by project code)
5. **Classify projects** using config/cost_centers.csv:
   - Revenue Center = in Pro Forma with revenue > $0
   - Cost Center = in cost_centers.csv
   - Non-Revenue Client = has hours/expenses but NOT in Pro Forma (auto-detected)
6. **Calculate SGA Override** = Total Cost Centers - Starset Dev Cost (from config)
7. **Allocate SG&A** → All revenue projects (pro-rata by revenue)
8. **Allocate Data Infrastructure** → Data category projects only (pro-rata)
9. **Allocate Wellbeing** → Wellness category projects only (pro-rata)
10. **Calculate final margins** = Revenue - Labor - Expenses - SG&A - Data - Wellbeing
11. **Generate 3 tables** → Export CSVs + validation log

### Key Design Decisions:
- ✅ **Config-driven:** Cost centers in editable CSV file (config/cost_centers.csv)
- ✅ **Auto-detect:** Non-revenue clients (no manual list)
- ✅ **Trust Pro Forma:** Category column is source of truth for Data/Wellness/Advisory
- ✅ **Flexible validation:** Warn on structure changes, don't fail hard
- ✅ **No aggregation:** Clean project codes from the start (TH has been cleaning data for 90 days)
- ❌ **Removed:** TKF/HWM/HPA aggregation rules (one-time historical cleanup only)

---

## Success Criteria

- [ ] Web interface allows uploading 5 required monthly files
- [ ] Data processing engine successfully executes all 12 steps
- [ ] Generates accurate Revenue Adjustment Table with complete cost waterfall
- [ ] Produces Cost Center and Non-Revenue Client summaries
- [ ] Exports CSV reports for download
- [ ] Validation checks ensure data quality
- [ ] Code is documented and maintainable

---

## Technical Architecture

### Stack Decisions
- **Backend:** Python 3.13+ with Flask
- **Data Processing:** pandas, openpyxl
- **Frontend:** HTML/CSS/JavaScript (vanilla JS, minimal dependencies)
- **Storage:** Local filesystem (uploads/ and outputs/ directories)
- **Deployment:** Dockerized for portability

### Project Structure
```
th-monthly-performance/
├── app.py                      # Flask application entry point
├── config.py                   # Configuration and paths
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container definition
├── .gitignore                  # Exclude uploads, outputs
├── README.md                   # Project documentation
├── PROJECT_PLAN.md            # This file
├── config/                     # Configuration files (editable by team)
│   ├── cost_centers.csv       # Cost center definitions
│   └── settings.json          # App settings (Starset code, etc.)
├── analysis/                   # Core business logic
│   ├── __init__.py
│   ├── data_loader.py         # Load and validate input files
│   ├── classification.py      # Revenue/Cost/Non-Revenue classification
│   ├── cost_allocation.py     # SG&A, Data, Wellbeing allocation logic
│   ├── calculators.py         # Labor, expenses, margin calculations
│   └── validators.py          # Quality control checks
├── web/
│   ├── routes.py              # Web application routes
│   ├── templates/             # HTML templates
│   └── static/                # CSS, JS, assets
├── tests/
│   ├── fixtures/              # Sample data files
│   ├── test_data_loader.py
│   ├── test_classification.py
│   └── test_cost_allocation.py
├── uploads/                    # User uploaded files (gitignored)
├── outputs/                    # Generated reports (gitignored)
└── docs/
    └── Business_Rules.pdf     # Full technical specification
```
│   └── validators.py          # Quality control checks
├── web/
│   ├── routes.py              # Flask routes
│   ├── templates/
│   │   ├── base.html
│   │   ├── upload.html
│   │   ├── processing.html
│   │   ├── dashboard.html
│   │   └── reports.html
│   └── static/
│       ├── css/
│       │   └── style.css
│       └── js/
│           └── main.js
├── tests/
│   ├── fixtures/              # Sample data files
│   ├── test_data_loader.py
│   ├── test_aggregation.py
│   ├── test_cost_allocation.py
│   └── test_integration.py
├── uploads/                    # User uploaded files (gitignored)
├── outputs/                    # Generated reports (gitignored)
└── docs/
    └── Business_Rules.pdf     # Full specification
```

---

## Phase 1: Foundation (Days 1-2)

### Setup & Infrastructure

- [x] Create project folder structure
- [x] Write README.md
- [x] Write PROJECT_PLAN.md
- [ ] Initialize Git repository
- [ ] Create GitHub repo: github.com/thtopher/th-monthly-performance
- [ ] Push initial commit
- [ ] Create .gitignore (exclude uploads/, outputs/, *.xlsx, venv/)
- [ ] Set up Python virtual environment
- [ ] Create requirements.txt with initial dependencies:
  - Flask
  - pandas
  - openpyxl
  - python-dotenv
  - pytest (for testing)
- [ ] Create config.py with paths and settings
- [ ] Create basic Flask app.py skeleton

### Data Loading Module

**File:** `analysis/data_loader.py`

- [ ] Write ProFormaLoader class
  - Load with header=None
  - Extract rows 9-163, columns [0, 1, 2, 12]
  - **Also extract Category column (Column A, index 0)** for Data/Wellness/Advisory tags
  - Clean project codes (strip whitespace)
  - Convert revenue to numeric
  - Validate Cell M6 equals sum
  - **Flexible validation:** Warn if structure differs but don't fail hard
- [ ] Write CompensationLoader class
  - Load staff names and hourly rates
  - Validate no missing values
  - Return as dictionary: {name: rate}
- [ ] Write HarvestHoursLoader class
  - Load date, project code, last name, hours
  - Validate date range matches month (warn if outside)
  - Validate no missing project codes (warn if found)
  - **Flexible:** Handle column name variations
- [ ] Write HarvestExpensesLoader class
  - Load project code and expense amounts
  - Handle various column name variations
  - Validate amounts are numeric
  - **Flexible:** Try multiple strategies to find columns
- [ ] Write PLLoader class
  - Extract Data Services value (search for "Data Services" row)
  - Extract Wellbeing Coaches value (search for "Wellbeing Coaches" row)
  - **Flexible:** Search by text, not just row number
  - Return as dictionary
- [ ] Write DataLoader orchestrator class
  - Accepts 5 file paths
  - Calls all individual loaders
  - Returns validated data bundle
  - Collects warnings (don't fail on first warning)
  - Raises clear errors only on critical failures

### Testing Data Loading

- [ ] Create `tests/fixtures/` with sample October data
- [ ] Write test_data_loader.py
  - Test each loader independently
  - Test validation catches errors
  - Test DataLoader orchestration
- [ ] Run tests, ensure all pass

---

## Phase 2: Core Analysis Engine (Days 3-4)

### Configuration Files Setup

**File:** `config/cost_centers.csv`

Create CSV with cost center definitions (team-editable):
```csv
code,description
THS-25-01-DEV,Business Development
THS-25-01-BAD,Business Administration
THS-25-01-MTG,Internal Meetings
THS-25-01-SAD,Starset Dev Cost
THS-25-01-OOO,Out of Office
THS-25-01-PAD,Personal Administration
THS-25-01-PRO,Professional Development
THS-25-01-SPP,Internal Special Projects
THS-25-01-TEA,Team Building
THS-25-01-COM,Communications
THS-25-01-CSR,Corporate Social Responsibility
HC3,Health Care Council of Chicago
GEH,Work Place Well-Being Administration
MAR-24-01-PAC,PACES
MAR-24-01-HFM,Health Forum Management
BEH-25-01-APR,Alliance for Addiction Payment Reform
```

**File:** `config/settings.json`

Create JSON with app settings:
```json
{
  "starset_dev_code": "THS-25-01-SAD",
  "expected_work_weeks": 50,
  "hours_per_week": 52,
  "months_per_year": 12
}
```

- [ ] Create config/ directory
- [ ] Create cost_centers.csv with initial data
- [ ] Create settings.json with defaults
- [ ] Document how team can update cost centers

### Classification Module

**File:** `analysis/classification.py`

- [ ] Write ProjectClassifier class
  - Load cost center codes from config/cost_centers.csv
  - classify_project_code() method returns: "revenue_center", "cost_center", or "non_revenue_client"
  - Logic:
    - Revenue Center = project code in Pro Forma with revenue > 0
    - Cost Center = project code in cost_centers.csv
    - Non-Revenue Client = has hours/expenses but NOT in Pro Forma (auto-detected)
- [ ] Write classify_all_hours() function
  - Add Category column to hours dataframe
  - Use ProjectClassifier to determine category
- [ ] Write classify_all_expenses() function
  - Add Category column to expenses dataframe
  - Use ProjectClassifier to determine category

### Cost Calculation Module

**File:** `analysis/calculators.py`

- [ ] Write calculate_labor_costs() function
  - Merge hours with compensation rates
  - Calculate: hours × rate = labor cost
  - Group by project code and category
  - Return three dataframes: revenue, cost_center, non_revenue
- [ ] Write calculate_expense_costs() function
  - Group expenses by project code and category
  - Return three dataframes
- [ ] Write calculate_sga_override() function
  - Sum all cost center labor + expenses
  - Subtract Starset Dev Cost (THS-25-01-SAD)
  - Return SGA Override amount

### Cost Allocation Module

**File:** `analysis/cost_allocation.py`

- [ ] Write allocate_sga() function
  - Takes revenue dataframe and SGA Override amount
  - Calculates pro-rata: (project revenue / total revenue) × SGA Override
  - Adds SGA Offset column
- [ ] Write allocate_data_infrastructure() function
  - Filter to Data projects only
  - Calculate: Starset Dev Cost + P&L Data Services
  - Allocate pro-rata across Data projects
  - Adds Data Offset column (0 for non-Data)
- [ ] Write allocate_wellbeing() function
  - Filter to Wellness projects only
  - Use P&L Wellbeing Coaches amount
  - Allocate pro-rata across Wellness projects
  - Adds Wellbeing Offset column (0 for non-Wellness)
- [ ] Write calculate_final_margins() function
  - Final Margin = Revenue - Labor - Expenses - SGA - Data - Wellbeing
  - Margin % = (Final Margin / Revenue) × 100
  - Adds both columns

### Main Analysis Pipeline

**File:** `analysis/__init__.py` or `analysis/pipeline.py`

- [ ] Write AnalysisPipeline class
  - __init__() takes DataLoader output + config settings
  - run() method executes simplified 10-step process:
    1. Extract revenue table from Pro Forma
    2. Filter to revenue > 0 (these are Revenue Centers)
    3. Classify all hours/expenses using ProjectClassifier
    4. Calculate labor costs (all three categories)
    5. Calculate expense costs (all three categories)
    6. Merge labor + expenses to revenue table
    7. Calculate SGA Override (Cost Centers - Starset Dev)
    8. Allocate SGA to all revenue projects (pro-rata)
    9. Allocate Data Infrastructure to Data category projects (pro-rata)
    10. Allocate Wellbeing to Wellness category projects (pro-rata)
    11. Calculate final margins
  - Returns three dataframes: revenue_centers, cost_centers, non_revenue_clients
  - Saves intermediate CSVs to outputs/YYYY-MM/ directory
  - Saves validation log with warnings

### Testing Analysis Engine

- [ ] Write test_classification.py
  - Test cost center loading from CSV
  - Test auto-detection of non-revenue clients
  - Test revenue center identification
  - Test category tagging (Data/Wellness/Advisory)
- [ ] Write test_cost_allocation.py
  - Test SGA pro-rata math
  - Test Data Infrastructure allocation (Data only)
  - Test Wellbeing allocation (Wellness only)
  - Verify totals match exactly
- [ ] Write test_integration.py
  - Load sample October data
  - Run full pipeline
  - Verify final outputs match expected results
  - Compare against David's Excel baseline
- [ ] Run all tests, ensure passing

---

## Phase 3: Validation & Quality Control (Day 5)

### Validators Module

**File:** `analysis/validators.py`

- [ ] Write DataCompletenessValidator
  - All required files present
  - All files for correct month
  - No missing critical fields
  - All staff in Hours have Compensation rates
- [ ] Write MathematicalValidator
  - Revenue sum equals Pro Forma M6
  - Total hours match across categories
  - Total expenses match across categories
  - SGA Offset sum equals SGA Override
  - Data Offset sum equals Data Infrastructure
  - Wellbeing Offset sum equals Wellbeing Coaches
- [ ] Write ReasonablenessValidator
  - Overall margin % in expected range (20-40%)
  - Labor as % of revenue reasonable (15-30%)
  - No extreme negative margins (< -50%)
  - Flagging outliers for review
- [ ] Write ValidationReport class
  - Collects all validation results
  - Generates human-readable report
  - Indicates PASS/WARN/FAIL for each check
- [ ] Integrate validators into pipeline
  - Run after data loading
  - Run after final calculations
  - Display validation report before finalizing

### Testing Validators

- [ ] Write test_validators.py
  - Test with good data (should pass)
  - Test with bad data (should catch errors)
  - Test validation report generation

---

## Phase 4: Web Interface (Days 6-7)

### Backend Routes

**File:** `web/routes.py`

- [ ] Route: GET / (home page)
  - Redirect to /upload
- [ ] Route: GET /upload
  - Render upload form
  - Show instructions for required files
- [ ] Route: POST /upload
  - Accept 5 file uploads
  - Validate file names match expected patterns
  - Validate file extensions (.xlsx)
  - Save to uploads/YYYY-MM/ directory
  - Store session data (month, file paths)
  - Redirect to /processing
- [ ] Route: GET /processing
  - Show "Processing..." page
  - Trigger background analysis (or run synchronously for MVP)
  - Redirect to /dashboard when complete
- [ ] Route: GET /dashboard
  - Load analysis results from outputs/
  - Calculate summary metrics
  - Render dashboard with key numbers
- [ ] Route: GET /reports
  - List available reports for download
  - Show Revenue Centers table
  - Show Cost Centers table
  - Show Non-Revenue Clients table
- [ ] Route: GET /download/<report_name>
  - Serve CSV files for download
  - Set proper content-disposition headers
- [ ] Route: GET /validation
  - Show validation report
  - Display PASS/WARN/FAIL checks

### Frontend Templates

**Design Reference:** Based on existing Third Horizon presentation slides (see screenshots in project folder)

**File:** `web/templates/base.html`
- [ ] Create base template with:
  - Header with Third Horizon logo (top right)
  - Page title area (top left)
  - Main content area
  - Navigation (minimal, clean)
  - Link to CSS
  - Montserrat or similar professional font

**File:** `web/templates/upload.html`
- [ ] File upload form with 5 file inputs
- [ ] Clear labels matching expected file names
- [ ] Month selector (dropdown or date picker)
- [ ] Submit button (Third Horizon blue)
- [ ] Client-side validation (file types, required fields)
- [ ] Instructions panel

**File:** `web/templates/processing.html`
- [ ] Loading spinner/animation
- [ ] Status messages
- [ ] Progress indicator (if feasible)

**File:** `web/templates/dashboard.html`
- [ ] Title: "Overall Performance Dashboard - [Month] [Year]"
- [ ] Three KPI cards (horizontal layout):
  - Total Revenue (large number + label)
  - Final Contribution Margin (large number + label)
  - Overall Margin % (large number + label)
  - Yellow/gold left border accent
- [ ] Two-column layout below:
  - **Left:** Cost Breakdown
    - Labor Cost ($amount and %)
    - Expense Cost ($amount and %)
    - SG&A Offset ($amount and %)
    - Data Infrastructure ($amount and %) - RED if significant
    - Wellbeing Coaches ($amount and %)
  - **Right:** Activity Categories
    - Revenue Centers: X Projects (green)
    - Cost Centers: X Centers (orange)
    - Non-Revenue Clients: X Projects (red)
- [ ] Quick links to detailed reports
- [ ] Download buttons for CSV exports

**File:** `web/templates/revenue_centers.html`
- [ ] Title: "Revenue Center Analysis - Projects X-Y"
- [ ] Subtitle: "Complete Cost Waterfall and Margin Analysis"
- [ ] Professional table with columns:
  - Project Name | Revenue | Labor | Expenses | SG&A | Data | Wellness | Margin | Margin %
- [ ] Pagination (15-20 projects per page)
- [ ] Color coding:
  - GREEN text for positive margins
  - RED text for negative margins
- [ ] Currency formatting: $X,XXX
- [ ] Percentage formatting: XX.X%
- [ ] TOTAL row at bottom (bold)
- [ ] Export to CSV button

**File:** `web/templates/margin_chart.html`
- [ ] Title: "Revenue Center Margin Contribution"
- [ ] Subtitle: "Final Margin by Project (Sorted Highest to Lowest)"
- [ ] Horizontal bar chart:
  - Y-axis: Project names with codes
  - X-axis: Dollar amounts
  - Green bars extending right for positive margins
  - Red bars extending left for negative margins
  - Clear $0 center line
  - Scale from -$10,000 to max(positive margins)
- [ ] Use Chart.js or similar for rendering

**File:** `web/templates/cost_centers.html`
- [ ] Title: "Cost Center Analysis - Summary"
- [ ] Subtitle: "Internal Investment and Overhead Allocation"
- [ ] Professional table with columns:
  - Cost Center Description | Hours | Labor Cost | % of Total
- [ ] Sorted by Labor Cost descending
- [ ] Highlight Starset Dev Cost row (special treatment note)
- [ ] Show SG&A Override calculation clearly
- [ ] Export to CSV button

**File:** `web/templates/non_revenue_clients.html`
- [ ] Similar table styling to revenue centers
- [ ] Show: Project Name | Hours | Labor Cost | Expense Cost | Total Cost
- [ ] Explanatory note about why no revenue

**File:** `web/static/css/style.css`
- [ ] Third Horizon color palette:
  - Primary blue: #2C5282 (headers, titles)
  - Accent gold/yellow: #F6AD55 (KPI card borders)
  - Success green: #48BB78 (positive margins)
  - Error red: #F56565 (negative margins)
  - Orange: #ED8936 (cost centers)
  - Dark navy: #2D3748 (table headers)
  - Light gray: #F7FAFC (alternating rows)
- [ ] Typography:
  - Headers: Montserrat Bold
  - Body: Montserrat Regular
  - Numbers: Tabular figures for alignment
- [ ] Professional table styles:
  - Dark header row with white text
  - Alternating row colors (white/light gray)
  - Hover effects
  - Right-align numeric columns
- [ ] Card styles for KPIs:
  - White background
  - Subtle shadow
  - Yellow/gold left border (4px)
  - Large number (48px)
  - Small label below (16px)
- [ ] Responsive design (mobile-friendly)
- [ ] Print-friendly styles

**File:** `web/static/js/main.js`
- [ ] Client-side form validation
- [ ] File name validation
- [ ] Table sorting functionality
- [ ] Chart.js integration for margin chart
- [ ] Table pagination
- [ ] AJAX for async processing (optional for MVP)

### Testing Web Interface

- [ ] Manual testing: upload flow
- [ ] Manual testing: dashboard display
- [ ] Manual testing: report downloads
- [ ] Manual testing: validation report
- [ ] Test error handling (bad files, missing files)

---

## Phase 5: Polish & Documentation (Day 8)

### Error Handling

- [ ] Graceful error messages for users
- [ ] Log errors to file for debugging
- [ ] Handle file upload failures
- [ ] Handle processing failures
- [ ] Handle missing/corrupted data

### Documentation

- [ ] Complete docstrings for all functions
- [ ] Add inline comments for complex logic
- [ ] Update README with:
  - Installation instructions
  - Usage guide
  - Screenshots (if time permits)
  - Troubleshooting section
- [ ] Create USER_GUIDE.md for Third Horizon team
  - How to prepare input files
  - How to upload and run analysis
  - How to interpret results
  - Common issues and solutions

### Code Quality

- [ ] Run linter (flake8 or black)
- [ ] Format code consistently
- [ ] Remove debug print statements
- [ ] Remove commented-out code
- [ ] Add type hints where helpful

### Performance Optimization

- [ ] Profile slow operations
- [ ] Optimize pandas operations if needed
- [ ] Consider caching for repeated calculations

---

## Phase 6: Deployment (Day 9)

### Docker Setup

**File:** `Dockerfile`
- [ ] Create Dockerfile
  - Base image: python:3.13-slim
  - Install dependencies
  - Copy application code
  - Expose port 5000
  - CMD to run Flask app

**File:** `docker-compose.yml` (optional)
- [ ] Define service
- [ ] Mount volumes for uploads/outputs
- [ ] Environment variables

### Deployment Testing

- [ ] Build Docker image
- [ ] Run container locally
- [ ] Test full workflow in container
- [ ] Verify file persistence

### Deployment Options Research

- [ ] Document options for David:
  - Run locally on macOS
  - Deploy to VPS (DigitalOcean, Linode)
  - Deploy to Heroku
  - Deploy to Railway
  - Deploy to Render
- [ ] Provide cost estimates for each
- [ ] Recommend simplest option

---

## Phase 7: Handoff & Training (Day 10)

### Handoff Materials

- [ ] Complete README.md
- [ ] Complete USER_GUIDE.md
- [ ] Sample data files in docs/samples/
- [ ] Video walkthrough (optional, if time permits)
- [ ] Known issues document

### Training Session

- [ ] Schedule walkthrough with David
- [ ] Demonstrate upload → processing → reports flow
- [ ] Show validation reports
- [ ] Explain error messages
- [ ] Show how to download results
- [ ] Answer questions
- [ ] Get feedback for v2

### Future Enhancements Backlog

Document potential v2 features:
- [ ] Multi-user support with authentication
- [ ] Historical trend analysis (compare months)
- [ ] Interactive charts/graphs (Chart.js or similar)
- [ ] Automated email reports
- [ ] API endpoints for programmatic access
- [ ] Cloud storage migration (Cloudflare R2)
- [ ] Real-time progress updates during processing
- [ ] Project-level drill-down views
- [ ] Customizable cost allocation rules
- [ ] Export to Excel with formatting
- [ ] Budget vs actual comparisons

---

## Risk Management

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Excel file format changes | Medium | High | Strict file validation, clear error messages |
| Pandas memory issues with large files | Low | Medium | Test with maximum expected file sizes |
| Calculation errors in complex formulas | Medium | High | Comprehensive unit tests, validate against David's existing Excel |
| File upload security issues | Low | High | Filename validation, file size limits, secure_filename() |

### Project Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Requirements misunderstood | Low | High | Frequent check-ins with David, use Business Rules as source of truth |
| Timeline slips | Medium | Medium | MVP focus, defer nice-to-haves to v2 |
| Deployment complications | Medium | Low | Docker ensures consistency, provide multiple deployment options |

---

## Testing Strategy

### Unit Tests
- Test each module independently
- Mock data inputs
- Verify calculations match expected outputs
- Target: 80%+ code coverage

### Integration Tests
- Test full pipeline with sample data
- Verify outputs match Excel baseline (from David's current system)
- Test all aggregation rules
- Test all validation checks

### Manual Testing
- Upload workflow
- Error handling
- Report generation
- Download functionality
- Cross-browser testing (Chrome, Firefox, Safari)

---

## Success Metrics

### Must Have (MVP)
- ✅ Processes October 2025 data correctly
- ✅ Generates accurate Revenue Adjustment Table
- ✅ Validation checks catch common errors
- ✅ Downloadable CSV reports

### Should Have
- ✅ Clean, professional UI
- ✅ Comprehensive error messages
- ✅ Documentation for team members
- ✅ Docker deployment option

### Nice to Have (v2)
- Interactive dashboards with charts
- Month-over-month comparisons
- Automated scheduling
- Email notifications

---

## Timeline

| Phase | Days | Key Deliverables |
|-------|------|------------------|
| 1. Foundation | 1-2 | Repo setup, data loading works |
| 2. Analysis Engine | 3-4 | All 12 steps complete, tests passing |
| 3. Validation | 5 | Quality control checks implemented |
| 4. Web Interface | 6-7 | Upload and reports working |
| 5. Polish | 8 | Documentation complete |
| 6. Deployment | 9 | Docker container ready |
| 7. Handoff | 10 | Training complete, v2 backlog |

**Target:** Working prototype by end of weekend (3-4 days intensive work)

**Realistic:** Fully polished v1 in 7-10 days

---

## Next Immediate Steps

1. ✅ Create project plan (this document)
2. Initialize Git repository
3. Create GitHub repo
4. Set up Python virtual environment
5. Create initial file structure
6. Write config.py
7. Start Phase 1: Data loading module

---

## Notes & Questions for David

- Do you have sample data files I can use for testing?
- Are there any other aggregation rules beyond TKF, HWM, HPA?
- Do cost center codes ever change month-to-month?
- Any specific branding/styling preferences for the web interface?
- Preferred deployment environment (local Mac, VPS, cloud)?
- Any additional validation checks you'd like beyond what's in Business Rules doc?

---

**Status:** Planning Complete - Ready to Begin Implementation
**Next Action:** Initialize Git repository and create project structure
