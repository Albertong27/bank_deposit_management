from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
import os
from datetime import datetime, timedelta
from functools import wraps
from models import DepositManager, ConfigManager, DatabaseManager, UserManager

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'


# Inject common template variables (year, app name)
@app.context_processor
def inject_globals():
    return {
        'current_year': datetime.now().year,
        'app_name': 'Bank Deposit Management',
        'company_name': 'Simply Smart X Alpha'
    }

# Initialize managers
db_manager = DatabaseManager()
deposit_manager = DepositManager(db_manager)
config_manager = ConfigManager(db_manager)
user_manager = UserManager(db_manager)

# Authentication decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        
        user = user_manager.get_user(session['user_id'])
        if not user or not user['is_admin']:
            flash('Admin access required.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = user_manager.authenticate_user(username, password)
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = user['is_admin']
            flash(f'Welcome back, {username}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    """Home page showing user's deposits"""
    user_id = session['user_id']
    deposits = deposit_manager.get_all_deposits(user_id)
    return render_template('index.html', deposits=deposits)

@app.route('/add_deposit', methods=['GET', 'POST'])
@login_required
def add_deposit():
    """Add a new deposit"""
    user_id = session['user_id']
    if request.method == 'POST':
        try:
            data = {
                'account_holder': request.form['account_holder'],
                'account_number': request.form['account_number'],
                'bank_name': request.form['bank_name'],
                'principal_amount': float(request.form['principal_amount']),
                'interest_rate': float(request.form['interest_rate']),
                'deposit_date': request.form['deposit_date'],
                'maturity_date': request.form['maturity_date'],
                'tax_rate': float(request.form.get('tax_rate', config_manager.get_default_tax_rate(user_id)))
            }
            
            deposit_manager.add_deposit(data, user_id)
            flash('Deposit added successfully!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'Error adding deposit: {str(e)}', 'error')
    
    banks = config_manager.get_banks(user_id)
    default_tax_rate = config_manager.get_default_tax_rate(user_id)
    return render_template('add_deposit.html', banks=banks, default_tax_rate=default_tax_rate)

@app.route('/deposit/<deposit_id>')
@login_required
def view_deposit(deposit_id):
    """View details of a specific deposit"""
    user_id = session['user_id']
    deposit = deposit_manager.get_deposit(deposit_id, user_id)
    if not deposit:
        flash('Deposit not found!', 'error')
        return redirect(url_for('index'))
    
    return render_template('view_deposit.html', deposit=deposit)

@app.route('/edit_deposit/<deposit_id>', methods=['GET', 'POST'])
@login_required
def edit_deposit(deposit_id):
    """Edit an existing deposit"""
    user_id = session['user_id']
    deposit = deposit_manager.get_deposit(deposit_id, user_id)
    if not deposit:
        flash('Deposit not found!', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        try:
            data = {
                'account_holder': request.form['account_holder'],
                'account_number': request.form['account_number'],
                'bank_name': request.form['bank_name'],
                'principal_amount': float(request.form['principal_amount']),
                'interest_rate': float(request.form['interest_rate']),
                'deposit_date': request.form['deposit_date'],
                'maturity_date': request.form['maturity_date'],
                'tax_rate': float(request.form.get('tax_rate', config_manager.get_default_tax_rate(user_id)))
            }
            
            deposit_manager.update_deposit(deposit_id, data, user_id)
            flash('Deposit updated successfully!', 'success')
            return redirect(url_for('view_deposit', deposit_id=deposit_id))
        except Exception as e:
            flash(f'Error updating deposit: {str(e)}', 'error')
    
    banks = config_manager.get_banks(user_id)
    return render_template('edit_deposit.html', deposit=deposit, banks=banks)

@app.route('/delete_deposit/<deposit_id>', methods=['POST'])
@login_required
def delete_deposit(deposit_id):
    """Delete a deposit"""
    user_id = session['user_id']
    try:
        deposit_manager.delete_deposit(deposit_id, user_id)
        flash('Deposit deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting deposit: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/summary')
@login_required
def summary():
    """Show summary of user's deposits"""
    user_id = session['user_id']
    summary_data = deposit_manager.get_summary(user_id)
    return render_template('summary.html', summary=summary_data)

@app.route('/banks')
@login_required
def banks():
    """Manage user's banks and their default interest rates"""
    user_id = session['user_id']
    banks = config_manager.get_banks(user_id)
    return render_template('banks.html', banks=banks)

@app.route('/add_bank', methods=['POST'])
@login_required
def add_bank():
    """Add a new bank for the user"""
    user_id = session['user_id']
    try:
        bank_name = request.form['bank_name']
        default_interest_rate = float(request.form['default_interest_rate'])
        
        user_manager.add_user_bank(user_id, bank_name, default_interest_rate)
        flash(f'Bank {bank_name} added successfully!', 'success')
    except Exception as e:
        flash(f'Error adding bank: {str(e)}', 'error')
    
    return redirect(url_for('banks'))

@app.route('/update_bank', methods=['POST'])
@login_required
def update_bank():
    """Update user's bank default interest rate"""
    user_id = session['user_id']
    try:
        bank_name = request.form['bank_name']
        default_interest_rate = float(request.form['default_interest_rate'])
        
        user_manager.update_user_bank(user_id, bank_name, default_interest_rate)
        flash(f'Bank {bank_name} updated successfully!', 'success')
    except Exception as e:
        flash(f'Error updating bank: {str(e)}', 'error')
    
    return redirect(url_for('banks'))

@app.route('/delete_bank', methods=['POST'])
@login_required
def delete_bank():
    """Delete a user's bank"""
    user_id = session['user_id']
    try:
        bank_name = request.form['bank_name']
        user_manager.delete_user_bank(user_id, bank_name)
        flash(f'Bank {bank_name} deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting bank: {str(e)}', 'error')
    
    return redirect(url_for('banks'))

@app.route('/settings')
@login_required
def settings():
    """Manage user's application settings"""
    user_id = session['user_id']
    default_tax_rate = config_manager.get_default_tax_rate(user_id)
    currency_symbol = config_manager.get_currency_symbol(user_id)
    return render_template('settings.html', default_tax_rate=default_tax_rate, currency_symbol=currency_symbol)

@app.route('/update_settings', methods=['POST'])
@login_required
def update_settings():
    """Update user's application settings"""
    user_id = session['user_id']
    try:
        default_tax_rate = float(request.form['default_tax_rate'])
        user_manager.set_user_setting(user_id, 'default_tax_rate', str(default_tax_rate))
        flash('Settings updated successfully!', 'success')
    except Exception as e:
        flash(f'Error updating settings: {str(e)}', 'error')
    
    return redirect(url_for('settings'))

# Admin user management routes
@app.route('/admin/users')
@admin_required
def admin_users():
    """Admin page to manage users"""
    users = user_manager.get_all_users()
    return render_template('admin_users.html', users=users)

@app.route('/admin/add_user', methods=['POST'])
@admin_required
def admin_add_user():
    """Add a new user (admin only)"""
    try:
        username = request.form['username']
        password = request.form['password']
        is_admin = 'is_admin' in request.form
        
        # Check if username already exists
        existing_user = user_manager.get_user_by_username(username)
        if existing_user:
            flash(f'Username {username} already exists!', 'error')
            return redirect(url_for('admin_users'))
        
        user_manager.create_user(username, password, is_admin)
        flash(f'User {username} created successfully!', 'success')
    except Exception as e:
        flash(f'Error creating user: {str(e)}', 'error')
    
    return redirect(url_for('admin_users'))

@app.route('/admin/update_user_password', methods=['POST'])
@admin_required
def admin_update_user_password():
    """Update user password (admin only)"""
    try:
        user_id = int(request.form['user_id'])
        new_password = request.form['new_password']
        
        user_manager.update_user_password(user_id, new_password)
        flash('Password updated successfully!', 'success')
    except Exception as e:
        flash(f'Error updating password: {str(e)}', 'error')
    
    return redirect(url_for('admin_users'))

@app.route('/admin/delete_user', methods=['POST'])
@admin_required
def admin_delete_user():
    """Delete a user (admin only)"""
    try:
        user_id = int(request.form['user_id'])
        
        # Prevent admin from deleting themselves
        if user_id == session['user_id']:
            flash('You cannot delete your own account!', 'error')
            return redirect(url_for('admin_users'))
        
        user_manager.delete_user(user_id)
        flash('User deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting user: {str(e)}', 'error')
    
    return redirect(url_for('admin_users'))

@app.route('/api/deposits')
@login_required
def api_deposits():
    """API endpoint to get user's deposits as JSON"""
    user_id = session['user_id']
    deposits = deposit_manager.get_all_deposits(user_id)
    return jsonify(deposits)

if __name__ == '__main__':
    app.run(debug=True)
