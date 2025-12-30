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
        """Load and process Pro Forma file."""
        # TODO: Implement Pro Forma loading
        # - Detect header row (contains Jan...Dec)
        # - Identify month column
        # - Extract allocation_tag from Column A
        # - Extract project_name from Column B
        # - Extract project_code from Column C
        # - Aggregate duplicate codes
        # - Validate totals
        raise NotImplementedError("ProFormaLoader not yet implemented")


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
        """Load and process Compensation file."""
        # TODO: Implement Compensation loading
        # - Try Strategy A first
        # - Fall back to Strategy B if needed
        # - Validate unique Last Name
        # - Log which strategy was used
        raise NotImplementedError("CompensationLoader not yet implemented")


class HarvestHoursLoader:
    """Load Harvest Hours time tracking file."""

    def __init__(self, filepath: str, month: str):
        self.filepath = Path(filepath)
        self.month = month

    def load(self) -> pd.DataFrame:
        """Load and process Harvest Hours file."""
        # TODO: Implement Harvest Hours loading
        # - Read columns flexibly (synonyms)
        # - Validate month date range (WARN if outside)
        # - Normalize contract codes
        raise NotImplementedError("HarvestHoursLoader not yet implemented")


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
        # TODO: Implement Harvest Expenses loading
        # - Read columns flexibly
        # - Apply reimbursable filter
        # - Log exclusion counts
        raise NotImplementedError("HarvestExpensesLoader not yet implemented")


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
        # TODO: Implement P&L loading
        # - Read IncomeStatement sheet
        # - Find Total column
        # - Load account tagging config
        # - Apply bucketing rules (exact, contains, regex)
        # - Default unmatched to SGA
        raise NotImplementedError("PnLLoader not yet implemented")
