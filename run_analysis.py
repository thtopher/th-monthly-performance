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

    try:
        # Phase 1: Load files
        print("[INFO] Loading files...")

        from analysis.loaders import (
            ProFormaLoader, CompensationLoader, HarvestHoursLoader,
            HarvestExpensesLoader, PnLLoader
        )

        proforma_df = ProFormaLoader(args.proforma, args.month).load()
        comp_df = CompensationLoader(args.compensation).load()
        hours_df = HarvestHoursLoader(args.hours, args.month).load()
        expenses_df = HarvestExpensesLoader(args.expenses).load()
        pnl_df = PnLLoader(args.pl).load()

        print()

        # Phase 2: Classification
        print("[INFO] Classifying projects...")
        from analysis.classification import ProjectClassifier, classify_all_activity
        classifier = ProjectClassifier()
        classified = classify_all_activity(proforma_df, hours_df, expenses_df, classifier)

        print()

        # Phase 3: Computations
        print("[INFO] Computing costs...")
        from analysis.computations import (
            calculate_labor_costs, calculate_expense_costs, merge_direct_costs
        )
        labor_df = calculate_labor_costs(hours_df, comp_df)
        expense_df = calculate_expense_costs(expenses_df)
        revenue_df = merge_direct_costs(proforma_df, labor_df, expense_df)

        # Compute cost center totals (labor + expenses)
        if not classified['cost_centers'].empty:
            cc = classified['cost_centers'].copy()
            cc_codes = set(cc['contract_code'].astype(str))
            labor_cc = labor_df[labor_df['contract_code'].isin(cc_codes)][['contract_code', 'labor_cost']]
            expense_cc = expense_df[expense_df['contract_code'].isin(cc_codes)][['contract_code', 'expense_cost']]
            cc = cc.merge(labor_cc, on='contract_code', how='left')
            cc = cc.merge(expense_cc, on='contract_code', how='left')
            cc['labor_cost'] = cc['labor_cost'].fillna(0.0)
            cc['expense_cost'] = cc['expense_cost'].fillna(0.0)
            cc['total_cost'] = (cc['labor_cost'] + cc['expense_cost']).astype(float)
            classified['cost_centers'] = cc

        # Compute non-revenue client totals (labor + expenses)
        if not classified['non_revenue_clients'].empty:
            nrc = classified['non_revenue_clients'].copy()
            nrc_codes = set(nrc['contract_code'].astype(str))
            labor_nrc = labor_df[labor_df['contract_code'].isin(nrc_codes)][['contract_code', 'labor_cost']]
            expense_nrc = expense_df[expense_df['contract_code'].isin(nrc_codes)][['contract_code', 'expense_cost']]
            nrc = nrc.merge(labor_nrc, on='contract_code', how='left')
            nrc = nrc.merge(expense_nrc, on='contract_code', how='left')
            nrc['labor_cost'] = nrc['labor_cost'].fillna(0.0)
            nrc['expense_cost'] = nrc['expense_cost'].fillna(0.0)
            nrc['total_cost'] = (nrc['labor_cost'] + nrc['expense_cost']).astype(float)
            classified['non_revenue_clients'] = nrc

        print()

        # Phase 4: Allocations
        print("[INFO] Allocating overhead...")
        from analysis.allocations import OverheadAllocator, calculate_margins
        import json
        with open('config/settings.json') as f:
            settings = json.load(f)
        allocator = OverheadAllocator(tolerance=settings['allocation_tolerance'])
        pools = allocator.calculate_pools(
            pnl_df,
            classified['cost_centers'],
            include_cc_in_sga=settings['include_cost_center_overhead_in_sga_pool']
        )
        revenue_df = allocator.allocate_sga(revenue_df, pools['sga_pool'])
        revenue_df = allocator.allocate_data(revenue_df, pools['data_pool'])
        revenue_df = allocator.allocate_workplace(revenue_df, pools['workplace_pool'])
        revenue_df = calculate_margins(revenue_df)

        print()

        # Phase 5: Validation
        print("[INFO] Validating results...")
        from analysis.validators import run_all_validations
        data = {
            'revenue_centers': revenue_df,
            'cost_centers': classified['cost_centers'],
            'non_revenue_clients': classified['non_revenue_clients'],
            'proforma': proforma_df,
            'hours': hours_df,
            'expenses': expenses_df,
            'compensation': comp_df,
            'pnl': pnl_df,
            'pools': pools,
        }
        validation_results = run_all_validations(data, tolerance=settings['allocation_tolerance'])
        print(f"[INFO] {validation_results.summary()}")
        print()

        # Phase 6: Output
        print("[INFO] Generating outputs...")
        from analysis.outputs import (
            write_revenue_centers, write_cost_centers,
            write_non_revenue_clients, write_validation_report
        )
        output_path = Path(args.output_dir) / args.month
        write_revenue_centers(revenue_df, output_path)
        write_cost_centers(classified['cost_centers'], output_path)
        write_non_revenue_clients(classified['non_revenue_clients'], output_path)
        write_validation_report(validation_results, output_path, args.month)

        print()
        print("=" * 70)
        print("[SUCCESS] Processing complete!")
        print(f"[INFO] Outputs saved to: {output_path}")
        print(f"[INFO] Review {output_path}/validation_report.md for details")
        print("=" * 70)

        return 0

    except Exception as e:
        print()
        print("=" * 70)
        print("[ERROR] Processing failed:")
        print(f"  {str(e)}")
        print("=" * 70)
        return 1


if __name__ == '__main__':
    sys.exit(main())
