# Project Plan: Monthly Performance Analysis System

**Version:** 3.0 (Complete)
**Date:** December 31, 2025
**Status:** Production Ready

---

## Goal

Deliver a **web-based** deterministic, auditable monthly analysis platform that:
- accepts five monthly source files via web interface,
- produces three CSV outputs + a validation report,
- provides interactive dashboard with drill-down capabilities,
- matches David's current Excel tracker logic (pro-rata allocations; contract-code joins; reimbursable filtering),
- is reproducible, auditable, and production-ready.

**Status:** ✅ **COMPLETE** - All phases delivered

---

## Executive Summary

The TH Monthly Performance Analysis System v3.0 has been successfully delivered as a complete, production-ready web application. The system processes five monthly source files (Pro Forma, Compensation, Harvest Hours, Harvest Expenses, P&L) and generates comprehensive project-level performance metrics with an interactive dashboard.

### Key Achievements

✅ **Core Analysis Engine** (Phases 0-4)
- CLI-first deterministic processing
- Five-file ingestion with normalization
- Pro-rata overhead allocation
- Complete validation framework
- CSV outputs with audit trails

✅ **Web Interface** (Phase 6-7)
- Flask web application
- Interactive upload interface
- Results dashboard with 6 tabs
- Drill-down functionality
- Real-time filtering and sorting

✅ **Advanced Features** (v3.0 Enhancements)
- Margin visualization chart
- THS code auto-classification
- Dual CSV export (full + current view)
- Active/inactive project toggles
- Allocation calculation transparency
- Mobile-responsive design

---

## Phase 0: CLI Infrastructure ✅ COMPLETE

### 1. Repository initialization ✅
- ✅ Created GitHub repo structure
- ✅ Initialized project structure (analysis/, config/, tests/, outputs/, templates/, static/)
- ✅ Created .gitignore (excludes outputs/, *.xlsx, .venv/)
- ✅ Created requirements.txt (pandas, openpyxl, pytest, flask)

### 2. CLI entry point ✅
- ✅ Created `run_analysis.py` with argparse
- ✅ Implemented full command-line interface with progress logging
- ✅ Added error handling and validation feedback

### 3. Configuration files ✅
- ✅ Created `config/cost_centers.csv` with production data
- ✅ Created `config/category_mapping.csv` (BEH/PAD/MAR/WWB/CMH → Advisory/Data/Wellness)
- ✅ Created `config/pnl_account_tags.csv` (account matching rules)
- ✅ Created `config/settings.json` (hours_per_week: 50, weeks_per_year: 52, etc.)

---

## Phase 1: Data Contracts ✅ COMPLETE

### 1. Contract code normalization ✅
- ✅ Implemented `normalize_contract_code()`:
  - trim whitespace
  - remove non-breaking spaces
  - preserve case
- ✅ Unit tests for edge cases

### 2. Canonical intermediate tables ✅
- ✅ `projects` (from Pro Forma)
- ✅ `hours` (from Harvest Hours)
- ✅ `expenses` (from Harvest Expenses)
- ✅ `pnl_accounts` (from P&L)

---

## Phase 2: Data Loaders ✅ COMPLETE

### ProFormaLoader ✅
- ✅ Detects header row by scanning first 10 rows for month sequence
- ✅ Identifies selected month column by matching `Jan…Dec`
- ✅ Extracts:
  - allocation_tag from Column A (`Data` / `Wellness` / blank)
  - project_name from Column B
  - project_code from Column C
  - proforma section from nearest header row
- ✅ **Aggregates duplicates by project_code**
- ✅ Validates totals against Base Revenue (fallback: Forecasted Revenue)

### CompensationLoader ✅
- ✅ Supports Strategy A: read `Base Cost Per Hour`
- ✅ Supports Strategy B: compute hourly cost from Total or components
- ✅ Validates unique staff key (Last Name) and no missing/zero hourly costs

### HarvestHoursLoader ✅
- ✅ Reads columns flexibly (synonyms)
- ✅ Validates month date range (excludes out-of-month rows with WARN)
- ✅ Output fields: date, project_code, staff_key, hours

### HarvestExpensesLoader ✅
- ✅ Reads columns flexibly (synonyms)
- ✅ **Filters reimbursable:** Billable == Yes → exclude
- ✅ Defaults unknown billable → warn + include
- ✅ Output fields: date, project_code, amount_included, description/notes

### PnLLoader ✅
- ✅ Loads `IncomeStatement`
- ✅ Identifies `Total` column (fallback: rightmost numeric)
- ✅ Extracts account rows and totals
- ✅ Applies `config/pnl_account_tags.csv` to bucket accounts:
  - DATA, WORKPLACE, NIL, SGA

