"""
Data Loaders for TH Monthly Performance Analysis

Loads and validates the 5 source files:
1. Pro Forma (revenue, allocation tags, duplicate aggregation)
2. Compensation (Strategy A: direct read, Strategy B: compute)
3. Harvest Hours (time tracking)
4. Harvest Expenses (with reimbursable filtering)
5. P&L (config-driven account bucketing)
"""

import pandas as pd
from pathlib import Path


def normalize_contract_code(code: str) -> str:
    """
    Normalize contract code for consistent joins.

    Rules:
    - Trim whitespace
    - Remove non-breaking spaces
    - Preserve case (codes are case-sensitive)
    - Treat empty/missing as invalid

    Args:
        code: Raw contract code from source file

    Returns:
        Normalized contract code

    Raises:
        ValueError: If code is empty after normalization
    """
    if pd.isna(code):
        raise ValueError("Contract code is missing")

    # Convert to string and normalize whitespace
    normalized = str(code).strip()

    # Remove non-breaking spaces and other invisible characters
    normalized = normalized.replace('\xa0', ' ')  # Non-breaking space
    normalized = ' '.join(normalized.split())  # Collapse multiple spaces

    if not normalized:
        raise ValueError("Contract code is empty after normalization")

    return normalized


class ProFormaLoader:
    """
    Load Pro Forma revenue file.

    v3.0 Requirements:
    - Read Column A for allocation tags (Data/Wellness/blank)
    - Aggregate duplicate contract codes
    - Detect conflict if same code has both Data and Wellness tags
    - Dynamic month column detection
    - Section-based category headers (BEH/PAD/MAR/WWB/CMH)
    """

    def __init__(self, filepath: str, month: str):
        self.filepath = Path(filepath)
        self.month = month

    def load(self) -> pd.DataFrame:
        """
        Load Pro Forma file.

        Returns:
            DataFrame matching PROFORMA_SCHEMA (after aggregation)
        """
        df = pd.read_excel(self.filepath, sheet_name='PRO FORMA 2025', header=None)

        # Find header row (contains months) and month column
        header_row_idx = self._find_header_row(df)
        header = df.iloc[header_row_idx]
        month_col_idx = self._find_month_column(header, self.month)

        # Find total revenue row
        total_revenue_row_idx = self._find_total_revenue_row(df)
        total_revenue = float(df.iloc[total_revenue_row_idx, month_col_idx])

        # Extract projects
        projects = []
        current_section = None

        for idx in range(header_row_idx + 1, len(df)):
            row = df.iloc[idx]
            col_a = row[0]  # Allocation tag
            col_b = row[1]  # Project name or section header
            col_c = row[2]  # Contract code
            revenue_val = row[month_col_idx]

            # Skip empty rows
            if pd.isna(col_b) and pd.isna(col_c):
                continue

            # Section header (has name but no code)
            if pd.notna(col_b) and pd.isna(col_c):
                current_section = self._extract_section_name(str(col_b))
                continue

            # Project row (has both name and code)
            if pd.notna(col_b) and pd.notna(col_c):
                allocation_tag = str(col_a).strip() if pd.notna(col_a) else ''

                projects.append({
                    'contract_code_raw': str(col_c),
                    'project_name': str(col_b).strip(),
                    'proforma_section': current_section,
                    'allocation_tag': allocation_tag if allocation_tag in ['Data', 'Wellness'] else '',
                    'revenue': float(revenue_val) if pd.notna(revenue_val) else 0.0,
                })

        projects_df = pd.DataFrame(projects)
        if projects_df.empty:
            raise ValueError("No projects found in Pro Forma after parsing")

        # Normalize codes
        projects_df['contract_code'] = projects_df['contract_code_raw'].apply(normalize_contract_code)

        # Aggregate duplicates and validate allocation tags
        aggregated = self._aggregate_duplicates(projects_df)

        # Map categories from config
        category_mapping = self._load_category_mapping()
        aggregated['analysis_category'] = aggregated['proforma_section'].map(category_mapping)
        aggregated['analysis_category'].fillna('Unknown', inplace=True)

        # Validate total revenue
        calculated_total = aggregated['revenue'].sum()
        if abs(calculated_total - total_revenue) > 0.01:
            raise ValueError(
                f"Revenue sum mismatch: calculated ${calculated_total:,.2f} "
                f"vs total ${total_revenue:,.2f} (diff: ${abs(calculated_total - total_revenue):,.2f})"
            )

        print(f"[INFO] ✓ Pro Forma: {len(aggregated)} projects, revenue ${total_revenue:,.2f}")
        print(
            f"[INFO] ✓ Allocation tags: {sum(aggregated['allocation_tag'] == 'Data')} Data, "
            f"{sum(aggregated['allocation_tag'] == 'Wellness')} Wellness, "
            f"{sum(aggregated['allocation_tag'] == '')} untagged"
        )

        return aggregated[['contract_code', 'project_name', 'proforma_section',
                           'analysis_category', 'allocation_tag', 'revenue']]

    def _find_header_row(self, df: pd.DataFrame) -> int:
        """
        Find header row by scanning for month sequence.

        Looks for rows containing 'Jan', 'Feb', 'Mar' (case-insensitive).
        """
        max_scan = min(10, len(df))
        for idx in range(max_scan):
            row_text = ' '.join(df.iloc[idx].astype(str))
            if all(month in row_text for month in ['Jan', 'Feb', 'Mar']):
                return idx
        raise ValueError("Cannot find header row with month sequence (Jan, Feb, Mar)")

    def _find_month_column(self, header: pd.Series, month_name: str) -> int:
        """
        Find column index for specified month.
        Tries full name, 3-letter abbrev, and case-insensitive.
        """
        # Try full month name
        for idx, val in enumerate(header):
            if str(val).strip() == month_name:
                return idx

        # Try abbreviated (first 3 letters)
        month_abbrev = month_name[:3]
        for idx, val in enumerate(header):
            if str(val).strip() == month_abbrev:
                return idx

        # Try case-insensitive
        for idx, val in enumerate(header):
            if str(val).strip().lower() == month_name.lower():
                return idx

        raise ValueError(f"Cannot find month column for '{month_name}' in header")

    def _find_total_revenue_row(self, df: pd.DataFrame) -> int:
        """
        Find row containing total revenue by scanning column B.

        Looks for 'Base Revenue' or 'Forecasted Revenue' in column B within first 20 rows.
        """
        max_scan = min(20, len(df))
        for idx in range(max_scan):
            col_b_val = str(df.iloc[idx, 1]).lower()
            if 'base revenue' in col_b_val or 'forecasted revenue' in col_b_val:
                return idx
        raise ValueError("Cannot find total revenue row (Base Revenue or Forecasted Revenue)")

    def _extract_section_name(self, text: str) -> str:
        """Extract section name from header text (e.g., BEH/PAD/MAR/WWB/CMH)."""
        text = text.strip()
        for pattern in ['BEH', 'PAD', 'MAR', 'WWB', 'CMH']:
            if pattern in text.upper():
                return text
        return text

    def _aggregate_duplicates(self, projects_df: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregate duplicate contract codes with conflict detection for allocation_tag.
        """
        # Check for conflicts BEFORE aggregation
        for code in projects_df['contract_code'].unique():
            code_rows = projects_df[projects_df['contract_code'] == code]
            tags = set(code_rows['allocation_tag'].dropna())
            tags.discard('')
            if 'Data' in tags and 'Wellness' in tags:
                raise ValueError(
                    f"Allocation tag conflict for contract code '{code}': Found both 'Data' and 'Wellness' tags. Please fix Pro Forma."
                )

        def reconcile_tag(tags):
            tags_set = set(tags.dropna())
            tags_set.discard('')
            if 'Data' in tags_set:
                return 'Data'
            if 'Wellness' in tags_set:
                return 'Wellness'
            return ''

        aggregated = projects_df.groupby('contract_code').agg({
            'project_name': 'first',
            'proforma_section': 'first',
            'allocation_tag': reconcile_tag,
            'revenue': 'sum',
        }).reset_index()

        duplicates_count = len(projects_df) - len(aggregated)
        if duplicates_count > 0:
            print(f"[INFO] ✓ Aggregated {duplicates_count} duplicate contract codes")

        return aggregated

    def _load_category_mapping(self) -> dict:
        """Load Pro Forma section -> analysis category mapping from config/category_mapping.csv."""
        mapping_df = pd.read_csv('config/category_mapping.csv')
        return dict(zip(mapping_df['pro_forma_category'], mapping_df['analysis_category']))


class CompensationLoader:
    """
    Load Compensation file with dual strategy.

    v3.0 Requirements:
    - Strategy A (Preferred): Read 'Base Cost Per Hour' directly
    - Strategy B (Fallback): Compute from Total or components
    - Expected hours per month: 216.67
    - Unique Last Name validation (FAIL if duplicates)
    """

    def __init__(self, filepath: str):
        self.filepath = Path(filepath)
        self.expected_hours_per_month = 216.6667

    def load(self) -> pd.DataFrame:
        """
        Load Compensation file.

        Returns:
            DataFrame matching COMPENSATION_SCHEMA
        """
        df = pd.read_excel(self.filepath)

        # Strategy A: direct read of hourly cost
        base_cost_col = self._find_column(df, ['Base Cost Per Hour', 'Base Cost/Hour', 'Hourly Cost'])
        if base_cost_col:
            print(f"[INFO] ✓ Strategy A: Read '{base_cost_col}' directly")
            result = self._load_strategy_a(df, base_cost_col)
        else:
            print("[INFO] Strategy B: Computing hourly cost from components")
            result = self._load_strategy_b(df)

        # Validate unique Last Name
        last_name_col = self._find_column(df, ['Last Name', 'LastName', 'Name'], required=True)
        duplicates = result[result['staff_key'].duplicated()]
        if len(duplicates) > 0:
            dup_names = ', '.join(duplicates['staff_key'].tolist())
            raise ValueError(
                f"Duplicate Last Names found in Compensation file: {dup_names}. Cannot use Last Name as unique key. Consider adding Employee ID."
            )

        print(f"[INFO] ✓ {len(result)} staff members, avg ${result['hourly_cost'].mean():.2f}/hr")
        return result

    def _load_strategy_a(self, df: pd.DataFrame, cost_col: str) -> pd.DataFrame:
        """Strategy A: Read Base Cost Per Hour directly."""
        last_name_col = self._find_column(df, ['Last Name', 'LastName'], required=True)
        return pd.DataFrame({
            'staff_key': df[last_name_col].astype(str).str.strip(),
            'hourly_cost': pd.to_numeric(df[cost_col], errors='coerce'),
            'strategy_used': 'A',
        })

    def _load_strategy_b(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Strategy B: Compute hourly cost from Total or components.

        Formula:
            Monthly Cost = Base + Taxes + ICHRA + 401k + Assistant + Wellbeing + Travel
            Hourly Cost = Monthly Cost / 216.6667
        """
        last_name_col = self._find_column(df, ['Last Name', 'LastName'], required=True)

        total_col = self._find_column(df, ['Total', 'Total Compensation', 'Monthly Total'])
        if total_col:
            monthly_cost = pd.to_numeric(df[total_col], errors='coerce')
        else:
            components = {
                'base': self._find_column(df, ['Base Compensation', 'Base', 'Base Comp'], required=True),
                'taxes': self._find_column(df, ['Company Taxes Paid', 'Taxes', 'Company Taxes'], required=True),
                'ichra': self._find_column(df, ['ICHRA Contribution', 'ICHRA'], required=True),
                'k401': self._find_column(df, ['401k Match', '401k', '401K Match'], required=True),
                'assistant': self._find_column(df, ['Executive Assistant', 'Assistant', 'Exec Assistant'], required=True),
                'wellbeing': self._find_column(df, ['Well Being Card', 'Wellbeing', 'Well-being'], required=True),
                'travel': self._find_column(df, ['Travel & Expenses', 'Travel', 'Travel and Expenses'], required=True),
            }
            monthly_cost = sum(pd.to_numeric(df[col], errors='coerce') for col in components.values())

        hourly_cost = monthly_cost / self.expected_hours_per_month
        return pd.DataFrame({
            'staff_key': df[last_name_col].astype(str).str.strip(),
            'hourly_cost': hourly_cost,
            'strategy_used': 'B',
        })

    def _find_column(self, df: pd.DataFrame, candidates: list, required: bool = False) -> str | None:
        """
        Find column by trying multiple candidate names (case-insensitive).

        Args:
            df: DataFrame to search
            candidates: List of column names to try
            required: If True, raise error if not found

        Returns:
            Column name if found, None otherwise
        """
        for candidate in candidates:
            for col in df.columns:
                if str(col).strip().lower() == candidate.lower():
                    return col
        if required:
            raise ValueError(f"Required column not found. Tried: {candidates}")
        return None


class HarvestHoursLoader:
    """Load Harvest Hours time tracking file."""

    def __init__(self, filepath: str, month: str):
        self.filepath = Path(filepath)
        self.month = month

    def load(self) -> pd.DataFrame:
        """
        Load Harvest Hours file.

        Returns:
            DataFrame matching HOURS_SCHEMA
        """
        df = pd.read_excel(self.filepath)

        # Find columns flexibly
        date_col = self._find_column(df, ['Date', 'Spent Date', 'Work Date'], required=True)
        code_col = self._find_column(df, ['Project Code', 'Project', 'Code'], required=True)
        hours_col = self._find_column(df, ['Hours', 'Hours (h)', 'Hours (decimal)'], required=True)
        name_col = self._find_column(df, ['Last Name', 'LastName', 'Person'], required=True)

        # Convert to standard schema
        result = pd.DataFrame({
            'date': pd.to_datetime(df[date_col]),
            'contract_code': df[code_col].astype(str).apply(normalize_contract_code),
            'staff_key': df[name_col].astype(str).str.strip(),
            'hours': pd.to_numeric(df[hours_col], errors='coerce'),
        })

        # Validate month date range (WARN if outside)
        month_start, month_end = self._get_month_range(self.month)
        outside_month = result[(result['date'] < month_start) | (result['date'] > month_end)]
        if len(outside_month) > 0:
            print(f"[WARN] {len(outside_month)} Harvest Hours rows outside month range (excluded)")
            result = result[(result['date'] >= month_start) & (result['date'] <= month_end)]

        print(f"[INFO] ✓ Harvest Hours: {len(result)} rows, {result['hours'].sum():.1f} total hours")
        return result

    def _find_column(self, df: pd.DataFrame, candidates: list, required: bool = False) -> str | None:
        for candidate in candidates:
            for col in df.columns:
                if str(col).strip().lower() == candidate.lower():
                    return col
        if required:
            raise ValueError(f"Required column not found. Tried: {candidates}")
        return None

    def _get_month_range(self, month: str) -> tuple:
        """
        Parse month string like 'November2025' and return (start_date, end_date).
        """
        import re
        from datetime import datetime
        from calendar import monthrange

        m = re.match(r"([A-Za-z]+)(\d{4})", month)
        if not m:
            raise ValueError(f"Invalid month format: {month}. Expected e.g. 'November2025'")
        month_name, year_str = m.groups()
        year = int(year_str)
        try:
            dt = datetime.strptime(month_name, "%B")
            month_num = dt.month
        except ValueError:
            try:
                dt = datetime.strptime(month_name[:3], "%b")
                month_num = dt.month
            except ValueError:
                raise ValueError(f"Invalid month name: {month_name}")

        start = datetime(year, month_num, 1)
        end = datetime(year, month_num, monthrange(year, month_num)[1])
        return start, end


class HarvestExpensesLoader:
    """
    Load Harvest Expenses file with reimbursable filtering.

    v3.0 Requirements:
    - Filter by Billable column
    - Billable = Yes → exclude (reimbursable)
    - Billable = No → include (non-reimbursable)
    - Billable = blank → warn + include (conservative)
    """

    def __init__(self, filepath: str):
        self.filepath = Path(filepath)

    def load(self) -> pd.DataFrame:
        """Load and filter Harvest Expenses file."""
        df = pd.read_excel(self.filepath)

        # Flexible columns
        date_col = self._find_column(df, ['Date', 'Spent Date', 'Expense Date'], required=True)
        code_col = self._find_column(df, ['Project Code', 'Project', 'Code'], required=True)
        amount_col = self._find_column(df, ['Amount', 'Total Amount', 'Amount (USD)'], required=True)
        billable_col = self._find_column(df, ['Billable', 'Is Billable', 'Billable?'], required=True)

        # Normalize basic frame
        base = pd.DataFrame({
            'date': pd.to_datetime(df[date_col]),
            'contract_code': df[code_col].astype(str).apply(normalize_contract_code),
            'amount': pd.to_numeric(df[amount_col], errors='coerce').fillna(0.0),
            'billable': df[billable_col],
        })

        # Interpret billable values (Yes/No/blank)
        def parse_billable(v):
            if pd.isna(v):
                return None
            s = str(v).strip().lower()
            if s in ['yes', 'y', 'true', '1']:
                return True
            if s in ['no', 'n', 'false', '0']:
                return False
            return None  # unknown

        base['billable_bool'] = base['billable'].apply(parse_billable)

        # Exclusions and inclusions
        reimbursable = base[base['billable_bool'] == True]
        non_reimbursable = base[base['billable_bool'] == False]
        unknown = base[base['billable_bool'].isna()]

        if len(unknown) > 0:
            print(f"[WARN] {len(unknown)} expenses have unknown Billable value (included as non-reimbursable)")

        included = pd.concat([non_reimbursable, unknown], ignore_index=True)
        excluded_count = len(reimbursable)
        if excluded_count > 0:
            print(f"[INFO] ✓ Excluded {excluded_count} reimbursable expenses (Billable=Yes)")

        # Final output
        out = included[['date', 'contract_code', 'amount']].copy()
        out['was_reimbursable'] = False
        return out

    def _find_column(self, df: pd.DataFrame, candidates: list, required: bool = False) -> str | None:
        for candidate in candidates:
            for col in df.columns:
                if str(col).strip().lower() == candidate.lower():
                    return col
        if required:
            raise ValueError(f"Required column not found. Tried: {candidates}")
        return None


class PnLLoader:
    """
    Load P&L file with config-driven account bucketing.

    v3.0 Requirements:
    - Read IncomeStatement sheet
    - Identify Total column
    - Apply config/pnl_account_tags.csv for bucketing
    - Buckets: DATA, WORKPLACE, NIL, SGA (default)
    """

    def __init__(self, filepath: str, config_path: str = "config/pnl_account_tags.csv"):
        self.filepath = Path(filepath)
        self.config_path = Path(config_path)

    def load(self) -> pd.DataFrame:
        """Load and bucket P&L accounts."""
        df = pd.read_excel(self.filepath, sheet_name='IncomeStatement', header=0)

        # Determine total column index
        total_col_idx = self._find_total_column(df)

        # Load account tagging config
        tags_config = pd.read_csv(self.config_path)

        # Extract accounts and bucket them
        results = []
        unmatched = []

        for idx, row in df.iterrows():
            account_name = str(row[0]).strip()  # Account name in first column
            amount = row[total_col_idx]
            if pd.isna(amount) or amount == 0:
                continue

            bucket, matched_by = self._match_account(account_name, tags_config)
            if bucket == 'SGA' and matched_by == 'default':
                unmatched.append(account_name)

            results.append({
                'account_name': account_name,
                'amount': float(amount),
                'bucket': bucket,
                'matched_by': matched_by,
            })

        result = pd.DataFrame(results)

        if unmatched:
            print(f"[WARN] {len(unmatched)} P&L accounts defaulted to SG&A (unmatched):")
            for acc in unmatched[:5]:
                print(f"  - {acc}")
            if len(unmatched) > 5:
                print(f"  ... and {len(unmatched) - 5} more")

        # Print bucket summary
        for bucket in ['DATA', 'WORKPLACE', 'NIL', 'SGA']:
            bucket_total = result[result['bucket'] == bucket]['amount'].sum()
            bucket_count = len(result[result['bucket'] == bucket])
            print(f"[INFO] ✓ {bucket}: ${bucket_total:,.2f} ({bucket_count} accounts)")

        return result

    def _find_total_column(self, df: pd.DataFrame) -> int:
        """
        Find Total column: header contains 'Total' or rightmost numeric.
        """
        # Try header match
        for idx, col in enumerate(df.columns):
            if 'total' in str(col).lower():
                return idx
        # Fall back to rightmost numeric-like column by sampling
        for idx in range(len(df.columns) - 1, -1, -1):
            try:
                # If conversion to numeric for a sample of values yields numbers, accept
                sample = pd.to_numeric(df.iloc[:10, idx], errors='coerce')
                if sample.notna().any():
                    return idx
            except Exception:
                continue
        raise ValueError("Cannot find Total column in P&L")

    def _match_account(self, account_name: str, config: pd.DataFrame) -> tuple:
        """Match account name against config rules. Returns (bucket, matched_by)."""
        import re
        for _, rule in config.iterrows():
            match_type = rule['match_type']
            pattern = rule['pattern']
            bucket = rule['bucket']

            if match_type == 'exact':
                if account_name == pattern:
                    return bucket, 'exact'
            elif match_type == 'contains':
                if str(pattern).lower() in account_name.lower():
                    return bucket, 'contains'
            elif match_type == 'regex':
                if re.search(pattern, account_name, re.IGNORECASE):
                    return bucket, 'regex'
        return 'SGA', 'default'
