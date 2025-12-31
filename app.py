#!/usr/bin/env python3
"""
TH Monthly Performance Analysis - Flask Web Interface

Provides a web UI for uploading files and running the analysis.
"""

import os
import json
from pathlib import Path
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, send_file, flash, session

# Import analysis modules
from analysis.loaders import (
    ProFormaLoader, CompensationLoader, HarvestHoursLoader,
    HarvestExpensesLoader, PnLLoader
)
from analysis.classification import ProjectClassifier, classify_all_activity
from analysis.computations import calculate_labor_costs, calculate_expense_costs, merge_direct_costs
from analysis.allocations import OverheadAllocator, calculate_margins
from analysis.validators import run_all_validations
from analysis.outputs import (
    write_revenue_centers, write_cost_centers,
    write_non_revenue_clients, write_validation_report
)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['UPLOAD_FOLDER'] = Path('./uploads')
app.config['OUTPUT_FOLDER'] = Path('./outputs')

# Ensure directories exist
app.config['UPLOAD_FOLDER'].mkdir(exist_ok=True)
app.config['OUTPUT_FOLDER'].mkdir(exist_ok=True)

# Load settings
with open('config/settings.json') as f:
    SETTINGS = json.load(f)

ALLOWED_EXTENSIONS = {'xlsx'}


