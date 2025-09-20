import sqlite3
import os
import bcrypt
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class DatabaseManager:
    def __init__(self, db_file: str = 'data/bank_deposits.db'):
        self.db_file = db_file
        self.ensure_data_directory()
        self.init_database()
    
    def ensure_data_directory(self):
        """Ensure the data directory exists"""
        os.makedirs(os.path.dirname(self.db_file), exist_ok=True)
    
    def init_database(self):
        """Initialize the database with required tables"""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            
            # Create banks table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS banks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    default_interest_rate REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create deposits table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS deposits (
                    deposit_id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    account_holder TEXT NOT NULL,
                    account_number TEXT NOT NULL,
                    bank_name TEXT NOT NULL,
                    principal_amount REAL NOT NULL,
                    interest_rate REAL NOT NULL,
                    deposit_date DATE NOT NULL,
                    maturity_date DATE NOT NULL,
                    tax_rate REAL NOT NULL,
                    days_period INTEGER NOT NULL,
                    time_period_years REAL NOT NULL,
                    interest_before_tax REAL NOT NULL,
                    tax_amount REAL NOT NULL,
                    interest_after_tax REAL NOT NULL,
                    total_maturity_amount REAL NOT NULL,
                    daily_interest_before_tax REAL NOT NULL,
                    daily_interest_after_tax REAL NOT NULL,
                    is_matured BOOLEAN NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                    FOREIGN KEY (bank_name) REFERENCES banks (name)
                )
            ''')
            
            # Create users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    is_admin BOOLEAN NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create user_settings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_settings (
                    user_id INTEGER NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, key),
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            ''')
            
            # Create user_banks table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_banks (
                    user_id INTEGER NOT NULL,
                    bank_name TEXT NOT NULL,
                    default_interest_rate REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, bank_name),
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            ''')
            
            # Create settings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Insert default settings if they don't exist
            cursor.execute('''
                INSERT OR IGNORE INTO settings (key, value) VALUES 
                ('currency', 'IDR'),
                ('currency_symbol', 'Rp'),
                ('default_tax_rate', '20.0')
            ''')
            
            conn.commit()
            
            # Migrate existing deposits table to add user_id column if it doesn't exist
            self._migrate_deposits_table()

    def _migrate_deposits_table(self):
        """Migrate existing deposits table to add user_id column"""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            
            # Check if user_id column exists
            cursor.execute("PRAGMA table_info(deposits)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'user_id' not in columns:
                # Add user_id column with default value 1 (admin user)
                cursor.execute("ALTER TABLE deposits ADD COLUMN user_id INTEGER DEFAULT 1")
                
                # Update existing deposits to belong to admin user (ID 1)
                cursor.execute("UPDATE deposits SET user_id = 1 WHERE user_id IS NULL")
                
                # Add foreign key constraint
                cursor.execute("""
                    CREATE TABLE deposits_new (
                        deposit_id TEXT PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        account_holder TEXT NOT NULL,
                        account_number TEXT NOT NULL,
                        bank_name TEXT NOT NULL,
                        principal_amount REAL NOT NULL,
                        interest_rate REAL NOT NULL,
                        deposit_date DATE NOT NULL,
                        maturity_date DATE NOT NULL,
                        tax_rate REAL NOT NULL,
                        days_period INTEGER NOT NULL,
                        time_period_years REAL NOT NULL,
                        interest_before_tax REAL NOT NULL,
                        tax_amount REAL NOT NULL,
                        interest_after_tax REAL NOT NULL,
                        total_maturity_amount REAL NOT NULL,
                        daily_interest_before_tax REAL NOT NULL,
                        daily_interest_after_tax REAL NOT NULL,
                        is_matured BOOLEAN NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                        FOREIGN KEY (bank_name) REFERENCES banks (name)
                    )
                """)
                
                # Copy data from old table to new table
                cursor.execute("""
                    INSERT INTO deposits_new 
                    SELECT * FROM deposits
                """)
                
                # Drop old table and rename new table
                cursor.execute("DROP TABLE deposits")
                cursor.execute("ALTER TABLE deposits_new RENAME TO deposits")
                
                conn.commit()

class UserManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self._create_initial_admin()
    
    def _create_initial_admin(self):
        """Create initial admin user if no users exist"""
        with sqlite3.connect(self.db_manager.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            
            if user_count == 0:
                # Create initial admin user
                password_hash = self._hash_password('admin123')
                cursor.execute('''
                    INSERT INTO users (username, password_hash, is_admin)
                    VALUES (?, ?, 1)
                ''', ('admin', password_hash))
                conn.commit()
    
    def _hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a password against its hash"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate a user and return user data if successful"""
        with sqlite3.connect(self.db_manager.db_file) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()
            
            if user and self.verify_password(password, user['password_hash']):
                return dict(user)
            return None
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        with sqlite3.connect(self.db_manager.db_file) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            user = cursor.fetchone()
            return dict(user) if user else None
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username"""
        with sqlite3.connect(self.db_manager.db_file) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()
            return dict(user) if user else None
    
    def create_user(self, username: str, password: str, is_admin: bool = False) -> int:
        """Create a new user"""
        password_hash = self._hash_password(password)
        with sqlite3.connect(self.db_manager.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (username, password_hash, is_admin, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (username, password_hash, is_admin))
            conn.commit()
            return cursor.lastrowid
    
    def update_user_password(self, user_id: int, new_password: str):
        """Update user password"""
        password_hash = self._hash_password(new_password)
        with sqlite3.connect(self.db_manager.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users 
                SET password_hash = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (password_hash, user_id))
            conn.commit()
    
    def delete_user(self, user_id: int):
        """Delete a user"""
        with sqlite3.connect(self.db_manager.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
    
    def get_all_users(self) -> List[Dict]:
        """Get all users"""
        with sqlite3.connect(self.db_manager.db_file) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, is_admin, created_at FROM users ORDER BY username")
            return [dict(row) for row in cursor.fetchall()]
    
    def get_user_setting(self, user_id: int, key: str, default_value: str = None) -> str:
        """Get a user-specific setting"""
        with sqlite3.connect(self.db_manager.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM user_settings WHERE user_id = ? AND key = ?", (user_id, key))
            result = cursor.fetchone()
            return result[0] if result else default_value
    
    def set_user_setting(self, user_id: int, key: str, value: str):
        """Set a user-specific setting"""
        with sqlite3.connect(self.db_manager.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO user_settings (user_id, key, value, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, key, value))
            conn.commit()
    
    def get_user_banks(self, user_id: int) -> Dict:
        """Get user-specific banks"""
        with sqlite3.connect(self.db_manager.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT bank_name, default_interest_rate FROM user_banks WHERE user_id = ? ORDER BY bank_name", (user_id,))
            banks = {}
            for row in cursor.fetchall():
                banks[row[0]] = {
                    'name': row[0],
                    'default_interest_rate': row[1]
                }
            return banks
    
    def add_user_bank(self, user_id: int, bank_name: str, default_interest_rate: float):
        """Add a user-specific bank"""
        with sqlite3.connect(self.db_manager.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO user_banks (user_id, bank_name, default_interest_rate, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, bank_name, default_interest_rate))
            conn.commit()
    
    def update_user_bank(self, user_id: int, bank_name: str, default_interest_rate: float):
        """Update user-specific bank"""
        with sqlite3.connect(self.db_manager.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE user_banks 
                SET default_interest_rate = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND bank_name = ?
            ''', (default_interest_rate, user_id, bank_name))
            conn.commit()
    
    def delete_user_bank(self, user_id: int, bank_name: str):
        """Delete user-specific bank"""
        with sqlite3.connect(self.db_manager.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user_banks WHERE user_id = ? AND bank_name = ?", (user_id, bank_name))
            conn.commit()

class ConfigManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def get_currency_symbol(self, user_id: int = None):
        """Get the currency symbol (user-specific or global)"""
        if user_id:
            with sqlite3.connect(self.db_manager.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM user_settings WHERE user_id = ? AND key = 'currency_symbol'", (user_id,))
                result = cursor.fetchone()
                if result:
                    return result[0]
        
        with sqlite3.connect(self.db_manager.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = 'currency_symbol'")
            result = cursor.fetchone()
            return result[0] if result else 'Rp'
    
    def get_default_tax_rate(self, user_id: int = None):
        """Get the default tax rate (user-specific or global)"""
        if user_id:
            with sqlite3.connect(self.db_manager.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM user_settings WHERE user_id = ? AND key = 'default_tax_rate'", (user_id,))
                result = cursor.fetchone()
                if result:
                    return float(result[0])
        
        with sqlite3.connect(self.db_manager.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = 'default_tax_rate'")
            result = cursor.fetchone()
            return float(result[0]) if result else 20.0
    
    def get_banks(self, user_id: int = None):
        """Get all banks with their default interest rates (user-specific or global)"""
        banks = {}
        
        # Get user-specific banks first if user_id is provided
        if user_id:
            with sqlite3.connect(self.db_manager.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT bank_name, default_interest_rate FROM user_banks WHERE user_id = ? ORDER BY bank_name", (user_id,))
                for row in cursor.fetchall():
                    banks[row[0]] = {
                        'name': row[0],
                        'default_interest_rate': row[1]
                    }
        
        # If no user-specific banks or no user_id, get global banks
        if not banks:
            with sqlite3.connect(self.db_manager.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name, default_interest_rate FROM banks ORDER BY name")
                for row in cursor.fetchall():
                    banks[row[0]] = {
                        'name': row[0],
                        'default_interest_rate': row[1]
                    }
        
        return banks
    
    def add_bank(self, bank_name: str, default_interest_rate: float):
        """Add a new bank"""
        with sqlite3.connect(self.db_manager.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO banks (name, default_interest_rate, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (bank_name, default_interest_rate))
            conn.commit()
    
    def update_bank(self, bank_name: str, default_interest_rate: float):
        """Update bank's default interest rate"""
        with sqlite3.connect(self.db_manager.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE banks 
                SET default_interest_rate = ?, updated_at = CURRENT_TIMESTAMP
                WHERE name = ?
            ''', (default_interest_rate, bank_name))
            conn.commit()
    
    def delete_bank(self, bank_name: str):
        """Delete a bank"""
        with sqlite3.connect(self.db_manager.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM banks WHERE name = ?", (bank_name,))
            conn.commit()
    
    def update_default_tax_rate(self, tax_rate: float):
        """Update the default tax rate"""
        with sqlite3.connect(self.db_manager.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE settings 
                SET value = ?, updated_at = CURRENT_TIMESTAMP
                WHERE key = 'default_tax_rate'
            ''', (str(tax_rate),))
            conn.commit()

class DepositManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.config_manager = ConfigManager(db_manager)
    
    def generate_deposit_id(self) -> str:
        """Generate a unique deposit ID"""
        with sqlite3.connect(self.db_manager.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(CAST(SUBSTR(deposit_id, 4) AS INTEGER)) FROM deposits WHERE deposit_id LIKE 'DEP%'")
            result = cursor.fetchone()
            max_id = result[0] if result[0] is not None else 0
            return f"DEP{max_id + 1:03d}"
    
    def format_currency(self, amount: float) -> str:
        """Format amount in IDR currency"""
        currency_symbol = self.config_manager.get_currency_symbol()
        return f"{currency_symbol} {amount:,.0f}".replace(',', '.')
    
    def add_deposit(self, deposit_data: Dict, user_id: int) -> str:
        """Add a new deposit"""
        deposit_id = self.generate_deposit_id()
        
        # Calculate derived fields
        deposit_data['deposit_id'] = deposit_id
        deposit_data['user_id'] = user_id
        deposit_data['created_at'] = datetime.now().isoformat()
        
        # Calculate interest and maturity details
        self._calculate_deposit_details(deposit_data)
        
        with sqlite3.connect(self.db_manager.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO deposits (
                    deposit_id, user_id, account_holder, account_number, bank_name,
                    principal_amount, interest_rate, deposit_date, maturity_date,
                    tax_rate, days_period, time_period_years, interest_before_tax,
                    tax_amount, interest_after_tax, total_maturity_amount,
                    daily_interest_before_tax, daily_interest_after_tax, is_matured,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                deposit_data['deposit_id'],
                deposit_data['user_id'],
                deposit_data['account_holder'],
                deposit_data['account_number'],
                deposit_data['bank_name'],
                deposit_data['principal_amount'],
                deposit_data['interest_rate'],
                deposit_data['deposit_date'],
                deposit_data['maturity_date'],
                deposit_data['tax_rate'],
                deposit_data['days_period'],
                deposit_data['time_period_years'],
                deposit_data['interest_before_tax'],
                deposit_data['tax_amount'],
                deposit_data['interest_after_tax'],
                deposit_data['total_maturity_amount'],
                deposit_data['daily_interest_before_tax'],
                deposit_data['daily_interest_after_tax'],
                deposit_data['is_matured'],
                deposit_data['created_at'],
                datetime.now().isoformat()
            ))
            conn.commit()
        
        return deposit_id
    
    def get_deposit(self, deposit_id: str, user_id: int = None) -> Optional[Dict]:
        """Get a specific deposit by ID"""
        with sqlite3.connect(self.db_manager.db_file) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            if user_id:
                cursor.execute("SELECT * FROM deposits WHERE deposit_id = ? AND user_id = ?", (deposit_id, user_id))
            else:
                cursor.execute("SELECT * FROM deposits WHERE deposit_id = ?", (deposit_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def get_all_deposits(self, user_id: int = None) -> List[Dict]:
        """Get all deposits (user-specific or all)"""
        with sqlite3.connect(self.db_manager.db_file) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            if user_id:
                cursor.execute("SELECT * FROM deposits WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
            else:
                cursor.execute("SELECT * FROM deposits ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]
    
    def update_deposit(self, deposit_id: str, deposit_data: Dict, user_id: int = None):
        """Update an existing deposit"""
        # Get original creation time
        original_deposit = self.get_deposit(deposit_id, user_id)
        if not original_deposit:
            raise ValueError(f"Deposit {deposit_id} not found")
        
        # Preserve original creation time and user_id
        deposit_data['deposit_id'] = deposit_id
        deposit_data['user_id'] = original_deposit['user_id']
        deposit_data['created_at'] = original_deposit['created_at']
        deposit_data['updated_at'] = datetime.now().isoformat()
        
        # Recalculate interest and maturity details
        self._calculate_deposit_details(deposit_data)
        
        with sqlite3.connect(self.db_manager.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE deposits SET
                    account_holder = ?, account_number = ?, bank_name = ?,
                    principal_amount = ?, interest_rate = ?, deposit_date = ?,
                    maturity_date = ?, tax_rate = ?, days_period = ?,
                    time_period_years = ?, interest_before_tax = ?, tax_amount = ?,
                    interest_after_tax = ?, total_maturity_amount = ?,
                    daily_interest_before_tax = ?, daily_interest_after_tax = ?,
                    is_matured = ?, updated_at = ?
                WHERE deposit_id = ?
            ''', (
                deposit_data['account_holder'],
                deposit_data['account_number'],
                deposit_data['bank_name'],
                deposit_data['principal_amount'],
                deposit_data['interest_rate'],
                deposit_data['deposit_date'],
                deposit_data['maturity_date'],
                deposit_data['tax_rate'],
                deposit_data['days_period'],
                deposit_data['time_period_years'],
                deposit_data['interest_before_tax'],
                deposit_data['tax_amount'],
                deposit_data['interest_after_tax'],
                deposit_data['total_maturity_amount'],
                deposit_data['daily_interest_before_tax'],
                deposit_data['daily_interest_after_tax'],
                deposit_data['is_matured'],
                deposit_data['updated_at'],
                deposit_id
            ))
            conn.commit()
    
    def delete_deposit(self, deposit_id: str, user_id: int = None):
        """Delete a deposit"""
        with sqlite3.connect(self.db_manager.db_file) as conn:
            cursor = conn.cursor()
            if user_id:
                cursor.execute("DELETE FROM deposits WHERE deposit_id = ? AND user_id = ?", (deposit_id, user_id))
            else:
                cursor.execute("DELETE FROM deposits WHERE deposit_id = ?", (deposit_id,))
            if cursor.rowcount == 0:
                raise ValueError(f"Deposit {deposit_id} not found")
            conn.commit()
    
    def _calculate_deposit_details(self, deposit_data: Dict):
        """Calculate interest, tax, and maturity details"""
        principal = deposit_data['principal_amount']
        interest_rate = deposit_data['interest_rate']
        deposit_date = datetime.fromisoformat(deposit_data['deposit_date'])
        maturity_date = datetime.fromisoformat(deposit_data['maturity_date'])
        tax_rate = deposit_data.get('tax_rate', 0)
        
        # Calculate time period in days and years
        days_period = (maturity_date - deposit_date).days
        time_period_years = days_period / 365
        
        # Calculate interest using the formula: (principal * interest_rate%) / 365 * days
        interest_before_tax = (principal * (interest_rate / 100) / 365) * days_period
        
        # Calculate tax on interest
        tax_amount = interest_before_tax * (tax_rate / 100)
        
        # Calculate interest after tax
        interest_after_tax = interest_before_tax - tax_amount
        
        # Calculate total maturity amount
        total_maturity_amount = principal + interest_after_tax
        
        # Calculate daily interest (for end-of-day calculations)
        daily_interest_rate = (interest_rate / 100) / 365
        daily_interest_before_tax = principal * daily_interest_rate
        daily_interest_after_tax = daily_interest_before_tax * (1 - tax_rate / 100)
        
        # Store calculated values
        deposit_data.update({
            'days_period': days_period,
            'time_period_years': round(time_period_years, 4),
            'interest_before_tax': round(interest_before_tax, 2),
            'tax_amount': round(tax_amount, 2),
            'interest_after_tax': round(interest_after_tax, 2),
            'total_maturity_amount': round(total_maturity_amount, 2),
            'daily_interest_before_tax': round(daily_interest_before_tax, 2),
            'daily_interest_after_tax': round(daily_interest_after_tax, 2),
            'is_matured': datetime.now() >= maturity_date
        })
    
    def get_summary(self, user_id: int = None) -> Dict:
        """Get summary statistics of deposits (user-specific or all)"""
        with sqlite3.connect(self.db_manager.db_file) as conn:
            cursor = conn.cursor()
            if user_id:
                cursor.execute("SELECT COUNT(*) FROM deposits WHERE user_id = ?", (user_id,))
            else:
                cursor.execute("SELECT COUNT(*) FROM deposits")
            total_deposits = cursor.fetchone()[0]
            
            if total_deposits == 0:
                return {
                    'total_deposits': 0,
                    'total_principal': 0,
                    'total_interest_before_tax': 0,
                    'total_interest_after_tax': 0,
                    'total_tax_paid': 0,
                    'total_maturity_amount': 0,
                    'average_interest_rate': 0,
                    'matured_deposits': 0,
                    'active_deposits': 0,
                    'currency_symbol': self.config_manager.get_currency_symbol(user_id)
                }
            
            if user_id:
                cursor.execute('''
                    SELECT 
                        SUM(principal_amount) as total_principal,
                        SUM(interest_before_tax) as total_interest_before_tax,
                        SUM(interest_after_tax) as total_interest_after_tax,
                        SUM(tax_amount) as total_tax_paid,
                        SUM(total_maturity_amount) as total_maturity_amount,
                        AVG(interest_rate) as average_interest_rate,
                        SUM(CASE WHEN is_matured = 1 THEN 1 ELSE 0 END) as matured_deposits,
                        SUM(CASE WHEN is_matured = 0 THEN 1 ELSE 0 END) as active_deposits
                    FROM deposits WHERE user_id = ?
                ''', (user_id,))
            else:
                cursor.execute('''
                    SELECT 
                        SUM(principal_amount) as total_principal,
                        SUM(interest_before_tax) as total_interest_before_tax,
                        SUM(interest_after_tax) as total_interest_after_tax,
                        SUM(tax_amount) as total_tax_paid,
                        SUM(total_maturity_amount) as total_maturity_amount,
                        AVG(interest_rate) as average_interest_rate,
                        SUM(CASE WHEN is_matured = 1 THEN 1 ELSE 0 END) as matured_deposits,
                        SUM(CASE WHEN is_matured = 0 THEN 1 ELSE 0 END) as active_deposits
                    FROM deposits
                ''')
            
            result = cursor.fetchone()
            
            return {
                'total_deposits': total_deposits,
                'total_principal': round(result[0], 2),
                'total_interest_before_tax': round(result[1], 2),
                'total_interest_after_tax': round(result[2], 2),
                'total_tax_paid': round(result[3], 2),
                'total_maturity_amount': round(result[4], 2),
                'average_interest_rate': round(result[5], 4),
                'matured_deposits': result[6],
                'active_deposits': result[7],
                'currency_symbol': self.config_manager.get_currency_symbol(user_id)
            }