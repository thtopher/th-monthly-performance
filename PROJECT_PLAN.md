# Project Plan: Monthly Performance Analysis System

**Version:** 3.0  
**Date:** December 30, 2025  

---

## Goal

Deliver a **CLI-first** deterministic, auditable monthly analysis engine that:
- accepts five monthly source files via command-line arguments,
- produces three CSV outputs + a validation report,
- matches David's current Excel tracker logic (pro-rata allocations; contract-code joins; reimbursable filtering),
- is reproducible, auditable, and perfect for automation.

**MVP:** CLI tool (Phases 1-4, ~3-5 days)
**Future:** Optional web interface (Phases 5-6)

---

## Phase 0: CLI Infrastructure (Day 1 - Setup)

### 1. Repository initialization
- [ ] Create GitHub repo: `github.com/thtopher/th-monthly-performance`
- [ ] Initialize project structure (analysis/, config/, tests/, outputs/)
- [ ] Create .gitignore (exclude outputs/, *.xlsx, .venv/)
- [ ] Create requirements.txt (pandas, openpyxl, pytest)

### 2. CLI entry point
- [ ] Create `run_analysis.py` with argparse:
  ```python
  import argparse

  def main():
      parser = argparse.ArgumentParser(description='TH Monthly Performance Analysis')
      parser.add_argument('--month', required=True, help='Month and year (e.g., November2025)')
      parser.add_argument('--proforma', required=True, help='Path to Pro Forma file')
      parser.add_argument('--compensation', required=True, help='Path to Compensation file')
      parser.add_argument('--hours', required=True, help='Path to Harvest Hours file')
      parser.add_argument('--expenses', required=True, help='Path to Harvest Expenses file')
      parser.add_argument('--pl', required=True, help='Path to P&L file')
      parser.add_argument('--output-dir', default='./outputs', help='Output directory')

      args = parser.parse_args()

      # Pipeline execution (to be implemented)
      print(f"[INFO] Loading files for {args.month}...")

  if __name__ == '__main__':
      main()
  ```

### 3. Configuration files (initial)
- [ ] Create `config/cost_centers.csv` with demo data
- [ ] Create `config/category_mapping.csv` (BEH/PAD/MAR/WWB/CMH → Advisory/Data/Wellness)
- [ ] Create `config/pnl_account_tags.csv` (account matching rules)
- [ ] Create `config/settings.json` (hours_per_week: 50, weeks_per_year: 52, etc.)

---

## Phase 1: Align on Data Contracts (Day 1)

### 1. Confirm “contract code” normalization
- [ ] Implement `normalize_contract_code()`:
  - trim whitespace
  - remove non-breaking spaces
  - keep case
- [ ] Unit test against example Pro Forma codes with trailing spaces (e.g., `MAR-24-01-MSL `).

### 2. Define canonical intermediate tables
- [ ] `projects` (from Pro Forma)
- [ ] `hours` (from Harvest Hours)
- [ ] `expenses` (from Harvest Expenses)
- [ ] `pnl_accounts` (from P&L)

---

## Phase 2: Data Loaders (Days 2–3)

### ProFormaLoader
- [ ] Detect header row by scanning first 10 rows for month sequence
- [ ] Identify selected month column by matching `Jan…Dec`
- [ ] Extract:
  - allocation_tag from Column A (`Data` / `Wellness` / blank)
  - project_name from Column B
  - project_code from Column C
  - proforma section from nearest header row (Column B text where Column C blank)
- [ ] **Aggregate duplicates by project_code**
- [ ] Validate totals against Base Revenue (fallback: Forecasted Revenue)

### CompensationLoader
- [ ] Support Strategy A: read `Base Cost Per Hour`
- [ ] Support Strategy B: compute hourly cost from Total or components
- [ ] Validate unique staff key (Last Name) and no missing/zero hourly costs

### HarvestHoursLoader
- [ ] Read columns flexibly (synonyms)
- [ ] Validate month date range (exclude out-of-month rows with WARN)
- [ ] Output fields: date, project_code, staff_key, hours

### HarvestExpensesLoader
- [ ] Read columns flexibly (synonyms)
- [ ] **Filter reimbursable:** Billable == Yes → exclude
- [ ] Default unknown billable → warn + include
- [ ] Output fields: date, project_code, amount_included

### PnLLoader
- [ ] Load `IncomeStatement`
- [ ] Identify `Total` column (fallback: rightmost numeric)
- [ ] Extract account rows and totals
- [ ] Apply `config/pnl_account_tags.csv` to bucket accounts:
  - DATA, WORKPLACE, NIL, SGA

---

