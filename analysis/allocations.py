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
        # P&L buckets
        data_pnl = pnl_df[pnl_df['bucket'] == 'DATA']['amount'].sum() if not pnl_df.empty else 0.0
        workplace_pnl = pnl_df[pnl_df['bucket'] == 'WORKPLACE']['amount'].sum() if not pnl_df.empty else 0.0
        sga_pnl = pnl_df[pnl_df['bucket'] == 'SGA']['amount'].sum() if not pnl_df.empty else 0.0

        data_pool = data_pnl
        sga_pool = sga_pnl

        if include_cc_in_sga and not cost_centers_df.empty:
            # Add cost center totals by assigned pool if available
            if 'total_cost' in cost_centers_df.columns and 'pool' in cost_centers_df.columns:
                data_cc = cost_centers_df[cost_centers_df['pool'] == 'DATA']['total_cost'].sum()
                sga_cc = cost_centers_df[cost_centers_df['pool'] == 'SGA']['total_cost'].sum()
                data_pool += float(data_cc)
                sga_pool += float(sga_cc)

        workplace_pool = workplace_pnl

        return {
            'sga_pool': float(sga_pool),
            'data_pool': float(data_pool),
            'workplace_pool': float(workplace_pool),
        }

    def allocate_sga(self, revenue_df: pd.DataFrame, sga_pool: float) -> pd.DataFrame:
        """
        Allocate SG&A pool across all revenue centers.

        Args:
            revenue_df: Revenue centers with revenue amounts
            sga_pool: Total SG&A pool to allocate

        Returns:
            DataFrame with sga_allocation column added
        """
        total_rev = revenue_df['revenue'].sum()
        if total_rev <= 0:
            revenue_df['sga_allocation'] = 0.0
            return revenue_df

        alloc = (revenue_df['revenue'] / total_rev) * float(sga_pool)
        revenue_df = revenue_df.copy()
        revenue_df['sga_allocation'] = alloc

        # Validate reconciliation
        if abs(revenue_df['sga_allocation'].sum() - float(sga_pool)) > self.tolerance:
            raise ValueError("SG&A allocation does not reconcile to pool within tolerance")
        return revenue_df

    def allocate_data(self, revenue_df: pd.DataFrame, data_pool: float) -> pd.DataFrame:
        """
        Allocate Data Infrastructure pool to Data-tagged revenue centers only.

        Args:
            revenue_df: Revenue centers with allocation_tag
            data_pool: Total Data Infrastructure pool to allocate

        Returns:
            DataFrame with data_allocation column added (0 for non-Data projects)
        """
        revenue_df = revenue_df.copy()
        revenue_df['data_allocation'] = 0.0
        data_df = revenue_df[revenue_df['allocation_tag'] == 'Data']
        total_rev = data_df['revenue'].sum()
        if total_rev <= 0:
            # Nothing to allocate
            return revenue_df

        alloc = (data_df['revenue'] / total_rev) * float(data_pool)
        revenue_df.loc[data_df.index, 'data_allocation'] = alloc

        if abs(revenue_df['data_allocation'].sum() - float(data_pool)) > self.tolerance:
            raise ValueError("Data allocation does not reconcile to pool within tolerance")
        return revenue_df

    def allocate_workplace(self, revenue_df: pd.DataFrame, workplace_pool: float) -> pd.DataFrame:
        """
        Allocate Workplace Well-being pool to Wellness-tagged revenue centers only.

        Args:
            revenue_df: Revenue centers with allocation_tag
            workplace_pool: Total Workplace Well-being pool to allocate

        Returns:
            DataFrame with workplace_allocation column added (0 for non-Wellness projects)
        """
        revenue_df = revenue_df.copy()
        revenue_df['workplace_allocation'] = 0.0
        w_df = revenue_df[revenue_df['allocation_tag'] == 'Wellness']
        total_rev = w_df['revenue'].sum()
        if total_rev <= 0:
            return revenue_df

        alloc = (w_df['revenue'] / total_rev) * float(workplace_pool)
        revenue_df.loc[w_df.index, 'workplace_allocation'] = alloc

        if abs(revenue_df['workplace_allocation'].sum() - float(workplace_pool)) > self.tolerance:
            raise ValueError("Workplace allocation does not reconcile to pool within tolerance")
        return revenue_df


def calculate_margins(revenue_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate final margins.

    Args:
        revenue_df: Revenue centers with all costs and allocations

    Returns:
        DataFrame with margin_dollars and margin_percent columns added
    """
    df = revenue_df.copy()
    for col in ['labor_cost', 'expense_cost', 'sga_allocation', 'data_allocation', 'workplace_allocation']:
        if col not in df.columns:
            df[col] = 0.0
        df[col] = df[col].fillna(0.0)

    df['margin_dollars'] = (
        df['revenue']
        - df['labor_cost']
        - df['expense_cost']
        - df['sga_allocation']
        - df['data_allocation']
        - df['workplace_allocation']
    )
    df['margin_percent'] = df.apply(
        lambda r: (r['margin_dollars'] / r['revenue'] * 100.0) if r['revenue'] else 0.0,
        axis=1,
    )
    return df
