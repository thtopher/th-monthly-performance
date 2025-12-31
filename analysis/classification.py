"""
Project Classification for TH Monthly Performance Analysis

Classifies all activity into three mutually exclusive categories:
1. Revenue Centers - In Pro Forma with revenue > 0
2. Cost Centers - Listed in config/cost_centers.csv
3. Non-Revenue Clients - Has activity but not revenue center and not cost center
"""

import pandas as pd
from pathlib import Path
import pandas as pd


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
        df = pd.read_csv(self.cost_centers_path)
        return set(df['code'].astype(str))

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
        is_cost_center = project_code in self.cost_centers

        if is_revenue_center and is_cost_center:
            raise ValueError(
                f"Classification conflict for '{project_code}': Code appears as both Revenue Center (Pro Forma) and Cost Center (config). Please resolve."
            )

        if is_revenue_center:
            return 'revenue_center'
        elif is_cost_center:
            return 'cost_center'
        else:
            return 'non_revenue_client'


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
    # Determine sets
    revenue_codes = set(revenue_df['contract_code'].astype(str))
    hours_codes = set(hours_df['contract_code'].astype(str)) if not hours_df.empty else set()
    expense_codes = set(expenses_df['contract_code'].astype(str)) if not expenses_df.empty else set()
    activity_codes = hours_codes.union(expense_codes)

    all_codes = revenue_codes.union(activity_codes).union(classifier.cost_centers)

    classifications = {}
    for code in all_codes:
        classifications[code] = classifier.classify(code, code in revenue_codes)

    # Split
    revenue_center_codes = {c for c, cls in classifications.items() if cls == 'revenue_center'}
    cost_center_codes = {c for c, cls in classifications.items() if cls == 'cost_center'}
    non_rev_codes = {c for c, cls in classifications.items() if cls == 'non_revenue_client'}

    # Revenue centers: filter provided revenue_df to those codes
    revenue_centers_df = revenue_df[revenue_df['contract_code'].isin(revenue_center_codes)].copy()

    # Cost centers: from config, filter to classified codes, bring pool/description
    cc_config = pd.read_csv(classifier.cost_centers_path)
    cost_centers_df = cc_config[cc_config['code'].isin(cost_center_codes)].copy()
    cost_centers_df.rename(columns={'code': 'contract_code'}, inplace=True)
    # Initialize totals to 0.0; can be enriched later in pipeline
    cost_centers_df['total_cost'] = 0.0

    # Non-revenue clients: minimal frame of codes with placeholders
    non_revenue_clients_df = pd.DataFrame({
        'contract_code': sorted(non_rev_codes)
    })

    return {
        'revenue_centers': revenue_centers_df,
        'cost_centers': cost_centers_df,
        'non_revenue_clients': non_revenue_clients_df,
    }