---

## Phase 3: Core Engine ✅ COMPLETE

### ProjectClassifier ✅
- ✅ Revenue center = revenue > 0 in Pro Forma
- ✅ Cost center = listed in `config/cost_centers.csv` OR starts with `THS-` (v3.0)
- ✅ Non-revenue client = activity but not revenue center and not cost center
- ✅ Conflict detection (revenue & cost center) → FAIL
- ✅ **THS auto-classification** with revenue precedence

### CostCalculator ✅
- ✅ Labor cost = hours × hourly_cost (join on staff key)
- ✅ Expense cost = sum included expenses
- ✅ Merge direct costs into revenue table
- ✅ NaN handling for missing compensation data

### OverheadAllocator ✅
- ✅ Computes pools:
  - SG&A pool (P&L SGA + optional cost center overhead)
  - Data pool (P&L DATA + optional DATA cost center pool)
  - Workplace pool (P&L WORKPLACE)
- ✅ Allocates:
  - SG&A across all revenue centers by revenue share
  - Data across Data-tagged revenue centers by revenue share
  - Workplace across Wellness-tagged revenue centers by revenue share
- ✅ Validates allocation totals match pool totals (±$0.01)

### MarginCalculator ✅
- ✅ Computes margin dollars and margin %
- ✅ Handles zero revenue edge cases (skip margin% calculation)

---

## Phase 4: Validation & Reporting ✅ COMPLETE

### Validators ✅
- ✅ DataCompletenessValidator (required files; required columns)
- ✅ KeyIntegrityValidator (missing comp rates; duplicate staff key)
- ✅ MathematicalValidator (revenue totals; pool allocations; reconciliations)
- ✅ ClassificationValidator (revenue vs cost center conflicts)

### Outputs ✅
- ✅ Write revenue_centers.csv
- ✅ Write cost_centers.csv
- ✅ Write non_revenue_clients.csv
- ✅ Write validation_report.md
- ✅ Write _pools.json (v3.0 - allocation detail)

---

## Phase 5: QA Against David's Baseline ✅ COMPLETE

**Critical for CLI MVP:**
- ✅ Ran engine on November 2025 example set via CLI
- ✅ Compared outputs to David's tracker totals (revenue, labor, expense, allocations)
- ✅ Reviewed mismatches with David and adjusted configs:
  - cost center definitions
  - P&L account tags
  - allocation tag handling
- ✅ Iterated on validation rules based on real-world edge cases
- ✅ All reconciliation checks pass within ±$0.01 tolerance

---

## Phase 6: Web Upload UI ✅ COMPLETE

**Flask Application:**
- ✅ Created `app.py` Flask application
- ✅ Built upload form accepting 5 files
- ✅ Month detection from filenames
- ✅ Runs pipeline backend, shows validation report in browser
- ✅ Provides download links for CSV outputs
- ✅ Session management for multi-user access
- ✅ Error handling with user-friendly messages

**Upload Interface (`templates/index.html`):**
- ✅ Clean, professional upload form
- ✅ File type validation (client-side)
- ✅ Drag-and-drop support
- ✅ Progress indicators
- ✅ Clear instructions for each file type

---

## Phase 7: Interactive Dashboard ✅ COMPLETE (v3.0)

**Dashboard Features:**
- ✅ Six-tab navigation:
  1. Revenue Centers - Full P&L table
  2. Margin Analysis - Visual chart (NEW)
  3. Cost Centers - Internal overhead
  4. Non-Revenue Clients - Exceptions
  5. Validation Report - Audit trail
  6. Methodology - Documentation

**Drill-Down Functionality:**
- ✅ Expandable rows (▶) on Revenue Centers and Cost Centers
- ✅ Hours detail by person with rates
- ✅ Expense detail by line item
- ✅ Allocation calculation walkthrough with formulas
- ✅ DataTables integration for detail tables
- ✅ Default sorting (hours: hours desc, expenses: amount desc)

**Table Interactivity:**
- ✅ DataTables.js integration
- ✅ Sortable columns (click header to sort)
- ✅ Live search/filter
- ✅ Pagination (25 rows default)
- ✅ Responsive column widths
- ✅ **Dual CSV export**:
  - Download Full CSV (original output)
  - Download Current View CSV (respects sorting/filtering)

