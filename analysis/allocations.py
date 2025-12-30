"""
Overhead Allocation for TH Monthly Performance Analysis

Allocates three overhead pools pro-rata by revenue:
1. SG&A - All revenue centers
2. Data Infrastructure - Data-tagged revenue centers only
3. Workplace Well-being - Wellness-tagged revenue centers only
"""

import pandas as pd


class OverheadAllocator:
    """
    Allocate overhead pools to revenue centers.

    v3.0 Requirements:
    - SG&A pool = P&L SGA + optional Harvest cost center overhead
    - Data pool = P&L DATA + optional DATA cost centers
    - Workplace pool = P&L WORKPLACE
    - Pro-rata by revenue
    - Allocations must reconcile to pools (±$0.01)
    """

    def __init__(self, tolerance: float = 0.01):
        self.tolerance = tolerance

    def calculate_pools(self,
                       pnl_df: pd.DataFrame,
                       cost_centers_df: pd.DataFrame,
                       include_cc_in_sga: bool = True) -> dict:
        """
        Calculate overhead pools from P&L and cost centers.

        Args:
            pnl_df: P&L accounts with bucketing
            cost_centers_df: Cost center labor and expenses
            include_cc_in_sga: Whether to include cost center overhead in SG&A pool

        Returns:
            Dictionary with pool amounts:
            - 'sga_pool': SG&A overhead
            - 'data_pool': Data infrastructure
            - 'workplace_pool': Workplace well-being
        """
        # TODO: Implement pool calculation
        # - Sum P&L accounts by bucket (DATA, WORKPLACE, NIL, SGA)
        # - Optionally add cost center overhead to pools
        # - Return pool amounts
        raise NotImplementedError("calculate_pools not yet implemented")

    def allocate_sga(self, revenue_df: pd.DataFrame, sga_pool: float) -> pd.DataFrame:
        """
        Allocate SG&A pool across all revenue centers.

        Args:
            revenue_df: Revenue centers with revenue amounts
            sga_pool: Total SG&A pool to allocate

        Returns:
            DataFrame with sga_allocation column added
        """
        # TODO: Implement SG&A allocation
        # - Pro-rata by revenue: (project_revenue / total_revenue) * sga_pool
        # - Validate sum equals pool (±tolerance)
        raise NotImplementedError("allocate_sga not yet implemented")

    def allocate_data(self, revenue_df: pd.DataFrame, data_pool: float) -> pd.DataFrame:
        """
        Allocate Data Infrastructure pool to Data-tagged revenue centers only.

        Args:
            revenue_df: Revenue centers with allocation_tag
            data_pool: Total Data Infrastructure pool to allocate

        Returns:
            DataFrame with data_allocation column added (0 for non-Data projects)
        """
        # TODO: Implement Data Infrastructure allocation
        # - Filter to allocation_tag == 'Data'
        # - Pro-rata by revenue within Data projects
        # - Set 0 for non-Data projects
        # - Validate sum equals pool (±tolerance)
        raise NotImplementedError("allocate_data not yet implemented")

    def allocate_workplace(self, revenue_df: pd.DataFrame, workplace_pool: float) -> pd.DataFrame:
        """
        Allocate Workplace Well-being pool to Wellness-tagged revenue centers only.

        Args:
            revenue_df: Revenue centers with allocation_tag
            workplace_pool: Total Workplace Well-being pool to allocate

        Returns:
            DataFrame with workplace_allocation column added (0 for non-Wellness projects)
        """
        # TODO: Implement Workplace Well-being allocation
        # - Filter to allocation_tag == 'Wellness'
        # - Pro-rata by revenue within Wellness projects
        # - Set 0 for non-Wellness projects
        # - Validate sum equals pool (±tolerance)
        raise NotImplementedError("allocate_workplace not yet implemented")


def calculate_margins(revenue_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate final margins.

    Args:
        revenue_df: Revenue centers with all costs and allocations

    Returns:
        DataFrame with margin_dollars and margin_percent columns added
    """
    # TODO: Implement margin calculation
    # margin_dollars = revenue - labor_cost - expense_cost - sga_allocation - data_allocation - workplace_allocation
    # margin_percent = margin_dollars / revenue (handle division by zero)
    raise NotImplementedError("calculate_margins not yet implemented")
