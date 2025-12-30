"""
Validation Rules for TH Monthly Performance Analysis

Implements FAIL and WARN validation checks:
- FAIL: Critical errors that block processing
- WARN: Issues that continue with logging
"""

import pandas as pd
from typing import List, Tuple


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
        """Run all data completeness checks."""
        # TODO: Implement data completeness validation
        raise NotImplementedError("DataCompletenessValidator not yet implemented")


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
        """Run all key integrity checks."""
        # TODO: Implement key integrity validation
        # - Check unique Last Name
        # - Check all Harvest Hours staff have comp records
        # - Check allocation tag conflicts
        # - Check revenue/cost center conflicts
        raise NotImplementedError("KeyIntegrityValidator not yet implemented")


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
        """Run all mathematical reconciliation checks."""
        # TODO: Implement mathematical validation
        # - Revenue sum vs total
        # - Allocation sums vs pools
        raise NotImplementedError("MathematicalValidator not yet implemented")


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
        """Run all reasonableness checks."""
        # TODO: Implement reasonableness validation
        raise NotImplementedError("ReasonablenessValidator not yet implemented")


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