**Active/Inactive Management:**
- ✅ Revenue Centers: Auto-hide inactive projects (zero activity)
- ✅ Cost Centers: Auto-hide inactive centers
- ✅ Toggle buttons: "Show Inactive Projects (N)"
- ✅ Summary metrics update based on active/inactive counts

**Margin Visualization (NEW in v3.0):**
- ✅ Chart.js integration
- ✅ Horizontal bar chart sorted highest to lowest
- ✅ Green bars for positive margins
- ✅ Red bars for negative margins
- ✅ Project name + code labels
- ✅ Currency-formatted axes
- ✅ Hover tooltips with exact values
- ✅ Responsive height (1000px container)

**UI/UX Enhancements:**
- ✅ Mobile-responsive design
- ✅ Professional color scheme (no emojis)
- ✅ Consistent button styling
- ✅ Clear visual hierarchy
- ✅ Loading states
- ✅ Error messaging

**API Endpoints:**
- ✅ `/api/project_details/revenue/{code}` - Revenue center details
- ✅ `/api/project_details/cost_center/{code}` - Cost center details
- ✅ `/api/project_details/non_revenue/{code}` - Non-revenue client details
- ✅ JSON response with hours, expenses, allocations
- ✅ NaN handling for valid JSON output

---

## Phase 8: v3.0 Enhancements ✅ COMPLETE

### THS Auto-Classification ✅
- ✅ Automatic detection of THS- prefixed codes
- ✅ Revenue precedence logic (THS codes CAN be revenue centers)
- ✅ Default SGA pool assignment
- ✅ Auto-populate project names from Harvest
- ✅ Zero manual configuration required
- ✅ Validation report shows auto-classified codes

**Benefits Achieved:**
- Zero maintenance for new THS codes
- Self-documenting naming convention
- Correct handling of revenue-generating THS projects
- Reduced configuration burden

### Enhanced Drill-Down ✅
- ✅ Allocation calculation boxes (SG&A, Data, Wellness)
- ✅ Side-by-side layout for clear comparison
- ✅ Formula display with actual numbers
- ✅ Pool totals and revenue bases shown
- ✅ Project share percentages calculated
- ✅ Conditional display (only show relevant allocations)

### Download Current View ✅
- ✅ DataTables Buttons extension integration
- ✅ Hidden default buttons (triggered from header)
- ✅ "Download Full CSV" and "Download Current View CSV" side-by-side
- ✅ Current view respects:
  - Current sorting
  - Active search filters
  - All pages (not just current page)

### Methodology Documentation ✅
- ✅ Complete ETL process documentation
- ✅ Classification logic explained
- ✅ Pool calculation walkthrough
  - References actual P&L sheet ("IncomeStatement")
  - References actual column ("Total Amount")
  - References actual account names
  - References config file (pnl_account_tags.csv)
- ✅ Allocation formulas with examples
- ✅ Final outputs documented
- ✅ Key principles listed

---

## Definition of Done ✅ ACHIEVED

### CLI MVP Requirements (Phase 0-5) ✅
- ✅ CLI runs end-to-end with November 2025 example files
- ✅ All critical validations enforced (missing comp rates → FAIL)
- ✅ Allocations reconcile to pools (±$0.01)
- ✅ Outputs are reproducible and auditable
- ✅ Duplicate contract codes aggregated correctly
- ✅ Column A allocation tags respected
- ✅ Config-driven P&L account bucketing works
- ✅ validation_report.md shows all checks and warnings
- ✅ Console output provides clear progress feedback

### Web Interface Requirements (Phase 6-7) ✅
- ✅ Flask app runs on localhost:5000
- ✅ Upload interface accepts all 5 required files
- ✅ Results dashboard displays with all tabs
- ✅ Drill-down functionality works on all tables
- ✅ DataTables sorting and filtering operational
- ✅ CSV downloads work (both full and current view)
- ✅ Active/inactive toggles function correctly
- ✅ Margin visualization renders properly
- ✅ Validation report displays in browser
- ✅ Methodology tab shows complete documentation

### v3.0 Enhancement Requirements ✅
- ✅ THS auto-classification implemented and tested
- ✅ Margin chart displays with correct colors and sorting
- ✅ Download current view respects table state
- ✅ All emojis removed from interface
- ✅ Buttons properly positioned in headers
- ✅ NaN handling prevents JSON errors
- ✅ Allocation transparency shows formulas
- ✅ Mobile-responsive design tested

---

## Success Criteria ✅ MET

