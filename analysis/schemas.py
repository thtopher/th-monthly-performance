"""
Data schemas for intermediate tables.
All DataFrames follow these standard column definitions.
"""

# Note: pandas uses dtype-like hints; we provide canonical column names here.

# Pro Forma intermediate schema
PROFORMA_SCHEMA = {
    'contract_code': str,        # Normalized contract code (primary key after aggregation)
    'project_name': str,         # Project name (first non-empty if duplicates)
    'proforma_section': str,     # BEH/PAD/MAR/WWB/CMH (from section headers)
    'analysis_category': str,    # Next Gen Advisory/Data/Wellness (from mapping)
    'allocation_tag': str,       # Data/Wellness/blank (from Column A, reconciled if duplicates)
    'revenue': float,            # Monthly revenue (aggregated if duplicates)
}

# Compensation intermediate schema
COMPENSATION_SCHEMA = {
    'staff_key': str,            # Last Name (must be unique)
    'hourly_cost': float,        # Fully-loaded hourly cost
    'strategy_used': str,        # 'A' (direct read) or 'B' (computed)
}

# Harvest Hours intermediate schema
HOURS_SCHEMA = {
    'date': 'datetime64[ns]',    # Date of work
    'contract_code': str,        # Normalized contract code
    'staff_key': str,            # Last Name
    'hours': float,              # Hours worked
}

# Harvest Expenses intermediate schema
EXPENSES_SCHEMA = {
    'date': 'datetime64[ns]',    # Date of expense
    'contract_code': str,        # Normalized contract code
    'amount': float,             # Non-reimbursable expense amount (already filtered)
    'was_reimbursable': bool,    # Track what was excluded (for logging)
}

# P&L Accounts intermediate schema
PNL_SCHEMA = {
    'account_name': str,         # P&L account name
    'amount': float,             # Total amount
    'bucket': str,               # DATA/WORKPLACE/NIL/SGA
    'matched_by': str,           # exact/contains/regex/default
}

