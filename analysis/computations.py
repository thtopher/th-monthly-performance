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

    Note:
        Staff missing from compensation file will be excluded from labor cost calculations
        and flagged as a warning.
    """
    merged = hours_df.merge(
        comp_df[["staff_key", "hourly_cost"]],
        on="staff_key",
        how="left",
    )

    missing = merged[merged["hourly_cost"].isna()]
    if len(missing) > 0:
        missing_staff = sorted(set(missing["staff_key"].astype(str)))
        missing_hours = missing["hours"].sum()
        print(f"[WARN] {len(missing_staff)} staff missing compensation records ({missing_hours:.1f} hours excluded):")
        for staff in missing_staff[:5]:
            staff_hours = missing[missing["staff_key"] == staff]["hours"].sum()
            print(f"  - {staff}: {staff_hours:.1f} hours")
        if len(missing_staff) > 5:
            print(f"  ... and {len(missing_staff) - 5} more")

        # Exclude rows with missing compensation
        merged = merged[merged["hourly_cost"].notna()]

    merged["labor_cost"] = merged["hours"] * merged["hourly_cost"]

    labor_by_project = (
        merged.groupby("contract_code").agg({
            "hours": "sum",
            "labor_cost": "sum",
        }).reset_index()
    )

    return labor_by_project


def calculate_expense_costs(expenses_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate expense costs (already filtered to non-reimbursable).

    Args:
        expenses_df: Filtered expenses data (project_code, amount_included)

    Returns:
        DataFrame with expense costs by project_code
    """
    expense_by_project = (
        expenses_df.groupby("contract_code").agg({"amount": "sum"}).reset_index()
    )
    expense_by_project.rename(columns={"amount": "expense_cost"}, inplace=True)
    return expense_by_project


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
    out = revenue_df.merge(labor_df, on="contract_code", how="left")
    out = out.merge(expense_df, on="contract_code", how="left")
    out["hours"] = out.get("hours", 0).fillna(0.0)
    out["labor_cost"] = out.get("labor_cost", 0).fillna(0.0)
    out["expense_cost"] = out.get("expense_cost", 0).fillna(0.0)
    return out
