"""
Output Generation for TH Monthly Performance Analysis

Generates 4 output files:
1. revenue_centers.csv - Project-level P&L with margins
2. cost_centers.csv - Internal overhead analysis
3. non_revenue_clients.csv - Client work without revenue
4. validation_report.md - Detailed audit trail
"""

import pandas as pd
from pathlib import Path
from typing import Optional
from .validators import ValidationResult


def write_revenue_centers(df: pd.DataFrame, output_dir: str) -> Path:
    """
    Write revenue centers CSV.

    Args:
        df: Revenue centers DataFrame with all costs and allocations
        output_dir: Output directory path

    Returns:
        Path to created file
    """
    # TODO: Implement revenue centers CSV output
    # Columns: contract_code, project_name, proforma_section, analysis_category,
    #          allocation_tag, revenue, labor_cost, non_reimbursable_expense,
    #          sga_allocation, data_infrastructure_allocation, workplace_wellbeing_allocation,
    #          margin_dollars, margin_percent
    raise NotImplementedError("write_revenue_centers not yet implemented")


def write_cost_centers(df: pd.DataFrame, output_dir: str) -> Path:
    """
    Write cost centers CSV.

    Args:
        df: Cost centers DataFrame with labor and expenses
        output_dir: Output directory path

    Returns:
        Path to created file
    """
    # TODO: Implement cost centers CSV output
    # Columns: cost_center_code, description, labor_cost,
    #          non_reimbursable_expense, total_cost, notes
    raise NotImplementedError("write_cost_centers not yet implemented")


def write_non_revenue_clients(df: pd.DataFrame, output_dir: str) -> Path:
    """
    Write non-revenue clients CSV.

    Args:
        df: Non-revenue clients DataFrame
        output_dir: Output directory path

    Returns:
        Path to created file
    """
    # TODO: Implement non-revenue clients CSV output
    # Columns: project_code, project_name, labor_cost,
    #          non_reimbursable_expense, total_cost
    raise NotImplementedError("write_non_revenue_clients not yet implemented")


def write_validation_report(results: ValidationResult,
                           output_dir: str,
                           month: str,
                           metadata: Optional[dict] = None) -> Path:
    """
    Write validation report in Markdown format.

    Args:
        results: ValidationResult from validators
        output_dir: Output directory path
        month: Month being processed
        metadata: Optional metadata (file paths, counts, etc.)

    Returns:
        Path to created file
    """
    output_path = Path(output_dir) / "validation_report.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines = []
    lines.append(f"# Validation Report - {month}")
    lines.append("")
    lines.append(f"**Summary:** {results.summary()}")
    lines.append("")

    # Metadata section
    if metadata:
        lines.append("## Metadata")
        lines.append("")
        for key, value in metadata.items():
            lines.append(f"- **{key}:** {value}")
        lines.append("")

    # Passing checks
    if results.passes:
        lines.append("## ✓ Passing Checks")
        lines.append("")
        for check in results.passes:
            lines.append(f"- {check}")
        lines.append("")

    # Warnings
    if results.warnings:
        lines.append("## ⚠ Warnings")
        lines.append("")
        for warning in results.warnings:
            lines.append(f"- {warning}")
        lines.append("")

    # Failures
    if results.failures:
        lines.append("## ✗ Failures")
        lines.append("")
        for failure in results.failures:
            lines.append(f"- {failure}")
        lines.append("")

    # Write file
    with open(output_path, 'w') as f:
        f.write('\n'.join(lines))

    return output_path