def allowed_file(filename):
    """Check if file has allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """Main upload form."""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_files():
    """Handle file upload and run analysis."""
    try:
        # Get month
        month = request.form.get('month', '').strip()
        if not month:
            flash('Month is required', 'error')
            return redirect(url_for('index'))

        # Check all files are present
        required_files = ['proforma', 'compensation', 'hours', 'expenses', 'pl']
        uploaded_files = {}

        for file_key in required_files:
            if file_key not in request.files:
                flash(f'Missing {file_key} file', 'error')
                return redirect(url_for('index'))

            file = request.files[file_key]
            if file.filename == '':
                flash(f'No file selected for {file_key}', 'error')
                return redirect(url_for('index'))

            if not allowed_file(file.filename):
                flash(f'Invalid file type for {file_key}. Only .xlsx allowed', 'error')
                return redirect(url_for('index'))

            # Save file
            filename = secure_filename(f"{file_key}_{month}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
            filepath = app.config['UPLOAD_FOLDER'] / filename
            file.save(filepath)
            uploaded_files[file_key] = filepath

        # Run analysis
        result = run_analysis(month, uploaded_files)

        # Clean up uploaded files
        for filepath in uploaded_files.values():
            try:
                os.remove(filepath)
            except Exception:
                pass

        if result['success']:
            # Store result info in session
            session['last_analysis'] = {
                'month': month,
                'output_dir': str(result['output_dir']),
                'validation_summary': result['validation_summary'],
                'timestamp': datetime.now().isoformat()
            }
            return redirect(url_for('results'))
        else:
            flash(f"Analysis failed: {result['error']}", 'error')
            return redirect(url_for('index'))

    except Exception as e:
        flash(f'Error processing files: {str(e)}', 'error')
        return redirect(url_for('index'))


def run_analysis(month, files):
    """Run the analysis pipeline."""
    try:
        # Phase 1: Load files
        proforma_df = ProFormaLoader(str(files['proforma']), month).load()
        comp_df = CompensationLoader(str(files['compensation'])).load()
        hours_df = HarvestHoursLoader(str(files['hours']), month).load()
        expenses_df = HarvestExpensesLoader(str(files['expenses'])).load()
        pnl_df = PnLLoader(str(files['pl'])).load()

        # Phase 2: Classification
        classifier = ProjectClassifier()
        classified = classify_all_activity(proforma_df, hours_df, expenses_df, classifier)

        # Phase 3: Computations
        labor_df = calculate_labor_costs(hours_df, comp_df)
        expense_df = calculate_expense_costs(expenses_df)
        revenue_df = merge_direct_costs(proforma_df, labor_df, expense_df)

        # Compute cost center totals
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

        # Compute non-revenue client totals
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

        # Phase 4: Allocations
        allocator = OverheadAllocator(tolerance=SETTINGS['allocation_tolerance'])
        pools = allocator.calculate_pools(
            pnl_df,
            classified['cost_centers'],
            include_cc_in_sga=SETTINGS['include_cost_center_overhead_in_sga_pool']
        )
        revenue_df = allocator.allocate_sga(revenue_df, pools['sga_pool'])
        revenue_df = allocator.allocate_data(revenue_df, pools['data_pool'])
        revenue_df = allocator.allocate_workplace(revenue_df, pools['workplace_pool'])
        revenue_df = calculate_margins(revenue_df)

        # Phase 5: Validation
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
        validation_results = run_all_validations(data, tolerance=SETTINGS['allocation_tolerance'])

        # Phase 6: Output
        output_path = app.config['OUTPUT_FOLDER'] / month
        write_revenue_centers(revenue_df, output_path)
        write_cost_centers(classified['cost_centers'], output_path)
        write_non_revenue_clients(classified['non_revenue_clients'], output_path)
        write_validation_report(validation_results, output_path, month)

        # Save intermediate detail data for drill-down
        # Save hours with person, date, hours, rate
        hours_detail = hours_df.merge(comp_df[['staff_key', 'hourly_cost']], on='staff_key', how='left')
        hours_detail['labor_cost'] = hours_detail['hours'] * hours_detail['hourly_cost']
        hours_detail.to_csv(output_path / '_hours_detail.csv', index=False)

        # Save expenses detail
        if not expenses_df.empty:
            expenses_df.to_csv(output_path / '_expenses_detail.csv', index=False)

        # Save pools data for drill-down explanations
        import json
        data_tagged_revenue = revenue_df[revenue_df['allocation_tag'] == 'Data']['revenue'].sum()
        wellness_tagged_revenue = revenue_df[revenue_df['allocation_tag'] == 'Wellness']['revenue'].sum()

        pools_data = {
            'sga_pool': float(pools['sga_pool']),
            'data_pool': float(pools['data_pool']),
            'workplace_pool': float(pools['workplace_pool']),
            'total_revenue': float(revenue_df['revenue'].sum()),
            'data_tagged_revenue': float(data_tagged_revenue),
            'wellness_tagged_revenue': float(wellness_tagged_revenue)
        }
        with open(output_path / '_pools.json', 'w') as f:
            json.dump(pools_data, f, indent=2)

        return {
            'success': True,
            'output_dir': output_path,
            'validation_summary': validation_results.summary(),
            'pools': pools,
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


@app.route('/results')
def results():
    """Display analysis results."""
    analysis = session.get('last_analysis')
    if not analysis:
        flash('No analysis results available. Please upload files first.', 'warning')
        return redirect(url_for('index'))

    # Read CSV files as DataFrames
    import pandas as pd
    output_dir = Path(analysis['output_dir'])

    revenue_df = pd.read_csv(output_dir / 'revenue_centers.csv')
    cost_centers_df = pd.read_csv(output_dir / 'cost_centers.csv')
    non_revenue_df = pd.read_csv(output_dir / 'non_revenue_clients.csv')

    # Separate active and inactive revenue centers
    # A project is inactive if all financial columns are zero
    active_mask = (
        (revenue_df['revenue'].abs() > 0.01) |
        (revenue_df['labor_cost'].abs() > 0.01) |
        (revenue_df['expense_cost'].abs() > 0.01) |
        (revenue_df['sga_allocation'].abs() > 0.01) |
        (revenue_df['data_allocation'].abs() > 0.01) |
        (revenue_df['workplace_allocation'].abs() > 0.01) |
        (revenue_df['margin_dollars'].abs() > 0.01)
    )

    active_revenue_df = revenue_df[active_mask].copy()
    inactive_revenue_df = revenue_df[~active_mask].copy()

    # Separate active and inactive cost centers
    # A cost center is inactive if all cost columns are zero
    cost_center_active_mask = (
        (cost_centers_df['labor_cost'].abs() > 0.01) |
        (cost_centers_df['expense_cost'].abs() > 0.01) |
        (cost_centers_df['total_cost'].abs() > 0.01)
    )

    active_cost_centers_df = cost_centers_df[cost_center_active_mask].copy()
    inactive_cost_centers_df = cost_centers_df[~cost_center_active_mask].copy()

    # Calculate summary metrics (only from active projects)
    total_revenue = active_revenue_df['revenue'].sum()
    total_labor = active_revenue_df['labor_cost'].sum()
    total_expenses = active_revenue_df['expense_cost'].sum()
    total_sga = active_revenue_df['sga_allocation'].sum()
    total_data = active_revenue_df['data_allocation'].sum()
    total_workplace = active_revenue_df['workplace_allocation'].sum()
    total_margin = active_revenue_df['margin_dollars'].sum()
    overall_margin_pct = (total_margin / total_revenue * 100) if total_revenue > 0 else 0

    summary = {
        'total_revenue': total_revenue,
        'total_labor': total_labor,
        'total_expenses': total_expenses,
        'total_sga': total_sga,
        'total_data': total_data,
        'total_workplace': total_workplace,
        'total_margin': total_margin,
        'overall_margin_pct': overall_margin_pct,
        'revenue_center_count': len(active_revenue_df),
        'inactive_count': len(inactive_revenue_df),
        'cost_center_count': len(active_cost_centers_df),
        'inactive_cost_center_count': len(inactive_cost_centers_df),
        'non_revenue_count': len(non_revenue_df),
    }

    # Read validation report
    validation_file = output_dir / 'validation_report.md'
    validation_content = ''
    if validation_file.exists():
        with open(validation_file) as f:
            validation_content = f.read()

    return render_template('results.html',
                          analysis=analysis,
                          validation_content=validation_content,
                          summary=summary,
                          revenue_data=active_revenue_df.to_dict('records'),
                          inactive_revenue_data=inactive_revenue_df.to_dict('records'),
                          cost_center_data=active_cost_centers_df.to_dict('records'),
                          inactive_cost_center_data=inactive_cost_centers_df.to_dict('records'),
                          non_revenue_data=non_revenue_df.to_dict('records'))


@app.route('/api/project-detail/<month>/<contract_code>')
def project_detail(month, contract_code):
    """Get detailed breakdown for a specific project."""
    import pandas as pd
    import json

    output_dir = app.config['OUTPUT_FOLDER'] / month

    try:
        revenue_df = pd.read_csv(output_dir / 'revenue_centers.csv')
        project = revenue_df[revenue_df['contract_code'] == contract_code]

        if project.empty:
            return {'error': 'Project not found'}, 404

        project_row = project.iloc[0]

        # Load hours detail
        hours_detail_df = pd.read_csv(output_dir / '_hours_detail.csv')
        project_hours = hours_detail_df[hours_detail_df['contract_code'] == contract_code]

        # Load expenses detail
        expenses_detail = []
        expenses_file = output_dir / '_expenses_detail.csv'
        if expenses_file.exists():
            expenses_detail_df = pd.read_csv(expenses_file)
            project_expenses = expenses_detail_df[expenses_detail_df['contract_code'] == contract_code]
            if not project_expenses.empty:
                # Replace NaN with None for proper JSON serialization
                expenses_detail = project_expenses.where(pd.notna(project_expenses), None).to_dict('records')

        # Format hours detail - aggregate by person
        hours_detail = []
        total_hours = 0
        total_labor = 0
        if not project_hours.empty:
            # Group by person and sum hours/costs, sort by hours descending
            person_summary = project_hours.groupby('staff_key').agg({
                'hours': 'sum',
                'hourly_cost': 'first',  # Rate should be consistent per person
                'labor_cost': 'sum'
            }).reset_index().sort_values('hours', ascending=False)

            for _, row in person_summary.iterrows():
                # Handle missing compensation data (NaN values)
                hourly_cost = row['hourly_cost'] if pd.notna(row['hourly_cost']) else 0.0
                labor_cost = row['labor_cost'] if pd.notna(row['labor_cost']) else 0.0

                hours_detail.append({
                    'staff': row['staff_key'],
                    'hours': float(row['hours']),
                    'rate': float(hourly_cost),
                    'cost': float(labor_cost)
                })
                total_hours += float(row['hours'])
                total_labor += float(labor_cost)

        # Load pools data for allocation explanations
        pools_data = {}
        pools_file = output_dir / '_pools.json'
        if pools_file.exists():
            with open(pools_file) as f:
                pools_data = json.load(f)

        # Calculate allocation percentages and details
        revenue = float(project_row['revenue'])
        sga_pct = (float(project_row['sga_allocation']) / revenue * 100) if revenue > 0 else 0
        data_pct = (float(project_row['data_allocation']) / revenue * 100) if revenue > 0 else 0
        workplace_pct = (float(project_row['workplace_allocation']) / revenue * 100) if revenue > 0 else 0

        # SG&A calculation details
        sga_details = {}
        if pools_data and revenue > 0:
            total_revenue = pools_data.get('total_revenue', 0)
            sga_pool = pools_data.get('sga_pool', 0)
            revenue_share = (revenue / total_revenue * 100) if total_revenue > 0 else 0
            sga_details = {
                'sga_pool': sga_pool,
                'total_revenue': total_revenue,
                'project_revenue': revenue,
                'revenue_share_pct': revenue_share,
                'sga_allocation': float(project_row['sga_allocation'])
            }

        # Data allocation calculation details (only if Data-tagged)
        data_details = {}
        if pools_data and revenue > 0 and project_row['allocation_tag'] == 'Data':
            data_tagged_revenue = pools_data.get('data_tagged_revenue', 0)
            data_pool = pools_data.get('data_pool', 0)
            data_share = (revenue / data_tagged_revenue * 100) if data_tagged_revenue > 0 else 0
            data_details = {
                'data_pool': data_pool,
                'data_tagged_revenue': data_tagged_revenue,
                'project_revenue': revenue,
                'data_share_pct': data_share,
                'data_allocation': float(project_row['data_allocation'])
            }

        # Wellness allocation calculation details (only if Wellness-tagged)
        wellness_details = {}
        if pools_data and revenue > 0 and project_row['allocation_tag'] == 'Wellness':
            wellness_tagged_revenue = pools_data.get('wellness_tagged_revenue', 0)
            workplace_pool = pools_data.get('workplace_pool', 0)
            wellness_share = (revenue / wellness_tagged_revenue * 100) if wellness_tagged_revenue > 0 else 0
            wellness_details = {
                'workplace_pool': workplace_pool,
                'wellness_tagged_revenue': wellness_tagged_revenue,
                'project_revenue': revenue,
                'wellness_share_pct': wellness_share,
                'workplace_allocation': float(project_row['workplace_allocation'])
            }

        detail = {
            'project_name': project_row['project_name'],
            'contract_code': contract_code,
            'calculation': {
                'revenue': float(project_row['revenue']),
                'labor_cost': float(project_row['labor_cost']),
                'labor_hours': total_hours,
                'labor_avg_rate': (total_labor / total_hours) if total_hours > 0 else 0,
                'expense_cost': float(project_row['expense_cost']),
                'sga_allocation': float(project_row['sga_allocation']),
                'sga_pct': sga_pct,
                'data_allocation': float(project_row['data_allocation']),
                'data_pct': data_pct,
                'data_tagged': project_row['allocation_tag'] == 'Data',
                'workplace_allocation': float(project_row['workplace_allocation']),
                'workplace_pct': workplace_pct,
                'wellness_tagged': project_row['allocation_tag'] == 'Wellness',
                'margin_dollars': float(project_row['margin_dollars']),
                'margin_percent': float(project_row['margin_percent']),
            },
            'sga_details': sga_details,
            'data_details': data_details,
            'wellness_details': wellness_details,
            'hours_detail': hours_detail,
            'expenses_detail': expenses_detail
        }

        return detail

    except Exception as e:
        return {'error': str(e)}, 500


@app.route('/api/cost-center-detail/<month>/<contract_code>')
def cost_center_detail(month, contract_code):
    """Get detailed breakdown for a specific cost center."""
    import pandas as pd

    output_dir = app.config['OUTPUT_FOLDER'] / month

    try:
        cost_centers_df = pd.read_csv(output_dir / 'cost_centers.csv')
        cost_center = cost_centers_df[cost_centers_df['contract_code'] == contract_code]

        if cost_center.empty:
            return {'error': 'Cost center not found'}, 404

        cc_row = cost_center.iloc[0]

        # Load hours detail
        hours_detail_df = pd.read_csv(output_dir / '_hours_detail.csv')
        cc_hours = hours_detail_df[hours_detail_df['contract_code'] == contract_code]

        # Load expenses detail
        expenses_detail = []
        expenses_file = output_dir / '_expenses_detail.csv'
        if expenses_file.exists():
            expenses_detail_df = pd.read_csv(expenses_file)
            cc_expenses = expenses_detail_df[expenses_detail_df['contract_code'] == contract_code]
            if not cc_expenses.empty:
                # Replace NaN with None for proper JSON serialization
                expenses_detail = cc_expenses.where(pd.notna(cc_expenses), None).to_dict('records')

        # Format hours detail - aggregate by person
        hours_detail = []
        total_hours = 0
        total_labor = 0
        if not cc_hours.empty:
            person_summary = cc_hours.groupby('staff_key').agg({
                'hours': 'sum',
                'hourly_cost': 'first',
                'labor_cost': 'sum'
            }).reset_index().sort_values('hours', ascending=False)

            for _, row in person_summary.iterrows():
                # Handle missing compensation data (NaN values)
                hourly_cost = row['hourly_cost'] if pd.notna(row['hourly_cost']) else 0.0
                labor_cost = row['labor_cost'] if pd.notna(row['labor_cost']) else 0.0

                hours_detail.append({
                    'staff': row['staff_key'],
                    'hours': float(row['hours']),
                    'rate': float(hourly_cost),
                    'cost': float(labor_cost)
                })
                total_hours += float(row['hours'])
                total_labor += float(labor_cost)

        detail = {
            'name': cc_row['description'] if 'description' in cc_row else contract_code,
            'contract_code': contract_code,
            'type': 'cost_center',
            'labor_cost': float(cc_row['labor_cost']) if 'labor_cost' in cc_row else 0.0,
            'expense_cost': float(cc_row['expense_cost']) if 'expense_cost' in cc_row else 0.0,
            'total_cost': float(cc_row['total_cost']) if 'total_cost' in cc_row else 0.0,
            'hours_detail': hours_detail,
            'expenses_detail': expenses_detail
        }

        return detail

    except Exception as e:
        return {'error': str(e)}, 500


@app.route('/api/non-revenue-detail/<month>/<contract_code>')
def non_revenue_detail(month, contract_code):
    """Get detailed breakdown for a specific non-revenue client."""
    import pandas as pd

    output_dir = app.config['OUTPUT_FOLDER'] / month

    try:
        non_revenue_df = pd.read_csv(output_dir / 'non_revenue_clients.csv')
        non_revenue = non_revenue_df[non_revenue_df['contract_code'] == contract_code]

        if non_revenue.empty:
            return {'error': 'Non-revenue client not found'}, 404

        nrc_row = non_revenue.iloc[0]

        # Load hours detail
        hours_detail_df = pd.read_csv(output_dir / '_hours_detail.csv')
        nrc_hours = hours_detail_df[hours_detail_df['contract_code'] == contract_code]

        # Load expenses detail
        expenses_detail = []
        expenses_file = output_dir / '_expenses_detail.csv'
        if expenses_file.exists():
            expenses_detail_df = pd.read_csv(expenses_file)
            nrc_expenses = expenses_detail_df[expenses_detail_df['contract_code'] == contract_code]
            if not nrc_expenses.empty:
                # Replace NaN with None for proper JSON serialization
                expenses_detail = nrc_expenses.where(pd.notna(nrc_expenses), None).to_dict('records')

        # Format hours detail - aggregate by person
        hours_detail = []
        total_hours = 0
        total_labor = 0
        if not nrc_hours.empty:
            person_summary = nrc_hours.groupby('staff_key').agg({
                'hours': 'sum',
                'hourly_cost': 'first',
                'labor_cost': 'sum'
            }).reset_index().sort_values('hours', ascending=False)

            for _, row in person_summary.iterrows():
                # Handle missing compensation data (NaN values)
                hourly_cost = row['hourly_cost'] if pd.notna(row['hourly_cost']) else 0.0
                labor_cost = row['labor_cost'] if pd.notna(row['labor_cost']) else 0.0

                hours_detail.append({
                    'staff': row['staff_key'],
                    'hours': float(row['hours']),
                    'rate': float(hourly_cost),
                    'cost': float(labor_cost)
                })
                total_hours += float(row['hours'])
                total_labor += float(labor_cost)

        detail = {
            'name': nrc_row['project_name'] if 'project_name' in nrc_row else contract_code,
            'contract_code': contract_code,
            'type': 'non_revenue_client',
            'labor_cost': float(nrc_row['labor_cost']) if 'labor_cost' in nrc_row else 0.0,
            'expense_cost': float(nrc_row['expense_cost']) if 'expense_cost' in nrc_row else 0.0,
            'total_cost': float(nrc_row['total_cost']) if 'total_cost' in nrc_row else 0.0,
            'hours_detail': hours_detail,
            'expenses_detail': expenses_detail
        }

        return detail

    except Exception as e:
        return {'error': str(e)}, 500


@app.route('/download/<month>/<filename>')
def download_file(month, filename):
    """Download a generated output file."""
    filepath = app.config['OUTPUT_FOLDER'] / month / filename
    if not filepath.exists():
        flash('File not found', 'error')
        return redirect(url_for('results'))

    return send_file(filepath, as_attachment=True)


@app.errorhandler(413)
def too_large(e):
    """Handle file too large error."""
    flash('File is too large. Maximum size is 50MB.', 'error')
    return redirect(url_for('index'))


if __name__ == '__main__':
    # Get port from environment variable (for cloud deployment) or default to 5000
    port = int(os.environ.get('PORT', 5000))
    # Only enable debug mode in development
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(debug=debug, host='0.0.0.0', port=port)
