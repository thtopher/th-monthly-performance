"""
Project Classification for TH Monthly Performance Analysis

Classifies all activity into three mutually exclusive categories:
1. Revenue Centers - In Pro Forma with revenue > 0
2. Cost Centers - Listed in config/cost_centers.csv
3. Non-Revenue Clients - Has activity but not revenue center and not cost center
"""

import pandas as pd
from pathlib import Path


class ProjectClassifier:
    """
    Classify projects into Revenue Centers, Cost Centers, or Non-Revenue Clients.

    v3.0 Requirements:
    - Revenue center = revenue > 0 in Pro Forma
    - Cost center = listed in config/cost_centers.csv
    - Non-revenue client = activity but neither of the above
    - FAIL if code is both revenue center AND cost center (conflict)
    """

    def __init__(self, cost_centers_path: str = "config/cost_centers.csv"):
        self.cost_centers_path = Path(cost_centers_path)
        self.cost_centers = self._load_cost_centers()

    def _load_cost_centers(self) -> set:
        """Load cost center codes from config."""
        # TODO: Load cost center codes from CSV
        raise NotImplementedError("_load_cost_centers not yet implemented")

    def classify(self, project_code: str, is_revenue_center: bool) -> str:
        """
        Classify a single project code.

        Args:
            project_code: Normalized contract code
            is_revenue_center: Whether code appears in Pro Forma with revenue > 0

        Returns:
            Classification: 'revenue_center', 'cost_center', or 'non_revenue_client'

        Raises:
            ValueError: If code is both revenue center and cost center (conflict)
        """
        # TODO: Implement classification logic
        # - Check if revenue center
        # - Check if cost center
        # - Detect conflicts (FAIL)
        # - Default to non-revenue client
        raise NotImplementedError("classify not yet implemented")


def classify_all_activity(revenue_df: pd.DataFrame,
                          hours_df: pd.DataFrame,
                          expenses_df: pd.DataFrame,
                          classifier: ProjectClassifier) -> dict:
    """
    Classify all activity from all sources.

    Args:
        revenue_df: Pro Forma revenue centers
        hours_df: Harvest hours data
        expenses_df: Harvest expenses data
        classifier: ProjectClassifier instance

    Returns:
        Dictionary with three DataFrames:
        - 'revenue_centers': Revenue-bearing projects
        - 'cost_centers': Internal overhead
        - 'non_revenue_clients': Client work without revenue
    """
    # TODO: Implement classification of all activity
    # - Get all unique project codes from all sources
    # - Classify each code
    # - Split into three categories
    raise NotImplementedError("classify_all_activity not yet implemented")
