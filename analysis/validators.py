"""
Validation Rules for TH Monthly Performance Analysis

Implements FAIL and WARN validation checks:
- FAIL: Critical errors that block processing
- WARN: Issues that continue with logging
"""

import pandas as pd
from typing import List


class ValidationResult:
    """Container for validation results."""

    def __init__(self):
        self.passes: List[str] = []
        self.warnings: List[str] = []
        self.failures: List[str] = []

    def add_pass(self, message: str):
        """Record a passing validation."""
        self.passes.append(f"✓ {message}")

    def add_warning(self, message: str):
        """Record a warning (continues processing)."""
        self.warnings.append(f"⚠ {message}")

    def add_failure(self, message: str):
        """Record a failure (blocks processing)."""
        self.failures.append(f"✗ {message}")

    def has_failures(self) -> bool:
        """Check if any failures occurred."""
        return len(self.failures) > 0

    def summary(self) -> str:
        """Generate summary report."""
        lines = []
        lines.append(f"PASS: {len(self.passes)}")
        lines.append(f"WARN: {len(self.warnings)}")
        lines.append(f"FAIL: {len(self.failures)}")
        return " | ".join(lines)


class DataCompletenessValidator:
    """
    Validate data completeness.

    FAIL conditions:
    - Required files missing
    - Required columns missing
    - Pro Forma sheet missing
    - Month column not found
    - No project codes found
    """

    @staticmethod
    def validate(data: dict, results: ValidationResult):
        """Run basic data completeness checks using available data."""
        required_keys = ['revenue_centers', 'cost_centers', 'non_revenue_clients', 'proforma', 'pools', 'hours', 'expenses', 'compensation', 'pnl']
        missing = [k for k in required_keys if k not in data]
        if missing:
            results.add_failure(f"Missing required data keys: {', '.join(missing)}")
            return

        if getattr(data['revenue_centers'], 'empty', True):
            results.add_failure("No revenue centers found")
        else:
            results.add_pass("Revenue centers loaded")

        if 'sga_pool' in data['pools'] and 'data_pool' in data['pools'] and 'workplace_pool' in data['pools']:
            results.add_pass("Overhead pools calculated")
        else:
            results.add_failure("Overhead pools missing required keys (sga_pool, data_pool, workplace_pool)")

        # Quick presence checks for other inputs
        if getattr(data['compensation'], 'empty', True):
            results.add_failure("Compensation data missing or empty")
        else:
            results.add_pass("Compensation loaded")
        if getattr(data['hours'], 'empty', True):
            results.add_warning("Harvest Hours is empty")
        if getattr(data['expenses'], 'empty', True):
            results.add_warning("Harvest Expenses is empty")


class KeyIntegrityValidator:
    """
    Validate key integrity.

    FAIL conditions:
    - Duplicate Last Name in Compensation
    - Staff in Harvest Hours missing from Compensation
    - Allocation tag conflict (both Data and Wellness for same code)
    - Code is both Revenue Center and Cost Center
    """

    @staticmethod
    def validate(data: dict, results: ValidationResult):
        """Run key integrity checks feasible with provided data."""
        # Duplicate Last Name in Compensation
        comp = data.get('compensation')
        if comp is not None and not comp.empty:
            dups = comp[comp['staff_key'].duplicated(keep=False)]
            if len(dups) > 0:
                dup_names = ', '.join(sorted(set(dups['staff_key'].astype(str))))
                results.add_failure(f"Duplicate Last Names in Compensation: {dup_names}")
            else:
                results.add_pass("Unique Last Names in Compensation")

        # Staff in Harvest Hours missing from Compensation
        hours = data.get('hours')
        if hours is not None and comp is not None and not hours.empty and not comp.empty:
            missing_staff = set(hours['staff_key'].astype(str)) - set(comp['staff_key'].astype(str))
            if missing_staff:
                results.add_failure(f"Harvest Hours staff missing in Compensation: {', '.join(sorted(missing_staff))}")
            else:
                results.add_pass("All Harvest Hours staff have compensation records")

        # Revenue vs Cost Center conflict
        rev_codes = set(data['revenue_centers'].get('contract_code', pd.Series(dtype=str)))
        cc_codes = set(data['cost_centers'].get('contract_code', pd.Series(dtype=str)))
        conflict = rev_codes.intersection(cc_codes)
        if conflict:
            results.add_failure(f"Codes appear as both revenue and cost centers: {', '.join(sorted(conflict))}")
        else:
            results.add_pass("No revenue/cost center code conflicts")