### CLI Command (Still Works)
```bash
python run_analysis.py \
  --month "November2025" \
  --proforma "demo_files/(Proforma)November2025.xlsx" \
  --compensation "demo_files/(Compensation)November2025.xlsx" \
  --hours "demo_files/(HarvestHours)November2025.xlsx" \
  --expenses "demo_files/(HarvestExpenses)November2025.xlsx" \
  --pl "demo_files/(P&L)November2025.xlsx"

# ✅ Output: 5 files in outputs/November2025/
# - revenue_centers.csv (47 projects with correct margins)
# - cost_centers.csv (18 centers including THS auto-classified)
# - non_revenue_clients.csv (6 projects)
# - validation_report.md (all checks passed)
# - _pools.json (allocation detail)
```

### Web Interface (Primary Method)
```bash
python app.py
# Open http://localhost:5000
# Upload 5 files
# View interactive dashboard
# ✅ All features functional
```

---

## Timeline - Actual vs. Planned

| Phase | Planned | Actual | Deliverable | Status |
|-------|---------|--------|-------------|--------|
| 0. CLI Infrastructure | 1 day | 1 day | run_analysis.py skeleton, configs | ✅ Complete |
| 1. Data Contracts | 1 day | 1 day | normalize_contract_code(), intermediate tables | ✅ Complete |
| 2. Data Loaders | 2-3 days | 2 days | All 5 loaders with Column A tags, aggregation | ✅ Complete |
| 3. Core Engine | 1 day | 1 day | Classification, cost calc, allocation, margin | ✅ Complete |
| 4. Validation & Output | 1 day | 1 day | All validators, CSV writers, validation report | ✅ Complete |
| 5. QA vs Baseline | 1 day | 1 day | Compare to David's Excel, iterate on edge cases | ✅ Complete |
| 6. Web UI Base | 2 days | 2 days | Flask upload interface, basic results display | ✅ Complete |
| 7. Dashboard Features | 2 days | 3 days | DataTables, drill-down, validation display | ✅ Complete |
| 8. v3.0 Enhancements | N/A | 2 days | Margin chart, THS auto-class, current view export | ✅ Complete |

**Total Time:** ~14 days (including enhancements)
**Target:** 7-8 days for web interface
**Actual:** Exceeded target with additional features

---

## Key Technical Decisions

### Architecture Choices ✅
1. **Flask over Django** - Lightweight, perfect for small team tool
2. **Pandas for data processing** - Industry standard, excellent Excel support
3. **DataTables.js** - Mature, feature-rich table library
4. **Chart.js** - Simple, effective visualization
5. **Session-based state** - Works for small team, no database needed
6. **File-based storage** - Outputs organized by month in filesystem

### Design Patterns ✅
1. **Separation of concerns** - analysis/ modules independent of web layer
2. **Config-driven behavior** - No code changes for new cost centers or P&L accounts
3. **Fail-fast validation** - Critical errors stop processing immediately
4. **Progressive enhancement** - CLI works standalone, web adds convenience
5. **Deterministic processing** - Same inputs always produce same outputs

### Quality Measures ✅
1. **Comprehensive validation** - 20+ validation rules with clear error messages
2. **Audit trail** - validation_report.md provides complete transparency
3. **Reconciliation checks** - All allocations must sum to pools (±$0.01)
4. **Error handling** - Graceful degradation, user-friendly messages
5. **NaN handling** - Prevents crashes from missing data

---

## Production Readiness Checklist ✅

### Core Functionality ✅
- ✅ Five-file ingestion works reliably
- ✅ All calculations match David's Excel tracker
- ✅ Validation catches all known error scenarios
- ✅ CSV outputs are correctly formatted
- ✅ Web dashboard displays all data accurately

### Error Handling ✅
- ✅ Missing files → Clear error message
- ✅ Invalid file format → Specific file/sheet error
- ✅ Missing compensation → Lists all staff without rates
- ✅ Classification conflicts → Exact code and conflict type
- ✅ NaN values → Graceful handling, no crashes

### Documentation ✅
- ✅ README.md - Complete user guide
- ✅ BUSINESS_RULES.md - Technical specification
- ✅ PROJECT_PLAN.md - This document
- ✅ In-app Methodology tab - Transparent calculations
- ✅ Validation report - Audit trail for each run

### Configuration ✅
- ✅ cost_centers.csv - Tested with production data
- ✅ category_mapping.csv - All Pro Forma sections mapped
- ✅ pnl_account_tags.csv - All accounts categorized
- ✅ settings.json - Correct monthly hours calculation

### Testing ✅
- ✅ November 2025 test data - Complete validation
- ✅ All reconciliation checks pass
- ✅ Edge cases handled (missing data, NaN values)
- ✅ THS auto-classification tested
- ✅ Web interface tested in multiple browsers

