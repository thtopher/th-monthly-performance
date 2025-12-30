# Business Rules: Monthly Performance Analysis System

**Version:** 2.0
**Date:** December 30, 2025
**Author:** Topher (based on original work by David)
**Purpose:** Technical specification for Third Horizon's automated monthly performance analysis

---

## Table of Contents

1. [Overview](#overview)
2. [Core Business Rules](#core-business-rules)
3. [File Requirements](#file-requirements)
4. [Data Classification](#data-classification)
5. [Cost Allocation Formulas](#cost-allocation-formulas)
6. [Configuration Management](#configuration-management)
7. [Validation Rules](#validation-rules)
8. [Output Specifications](#output-specifications)
9. [Quality Control](#quality-control)
10. [Troubleshooting](#troubleshooting)

---

## 1. Overview

### 1.1 Purpose

This system automates Third Horizon's monthly financial analysis by transforming operational data into actionable profitability insights. The application processes five monthly data files to generate project-level margin analysis with complete cost allocation.

### 1.2 Business Context

Third Horizon operates across three practice areas:
- **Data** - Data analytics and infrastructure consulting
- **Wellness** - Wellbeing program development and coaching
- **Next Gen Advisory** - Strategic advisory services

The firm tracks all activities through Harvest (time tracking) and maintains a master revenue Pro Forma. Monthly overhead costs include:
- **SG&A (Selling, General & Administrative)** - Business development, administration, internal meetings
- **Data Infrastructure** - Internal data platform development and external data services
- **Wellbeing Coaches** - Internal wellbeing coaching staff

### 1.3 Key Objectives

1. **Provide true project-level profitability** - Complete cost waterfall showing all allocated overhead
2. **Enable data-driven decisions** - Clear visibility into which projects drive margin vs consume resources
3. **Streamline monthly reporting** - Automated process replacing manual Excel analysis
4. **Maintain team accessibility** - Config-driven design allows business users to update settings without code changes

### 1.4 Scope

**In Scope:**
- Repeating monthly business logic for cost allocation and margin calculation
- Config-driven cost center management
- Auto-detection of non-revenue client work
- Web-based upload interface and dashboard
- CSV report generation

**Out of Scope:**
- Historical data cleanup and aggregation (TKF, HWM, HPA merges were one-time fixes)
- Forecast or budget modeling
- Integration with accounting systems
- Multi-month trend analysis (future enhancement)

---

## 2. Core Business Rules

### 2.1 The 10-Step Process

The application follows this exact sequence each month:

#### Step 1: Load and Validate Files
- Read all 5 input files (Pro Forma, Compensation, Harvest Hours, Harvest Expenses, P&L)
- Perform structural validation (required columns present, data types correct)
- Log warnings for data quality issues but proceed unless critical error

#### Step 2: Extract Revenue Table from Pro Forma
- Read "PRO FORMA 2025" sheet
- Extract rows 10-164
- Columns: Category (A), Project Name (B), Project Code (C), Monthly Revenue (M)
- Validate Cell M6 contains SUM formula for total revenue
- **Filter to revenue > $0** - these become Revenue Centers

#### Step 3: Classify All Hours and Expenses
- For each unique project code in Harvest Hours or Harvest Expenses:
  - **Revenue Center** = project code in Pro Forma with revenue > 0
  - **Cost Center** = project code in config/cost_centers.csv
  - **Non-Revenue Client** = has hours/expenses but NOT in Pro Forma with revenue > 0 (auto-detected)
- All activity must fall into exactly one category

#### Step 4: Calculate Labor Costs (All Categories)
- For each project code in Harvest Hours:
  - Join to Compensation file by Last Name
  - Calculate: Hours × Base Cost Per Hour
  - Sum by project code
- Separate totals calculated for Revenue Centers, Cost Centers, Non-Revenue Clients

#### Step 5: Calculate Expense Costs (All Categories)
- For each project code in Harvest Expenses:
  - Sum expense amounts by project code
- Separate totals calculated for Revenue Centers, Cost Centers, Non-Revenue Clients

#### Step 6: Merge Labor and Expenses to Revenue Table
- Join labor costs to revenue table by project code
- Join expense costs to revenue table by project code
- Fill missing values with 0 (project has revenue but no hours/expenses logged)

#### Step 7: Calculate SG&A Override
```
SG&A Override = Total Cost Center Labor + Total Cost Center Expenses - Starset Dev Cost

Where:
- Total Cost Center Labor = sum of all labor for projects in cost_centers.csv
- Total Cost Center Expenses = sum of all expenses for projects in cost_centers.csv
- Starset Dev Cost = labor + expenses for project code matching settings.starset_dev_code
```

**Starset Dev Cost** is separated because it contributes to Data Infrastructure, not general SG&A.

#### Step 8: Allocate SG&A to All Revenue Projects (Pro-Rata)
- SG&A Override is distributed to **ALL revenue-bearing projects** regardless of category
- Pro-rata allocation based on revenue share

```
Project SG&A Allocation = (Project Revenue / Total Revenue) × SG&A Override
```

**Example:**
- Total Revenue: $750,000
- SG&A Override: $200,000
- Project A Revenue: $75,000 (10% of total)
- Project A SG&A: $20,000 (10% of SG&A Override)

#### Step 9: Allocate Data Infrastructure to Data Projects (Pro-Rata)
```
Data Infrastructure = Starset Dev Cost + P&L Data Services

Where:
- Starset Dev Cost = from Step 7 calculation
- P&L Data Services = value from P&L file, row labeled "Data Services"
```

- Data Infrastructure is distributed **ONLY to Data category projects**
- Pro-rata allocation based on Data project revenue share

```
Project Data Allocation = (Project Revenue / Total Data Revenue) × Data Infrastructure
```

**Example:**
- Total Data Revenue: $400,000
- Data Infrastructure: $155,000
- Project A (Data) Revenue: $80,000 (20% of Data total)
- Project A Data Allocation: $31,000 (20% of Data Infrastructure)

**Non-Data projects receive $0 Data allocation.**

#### Step 10: Allocate Wellbeing Coaches to Wellness Projects (Pro-Rata)
```
Wellbeing Coaches = P&L value from row labeled "Wellbeing Coaches"
```

- Wellbeing Coaches is distributed **ONLY to Wellness category projects**
- Pro-rata allocation based on Wellness project revenue share

```
Project Wellbeing Allocation = (Project Revenue / Total Wellness Revenue) × Wellbeing Coaches
```

**Example:**
- Total Wellness Revenue: $150,000
- Wellbeing Coaches: $45,000
- Project A (Wellness) Revenue: $30,000 (20% of Wellness total)
- Project A Wellbeing Allocation: $9,000 (20% of Wellbeing Coaches)

**Non-Wellness projects receive $0 Wellbeing allocation.**

#### Step 11: Calculate Final Margins
```
Final Margin = Revenue - Labor - Expenses - SG&A - Data - Wellbeing

Margin % = (Final Margin / Revenue) × 100
```

All revenue projects now have complete cost waterfall.

### 2.2 Category Assignment Logic

Projects are tagged with one of three categories in Pro Forma Column A:
- **"Data"** - Data analytics and infrastructure work
- **"Wellness"** - Wellbeing programs and coaching
- **"Next Gen Advisory"** - Strategic advisory (does not receive Data or Wellbeing allocations)

**Rule:** Trust the Category column in Pro Forma. This is maintained by the revenue team and is authoritative.

### 2.3 Mutual Exclusivity

Every project code in Harvest must be classified into **exactly one category**:
- Revenue Center
- Cost Center
- Non-Revenue Client

A project code cannot appear in multiple categories in the same month.

**Validation Check:** If project code appears in Pro Forma with revenue > 0 AND in cost_centers.csv, raise error. Business must resolve: either it's a revenue project or a cost center.

---

## 3. File Requirements

### 3.1 Pro Forma File

**File Naming Convention:** `(Proforma)[MonthYear].xlsx`
**Example:** `(Proforma)December2025.xlsx`

**Sheet Name:** `PRO FORMA 2025`

**Structure:**

| Row | Column A | Column B | Column C | Column M | Notes |
|-----|----------|----------|----------|----------|-------|
| 6 | (Header) | (Header) | (Header) | `=SUM(M10:M164)` | **MUST be SUM formula** |
| 10-164 | Category | Project Name | Project Code | Monthly Revenue | Data rows |

**Column Specifications:**

- **Column A (Category)**
  - Required values: "Data", "Wellness", "Next Gen Advisory"
  - Case-sensitive
  - No blank values for active projects

- **Column B (Project Name)**
  - Free text description
  - Used for display in reports

- **Column C (Project Code)**
  - Unique identifier (no duplicates)
  - Must match Harvest Hours and Harvest Expenses exactly
  - Format: `XXX-YY-ZZ-AAA` (e.g., `PAD-25-01-MMA`)

- **Column M (Monthly Revenue)**
  - Numeric values only (no formulas in rows 10-164)
  - Currency formatted (optional, read as number)
  - Value of 0 or blank = project has no revenue this month

**Validation Rules:**
1. Cell M6 must contain `=SUM(M10:M164)` formula
2. Sum of M10:M164 must equal M6 evaluated value
3. No duplicate project codes
4. All Category values must be one of three allowed values

**Example:**

```
Row 6:  | Category | Project Name | Project Code | =SUM(M10:M164) |
Row 10: | Data | Marsh McLennan | PAD-25-01-MMA | 69,027 |
Row 11: | Wellness | Mindful Learning | GEH-24-01-MFL | 8,500 |
Row 12: | Next Gen Advisory | Strategic Consulting | THS-25-02-STR | 42,000 |
```

### 3.2 Compensation File

**File Naming Convention:** `(Compensation)[MonthYear].xlsx`
**Example:** `(Compensation)December2025.xlsx`

**Sheet Name:** First sheet (name flexible)

**Structure:**

| Column 1 | Column 2 |
|----------|----------|
| Last Name | Base Cost Per Hour |

**Column Specifications:**

- **Column 1 (Last Name)**
  - Must match "Last Name" column in Harvest Hours exactly
  - Case-sensitive
  - Watch for extra spaces

- **Column 2 (Base Cost Per Hour)**
  - Numeric hourly rate
  - Represents fully-loaded cost (base salary + benefits + overhead)
  - Updated monthly by Aisha

**Validation Rules:**
1. No missing Last Names
2. No missing or zero Base Cost Per Hour values
3. All Last Names in Harvest Hours must have matching Compensation entry

**Example:**

```
| Last Name | Base Cost Per Hour |
|-----------|-------------------|
| Smith     | 125.50            |
| Johnson   | 98.75             |
| Williams  | 110.00            |
```

**Update Process:**
- Aisha provides updated Compensation file monthly
- Rates may change month-to-month based on organizational changes

### 3.3 Harvest Hours File

**File Naming Convention:** `(HarvestHours)[MonthYear].xlsx`
**Example:** `(HarvestHours)December2025.xlsx`

**Export Source:** Harvest "Detailed Time Report"

**Sheet Name:** First sheet (name flexible)

**Required Columns:**

| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| Date | Date | Date hours were logged |
| Project Code | Text | Must match Pro Forma or Cost Centers |
| Last Name | Text | Must match Compensation file |
| Hours | Numeric | Hours worked |

**Additional columns may be present** (Client, Task, Notes, etc.) - they are ignored.

**Validation Rules:**
1. All dates must fall within the reporting month
2. All Project Codes must match Pro Forma or cost_centers.csv or auto-detect as Non-Revenue Client
3. All Last Names must match Compensation file
4. Hours must be positive numbers
5. Total hours across all rows becomes validation check

**Example:**

```
| Date       | Project Code  | Last Name | Hours | Client        | Task      |
|------------|---------------|-----------|-------|---------------|-----------|
| 2025-12-01 | PAD-25-01-MMA | Smith     | 8.0   | Marsh McLennan| Analysis  |
| 2025-12-02 | THS-25-01-DEV | Johnson   | 4.5   | Third Horizon | Bus Dev   |
| 2025-12-03 | GEH-24-01-MFL | Williams  | 6.0   | Mindful Learn | Coaching  |
```

**Monthly Process:**
- Jordana exports from Harvest around 3rd week of month
- Includes all time logged in the calendar month

### 3.4 Harvest Expenses File

**File Naming Convention:** `(HarvestExpenses)[MonthYear].xlsx`
**Example:** `(HarvestExpenses)December2025.xlsx`

**Export Source:** Harvest "Detailed Expenses Report"

**Sheet Name:** First sheet (name flexible)

**Required Columns:**

| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| Project Code | Text | Must match Pro Forma or Cost Centers |
| Expense Amount | Numeric | Dollar amount of expense |

**Additional columns may be present** (Date, Category, Receipt, etc.) - they are ignored.

**Validation Rules:**
1. All Project Codes must match Pro Forma or cost_centers.csv or auto-detect as Non-Revenue Client
2. Expense Amount must be positive numbers
3. Total expenses across all rows becomes validation check

**Example:**

```
| Date       | Project Code  | Expense Amount | Category | Notes        |
|------------|---------------|----------------|----------|--------------|
| 2025-12-05 | PAD-25-01-MMA | 450.00         | Travel   | Flight SFO   |
| 2025-12-12 | GEH-24-01-MFL | 125.50         | Materials| Workshop kits|
```

**Note:** Expenses are less common than hours but follow same classification logic.

### 3.5 P&L File

**File Naming Convention:** `(P&L)[MonthYear].xlsx`
**Example:** `(P&L)December2025.xlsx`

**Sheet Name:** Flexible (application searches by row label)

**Required Row Labels:**

| Row Label | Data Column | Description |
|-----------|-------------|-------------|
| "Data Services" | Monthly value | External data platform costs |
| "Wellbeing Coaches" | Monthly value | Internal wellbeing staff costs |

**Search Logic:**
- Application searches for row where first column contains "Data Services" (case-insensitive)
- Extracts value from corresponding month column
- Same for "Wellbeing Coaches"

**This flexible design allows:**
- P&L template to change structure month-to-month
- Row order doesn't matter
- Additional rows are ignored

**Example:**

```
| Account              | Jan    | Feb    | ... | Dec    |
|---------------------|--------|--------|-----|--------|
| Revenue             | 750000 | 820000 | ... | 900000 |
| Data Services       | 12500  | 12500  | ... | 13000  |
| Wellbeing Coaches   | 45000  | 45000  | ... | 48000  |
| Office Rent         | 8000   | 8000   | ... | 8000   |
```

**Validation Rules:**
1. "Data Services" row must exist
2. "Wellbeing Coaches" row must exist
3. Values must be positive numbers

---

## 4. Data Classification

### 4.1 Classification Categories

All project codes in the system are classified into one of three mutually exclusive categories:

#### Revenue Centers
**Definition:** Client projects with revenue > $0 in the current reporting month

**Criteria:**
- Project code appears in Pro Forma
- Revenue value in Column M > 0

**Treatment:**
- Receive direct labor costs (hours × rates)
- Receive direct expense costs
- Receive pro-rata SG&A allocation (all revenue projects)
- Receive pro-rata Data Infrastructure allocation (Data category only)
- Receive pro-rata Wellbeing allocation (Wellness category only)
- Appear in Revenue Adjustment Table with complete cost waterfall

**Example:**
```
Project Code: PAD-25-01-MMA
Pro Forma Revenue: $69,027
Category: Data
→ Classified as Revenue Center
→ Receives: Labor + Expenses + SG&A + Data Infrastructure
```

#### Cost Centers
**Definition:** Internal overhead activities tracked separately

**Criteria:**
- Project code appears in `config/cost_centers.csv`

**Treatment:**
- Labor and expense costs are calculated
- **Starset Dev Cost** (code from settings.starset_dev_code) is separated for Data Infrastructure
- Remaining cost center costs become **SG&A Override**
- Costs are allocated to revenue projects (not shown per-project in cost center report)
- Reported separately in Cost Center Summary

**Example:**
```
Project Code: THS-25-01-DEV (Business Development)
In cost_centers.csv: Yes
Labor: $25,000
Expenses: $2,000
→ Classified as Cost Center
→ Contributes to SG&A Override pool
```

**Special Case: Starset Dev**
```
Project Code: THS-25-01-SAD (Starset Dev Cost)
In cost_centers.csv: Yes
Matches settings.starset_dev_code: Yes
Labor: $120,000
Expenses: $8,000
→ Classified as Cost Center
→ Contributes to Data Infrastructure pool (not SG&A)
```

#### Non-Revenue Clients
**Definition:** Client work performed without revenue recognition in current month

**Criteria:**
- Has hours logged in Harvest Hours OR expenses in Harvest Expenses
- Does NOT appear in Pro Forma with revenue > 0
- Does NOT appear in cost_centers.csv

**Auto-Detection:** This category is automatically detected. No manual list to maintain.

**Treatment:**
- Labor and expense costs are calculated
- Costs are tracked for visibility
- **NOT allocated to revenue projects** (these are true costs without revenue offset)
- Reported in Non-Revenue Client table

**Example:**
```
Project Code: THS-24-05-XYZ (Old project)
Pro Forma Revenue: $0 (or not in Pro Forma)
Harvest Hours: 15 hours logged
→ Classified as Non-Revenue Client
→ Costs tracked but not allocated elsewhere
```

**Why This Matters:**
- Shows true cost of proposal work, client onboarding, or wrap-up activities
- Helps business understand investment in non-billable client relationships

### 4.2 Classification Decision Tree

```
For each unique project code in Harvest:

1. Is project code in Pro Forma with Revenue > 0?
   YES → Revenue Center
   NO → Go to step 2

2. Is project code in config/cost_centers.csv?
   YES → Cost Center
   NO → Go to step 3

3. Non-Revenue Client (auto-detected)
```

### 4.3 Handling Edge Cases

**Case 1: Project in Pro Forma but Revenue = $0**
- Not a Revenue Center (revenue must be > 0)
- If has hours/expenses → Non-Revenue Client
- Rationale: No revenue to allocate overhead against

**Case 2: Project code in both Pro Forma and cost_centers.csv**
- **Error condition** - business must resolve
- A project cannot be both a client project and internal overhead
- Validation check will flag this

**Case 3: Project code in Harvest but nowhere else**
- Auto-classify as Non-Revenue Client
- Log warning for review
- Common for new projects not yet in Pro Forma

---

## 5. Cost Allocation Formulas

### 5.1 SG&A Override

#### Calculation

```
SG&A Override = Total Cost Center Costs - Starset Dev Cost

Where:
  Total Cost Center Costs = Σ (Labor + Expenses) for all codes in cost_centers.csv
  Starset Dev Cost = Labor + Expenses for project code = settings.starset_dev_code
```

#### Components

**Typical Cost Centers (included in SG&A):**
- Business Development (THS-25-01-DEV)
- Business Administration (THS-25-01-BAD)
- Internal Meetings (THS-25-01-MTG)
- Professional Development (THS-25-01-PRD)
- Marketing (THS-25-01-MKT)

**Excluded from SG&A:**
- Starset Dev Cost (THS-25-01-SAD) → goes to Data Infrastructure

#### Allocation Formula

SG&A Override is distributed to **ALL revenue-bearing projects** pro-rata by revenue:

```
Project SG&A Allocation = (Project Revenue / Total Revenue) × SG&A Override
```

#### Worked Example

**Inputs:**
- Total Revenue (all projects): $750,000
- Business Development Labor: $20,000
- Business Development Expenses: $3,000
- Business Administration Labor: $15,000
- Internal Meetings Labor: $8,000
- Starset Dev Labor: $120,000
- Starset Dev Expenses: $8,000

**Calculation:**
```
Total Cost Center Costs = ($20,000 + $3,000) + $15,000 + $8,000 + ($120,000 + $8,000)
                        = $23,000 + $15,000 + $8,000 + $128,000
                        = $174,000

Starset Dev Cost = $120,000 + $8,000 = $128,000

SG&A Override = $174,000 - $128,000 = $46,000
```

**Allocation to Projects:**

| Project | Revenue | Revenue % | SG&A Allocation |
|---------|---------|-----------|-----------------|
| Project A | $300,000 | 40% | $18,400 |
| Project B | $225,000 | 30% | $13,800 |
| Project C | $150,000 | 20% | $9,200 |
| Project D | $75,000 | 10% | $4,600 |
| **Total** | **$750,000** | **100%** | **$46,000** |

**Validation:** Sum of allocations ($46,000) must equal SG&A Override exactly.

### 5.2 Data Infrastructure

#### Calculation

```
Data Infrastructure = Starset Dev Cost + P&L Data Services

Where:
  Starset Dev Cost = Labor + Expenses for project code = settings.starset_dev_code
  P&L Data Services = Value from P&L file, row labeled "Data Services"
```

#### Components

**Starset Dev Cost:**
- Internal development of Third Horizon's data platform
- Staff time (Ike, data engineers) spent building proprietary tools
- Infrastructure costs (servers, APIs, databases)

**P&L Data Services:**
- External SaaS platforms (Snowflake, Tableau, etc.)
- Third-party data subscriptions
- Cloud infrastructure costs

#### Allocation Formula

Data Infrastructure is distributed **ONLY to Data category projects** pro-rata by Data revenue:

```
Project Data Allocation = (Project Revenue / Total Data Revenue) × Data Infrastructure

Where:
  Total Data Revenue = Σ Revenue for projects with Category = "Data"
```

**Projects with Category = "Wellness" or "Next Gen Advisory" receive $0 Data allocation.**

#### Worked Example

**Inputs:**
- Starset Dev Labor: $120,000
- Starset Dev Expenses: $8,000
- P&L Data Services: $27,500
- Total Data Revenue: $400,000

**Calculation:**
```
Data Infrastructure = ($120,000 + $8,000) + $27,500
                    = $128,000 + $27,500
                    = $155,500
```

**Allocation to Data Projects:**

| Project | Category | Revenue | Data Revenue % | Data Allocation |
|---------|----------|---------|----------------|-----------------|
| Project A | Data | $200,000 | 50% | $77,750 |
| Project B | Data | $120,000 | 30% | $46,650 |
| Project C | Data | $80,000 | 20% | $31,100 |
| Project D | Wellness | $150,000 | N/A | $0 |
| Project E | Advisory | $200,000 | N/A | $0 |
| **Data Total** | | **$400,000** | **100%** | **$155,500** |

**Validation:** Sum of Data allocations ($155,500) must equal Data Infrastructure exactly.

### 5.3 Wellbeing Coaches

#### Calculation

```
Wellbeing Coaches = P&L value from row labeled "Wellbeing Coaches"
```

#### Components

**Wellbeing Coaches:**
- Internal wellbeing coaching staff (Lauren, etc.)
- Staff who support Third Horizon's wellness projects
- Benefits, training, certification costs

#### Allocation Formula

Wellbeing Coaches is distributed **ONLY to Wellness category projects** pro-rata by Wellness revenue:

```
Project Wellbeing Allocation = (Project Revenue / Total Wellness Revenue) × Wellbeing Coaches

Where:
  Total Wellness Revenue = Σ Revenue for projects with Category = "Wellness"
```

**Projects with Category = "Data" or "Next Gen Advisory" receive $0 Wellbeing allocation.**

#### Worked Example

**Inputs:**
- P&L Wellbeing Coaches: $45,000
- Total Wellness Revenue: $150,000

**Allocation to Wellness Projects:**

| Project | Category | Revenue | Wellness Revenue % | Wellbeing Allocation |
|---------|----------|---------|-------------------|---------------------|
| Project A | Wellness | $60,000 | 40% | $18,000 |
| Project B | Wellness | $54,000 | 36% | $16,200 |
| Project C | Wellness | $36,000 | 24% | $10,800 |
| Project D | Data | $400,000 | N/A | $0 |
| Project E | Advisory | $200,000 | N/A | $0 |
| **Wellness Total** | | **$150,000** | **100%** | **$45,000** |

**Validation:** Sum of Wellbeing allocations ($45,000) must equal Wellbeing Coaches exactly.

### 5.4 Complete Cost Waterfall

For each Revenue Center project, the complete cost waterfall is:

```
Revenue                     (from Pro Forma)
- Labor                     (Hours × Rates from Harvest Hours × Compensation)
- Expenses                  (from Harvest Expenses)
- SG&A Allocation           (pro-rata on total revenue)
- Data Infrastructure       (pro-rata on Data revenue, if Category = "Data")
- Wellbeing Coaches         (pro-rata on Wellness revenue, if Category = "Wellness")
= Final Margin

Margin % = (Final Margin / Revenue) × 100
```

#### Example: Data Project

| Line Item | Amount | Calculation |
|-----------|--------|-------------|
| Revenue | $200,000 | From Pro Forma |
| Labor | ($45,000) | 360 hours × $125/hr |
| Expenses | ($5,000) | Travel, materials |
| SG&A Allocation | ($12,267) | ($200K / $750K) × $46K |
| Data Infrastructure | ($77,750) | ($200K / $400K) × $155.5K |
| Wellbeing Coaches | $0 | Not Wellness project |
| **Final Margin** | **$59,983** | |
| **Margin %** | **30.0%** | $59,983 / $200,000 |

#### Example: Wellness Project

| Line Item | Amount | Calculation |
|-----------|--------|-------------|
| Revenue | $60,000 | From Pro Forma |
| Labor | ($18,000) | 180 hours × $100/hr |
| Expenses | ($1,200) | Materials |
| SG&A Allocation | ($3,680) | ($60K / $750K) × $46K |
| Data Infrastructure | $0 | Not Data project |
| Wellbeing Coaches | ($18,000) | ($60K / $150K) × $45K |
| **Final Margin** | **$19,120** | |
| **Margin %** | **31.9%** | $19,120 / $60,000 |

#### Example: Advisory Project

| Line Item | Amount | Calculation |
|-----------|--------|-------------|
| Revenue | $200,000 | From Pro Forma |
| Labor | ($60,000) | 500 hours × $120/hr |
| Expenses | ($8,000) | Travel, consulting |
| SG&A Allocation | ($12,267) | ($200K / $750K) × $46K |
| Data Infrastructure | $0 | Not Data project |
| Wellbeing Coaches | $0 | Not Wellness project |
| **Final Margin** | **$119,733** | |
| **Margin %** | **59.9%** | $119,733 / $200,000 |

---

## 6. Configuration Management

### 6.1 Cost Centers Configuration

**File:** `config/cost_centers.csv`

**Purpose:** Define which project codes are treated as internal overhead (Cost Centers) vs client work.

**Format:**
```csv
code,description
THS-25-01-DEV,Business Development
THS-25-01-BAD,Business Administration
THS-25-01-MTG,Internal Meetings
THS-25-01-SAD,Starset Dev Cost
THS-25-01-PRD,Professional Development
THS-25-01-MKT,Marketing
```

**Columns:**
- **code** - Exact project code as it appears in Harvest
- **description** - Human-readable label for reporting

**Editing:**
1. Open `config/cost_centers.csv` in Excel or text editor
2. Add new row for new cost center
3. Remove row for retired cost center
4. Edit description to clarify purpose
5. Save file
6. Restart application

**No code changes required** - application reads this file on startup.

**Validation:**
- Code column must not have duplicates
- Code must match Harvest project code exactly (case-sensitive)
- If code appears in both Pro Forma and cost_centers.csv → error

### 6.2 Application Settings

**File:** `config/settings.json`

**Purpose:** Configure application-wide parameters and business constants.

**Format:**
```json
{
  "starset_dev_code": "THS-25-01-SAD",
  "expected_work_weeks": 50,
  "hours_per_week": 52,
  "months_per_year": 12
}
```

**Parameters:**

- **starset_dev_code**
  - Project code for Starset development (internal data platform)
  - This cost center is separated from SG&A and allocated to Data Infrastructure
  - Must match a code in cost_centers.csv
  - Type: String
  - Example: "THS-25-01-SAD"

- **expected_work_weeks**
  - Annual billable weeks for capacity planning (future use)
  - Accounts for holidays, PTO, etc.
  - Type: Integer
  - Example: 50

- **hours_per_week**
  - Standard work week hours (future use)
  - Type: Integer
  - Example: 52

- **months_per_year**
  - Used for annualization calculations (future use)
  - Type: Integer
  - Example: 12

**Editing:**
1. Open `config/settings.json` in text editor
2. Modify parameter values
3. Ensure valid JSON format (quotes around strings, no trailing commas)
4. Save file
5. Restart application

**Critical Setting:**
- `starset_dev_code` must be updated if Starset project code changes
- Incorrect value will misallocate costs between SG&A and Data Infrastructure

---

## 7. Validation Rules

### 7.1 Validation Philosophy

**Flexible Validation:** The system validates data quality but allows analysis to proceed unless critical errors are found.

- **Warnings** - Logged and displayed but do not block processing
- **Errors** - Block processing and require correction

**Rationale:** Monthly data often has minor inconsistencies (name spelling, new projects not in Pro Forma yet). The system should warn but not fail, allowing business judgment.

### 7.2 Critical Validations (Must Pass)

#### File Structure
- [ ] All 5 required files uploaded
- [ ] Files are readable (.xlsx format)
- [ ] Required sheets exist (e.g., "PRO FORMA 2025")
- [ ] Required columns exist in each file

#### Revenue Integrity
- [ ] Pro Forma Cell M6 contains SUM formula
- [ ] Sum of revenue rows (M10:M164) equals Cell M6 value
- [ ] No duplicate project codes in Pro Forma

#### Data Completeness
- [ ] All project codes in Harvest match Pro Forma OR cost_centers.csv OR auto-classify
- [ ] P&L contains "Data Services" row
- [ ] P&L contains "Wellbeing Coaches" row

#### Mathematical Accuracy
- [ ] SG&A allocations sum to SG&A Override (within $0.01 tolerance)
- [ ] Data Infrastructure allocations sum to Data Infrastructure total (within $0.01 tolerance)
- [ ] Wellbeing allocations sum to Wellbeing Coaches total (within $0.01 tolerance)

#### Classification Integrity
- [ ] No project code appears in both Pro Forma and cost_centers.csv
- [ ] Every project code falls into exactly one category

**If any critical validation fails → processing stops, error displayed, user must correct.**

### 7.3 Warning Validations (Flagged but Allow Processing)

#### Data Quality Warnings
- ⚠ Staff member in Harvest Hours not found in Compensation file
  - *Action: Flag for review, assume $0 cost for now*

- ⚠ Project code in Harvest not in Pro Forma or cost_centers.csv
  - *Action: Auto-classify as Non-Revenue Client, log for review*

- ⚠ Category value in Pro Forma not one of ["Data", "Wellness", "Next Gen Advisory"]
  - *Action: Flag project, exclude from category-specific allocations*

#### Reasonableness Warnings
- ⚠ Overall margin % outside typical range (20-40%)
  - *May indicate data issue or unusual month*

- ⚠ Individual project labor as % of revenue < 15% or > 30%
  - *May indicate underutilization or overstaffing*

- ⚠ Negative margin on project < -50%
  - *May indicate project classification error*

- ⚠ Data Infrastructure total outside expected range ($150K-$160K)
  - *May indicate missing costs or unusual month*

#### Date Validation Warnings
- ⚠ Harvest Hours dates outside reporting month
  - *Should be logged to correct month, flag for Jordana*

**Warnings are logged to output and displayed on dashboard but do not block report generation.**

### 7.4 Validation Report

Each processing run generates a validation log:

```
========================================
VALIDATION REPORT - December 2025
========================================

CRITICAL CHECKS (MUST PASS):
✓ All 5 files present
✓ Pro Forma revenue sum matches Cell M6
✓ No duplicate project codes
✓ All allocation pools sum correctly

WARNINGS (REVIEW RECOMMENDED):
⚠ Staff "Nguyen" found in Harvest but not in Compensation file
  → 12 hours logged, assuming $0 cost
  → ACTION: Add Nguyen to next month's Compensation file

⚠ Project code "THS-25-03-NEW" not found in Pro Forma or Cost Centers
  → 8 hours logged, $1,200 labor cost
  → Auto-classified as Non-Revenue Client
  → ACTION: Add to Pro Forma if revenue expected

REASONABLENESS ALERTS:
⚠ Overall margin: 18.5% (below typical 20-40% range)
  → Investigate if month had unusual costs

⚠ Project "PAD-25-01-XYZ" margin: -120%
  → Revenue: $5,000, Total Costs: $11,000
  → Review if project should be active

========================================
PROCESSING COMPLETED WITH 4 WARNINGS
========================================
```

---

## 8. Output Specifications

### 8.1 Revenue Centers Report

**File:** `revenue_centers.csv`

**Purpose:** Complete project-level profitability analysis for all revenue-bearing projects.

**Columns:**

| Column Name | Data Type | Description | Example |
|-------------|-----------|-------------|---------|
| Project Code | Text | Unique identifier | PAD-25-01-MMA |
| Project Name | Text | Display name | Marsh McLennan |
| Category | Text | Data/Wellness/Advisory | Data |
| Revenue | Currency | Monthly revenue | $69,027 |
| Labor | Currency | Direct labor costs | $18,450 |
| Expenses | Currency | Direct expenses | $2,100 |
| SG&A Offset | Currency | Allocated SG&A | $4,235 |
| Data Offset | Currency | Allocated Data Infrastructure | $26,781 |
| Wellbeing Offset | Currency | Allocated Wellbeing | $0 |
| Final Margin | Currency | Net profit | $17,461 |
| Margin % | Percentage | Margin as % of revenue | 25.3% |

**Sorting:** Descending by Revenue (highest revenue projects first)

**Formatting:**
- Currency: `$X,XXX.XX`
- Percentage: `XX.X%`
- Negative values in parentheses: `($1,234)`

**Row Count:** All projects with revenue > $0 (typically 30-50 projects)

**Example:**

```csv
Project Code,Project Name,Category,Revenue,Labor,Expenses,SG&A Offset,Data Offset,Wellbeing Offset,Final Margin,Margin %
PAD-25-01-MMA,Marsh McLennan,Data,$69027,$18450,$2100,$4235,$26781,$0,$17461,25.3%
GEH-24-01-MFL,Mindful Learning,Wellness,$8500,$2800,$150,$521,$0,$2550,$2479,29.2%
THS-25-02-STR,Strategic Consulting,Next Gen Advisory,$42000,$12600,$800,$2577,$0,$0,$26023,62.0%
```

### 8.2 Cost Centers Report

**File:** `cost_centers.csv`

**Purpose:** Summary of internal overhead investment by activity type.

**Columns:**

| Column Name | Data Type | Description | Example |
|-------------|-----------|-------------|---------|
| Cost Center Code | Text | Project code | THS-25-01-DEV |
| Description | Text | Activity name | Business Development |
| Hours | Numeric | Total hours | 180 |
| Labor Cost | Currency | Hours × rates | $22,500 |
| Expense Cost | Currency | Direct expenses | $3,200 |
| Total Cost | Currency | Labor + Expenses | $25,700 |
| % of Total | Percentage | Share of cost center pool | 55.8% |

**Sorting:** Descending by Total Cost (highest cost activities first)

**Row Count:** Number of active cost centers (typically 5-10)

**Summary Row:** Total of all cost centers

**Example:**

```csv
Cost Center Code,Description,Hours,Labor Cost,Expense Cost,Total Cost,% of Total
THS-25-01-DEV,Business Development,180,$22500,$3200,$25700,55.8%
THS-25-01-BAD,Business Administration,120,$15000,$500,$15500,33.7%
THS-25-01-MTG,Internal Meetings,40,$4800,$0,$4800,10.4%
TOTAL,All Cost Centers,340,$42300,$3700,$46000,100.0%
```

**Note:** Starset Dev Cost appears in this table but its costs flow to Data Infrastructure, not SG&A.

### 8.3 Non-Revenue Clients Report

**File:** `non_revenue_clients.csv`

**Purpose:** Track client work performed without current revenue recognition.

**Columns:**

| Column Name | Data Type | Description | Example |
|-------------|-----------|-------------|---------|
| Project Code | Text | Unique identifier | THS-24-05-OLD |
| Project Name | Text | Display name (if available) | Legacy Project Wrap-up |
| Hours | Numeric | Total hours logged | 24 |
| Labor Cost | Currency | Hours × rates | $3,000 |
| Expense Cost | Currency | Direct expenses | $450 |
| Total Cost | Currency | Labor + Expenses | $3,450 |

**Sorting:** Descending by Total Cost

**Row Count:** Variable (0-15 projects, depends on proposal activity and wrap-up work)

**Summary Row:** Total of all non-revenue clients

**Example:**

```csv
Project Code,Project Name,Hours,Labor Cost,Expense Cost,Total Cost
THS-25-03-PROP,New Client Proposal,40,$5000,$1200,$6200
THS-24-05-OLD,Legacy Wrap-up,24,$3000,$450,$3450
PAD-25-02-BIZ,Biz Consulting (Pre-SOW),16,$2000,$0,$2000
TOTAL,All Non-Revenue,80,$10000,$1650,$11650
```

**Business Insight:** High non-revenue costs may indicate:
- Active proposal pipeline (future revenue)
- Projects in transition (SOW gaps)
- Client relationship investment
- Need to convert proposals to signed work

---

## 9. Quality Control

### 9.1 Mathematical Reconciliation

**Every processing run must reconcile:**

#### Revenue Reconciliation
```
Sum of Revenue Centers Revenue = Pro Forma Cell M6 Value
```

**Validation:** Exact match required (no tolerance)

#### Hours Reconciliation
```
Revenue Centers Hours + Cost Centers Hours + Non-Revenue Hours = Total Harvest Hours
```

**Validation:** Exact match required

#### Expenses Reconciliation
```
Revenue Centers Expenses + Cost Centers Expenses + Non-Revenue Expenses = Total Harvest Expenses
```

**Validation:** Exact match required

#### SG&A Allocation Reconciliation
```
Sum of all Revenue Centers "SG&A Offset" = SG&A Override
```

**Validation:** Within $0.01 (rounding tolerance)

#### Data Infrastructure Reconciliation
```
Sum of all Data Projects "Data Offset" = Data Infrastructure Total
```

**Validation:** Within $0.01 (rounding tolerance)

**Note:** Non-Data projects must have $0 Data Offset

#### Wellbeing Reconciliation
```
Sum of all Wellness Projects "Wellbeing Offset" = Wellbeing Coaches Total
```

**Validation:** Within $0.01 (rounding tolerance)

**Note:** Non-Wellness projects must have $0 Wellbeing Offset

**If any reconciliation fails → error raised, processing stops.**

### 9.2 Reasonableness Checks

**Overall Performance:**
- Typical margin %: 20-40%
- Below 15%: Flag as unusually low (investigate costs)
- Above 50%: Flag as unusually high (verify revenue)

**Project-Level Metrics:**
- Labor as % of revenue: Typical 15-30%
- Below 10%: Underutilized (or high-value advisory)
- Above 40%: Overutilized (margin risk)

**Cost Pool Sizes:**
- SG&A Override: Typically $40K-$60K/month
- Data Infrastructure: Typically $150K-$160K/month
- Wellbeing Coaches: Typically $40K-$50K/month

**Significant deviations logged as warnings for review.**

### 9.3 Data Quality Dashboard

**The web interface displays:**

✅ **All Critical Validations Passed** (green checkmark)

⚠ **4 Warnings** (yellow icon)
- Click to expand and view details

📊 **Reconciliation Summary:**
- Revenue: $750,000 ✓
- Hours: 5,420 ✓
- Expenses: $28,500 ✓
- SG&A Allocated: $46,000 ✓
- Data Allocated: $155,500 ✓
- Wellbeing Allocated: $45,000 ✓

**Download Validation Log** (button to export full validation report)

---

## 10. Troubleshooting

### 10.1 Common Errors

#### Error: "Revenue mismatch - Pro Forma sum does not match Cell M6"

**Symptoms:**
```
Expected: $750,000 (Cell M6)
Calculated: $748,200 (Sum of rows)
Difference: $1,800
```

**Causes:**
1. Cell M6 formula references wrong range
2. Duplicate project codes causing double-counting
3. Manual values in Cell M6 instead of formula
4. Hidden rows with revenue not included in sum

**Solutions:**
1. Verify Cell M6 formula is `=SUM(M10:M164)`
2. Check for duplicate project codes: `=COUNTIF(C:C, C10) > 1`
3. Ensure no manual overrides in M6
4. Unhide all rows and verify range

#### Error: "Staff member [Name] not found in Compensation file"

**Symptoms:**
```
Warning: Staff "Nguyen" logged 12 hours but not in Compensation
Assuming $0 cost per hour
```

**Causes:**
1. New hire not yet added to Compensation file
2. Name spelling mismatch between Harvest and Compensation
3. Extra spaces in names

**Solutions:**
1. Add missing staff to Compensation file with hourly rate
2. Verify exact spelling match (case-sensitive):
   - Harvest: "Nguyen"
   - Compensation: "Nguyen" ✓ (not "Ngyen" or "nguyen")
3. Use Excel TRIM() function to remove extra spaces

#### Error: "Project code [CODE] appears in both Pro Forma and Cost Centers"

**Symptoms:**
```
Error: Project code THS-25-01-XYZ found in:
- Pro Forma with $15,000 revenue
- cost_centers.csv as "Special Project"
Classification conflict - cannot be both Revenue and Cost Center
```

**Causes:**
1. Project incorrectly added to both lists
2. Client project using internal cost center code

**Solutions:**
1. Determine true nature: Is this client revenue or internal overhead?
2. If revenue → Remove from cost_centers.csv
3. If internal → Remove from Pro Forma or set revenue to $0
4. Create new project code if needed to separate activities

### 10.2 Data Quality Issues

#### Issue: Total hours seem low for the month

**Diagnostic Steps:**
1. Check Harvest Hours export date range
2. Verify all staff submitted timesheets
3. Compare to previous months' typical hours
4. Look for missing weeks in Date column

**Expected Range:** 4,000-6,000 hours/month (depends on team size)

#### Issue: Margin % is negative on most projects

**Diagnostic Steps:**
1. Verify Pro Forma revenue is current month (not YTD or annual)
2. Check if SG&A Override is abnormally high
3. Review if Data Infrastructure total is reasonable
4. Ensure Compensation rates are monthly, not annual

**Common Mistake:** Pro Forma shows annual revenue ($900K) but Harvest has monthly hours

#### Issue: Data Infrastructure allocation seems very high

**Diagnostic Steps:**
1. Verify Starset Dev hours are reasonable (not including client billable work)
2. Check P&L Data Services value is monthly (not annual or YTD)
3. Confirm data projects have sufficient revenue to absorb allocation

**Expected Range:** $150K-$160K/month for Data Infrastructure

### 10.3 File Structure Problems

#### Problem: "Sheet 'PRO FORMA 2025' not found"

**Symptoms:**
```
Error: Expected sheet "PRO FORMA 2025" not found in Pro Forma file
Available sheets: ["Pro Forma 2025", "Assumptions"]
```

**Cause:** Sheet name has extra space or different capitalization

**Solution:** Rename sheet to exactly `PRO FORMA 2025` (all caps, space between words)

#### Problem: "Required column [Name] not found"

**Symptoms:**
```
Error: Column "Project Code" not found in Harvest Hours
Available columns: ["Date", "Client", "Project", "Task", ...]
```

**Cause:** Harvest export format changed or using wrong report type

**Solution:**
1. Re-export from Harvest using "Detailed Time Report"
2. Verify column headers match expected names exactly
3. Update application if Harvest permanently changed export format

### 10.4 Allocation Warnings

#### Warning: "Data project has no Data allocation"

**Symptoms:**
```
Warning: Project PAD-25-01-XYZ is Category "Data" but received $0 Data allocation
```

**Causes:**
1. Total Data Revenue is $0 (no revenue on any Data projects)
2. Pro-rata calculation resulted in < $0.01 (rounding)

**Actions:**
1. If Total Data Revenue = $0 → Expected behavior (no pool to allocate)
2. If rounding issue → Ignore (allocation will be $0 in report)

#### Warning: "Wellness project has no Wellbeing allocation"

**Symptoms:**
```
Warning: Project GEH-24-01-XYZ is Category "Wellness" but received $0 Wellbeing allocation
```

**Cause:** P&L Wellbeing Coaches value is $0 or missing

**Actions:**
1. Verify P&L file has "Wellbeing Coaches" row
2. Check if value is correct for the month
3. If legitimately $0 (coaches on leave, etc.) → Expected behavior

### 10.5 Performance Issues

#### Issue: Web upload times out

**Cause:** Large files or slow server

**Solutions:**
1. Increase upload timeout in Flask config
2. Verify file sizes are reasonable (< 5MB each)
3. Check server resources (CPU, memory)

#### Issue: Analysis processing takes > 2 minutes

**Diagnostic:**
- Expected processing time: 10-30 seconds
- Files with > 10,000 rows may take longer

**Solutions:**
1. Optimize pandas operations (vectorize instead of loops)
2. Add progress indicators to show processing status
3. Consider background job queue for large files

---

## Appendix A: Change Log

### Version 2.0 (December 30, 2025)
- **Removed:** TKF, HWM, HPA aggregation rules (one-time historical cleanup)
- **Added:** Config-driven cost center management (cost_centers.csv)
- **Added:** Auto-detection of non-revenue clients
- **Changed:** Trust Pro Forma Category column for Data/Wellness/Advisory tags
- **Changed:** Simplified from 12 steps to 10 steps
- **Changed:** Flexible validation (warn vs fail) approach

### Version 1.0 (Original - David's PDF)
- Initial business rules specification
- Included historical aggregation logic
- Manual non-revenue client lists
- Hard-coded cost center definitions

---

## Appendix B: Glossary

**Accrual Accounting** - Revenue recognized when earned, not when cash received

**Category** - Project classification (Data, Wellness, Next Gen Advisory) determining which overhead pools apply

**Cost Center** - Internal overhead activity (business development, admin, meetings)

**Data Infrastructure** - Starset Dev Cost + P&L Data Services, allocated to Data projects only

**Final Margin** - Net profit after all costs: Revenue - Labor - Expenses - SG&A - Data - Wellbeing

**Non-Revenue Client** - Client work with hours/expenses but no revenue in current month (auto-detected)

**Pro Forma** - Master revenue forecast maintained by revenue team

**Pro-Rata** - Proportional allocation based on revenue share

**Revenue Center** - Client project with revenue > $0 in current month

**SG&A Override** - Total cost center investment minus Starset Dev Cost, allocated to all revenue projects

**Starset Dev Cost** - Internal data platform development, separated from SG&A and allocated to Data Infrastructure

**Wellbeing Coaches** - Internal wellbeing staff costs, allocated to Wellness projects only

---

## Appendix C: Quick Reference

### Monthly Processing Checklist

**Week 3 of Month:**

- [ ] Jordana exports Harvest Hours (Detailed Time Report)
- [ ] Jordana exports Harvest Expenses (Detailed Expenses Report)
- [ ] Aisha provides updated Compensation file
- [ ] Finance provides Pro Forma file (current month column)
- [ ] Finance provides P&L file

**Upload to System:**

- [ ] Navigate to `http://[app-url]:5000`
- [ ] Upload all 5 files
- [ ] Click "Process"
- [ ] Review validation warnings
- [ ] Fix critical errors if any

**Review Outputs:**

- [ ] Download `revenue_centers.csv` - review margins
- [ ] Download `cost_centers.csv` - review overhead spend
- [ ] Download `non_revenue_clients.csv` - review proposal activity
- [ ] View web dashboard - check overall performance

**Business Review:**

- [ ] Overall margin % in healthy range (20-40%)?
- [ ] Any projects with negative margins (investigate)?
- [ ] SG&A Override reasonable ($40K-$60K)?
- [ ] Data Infrastructure reasonable ($150K-$160K)?
- [ ] High non-revenue costs (proposal pipeline)?

### File Naming Convention

```
(Proforma)December2025.xlsx
(Compensation)December2025.xlsx
(HarvestHours)December2025.xlsx
(HarvestExpenses)December2025.xlsx
(P&L)December2025.xlsx
```

### Config File Locations

```
config/cost_centers.csv     - Edit to add/remove cost centers
config/settings.json        - Edit Starset dev code and parameters
```

### Key Formulas

```
SG&A Override = Cost Centers - Starset Dev

Data Infrastructure = Starset Dev + P&L Data Services

Project SG&A = (Revenue / Total Revenue) × SG&A Override

Project Data = (Revenue / Data Revenue) × Data Infrastructure

Project Wellbeing = (Revenue / Wellness Revenue) × Wellbeing Coaches

Final Margin = Revenue - Labor - Expenses - SG&A - Data - Wellbeing
```

---

**End of Business Rules Document**
