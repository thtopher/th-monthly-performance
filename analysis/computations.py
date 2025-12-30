"""
Cost Computations for TH Monthly Performance Analysis

Computes:
1. Labor costs (hours × hourly_cost)
2. Expense costs (non-reimbursable only)
3. Direct cost merging into revenue table
"""

import pandas as pd


def calculate_labor_costs(hours_df: pd.DataFrame, comp_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate labor costs by joining hours with compensation rates.

    Args:
        hours_df: Harvest hours data (project_code, staff_key, hours)
        comp_df: Compensation data (staff_key, hourly_cost)

    Returns:
        DataFrame with labor costs by project_code

    Raises:
        ValueError: If any staff in hours_df missing from comp_df
    """
    # TODO: Implement labor cost calculation
    # - Join hours with compensation on staff_key
    # - FAIL if any staff missing compensation
    # - Calculate: labor_cost = hours × hourly_cost
    # - Group by project_code
    raise NotImplementedError("calculate_labor_costs not yet implemented")


def calculate_expense_costs(expenses_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate expense costs (already filtered to non-reimbursable).

    Args:
        expenses_df: Filtered expenses data (project_code, amount_included)

    Returns:
        DataFrame with expense costs by project_code
    """
    # TODO: Implement expense cost calculation
    # - Group by project_code
    # - Sum amount_included
    raise NotImplementedError("calculate_expense_costs not yet implemented")


def merge_direct_costs(revenue_df: pd.DataFrame,
                       labor_df: pd.DataFrame,
                       expense_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge direct costs into revenue centers table.

    Args:
        revenue_df: Revenue centers from Pro Forma
        labor_df: Labor costs by project_code
        expense_df: Expense costs by project_code

    Returns:
        DataFrame with revenue + direct costs
    """
    # TODO: Implement direct cost merge
    # - Left join revenue with labor (missing = 0)
    # - Left join revenue with expenses (missing = 0)
    raise NotImplementedError("merge_direct_costs not yet implemented")