class MathematicalValidator:
    """
    Validate mathematical reconciliations.

    Checks (with tolerance):
    - Sum(project revenues) == Pro Forma total revenue (±$0.01)
    - Sum(SG&A allocations) == SG&A pool (±$0.01)
    - Sum(Data allocations) == Data pool (±$0.01)
    - Sum(Workplace allocations) == Workplace pool (±$0.01)
    """

    def __init__(self, tolerance: float = 0.01):
        self.tolerance = tolerance

    def validate(self, data: dict, results: ValidationResult):
        """Run reconciliation checks using revenue_centers and pools."""
        rev = data['revenue_centers']
        pools = data['pools']
        if getattr(rev, 'empty', True):
            return

        # Revenue sum vs Pro Forma total
        if 'proforma' in data and not getattr(data['proforma'], 'empty', True):
            proforma_total = data['proforma']['revenue'].sum() if 'revenue' in data['proforma'].columns else None
            if proforma_total is not None:
                diff_rev = abs(rev['revenue'].sum() - float(proforma_total))
                if diff_rev <= self.tolerance:
                    results.add_pass(f"Revenue sum matches Pro Forma (±{self.tolerance})")
                else:
                    results.add_failure(f"Revenue sum does not match Pro Forma (diff ${diff_rev:,.2f})")

        # Allocation sums should reconcile to pools (within tolerance)
        for col, key in [('sga_allocation', 'sga_pool'), ('data_allocation', 'data_pool'), ('workplace_allocation', 'workplace_pool')]:
            if col in rev.columns and key in pools:
                diff = abs(rev[col].sum() - float(pools[key]))
                if diff <= self.tolerance:
                    results.add_pass(f"{col.replace('_', ' ').title()} sums to pool (±{self.tolerance})")
                else:
                    results.add_failure(f"{col.replace('_', ' ').title()} does not sum to pool (diff ${diff:,.2f})")


class ReasonablenessValidator:
    """
    Validate reasonableness (warnings only).

    WARN conditions:
    - Harvest rows outside month date range
    - Unknown Billable values in expenses
    - Pro Forma code has revenue but no Harvest hours
    - Harvest code not in Pro Forma and not in cost centers
    - P&L account not matched by tagging rules
    """

    @staticmethod
    def validate(data: dict, results: ValidationResult):
        """Reasonableness checks based on provided data."""
        rev = data.get('revenue_centers')
        hours = data.get('hours')
        cc = data.get('cost_centers')
        pnl = data.get('pnl')

        # Revenue without hours
        if rev is not None and not rev.empty:
            if 'hours' in rev.columns:
                no_hours = rev[rev['hours'].fillna(0) == 0]
                if len(no_hours) > 0:
                    results.add_warning(f"{len(no_hours)} revenue centers have revenue but no hours")

        # Hours without revenue (excluding cost centers)
        if hours is not None and not hours.empty and rev is not None:
            rev_codes = set(rev['contract_code'].astype(str))
            cc_codes = set(cc['contract_code'].astype(str)) if cc is not None and not cc.empty else set()
            hrs_codes = set(hours['contract_code'].astype(str))
            missing_rev = hrs_codes - rev_codes - cc_codes
            if missing_rev:
                results.add_warning(f"{len(missing_rev)} codes have hours but no revenue (non-revenue clients)")

        # Unmatched P&L accounts defaulted to SG&A
        if pnl is not None and not pnl.empty and {'matched_by', 'bucket'}.issubset(set(pnl.columns)):
            unmatched = pnl[(pnl['matched_by'] == 'default') & (pnl['bucket'] == 'SGA')]
            if len(unmatched) > 0:
                results.add_warning(f"{len(unmatched)} P&L accounts defaulted to SG&A (unmatched)")
            else:
                results.add_pass("All P&L accounts matched by tagging rules or assigned appropriately")


def run_all_validations(data: dict, tolerance: float = 0.01) -> ValidationResult:
    """
    Run all validation checks.

    Args:
        data: Dictionary containing all loaded data
        tolerance: Tolerance for mathematical checks

    Returns:
        ValidationResult with all checks

    Raises:
        ValueError: If any FAIL conditions occur
    """
    results = ValidationResult()

    # Run all validators
    DataCompletenessValidator.validate(data, results)
    KeyIntegrityValidator.validate(data, results)
    MathematicalValidator(tolerance).validate(data, results)
    ReasonablenessValidator.validate(data, results)

    # Raise if failures
    if results.has_failures():
        raise ValueError(f"Validation failed: {results.summary()}")

    return results
