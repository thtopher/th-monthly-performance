"""
Tests for data loaders

Tests the 5 file loaders:
- ProFormaLoader
- CompensationLoader
- HarvestHoursLoader
- HarvestExpensesLoader
- PnLLoader
"""

import pytest
from analysis.loaders import normalize_contract_code


class TestContractCodeNormalization:
    """Test contract code normalization."""

    def test_trim_whitespace(self):
        """Should trim leading/trailing whitespace."""
        assert normalize_contract_code("  BEH-25-01-XXX  ") == "BEH-25-01-XXX"

    def test_remove_non_breaking_spaces(self):
        """Should remove non-breaking spaces."""
        code_with_nbsp = "BEH-25-01-XXX\xa0"
        assert normalize_contract_code(code_with_nbsp) == "BEH-25-01-XXX"

    def test_collapse_multiple_spaces(self):
        """Should collapse multiple spaces into one."""
        assert normalize_contract_code("BEH  25  01  XXX") == "BEH 25 01 XXX"

    def test_preserve_case(self):
        """Should preserve case (codes are case-sensitive)."""
        assert normalize_contract_code("Beh-25-01-XXX") == "Beh-25-01-XXX"

    def test_empty_code_raises_error(self):
        """Should raise ValueError for empty codes."""
        with pytest.raises(ValueError, match="empty"):
            normalize_contract_code("   ")

    def test_missing_code_raises_error(self):
        """Should raise ValueError for missing codes."""
        with pytest.raises(ValueError, match="missing"):
            normalize_contract_code(None)


class TestProFormaLoader:
    """Test Pro Forma loader."""

    def test_placeholder(self):
        """Placeholder test - TODO: Implement."""
        # TODO: Test Column A allocation tags
        # TODO: Test duplicate code aggregation
        # TODO: Test conflict detection (Data + Wellness)
        # TODO: Test dynamic month column detection
        # TODO: Test revenue validation
        pass


class TestCompensationLoader:
    """Test Compensation loader."""

    def test_placeholder(self):
        """Placeholder test - TODO: Implement."""
        # TODO: Test Strategy A (read Base Cost Per Hour)
        # TODO: Test Strategy B (compute from components)
        # TODO: Test unique Last Name validation
        pass


class TestHarvestHoursLoader:
    """Test Harvest Hours loader."""

    def test_placeholder(self):
        """Placeholder test - TODO: Implement."""
        # TODO: Test column synonym handling
        # TODO: Test month date range validation
        pass


class TestHarvestExpensesLoader:
    """Test Harvest Expenses loader."""

    def test_placeholder(self):
        """Placeholder test - TODO: Implement."""
        # TODO: Test reimbursable filtering
        # TODO: Test Billable = Yes → exclude
        # TODO: Test Billable = No → include
        # TODO: Test Billable = blank → warn + include
        pass


class TestPnLLoader:
    """Test P&L loader."""

    def test_placeholder(self):
        """Placeholder test - TODO: Implement."""
        # TODO: Test Total column detection
        # TODO: Test config-driven account bucketing
        # TODO: Test exact/contains/regex matching
        # TODO: Test default to SGA for unmatched
        pass