## Phase 3: Core Engine (Days 3–4)

### ProjectClassifier
- [ ] Revenue center = revenue > 0 in Pro Forma
- [ ] Cost center = listed in `config/cost_centers.csv`
- [ ] Non-revenue client = activity but not revenue center and not cost center
- [ ] Conflict (revenue & cost center) → FAIL

### CostCalculator
- [ ] Labor cost = hours × hourly_cost (join on staff key)
- [ ] Expense cost = sum included expenses
- [ ] Merge direct costs into revenue table

### OverheadAllocator
- [ ] Compute pools:
  - SG&A pool (P&L SGA + optional cost center overhead)
  - Data pool (P&L DATA + optional DATA cost center pool)
  - Workplace pool (P&L WORKPLACE)
- [ ] Allocate:
  - SG&A across all revenue centers by revenue share
  - Data across Data-tagged revenue centers by revenue share
  - Workplace across Wellness-tagged revenue centers by revenue share
- [ ] Validate allocation totals match pool totals (±$0.01)

### MarginCalculator
- [ ] Compute margin dollars and margin %
- [ ] Ensure no division-by-zero errors (skip margin% when revenue == 0)

---

## Phase 4: Validation & Reporting (Day 5)

### Validators
- [ ] DataCompletenessValidator (required files; required columns)
- [ ] KeyIntegrityValidator (missing comp rates; duplicate staff key)
- [ ] MathematicalValidator (revenue totals; pool allocations; reconciliations)
- [ ] ClassificationValidator (revenue vs cost center conflicts)

### Outputs
- [ ] Write revenue_centers.csv
- [ ] Write cost_centers.csv
- [ ] Write non_revenue_clients.csv
- [ ] Write validation_report.md

---

## Phase 5: QA Against David's Baseline (Day 5)

**Critical for CLI MVP:**
- [ ] Run engine on November 2025 example set via CLI
- [ ] Compare outputs to David's tracker totals (revenue, labor, expense, allocations)
- [ ] Review mismatches with David and adjust configs:
  - cost center definitions
  - P&L account tags
  - allocation tag handling
- [ ] Iterate on validation rules based on real-world edge cases

---

## Phase 6: Web Upload UI (Days 6–7 - Optional Future)

**Post-MVP Enhancement:**
- [ ] Create `app.py` Flask application
- [ ] Build upload form accepting 5 files
- [ ] Month selector (or infer month from filenames)
- [ ] Run pipeline backend, show validation report in browser
- [ ] Provide download links for CSV outputs

---

## Definition of Done (CLI MVP)

### Must Have:
- ✅ CLI runs end-to-end with November 2025 example files
- ✅ All critical validations enforced (missing comp rates → FAIL)
- ✅ Allocations reconcile to pools (±$0.01)
- ✅ Outputs are reproducible and auditable
- ✅ Duplicate contract codes aggregated correctly
- ✅ Column A allocation tags respected
- ✅ Config-driven P&L account bucketing works
- ✅ validation_report.md shows all checks and warnings
- ✅ Console output provides clear progress feedback

### Success Command:
```bash
python run_analysis.py \
  --month "November2025" \
  --proforma "demo_files/(Proforma)November2025.xlsx" \
  --compensation "demo_files/(Compensation)November2025.xlsx" \
  --hours "demo_files/(HarvestHours)November2025.xlsx" \
  --expenses "demo_files/(HarvestExpenses)November2025.xlsx" \
  --pl "demo_files/(P&L)November2025.xlsx"

# Output: 4 files in outputs/November2025/
# - revenue_centers.csv (47 projects with correct margins)
# - cost_centers.csv (15 cost centers)
# - non_revenue_clients.csv (exceptions)
# - validation_report.md (all checks passed)
```

---

## Timeline

| Phase | Days | Deliverable | Status |
|-------|------|-------------|--------|
| 0. CLI Infrastructure | 1 | run_analysis.py skeleton, configs | **Start Here** |
| 1. Data Contracts | 1 | normalize_contract_code(), intermediate tables | |
| 2. Data Loaders | 2-3 | All 5 loaders with Column A tags, aggregation, P&L bucketing | |
| 3. Core Engine | 1 | Classification, cost calc, allocation, margin | |
| 4. Validation & Output | 1 | All validators, CSV writers, validation report | **CLI MVP Complete** |
| 5. QA vs Baseline | 1 | Compare to David's Excel, iterate on edge cases | |
| 6. Web UI (Optional) | 2-3 | Flask upload interface | Post-MVP |

**Target:** CLI MVP in 5 days
**Stretch:** Web interface in 7-8 days total