---

## Known Limitations & Future Enhancements

### Current Limitations
- Single-user session (not multi-tenant)
- No database (file-based storage)
- No historical trend analysis
- No budget vs actual comparisons
- Port 5000 conflicts with macOS AirPlay Receiver

### Potential Future Enhancements
1. **Multi-Month Analysis**
   - Trend charts across months
   - Year-over-year comparisons
   - Rolling 12-month metrics

2. **Budget Integration**
   - Budget vs actual variance
   - Forecast vs actual tracking
   - Alerts for overruns

3. **Team Utilization**
   - Staff utilization rates
   - Capacity planning
   - Skill-based allocation

4. **Custom Reporting**
   - Report builder interface
   - Saved report templates
   - Scheduled exports

5. **Database Backend**
   - Historical data retention
   - Multi-user support
   - Advanced querying

6. **API Extensions**
   - RESTful API for integrations
   - Webhook notifications
   - Third-party data connectors

**Note:** v3.0 is considered feature-complete for current operational needs. Future enhancements should be prioritized based on user feedback and business requirements.

---

## Deployment Notes

### System Requirements
- Python 3.13 or higher
- 2GB RAM minimum
- 100MB disk space (excluding uploaded files)
- Modern web browser (Chrome, Firefox, Safari, Edge)

### Installation Steps
```bash
# 1. Clone repository
git clone [repo-url]
cd TH\ Monthly\ Performance\ Analysis

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Verify configuration
ls config/
# Should see: cost_centers.csv, category_mapping.csv, pnl_account_tags.csv, settings.json

# 5. Run application
python app.py
# Open http://localhost:5000
```

### Port Configuration
If port 5000 is in use (macOS AirPlay Receiver):
```python
# Edit app.py, change last line to:
app.run(debug=True, port=5001)
```

### Monthly Operations
1. Collect 5 files from data sources
2. Open web interface (http://localhost:5000)
3. Upload files
4. Review validation report for warnings
5. Check margin analysis for surprises
6. Download CSVs for distribution
7. Archive uploaded files in outputs/[Month]/ directory

---

## Success Metrics ✅ ACHIEVED

### Quantitative Metrics
- ✅ 100% of November 2025 data processed successfully
- ✅ All reconciliation checks pass (±$0.01 tolerance)
- ✅ Zero classification conflicts after THS auto-classification
- ✅ 6 interactive dashboard tabs fully functional
- ✅ 18 cost centers tracked (including auto-classified)
- ✅ 47 revenue centers with complete P&L
- ✅ 6 non-revenue clients identified

### Qualitative Metrics
- ✅ User interface is intuitive and professional
- ✅ Documentation is comprehensive and clear
- ✅ Error messages are actionable
- ✅ Calculations are transparent and auditable
- ✅ System is maintainable and extensible

---

## Conclusion

**Project Status:** ✅ **PRODUCTION READY**

The TH Monthly Performance Analysis System v3.0 has been successfully delivered with all planned features plus additional enhancements. The system provides:

1. **Deterministic Analysis** - Same inputs always produce same outputs
2. **Interactive Dashboard** - Web-based interface with drill-down capabilities
3. **Margin Visualization** - Clear visual representation of project performance
4. **Automated Classification** - THS codes automatically detected as internal overhead
5. **Complete Transparency** - Methodology tab explains all calculations
6. **Flexible Exports** - Download full data or current filtered view
7. **Comprehensive Validation** - Catches errors before they affect results
8. **Professional UI** - Clean, modern interface suitable for executive review

The system is ready for immediate production use and requires no further development to support current operational needs.

**Next Steps:**
1. Begin using system for monthly analysis
2. Monitor for edge cases in real-world data
3. Gather user feedback for future enhancements
4. Consider database backend if multi-user access needed

**Maintenance:**
- Update `config/cost_centers.csv` as new cost centers are added
- Update `config/pnl_account_tags.csv` if P&L account names change
- No code changes required for routine operations

**Support:**
- Documentation: README.md, BUSINESS_RULES.md
- In-app: Methodology tab, Validation Report
- Code comments: Comprehensive inline documentation

---

## Acknowledgments

- **David** - Original Excel tracker logic and walkthrough
- **Aisha** - Compensation and P&L data requirements
- **Jordana** - Harvest export specifications
- **Greg** - Pro Forma structure and allocation tags
- **Third Horizon team** - Testing and feedback

**Developed by:** Topher Rasmussen
**Completion Date:** December 31, 2025
**Version:** 3.0 (Production)
