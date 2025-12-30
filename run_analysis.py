#!/usr/bin/env python3
"""
TH Monthly Performance Analysis - CLI Entry Point

Version: 3.0
Date: December 30, 2025

Deterministic monthly analysis engine that processes 5 source files
to generate project-level margins and overhead allocations.
"""

import argparse
import sys
from pathlib import Path


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description='TH Monthly Performance Analysis - Deterministic accounting engine',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example usage:
  python run_analysis.py \\
    --month "November2025" \\
    --proforma "demo_files/(Proforma)November2025.xlsx" \\
    --compensation "demo_files/(Compensation)November2025.xlsx" \\
    --hours "demo_files/(HarvestHours)November2025.xlsx" \\
    --expenses "demo_files/(HarvestExpenses)November2025.xlsx" \\
    --pl "demo_files/(P&L)November2025.xlsx"

Outputs will be saved to: outputs/November2025/
  - revenue_centers.csv
  - cost_centers.csv
  - non_revenue_clients.csv
  - validation_report.md
        """
    )

    # Required arguments
    parser.add_argument(
        '--month',
        required=True,
        help='Month and year (e.g., "November2025")'
    )
    parser.add_argument(
        '--proforma',
        required=True,
        help='Path to Pro Forma Excel file'
    )
    parser.add_argument(
        '--compensation',
        required=True,
        help='Path to Compensation Excel file'
    )
    parser.add_argument(
        '--hours',
        required=True,
        help='Path to Harvest Hours Excel file'
    )
    parser.add_argument(
        '--expenses',
        required=True,
        help='Path to Harvest Expenses Excel file'
    )
    parser.add_argument(
        '--pl',
        required=True,
        help='Path to P&L Excel file'
    )

    # Optional arguments
    parser.add_argument(
        '--output-dir',
        default='./outputs',
        help='Output directory (default: ./outputs)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Validate file paths exist
    files_to_check = [
        ('Pro Forma', args.proforma),
        ('Compensation', args.compensation),
        ('Harvest Hours', args.hours),
        ('Harvest Expenses', args.expenses),
        ('P&L', args.pl),
    ]

    missing_files = []
    for name, filepath in files_to_check:
        if not Path(filepath).exists():
            missing_files.append(f"{name}: {filepath}")

    if missing_files:
        print("[ERROR] Missing required files:")
        for missing in missing_files:
            print(f"  - {missing}")
        sys.exit(1)

    # Print startup banner
    print("=" * 70)
    print("TH Monthly Performance Analysis v3.0")
    print("=" * 70)
    print(f"[INFO] Processing month: {args.month}")
    print(f"[INFO] Output directory: {args.output_dir}")
    print()

    # TODO: Phase 1 - Data Loading
    print("[INFO] Loading files...")
    print("[TODO] Phase 1: Implement data loaders")
    print("  - ProFormaLoader (Column A tags, duplicate aggregation)")
    print("  - CompensationLoader (Strategy A/B)")
    print("  - HarvestHoursLoader")
    print("  - HarvestExpensesLoader (reimbursable filtering)")
    print("  - PnLLoader (config-driven account bucketing)")
    print()

    # TODO: Phase 2 - Classification
    print("[TODO] Phase 2: Implement classification")
    print("  - Revenue Centers")
    print("  - Cost Centers")
    print("  - Non-Revenue Clients")
    print()

    # TODO: Phase 3 - Computations
    print("[TODO] Phase 3: Implement computations")
    print("  - Labor costs (hours × hourly_cost)")
    print("  - Expense costs (non-reimbursable only)")
    print()

    # TODO: Phase 4 - Allocations
    print("[TODO] Phase 4: Implement allocations")
    print("  - SG&A pool → all revenue centers")
    print("  - Data Infrastructure pool → Data-tagged revenue centers")
    print("  - Workplace Well-being pool → Wellness-tagged revenue centers")
    print()

    # TODO: Phase 5 - Validation & Output
    print("[TODO] Phase 5: Implement validation & output")
    print("  - All validation checks")
    print("  - CSV generation")
    print("  - validation_report.md")
    print()

    print("=" * 70)
    print("[INFO] CLI skeleton loaded successfully!")
    print("[INFO] Ready for Phase 1 implementation")
    print("=" * 70)

    return 0


if __name__ == '__main__':
    sys.exit(main())
