from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_login import login_user, logout_user, current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime, timezone
import yfinance as yf
from typing import List, Dict
import os
import pandas as pd
import shutil
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import modules from organized packages
from config import get_config
from utils import (
    init_auth, 
    api_login_required, 
    User, 
    verify_credentials,
    parse_zone, 
    calculate_holdings, 
    validate_transaction_data,
    is_in_zone,
    format_refresh_response,
    clean_symbol,
    calculate_portfolio_xirr,
    create_startup_backup
)
from services import get_nse_price, get_scraped_price, get_stock_details

# Initialize Flask app
app = Flask(__name__)

# Load configuration (development or production)
app.config.from_object(get_config())

# Initialize CORS with configuration
CORS(app, origins=app.config['CORS_ORIGINS'], supports_credentials=True)

# Initialize authentication
login_manager, admin_username, admin_password_hash = init_auth(app)

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per minute"],
    storage_uri=app.config.get('RATELIMIT_STORAGE_URL', 'memory://')
)

# Initialize database
db = SQLAlchemy(app)

# Models
class Stock(db.Model):
    __tablename__ = 'stocks'
    
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    group_name = db.Column(db.String(50))  # e.g., "Bull Run", "Cup with Handle"
    sector = db.Column(db.String(100))  # e.g., "FMCG, Auto", "Banking"
    market_cap = db.Column(db.String(20))  # "Small", "Mid", "Large"
    buy_zone_price = db.Column(db.String(50))  # Support ranges like "250-300" or exact "250"
    sell_zone_price = db.Column(db.String(50))  # Support ranges like "700-800" or exact "750"
    average_zone_price = db.Column(db.String(50))  # Support ranges like "150-180" or exact "165"
    status = db.Column(db.String(20))  # "BUY", "SELL", "AVERAGE", "HOLD"
    current_price = db.Column(db.Float)
    day_change_pct = db.Column(db.Float)  # 1-day change percentage
    last_updated = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    notes = db.Column(db.Text)
    
    def to_dict(self):
        return {
            'id': self.id,
            'symbol': self.symbol,
            'name': self.name,
            'group_name': self.group_name,
            'sector': self.sector,
            'market_cap': self.market_cap,
            'buy_zone_price': self.buy_zone_price,
            'sell_zone_price': self.sell_zone_price,
            'average_zone_price': self.average_zone_price,
            'status': self.status,
            'current_price': self.current_price,
            'day_change_pct': self.day_change_pct,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'notes': self.notes
        }


class PortfolioTransaction(db.Model):
    __tablename__ = 'portfolio_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    stock_symbol = db.Column(db.String(20), nullable=False)
    stock_name = db.Column(db.String(100), nullable=False)
    transaction_type = db.Column(db.String(10), nullable=False)  # "BUY" or "SELL"
    quantity = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    transaction_date = db.Column(db.DateTime, nullable=False)
    reason = db.Column(db.Text)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    def to_dict(self):
        return {
            'id': self.id,
            'stock_symbol': self.stock_symbol,
            'stock_name': self.stock_name,
            'transaction_type': self.transaction_type,
            'quantity': self.quantity,
            'price': self.price,
            'transaction_date': self.transaction_date.isoformat(),
            'reason': self.reason,
            'notes': self.notes,
            'created_at': self.created_at.isoformat()
        }


class PortfolioSettings(db.Model):
    __tablename__ = 'portfolio_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    total_amount = db.Column(db.Float, default=0.0)  # Manual total portfolio amount for % calculation
    max_large_cap_pct = db.Column(db.Float, default=50.0)  # Max % allocation for Large Cap
    max_mid_cap_pct = db.Column(db.Float, default=30.0)  # Max % allocation for Mid Cap
    max_small_cap_pct = db.Column(db.Float, default=25.0)  # Max % allocation for Small Cap
    max_micro_cap_pct = db.Column(db.Float, default=15.0)  # Max % allocation for Micro Cap
    max_sector_pct = db.Column(db.Float, default=20.0)  # Max % allocation per sector
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    def to_dict(self):
        return {
            'id': self.id,
            'total_amount': self.total_amount,
            'max_large_cap_pct': self.max_large_cap_pct,
            'max_mid_cap_pct': self.max_mid_cap_pct,
            'max_small_cap_pct': self.max_small_cap_pct,
            'max_micro_cap_pct': self.max_micro_cap_pct,
            'max_sector_pct': self.max_sector_pct,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# ============================================================================
# Personal Finance Models - Multi-Asset Tracking
# ============================================================================

class MutualFund(db.Model):
    __tablename__ = 'mutual_funds'
    
    id = db.Column(db.Integer, primary_key=True)
    scheme_code = db.Column(db.String(20), unique=True, nullable=False)
    scheme_name = db.Column(db.String(200), nullable=False)
    fund_house = db.Column(db.String(100))
    category = db.Column(db.String(50))  # equity, debt, hybrid, other
    sub_category = db.Column(db.String(100))  # large cap, mid cap, etc.
    current_nav = db.Column(db.Float)
    day_change_pct = db.Column(db.Float)
    expense_ratio = db.Column(db.Float)
    last_updated = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    notes = db.Column(db.Text)
    
    def to_dict(self):
        return {
            'id': self.id,
            'scheme_code': self.scheme_code,
            'scheme_name': self.scheme_name,
            'fund_house': self.fund_house,
            'category': self.category,
            'sub_category': self.sub_category,
            'current_nav': self.current_nav,
            'day_change_pct': self.day_change_pct,
            'expense_ratio': self.expense_ratio,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'notes': self.notes
        }


class MutualFundTransaction(db.Model):
    __tablename__ = 'mutual_fund_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    scheme_code = db.Column(db.String(20), nullable=False)
    scheme_name = db.Column(db.String(200), nullable=False)
    transaction_type = db.Column(db.String(10), nullable=False)  # BUY, SELL, SWITCH
    units = db.Column(db.Float, nullable=False)
    nav = db.Column(db.Float, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    transaction_date = db.Column(db.DateTime, nullable=False)
    is_sip = db.Column(db.Boolean, default=False)
    sip_id = db.Column(db.String(50))  # For grouping SIP transactions
    reason = db.Column(db.Text)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    def to_dict(self):
        return {
            'id': self.id,
            'scheme_code': self.scheme_code,
            'scheme_name': self.scheme_name,
            'transaction_type': self.transaction_type,
            'units': self.units,
            'nav': self.nav,
            'amount': self.amount,
            'transaction_date': self.transaction_date.isoformat(),
            'is_sip': self.is_sip,
            'sip_id': self.sip_id,
            'reason': self.reason,
            'notes': self.notes,
            'created_at': self.created_at.isoformat()
        }


class FixedDeposit(db.Model):
    __tablename__ = 'fixed_deposits'
    
    id = db.Column(db.Integer, primary_key=True)
    bank_name = db.Column(db.String(100), nullable=False)
    account_number = db.Column(db.String(50))
    principal_amount = db.Column(db.Float, nullable=False)
    interest_rate = db.Column(db.Float, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    maturity_date = db.Column(db.Date, nullable=False)
    interest_frequency = db.Column(db.String(20))  # monthly, quarterly, annually, at_maturity
    maturity_amount = db.Column(db.Float)
    status = db.Column(db.String(20), default='active')  # active, matured, closed
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    def to_dict(self):
        return {
            'id': self.id,
            'bank_name': self.bank_name,
            'account_number': self.account_number,
            'principal_amount': self.principal_amount,
            'interest_rate': self.interest_rate,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'maturity_date': self.maturity_date.isoformat() if self.maturity_date else None,
            'interest_frequency': self.interest_frequency,
            'maturity_amount': self.maturity_amount,
            'status': self.status,
            'notes': self.notes,
            'created_at': self.created_at.isoformat()
        }


class EPFAccount(db.Model):
    __tablename__ = 'epf_accounts'
    
    id = db.Column(db.Integer, primary_key=True)
    employer_name = db.Column(db.String(100), nullable=False)
    uan_number = db.Column(db.String(50))
    opening_balance = db.Column(db.Float, default=0.0)
    opening_date = db.Column(db.Date)
    current_balance = db.Column(db.Float, default=0.0)
    last_updated = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    interest_rate = db.Column(db.Float)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    def to_dict(self):
        return {
            'id': self.id,
            'employer_name': self.employer_name,
            'uan_number': self.uan_number,
            'opening_balance': self.opening_balance,
            'opening_date': self.opening_date.isoformat() if self.opening_date else None,
            'current_balance': self.current_balance,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'interest_rate': self.interest_rate,
            'notes': self.notes,
            'created_at': self.created_at.isoformat()
        }


class EPFContribution(db.Model):
    __tablename__ = 'epf_contributions'
    
    id = db.Column(db.Integer, primary_key=True)
    epf_account_id = db.Column(db.Integer, db.ForeignKey('epf_accounts.id'), nullable=False)
    month_year = db.Column(db.String(20), nullable=False)  # Format: "2025-01"
    employee_contribution = db.Column(db.Float, default=0.0)
    employer_contribution = db.Column(db.Float, default=0.0)
    interest_earned = db.Column(db.Float, default=0.0)
    transaction_date = db.Column(db.Date, nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    def to_dict(self):
        return {
            'id': self.id,
            'epf_account_id': self.epf_account_id,
            'month_year': self.month_year,
            'employee_contribution': self.employee_contribution,
            'employer_contribution': self.employer_contribution,
            'interest_earned': self.interest_earned,
            'transaction_date': self.transaction_date.isoformat() if self.transaction_date else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat()
        }


class NPSAccount(db.Model):
    __tablename__ = 'nps_accounts'
    
    id = db.Column(db.Integer, primary_key=True)
    pran_number = db.Column(db.String(50), unique=True, nullable=False)
    scheme_type = db.Column(db.String(20))  # tier1, tier2
    current_value = db.Column(db.Float, default=0.0)
    units = db.Column(db.Float, default=0.0)
    nav = db.Column(db.Float)
    last_updated = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    def to_dict(self):
        return {
            'id': self.id,
            'pran_number': self.pran_number,
            'scheme_type': self.scheme_type,
            'current_value': self.current_value,
            'units': self.units,
            'nav': self.nav,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat()
        }


class NPSContribution(db.Model):
    __tablename__ = 'nps_contributions'
    
    id = db.Column(db.Integer, primary_key=True)
    nps_account_id = db.Column(db.Integer, db.ForeignKey('nps_accounts.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    nav = db.Column(db.Float)
    units = db.Column(db.Float)
    transaction_date = db.Column(db.Date, nullable=False)
    contribution_type = db.Column(db.String(20))  # self, employer
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    def to_dict(self):
        return {
            'id': self.id,
            'nps_account_id': self.nps_account_id,
            'amount': self.amount,
            'nav': self.nav,
            'units': self.units,
            'transaction_date': self.transaction_date.isoformat() if self.transaction_date else None,
            'contribution_type': self.contribution_type,
            'notes': self.notes,
            'created_at': self.created_at.isoformat()
        }


class SavingsAccount(db.Model):
    __tablename__ = 'savings_accounts'
    
    id = db.Column(db.Integer, primary_key=True)
    bank_name = db.Column(db.String(100), nullable=False)
    account_number = db.Column(db.String(50), nullable=False)
    account_type = db.Column(db.String(20))  # savings, current
    current_balance = db.Column(db.Float, default=0.0)
    interest_rate = db.Column(db.Float)
    last_updated = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    def to_dict(self):
        return {
            'id': self.id,
            'bank_name': self.bank_name,
            'account_number': self.account_number,
            'account_type': self.account_type,
            'current_balance': self.current_balance,
            'interest_rate': self.interest_rate,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat()
        }


class SavingsTransaction(db.Model):
    __tablename__ = 'savings_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('savings_accounts.id'), nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # deposit, withdrawal
    amount = db.Column(db.Float, nullable=False)
    balance_after = db.Column(db.Float)
    transaction_date = db.Column(db.Date, nullable=False)
    description = db.Column(db.String(200))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    def to_dict(self):
        return {
            'id': self.id,
            'account_id': self.account_id,
            'transaction_type': self.transaction_type,
            'amount': self.amount,
            'balance_after': self.balance_after,
            'transaction_date': self.transaction_date.isoformat() if self.transaction_date else None,
            'description': self.description,
            'notes': self.notes,
            'created_at': self.created_at.isoformat()
        }


class LendingRecord(db.Model):
    __tablename__ = 'lending_records'
    
    id = db.Column(db.Integer, primary_key=True)
    borrower_name = db.Column(db.String(100), nullable=False)
    principal_amount = db.Column(db.Float, nullable=False)
    interest_rate = db.Column(db.Float, default=0.0)
    start_date = db.Column(db.Date, nullable=False)
    tenure_months = db.Column(db.Integer)
    monthly_emi = db.Column(db.Float)
    total_repaid = db.Column(db.Float, default=0.0)
    outstanding_amount = db.Column(db.Float)
    status = db.Column(db.String(20), default='active')  # active, closed
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    def to_dict(self):
        return {
            'id': self.id,
            'borrower_name': self.borrower_name,
            'principal_amount': self.principal_amount,
            'interest_rate': self.interest_rate,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'tenure_months': self.tenure_months,
            'monthly_emi': self.monthly_emi,
            'total_repaid': self.total_repaid,
            'outstanding_amount': self.outstanding_amount,
            'status': self.status,
            'notes': self.notes,
            'created_at': self.created_at.isoformat()
        }


class OtherInvestment(db.Model):
    __tablename__ = 'other_investments'
    
    id = db.Column(db.Integer, primary_key=True)
    investment_type = db.Column(db.String(50), nullable=False)  # gold, bonds, crypto, real_estate, etc.
    description = db.Column(db.String(200), nullable=False)
    purchase_value = db.Column(db.Float, nullable=False)
    current_value = db.Column(db.Float)
    purchase_date = db.Column(db.Date)
    last_updated = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    def to_dict(self):
        return {
            'id': self.id,
            'investment_type': self.investment_type,
            'description': self.description,
            'purchase_value': self.purchase_value,
            'current_value': self.current_value,
            'purchase_date': self.purchase_date.isoformat() if self.purchase_date else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat()
        }


class IncomeTransaction(db.Model):
    __tablename__ = 'income_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(50), nullable=False)  # salary, bonus, investment, rental, freelance, other
    category = db.Column(db.String(100))
    amount = db.Column(db.Float, nullable=False)
    transaction_date = db.Column(db.Date, nullable=False)
    is_recurring = db.Column(db.Boolean, default=False)
    description = db.Column(db.String(200))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    def to_dict(self):
        return {
            'id': self.id,
            'source': self.source,
            'category': self.category,
            'amount': self.amount,
            'transaction_date': self.transaction_date.isoformat() if self.transaction_date else None,
            'is_recurring': self.is_recurring,
            'description': self.description,
            'notes': self.notes,
            'created_at': self.created_at.isoformat()
        }


class ExpenseTransaction(db.Model):
    __tablename__ = 'expense_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)  # housing, food, transport, utilities, etc.
    subcategory = db.Column(db.String(100))
    amount = db.Column(db.Float, nullable=False)
    transaction_date = db.Column(db.Date, nullable=False)
    payment_method = db.Column(db.String(50))  # cash, card, upi, bank_transfer
    is_recurring = db.Column(db.Boolean, default=False)
    description = db.Column(db.String(200))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    def to_dict(self):
        return {
            'id': self.id,
            'category': self.category,
            'subcategory': self.subcategory,
            'amount': self.amount,
            'transaction_date': self.transaction_date.isoformat() if self.transaction_date else None,
            'payment_method': self.payment_method,
            'is_recurring': self.is_recurring,
            'description': self.description,
            'notes': self.notes,
            'created_at': self.created_at.isoformat()
        }


class Budget(db.Model):
    __tablename__ = 'budgets'
    
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)
    monthly_limit = db.Column(db.Float)
    annual_limit = db.Column(db.Float)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    def to_dict(self):
        return {
            'id': self.id,
            'category': self.category,
            'monthly_limit': self.monthly_limit,
            'annual_limit': self.annual_limit,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'is_active': self.is_active,
            'notes': self.notes,
            'created_at': self.created_at.isoformat()
        }


class GlobalSettings(db.Model):
    __tablename__ = 'global_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    # Asset allocation targets
    max_equity_allocation_pct = db.Column(db.Float, default=70.0)
    max_debt_allocation_pct = db.Column(db.Float, default=30.0)
    min_emergency_fund_months = db.Column(db.Integer, default=6)
    
    # Income/Expense targets
    monthly_income_target = db.Column(db.Float, default=0.0)
    monthly_expense_target = db.Column(db.Float, default=0.0)
    
    # Other settings
    currency = db.Column(db.String(10), default='INR')
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    def to_dict(self):
        return {
            'id': self.id,
            'max_equity_allocation_pct': self.max_equity_allocation_pct,
            'max_debt_allocation_pct': self.max_debt_allocation_pct,
            'min_emergency_fund_months': self.min_emergency_fund_months,
            'monthly_income_target': self.monthly_income_target,
            'monthly_expense_target': self.monthly_expense_target,
            'currency': self.currency,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# ============================================================================
# Authentication Routes (No auth required)
# ============================================================================

@app.route('/api/auth/login', methods=['POST'])
@limiter.limit("5 per minute")  # Prevent brute force attacks
def login():
    """User login endpoint"""
    data = request.json
    
    if not data:
        return jsonify({'error': 'Request body required'}), 400
    
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    # Verify credentials
    if verify_credentials(username, password, admin_username, admin_password_hash):
        user = User(admin_username)
        login_user(user, remember=True)
        return jsonify({
            'message': 'Login successful',
            'username': username
        })
    
    return jsonify({'error': 'Invalid credentials'}), 401


@app.route('/api/auth/logout', methods=['POST'])
@api_login_required
def logout():
    """User logout endpoint"""
    logout_user()
    return jsonify({'message': 'Logged out successfully'})


@app.route('/api/auth/check', methods=['GET'])
def check_auth():
    """Check if user is authenticated"""
    if current_user.is_authenticated:
        return jsonify({
            'authenticated': True,
            'username': current_user.username
        })
    return jsonify({'authenticated': False}), 401


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring (no auth required)"""
    try:
        # Check database connection
        db.session.execute('SELECT 1')
        db_status = 'connected'
    except Exception as e:
        db_status = f'error: {str(e)}'
    
    return jsonify({
        'status': 'healthy',
        'database': db_status,
        'environment': app.config.get('ENV', 'unknown')
    })


# ============================================================================
# Stock Tracking Routes (Auth required)
# ============================================================================

@app.route('/api/stocks', methods=['GET'])
@api_login_required
def get_stocks():
    """Get all tracked stocks"""
    stocks = Stock.query.all()
    return jsonify([stock.to_dict() for stock in stocks])


@app.route('/api/stocks/<int:stock_id>', methods=['GET'])
@api_login_required
def get_stock(stock_id):
    """Get a specific stock"""
    stock = Stock.query.get_or_404(stock_id)
    return jsonify(stock.to_dict())


@app.route('/api/stocks', methods=['POST'])
@api_login_required
def create_stock():
    """Create a new stock tracking entry"""
    data = request.json
    
    # Check if stock already exists
    existing_stock = Stock.query.filter_by(symbol=data['symbol']).first()
    if existing_stock:
        return jsonify({'error': 'Stock with this symbol already exists'}), 400
    
    # Auto-fetch name, price, and 1D change from Screener.in if missing
    stock_name = data.get('name', '').strip()
    stock_price = data.get('current_price')
    day_change = data.get('day_change_pct')
    
    if not stock_name or not stock_price or day_change is None:
        # Try to fetch from Screener.in
        try:
            details = get_stock_details(data['symbol'].upper())
            if details:
                if not stock_name and details.get('name'):
                    stock_name = details['name']
                if not stock_price and details.get('price'):
                    stock_price = details['price']
                if day_change is None and details.get('day_change_pct') is not None:
                    day_change = details['day_change_pct']
                print(f"[OK] Auto-fetched details for {data['symbol']}: {stock_name} @ Rs.{stock_price} ({day_change:+.2f}%)" if day_change is not None else f"[OK] Auto-fetched details for {data['symbol']}: {stock_name} @ Rs.{stock_price}")
        except Exception as e:
            print(f"[WARN] Could not auto-fetch details: {str(e)}")
    
    # Name is still required - return error if missing
    if not stock_name:
        return jsonify({'error': 'Company name is required or could not be auto-fetched'}), 400
    
    stock = Stock(
        symbol=clean_symbol(data['symbol']),
        name=stock_name,
        group_name=data.get('group_name'),
        sector=data.get('sector'),
        market_cap=data.get('market_cap'),
        buy_zone_price=data.get('buy_zone_price'),
        sell_zone_price=data.get('sell_zone_price'),
        average_zone_price=data.get('average_zone_price'),
        status=data.get('status', 'WATCHING'),
        current_price=stock_price,  # Allow manual entry or auto-fetched
        day_change_pct=day_change,  # Auto-fetched 1D change
        notes=data.get('notes')
    )
    
    # Fetch current price automatically (only if still not available)
    if not stock.current_price:
        # Strategy: Try multiple sources in order
        # 1. Web Scraping (most reliable for Indian stocks)
        # 2. NSE India API
        # 3. Yahoo Finance API
        
        if stock.symbol.endswith('.NS') or stock.symbol.endswith('.BO'):
            # Try web scraping first (Google Finance, Moneycontrol, etc.)
            try:
                price = get_scraped_price(stock.symbol)
                if price:
                    stock.current_price = round(price, 2)
                    print(f"[OK] Web Scraper: Fetched {stock.symbol}: Rs.{stock.current_price}")
            except Exception as e:
                print(f"[WARN] Web scraper failed for {stock.symbol}: {str(e)}")
            
            # Fallback to NSE API
            if not stock.current_price:
                try:
                    price = get_nse_price(stock.symbol)
                    if price:
                        stock.current_price = round(price, 2)
                        print(f"[OK] NSE API: Fetched {stock.symbol}: Rs.{stock.current_price}")
                except Exception as e:
                    print(f"[WARN] NSE API failed for {stock.symbol}")
        
        # Fallback to Yahoo Finance for any stock
        if not stock.current_price:
            try:
                ticker = yf.Ticker(stock.symbol)
                info = ticker.history(period='1d')
                if not info.empty:
                    stock.current_price = round(info['Close'].iloc[-1], 2)
                    print(f"[OK] Yahoo Finance: Fetched {stock.symbol}: Rs.{stock.current_price}")
            except Exception as e:
                print(f"[WARN] Yahoo Finance failed for {stock.symbol}")
        
        # If all methods failed, log it
        if not stock.current_price:
            print(f"[FAIL] Could not fetch price for {stock.symbol} - all methods failed")
    
    db.session.add(stock)
    db.session.commit()
    
    return jsonify(stock.to_dict()), 201


@app.route('/api/stocks/<int:stock_id>', methods=['PUT'])
@api_login_required
def update_stock(stock_id):
    """Update a stock tracking entry"""
    stock = Stock.query.get_or_404(stock_id)
    data = request.json
    
    stock.name = data.get('name', stock.name)
    stock.group_name = data.get('group_name', stock.group_name)
    stock.sector = data.get('sector', stock.sector)
    stock.market_cap = data.get('market_cap', stock.market_cap)
    stock.buy_zone_price = data.get('buy_zone_price', stock.buy_zone_price)
    stock.sell_zone_price = data.get('sell_zone_price', stock.sell_zone_price)
    stock.average_zone_price = data.get('average_zone_price', stock.average_zone_price)
    stock.status = data.get('status', stock.status)
    stock.notes = data.get('notes', stock.notes)
    
    # Allow manual update of current price
    if 'current_price' in data:
        stock.current_price = data.get('current_price')
    
    db.session.commit()
    
    return jsonify(stock.to_dict())


@app.route('/api/stocks/<int:stock_id>', methods=['DELETE'])
@api_login_required
def delete_stock(stock_id):
    """Delete a stock tracking entry"""
    stock = Stock.query.get_or_404(stock_id)
    db.session.delete(stock)
    db.session.commit()
    
    return jsonify({'message': 'Stock deleted successfully'})


@app.route('/api/stocks/refresh-alert-stocks', methods=['POST'])
@api_login_required
def refresh_alert_stocks():
    """Refresh current prices for stocks that appear in any alert category"""
    
    # Get all stocks and portfolio holdings
    all_stocks = Stock.query.all()
    
    # Get holdings to determine which stocks user owns
    transactions = PortfolioTransaction.query.all()
    holdings = calculate_holdings(transactions)
    holding_symbols_normalized = set(normalize_symbol(s) for s in holdings.keys())
    
    # Identify all alert stocks
    alert_stock_ids = set()
    
    for stock in all_stocks:
        if not stock.current_price:
            continue
        
        # Flexible symbol matching (check with and without .NS/.BO suffix)
        is_in_holdings = normalize_symbol(stock.symbol) in holding_symbols_normalized
        current_price = stock.current_price
        
        # Buy zone alerts (only for non-holdings)
        if not is_in_holdings and stock.buy_zone_price:
            buy_min, buy_max = parse_zone(stock.buy_zone_price)
            if buy_min and buy_max:
                # In buy zone
                if buy_min <= current_price <= buy_max:
                    alert_stock_ids.add(stock.id)
                    continue
                # Near buy zone (within 3% above)
                upper_threshold = buy_max * 1.03
                if buy_max < current_price <= upper_threshold:
                    alert_stock_ids.add(stock.id)
                    continue
        
        # Sell zone alerts (only for holdings)
        if is_in_holdings and stock.sell_zone_price:
            sell_min, sell_max = parse_zone(stock.sell_zone_price)
            if sell_min and sell_max:
                # In sell zone
                if sell_min <= current_price <= sell_max:
                    alert_stock_ids.add(stock.id)
                    continue
                # Near sell zone (within 3% below)
                lower_threshold = sell_min * 0.97
                if lower_threshold <= current_price < sell_min:
                    alert_stock_ids.add(stock.id)
                    continue
        
        # Average zone alerts (only for holdings)
        if is_in_holdings and stock.average_zone_price:
            avg_min, avg_max = parse_zone(stock.average_zone_price)
            if avg_min and avg_max:
                # In average zone
                if avg_min <= current_price <= avg_max:
                    alert_stock_ids.add(stock.id)
                    continue
                # Near average zone (within 3% above or below)
                lower_threshold = avg_min * 0.97
                upper_threshold = avg_max * 1.03
                if lower_threshold <= current_price < avg_min or avg_max < current_price <= upper_threshold:
                    alert_stock_ids.add(stock.id)
                    continue
    
    if not alert_stock_ids:
        return jsonify(format_refresh_response(0, 0, 0))
    
    # Refresh prices for alert stocks
    alert_stocks = Stock.query.filter(Stock.id.in_(alert_stock_ids)).all()
    updated_count = 0
    failed_count = 0
    
    for stock in alert_stocks:
        updated = False
        
        # Try web scraping first for Indian stocks (ORIGINAL WORKING LOGIC)
        if stock.symbol.endswith('.NS') or stock.symbol.endswith('.BO'):
            try:
                # Use the ORIGINAL working scraper for price
                price = get_scraped_price(stock.symbol)
                if price:
                    stock.current_price = round(price, 2)
                    stock.last_updated = datetime.now(timezone.utc)
                    updated = True
                    
                    # Try to get day_change_pct separately (optional, don't fail if it doesn't work)
                    try:
                        details = get_stock_details(stock.symbol)
                        if details and details.get('day_change_pct') is not None:
                            stock.day_change_pct = details.get('day_change_pct')
                    except:
                        pass  # Day change is optional
                    
                    print(f"[OK] Scraper: Updated {stock.symbol} -> Rs.{stock.current_price}")
            except Exception as e:
                print(f"[WARN] Scraper failed for {stock.symbol}")
            
            # Fallback to NSE API
            if not updated:
                try:
                    price = get_nse_price(stock.symbol)
                    if price:
                        stock.current_price = round(price, 2)
                        stock.last_updated = datetime.now(timezone.utc)
                        updated = True
                        print(f"[OK] NSE API: Updated {stock.symbol} -> Rs.{stock.current_price}")
                except Exception as e:
                    print(f"[WARN] NSE API failed for {stock.symbol}")
        
        # Fallback to yfinance
        if not updated:
            try:
                price = get_yahoo_price(stock.symbol)
                if price:
                    stock.current_price = round(price, 2)
                    stock.last_updated = datetime.now(timezone.utc)
                    updated = True
                    yahoo_count += 1
                    print(f"[OK] yfinance: Updated {stock.symbol} -> Rs.{stock.current_price}")
            except Exception as e:
                print(f"[ERROR] All methods failed for {stock.symbol}")
        
        if updated:
            updated_count += 1
        else:
            failed_count += 1
    
    db.session.commit()
    
    # Return standardized response
    return jsonify(format_refresh_response(len(alert_stocks), updated_count, failed_count))

@app.route('/api/stocks/refresh-prices', methods=['POST'])
@api_login_required
def refresh_stock_prices():
    """Refresh current prices for all tracked stocks"""
    stocks = Stock.query.all()
    updated_count = 0
    failed_count = 0
    
    for stock in stocks:
        updated = False
        
        # Try web scraping first for Indian stocks (ORIGINAL WORKING LOGIC)
        if stock.symbol.endswith('.NS') or stock.symbol.endswith('.BO'):
            try:
                # Use the ORIGINAL working scraper for price
                price = get_scraped_price(stock.symbol)
                if price:
                    stock.current_price = round(price, 2)
                    stock.last_updated = datetime.now(timezone.utc)
                    updated = True
                    
                    # Try to get day_change_pct separately (optional, don't fail if it doesn't work)
                    try:
                        details = get_stock_details(stock.symbol)
                        if details and details.get('day_change_pct') is not None:
                            stock.day_change_pct = details.get('day_change_pct')
                    except:
                        pass  # Day change is optional
                    
                    print(f"[OK] Scraper: Updated {stock.symbol} -> Rs.{stock.current_price}")
            except Exception as e:
                print(f"[WARN] Scraper failed for {stock.symbol}")
            
            # Fallback to NSE API
            if not updated:
                try:
                    price = get_nse_price(stock.symbol)
                    if price:
                        stock.current_price = round(price, 2)
                        stock.last_updated = datetime.now(timezone.utc)
                        updated = True
                        print(f"[OK] NSE API: Updated {stock.symbol} -> Rs.{stock.current_price}")
                except:
                    pass
        
        # Fallback to Yahoo Finance
        if not updated:
            try:
                ticker = yf.Ticker(stock.symbol)
                info = ticker.history(period='1d')
                if not info.empty:
                    stock.current_price = round(info['Close'].iloc[-1], 2)
                    stock.last_updated = datetime.now(timezone.utc)
                    updated = True
                    print(f"[OK] Yahoo: Updated {stock.symbol} -> Rs.{stock.current_price}")
            except:
                pass
        
        if updated:
            updated_count += 1
        else:
            failed_count += 1
            print(f"[FAIL] Could not update {stock.symbol}")
    
    db.session.commit()
    
    # Return standardized response
    return jsonify(format_refresh_response(len(stocks), updated_count, failed_count))


@app.route('/api/stocks/groups', methods=['GET'])
@api_login_required
def get_stock_groups():
    """Get all unique stock groups"""
    groups = db.session.query(Stock.group_name).distinct().all()
    return jsonify([g[0] for g in groups if g[0]])


@app.route('/api/stocks/sectors', methods=['GET'])
@api_login_required
def get_stock_sectors():
    """Get all unique stock sectors"""
    sectors = db.session.query(Stock.sector).distinct().all()
    return jsonify([s[0] for s in sectors if s[0]])


@app.route('/api/stocks/fetch-details/<symbol>', methods=['GET'])
@api_login_required
def fetch_stock_details(symbol):
    """
    Fetch stock details from Screener.in (name + price) and determine default status
    based on whether stock is in holdings
    """
    try:
        # Get stock details from web scraping (Screener.in first)
        details = get_stock_details(symbol)
        
        if not details or not details.get('price'):
            return jsonify({
                'error': 'Could not fetch stock details. Please enter manually.',
                'symbol': symbol
            }), 404
        
        # Check if stock is in holdings
        transactions = PortfolioTransaction.query.filter_by(stock_symbol=symbol).all()
        total_quantity = 0
        for txn in transactions:
            if txn.transaction_type == 'BUY':
                total_quantity += txn.quantity
            elif txn.transaction_type == 'SELL':
                total_quantity -= txn.quantity
        
        # Set default status based on holdings
        default_status = 'HOLD' if total_quantity > 0 else 'WATCHING'
        
        return jsonify({
            'symbol': symbol,
            'name': details.get('name'),
            'price': details.get('price'),
            'day_change_pct': details.get('day_change_pct'),
            'status': default_status,
            'in_holdings': total_quantity > 0,
            'quantity': total_quantity if total_quantity > 0 else None
        })
    
    except Exception as e:
        print(f"[ERROR] fetch_stock_details failed: {str(e)}")
        return jsonify({
            'error': 'Failed to fetch stock details',
            'message': str(e)
        }), 500


# ============================================================================
# Portfolio Routes (Auth required)
# ============================================================================

@app.route('/api/portfolio/transactions', methods=['GET'])
@api_login_required
def get_portfolio_transactions():
    """Get all portfolio transactions"""
    transactions = PortfolioTransaction.query.order_by(PortfolioTransaction.transaction_date.desc()).all()
    return jsonify([t.to_dict() for t in transactions])


def normalize_symbol(symbol):
    """Remove .NS or .BO suffix for comparison"""
    return symbol.replace('.NS', '').replace('.BO', '').upper()


def find_stock_by_symbol(search_symbol):
    """
    Find stock matching symbol with flexible matching (with or without .NS/.BO suffix)
    """
    # Try exact match first
    stock = Stock.query.filter_by(symbol=search_symbol).first()
    if stock:
        return stock
    
    # Try normalized matching (without suffix)
    normalized_search = normalize_symbol(search_symbol)
    all_stocks = Stock.query.all()
    
    for stock in all_stocks:
        if normalize_symbol(stock.symbol) == normalized_search:
            return stock
    
    return None


def update_stock_status_from_holdings(stock_symbol):
    """
    Update stock status based on whether it's currently held in portfolio.
    Called after transaction create/update/delete to keep status in sync.
    """
    # Calculate total holdings for this stock (check both with and without suffix)
    normalized_symbol = normalize_symbol(stock_symbol)
    all_transactions = PortfolioTransaction.query.all()
    
    total_quantity = 0
    for txn in all_transactions:
        if normalize_symbol(txn.stock_symbol) == normalized_symbol:
            if txn.transaction_type == 'BUY':
                total_quantity += txn.quantity
            elif txn.transaction_type == 'SELL':
                total_quantity -= txn.quantity
    
    # Update stock status if it exists in Stock Tracking (flexible matching)
    stock = find_stock_by_symbol(stock_symbol)
    if stock:
        # Set status based on holdings
        if total_quantity > 0:
            stock.status = 'HOLD'
        else:
            # Only change to WATCHING if current status is HOLD
            # Don't override other statuses (BUY_ZONE, SELL_ZONE, etc.)
            if stock.status == 'HOLD':
                stock.status = 'WATCHING'
        
        db.session.commit()
    else:
        print(f"[WARNING] Stock {stock_symbol} not found in Stock Tracking table")


@app.route('/api/portfolio/transactions', methods=['POST'])
@api_login_required
def create_transaction():
    """Create a new portfolio transaction"""
    data = request.json
    
    # Validate transaction data
    is_valid, error_message = validate_transaction_data(data)
    if not is_valid:
        return jsonify({'error': error_message}), 400
    
    # Create transaction
    transaction = PortfolioTransaction(
        stock_symbol=clean_symbol(data['stock_symbol']),
        stock_name=data['stock_name'].strip(),
        transaction_type=data['transaction_type'].upper(),
        quantity=float(data['quantity']),
        price=float(data['price']),
        transaction_date=datetime.fromisoformat(data['transaction_date']),
        reason=data.get('reason'),
        notes=data.get('notes')
    )
    
    db.session.add(transaction)
    db.session.commit()
    
    # Update stock status based on new holdings
    update_stock_status_from_holdings(transaction.stock_symbol)
    
    return jsonify(transaction.to_dict()), 201


@app.route('/api/portfolio/transactions/<int:transaction_id>', methods=['PUT'])
@api_login_required
def update_transaction(transaction_id):
    """Update a portfolio transaction"""
    transaction = PortfolioTransaction.query.get_or_404(transaction_id)
    data = request.json
    
    # Validate updated fields
    if 'stock_symbol' in data:
        stock_symbol = data['stock_symbol'].strip()
        if not stock_symbol:
            return jsonify({'error': 'Stock symbol cannot be empty'}), 400
        transaction.stock_symbol = clean_symbol(stock_symbol)
    
    if 'stock_name' in data:
        stock_name = data['stock_name'].strip()
        if not stock_name:
            return jsonify({'error': 'Stock name cannot be empty'}), 400
        transaction.stock_name = stock_name
    
    if 'quantity' in data:
        try:
            quantity = float(data['quantity'])
            if quantity <= 0:
                return jsonify({'error': 'Quantity must be greater than 0'}), 400
            transaction.quantity = quantity
        except (ValueError, TypeError):
            return jsonify({'error': 'Quantity must be a valid number'}), 400
    
    if 'price' in data:
        try:
            price = float(data['price'])
            if price <= 0:
                return jsonify({'error': 'Price must be greater than 0'}), 400
            transaction.price = price
        except (ValueError, TypeError):
            return jsonify({'error': 'Price must be a valid number'}), 400
    
    if 'transaction_type' in data:
        transaction.transaction_type = data['transaction_type'].upper()
    transaction.transaction_date = datetime.fromisoformat(data['transaction_date']) if 'transaction_date' in data else transaction.transaction_date
    transaction.reason = data.get('reason', transaction.reason)
    transaction.notes = data.get('notes', transaction.notes)
    
    db.session.commit()
    
    # Update stock status based on updated holdings
    update_stock_status_from_holdings(transaction.stock_symbol)
    
    return jsonify(transaction.to_dict())


@app.route('/api/portfolio/transactions/<int:transaction_id>', methods=['DELETE'])
@api_login_required
def delete_transaction(transaction_id):
    """Delete a portfolio transaction"""
    transaction = PortfolioTransaction.query.get_or_404(transaction_id)
    stock_symbol = transaction.stock_symbol  # Save symbol before deleting
    
    db.session.delete(transaction)
    db.session.commit()
    
    # Update stock status based on remaining holdings
    update_stock_status_from_holdings(stock_symbol)
    
    return jsonify({'message': 'Transaction deleted successfully'})


@app.route('/api/portfolio/summary', methods=['GET'])
@api_login_required
def get_portfolio_summary():
    """Get portfolio summary with holdings and performance"""
    try:
        transactions = PortfolioTransaction.query.all()
        
        # Calculate holdings using utility function
        holdings = calculate_holdings(transactions)
        
        # Get current prices and calculate gains/losses
        summary = []
        total_invested = 0
        total_current_value = 0
        total_realized_pnl = 0  # Track total realized profit/loss from all SELL transactions
        
        for symbol, holding in holdings.items():
            # Accumulate realized P/L from all stocks (even those fully sold)
            total_realized_pnl += holding.get('realized_pnl', 0)
            
            if holding['quantity'] > 0:  # Only include current holdings in the table
                avg_price = holding['invested_amount'] / holding['quantity'] if holding['quantity'] > 0 else 0
                
                # Get current price from stocks table (flexible matching for .NS/.BO suffix)
                current_price = 0
                stock = find_stock_by_symbol(symbol)
                if stock and stock.current_price:
                    current_price = stock.current_price
                
                current_value = holding['quantity'] * current_price
                unrealized_pnl = current_value - holding['invested_amount']  # Unrealized P/L
                unrealized_pnl_pct = (unrealized_pnl / holding['invested_amount'] * 100) if holding['invested_amount'] > 0 else 0
                
                summary.append({
                    'symbol': symbol,
                    'name': holding['name'],
                    'quantity': holding['quantity'],
                    'avg_price': round(avg_price, 2),
                    'current_price': current_price,
                    'invested_amount': round(holding['invested_amount'], 2),
                    'current_value': round(current_value, 2),
                    'unrealized_pnl': round(unrealized_pnl, 2),  # Renamed from gain_loss
                    'unrealized_pnl_pct': round(unrealized_pnl_pct, 2),  # Renamed from gain_loss_pct
                    'realized_pnl': round(holding.get('realized_pnl', 0), 2),  # Add realized P/L per stock
                    'day_change_pct': stock.day_change_pct if stock else None,
                    'market_cap': stock.market_cap if stock else None,  # Add market cap for allocation color coding
                    'holding_period_days': holding.get('holding_period_days', 0)  # FIFO-based holding period
                })
                
                total_invested += holding['invested_amount']
                total_current_value += current_value
        
        total_unrealized_pnl = total_current_value - total_invested
        total_unrealized_pnl_pct = (total_unrealized_pnl / total_invested * 100) if total_invested > 0 else 0
        
        # Total P/L = Realized + Unrealized
        total_pnl = total_realized_pnl + total_unrealized_pnl
        
        # Calculate portfolio 1-day change (weighted average)
        portfolio_day_change_pct = 0
        if total_current_value > 0:
            weighted_change = 0
            for holding in summary:
                if holding['day_change_pct'] is not None:
                    weight = holding['current_value'] / total_current_value
                    weighted_change += holding['day_change_pct'] * weight
            portfolio_day_change_pct = weighted_change
        
        # Calculate XIRR (Extended Internal Rate of Return)
        xirr = calculate_portfolio_xirr(transactions, total_current_value)
        
        return jsonify({
            'holdings': summary,
            'total_invested': round(total_invested, 2),
            'total_current_value': round(total_current_value, 2),
            'total_realized_pnl': round(total_realized_pnl, 2),  # NEW: Total realized profit/loss
            'total_unrealized_pnl': round(total_unrealized_pnl, 2),  # Renamed from total_gain_loss
            'total_unrealized_pnl_pct': round(total_unrealized_pnl_pct, 2),  # Renamed from total_gain_loss_pct
            'total_pnl': round(total_pnl, 2),  # NEW: Combined realized + unrealized
            'portfolio_day_change_pct': round(portfolio_day_change_pct, 2),
            'xirr': xirr  # Extended Internal Rate of Return (annualized)
        })
    except Exception as e:
        print(f"ERROR in get_portfolio_summary: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Error calculating portfolio summary: {str(e)}'}), 500


@app.route('/api/portfolio/settings', methods=['GET'])
@api_login_required
def get_portfolio_settings():
    """Get portfolio settings (total amount for % calculation)"""
    settings = PortfolioSettings.query.first()
    if not settings:
        # Create default settings if none exist
        settings = PortfolioSettings(total_amount=0.0)
        db.session.add(settings)
        db.session.commit()
    return jsonify(settings.to_dict())


@app.route('/api/portfolio/settings', methods=['PUT'])
@api_login_required
def update_portfolio_settings():
    """Update portfolio settings (total amount and allocation thresholds)"""
    data = request.get_json()
    settings = PortfolioSettings.query.first()
    
    if not settings:
        settings = PortfolioSettings()
        db.session.add(settings)
    
    # Update all configurable fields
    if 'total_amount' in data:
        settings.total_amount = float(data['total_amount'])
    if 'max_large_cap_pct' in data:
        settings.max_large_cap_pct = float(data['max_large_cap_pct'])
    if 'max_mid_cap_pct' in data:
        settings.max_mid_cap_pct = float(data['max_mid_cap_pct'])
    if 'max_small_cap_pct' in data:
        settings.max_small_cap_pct = float(data['max_small_cap_pct'])
    if 'max_micro_cap_pct' in data:
        settings.max_micro_cap_pct = float(data['max_micro_cap_pct'])
    if 'max_sector_pct' in data:
        settings.max_sector_pct = float(data['max_sector_pct'])
    
    settings.updated_at = datetime.now(timezone.utc)
    
    db.session.commit()
    return jsonify(settings.to_dict())


# Initialize database tables on startup
with app.app_context():
    db.create_all()
    # Create automatic backup on startup
    try:
        create_startup_backup()
    except Exception as e:
        print(f"[WARN] Could not create startup backup: {e}")


# ============================================================================
# Analytics Routes (Auth required)
# ============================================================================

@app.route('/api/analytics/dashboard', methods=['GET'])
@api_login_required
def get_analytics_dashboard():
    """Get analytics dashboard data with key metrics and action items"""
    try:
        # Get all stocks
        stocks = Stock.query.all()
        
        # Get portfolio summary
        transactions = PortfolioTransaction.query.all()
        
        # Calculate holdings using utility function
        holdings = calculate_holdings(transactions)
        
        # Calculate total invested and current value
        total_invested = 0
        total_current_value = 0
        holdings_with_value = []
        
        for symbol, holding in holdings.items():
            if holding['quantity'] > 0:
                # Get current price from stocks table (flexible matching for .NS/.BO suffix)
                stock = find_stock_by_symbol(symbol)
                current_price = stock.current_price if stock and stock.current_price else 0
                
                current_value = holding['quantity'] * current_price
                total_invested += holding['invested_amount']
                total_current_value += current_value
                
                gain_loss = current_value - holding['invested_amount']
                gain_loss_pct = (gain_loss / holding['invested_amount'] * 100) if holding['invested_amount'] > 0 else 0
                
                holdings_with_value.append({
                    'symbol': symbol,
                    'name': holding['name'],
                    'quantity': holding['quantity'],
                    'invested_amount': holding['invested_amount'],
                    'current_value': current_value,
                    'current_price': current_price,
                    'gain_loss': gain_loss,
                    'gain_loss_pct': gain_loss_pct,
                    'day_change_pct': stock.day_change_pct if stock else None,
                    'sector': stock.sector if stock else None,
                    'market_cap': stock.market_cap if stock else None
                })
        
        # Calculate portfolio metrics
        total_gain_loss = total_current_value - total_invested
        total_gain_loss_pct = (total_gain_loss / total_invested * 100) if total_invested > 0 else 0
        
        # Calculate portfolio 1-day change (weighted average)
        portfolio_day_change_pct = 0
        if total_current_value > 0:
            weighted_change = 0
            for holding in holdings_with_value:
                if holding['day_change_pct'] is not None:
                    weight = holding['current_value'] / total_current_value
                    weighted_change += holding['day_change_pct'] * weight
            portfolio_day_change_pct = weighted_change
        
        # Get list of symbols currently in holdings (normalize for flexible matching)
        holding_symbols_normalized = set(normalize_symbol(s) for s in holdings.keys())
        
        # Find stocks near buy/sell/average zones (action items)
        action_items = {
            'in_buy_zone': [],
            'in_sell_zone': [],
            'in_average_zone': [],
            'near_buy_zone': [],
            'near_sell_zone': [],
            'near_average_zone': []
        }
        
        for stock in stocks:
            if not stock.current_price:
                continue
            
            current = stock.current_price
            # Flexible symbol matching (check with and without .NS/.BO suffix)
            is_in_holdings = normalize_symbol(stock.symbol) in holding_symbols_normalized
            
            # Check buy zone (only for stocks NOT in holdings)
            if not is_in_holdings:
                buy_min, buy_max = parse_zone(stock.buy_zone_price)
                if buy_min and buy_max:
                    if buy_min <= current <= buy_max:
                        action_items['in_buy_zone'].append({
                            'symbol': stock.symbol,
                            'name': stock.name,
                            'current_price': current,
                            'zone': stock.buy_zone_price,
                            'sector': stock.sector,
                            'market_cap': stock.market_cap
                        })
                    elif buy_max < current <= buy_max * 1.03:  # Within 3% above buy zone
                        action_items['near_buy_zone'].append({
                            'symbol': stock.symbol,
                            'name': stock.name,
                            'current_price': current,
                            'zone': stock.buy_zone_price,
                            'distance_pct': ((current - buy_max) / buy_max * 100),
                            'sector': stock.sector,
                            'market_cap': stock.market_cap
                        })
            
            # Check sell zone (only for stocks IN holdings)
            if is_in_holdings:
                sell_min, sell_max = parse_zone(stock.sell_zone_price)
                if sell_min and sell_max:
                    if sell_min <= current <= sell_max:
                        action_items['in_sell_zone'].append({
                            'symbol': stock.symbol,
                            'name': stock.name,
                            'current_price': current,
                            'zone': stock.sell_zone_price,
                            'sector': stock.sector,
                            'market_cap': stock.market_cap
                        })
                    elif sell_min * 0.97 <= current < sell_min:  # Within 3% below sell zone
                        action_items['near_sell_zone'].append({
                            'symbol': stock.symbol,
                            'name': stock.name,
                            'current_price': current,
                            'zone': stock.sell_zone_price,
                            'distance_pct': ((sell_min - current) / sell_min * 100),
                            'sector': stock.sector,
                            'market_cap': stock.market_cap
                        })
            
            # Check average zone (only for stocks IN holdings)
            if is_in_holdings:
                avg_min, avg_max = parse_zone(stock.average_zone_price)
                if avg_min and avg_max:
                    if avg_min <= current <= avg_max:
                        action_items['in_average_zone'].append({
                            'symbol': stock.symbol,
                            'name': stock.name,
                            'current_price': current,
                            'zone': stock.average_zone_price,
                            'sector': stock.sector,
                            'market_cap': stock.market_cap
                        })
                    elif avg_max < current <= avg_max * 1.03:  # Within 3% above average zone
                        action_items['near_average_zone'].append({
                            'symbol': stock.symbol,
                            'name': stock.name,
                            'current_price': current,
                            'zone': stock.average_zone_price,
                            'distance_pct': ((current - avg_max) / avg_max * 100),
                            'distance_type': 'above',
                            'sector': stock.sector,
                            'market_cap': stock.market_cap
                        })
                    elif avg_min * 0.97 <= current < avg_min:  # Within 3% below average zone
                        action_items['near_average_zone'].append({
                            'symbol': stock.symbol,
                            'name': stock.name,
                            'current_price': current,
                            'zone': stock.average_zone_price,
                            'distance_pct': ((avg_min - current) / avg_min * 100),
                            'distance_type': 'below',
                            'sector': stock.sector,
                            'market_cap': stock.market_cap
                        })
        
        # Count action items
        total_action_items = (len(action_items['in_buy_zone']) +
                             len(action_items['in_sell_zone']) +
                             len(action_items['in_average_zone']) +
                             len(action_items['near_buy_zone']) +
                             len(action_items['near_sell_zone']) +
                             len(action_items['near_average_zone']))
        
        # Top 5 Gainers and Losers (only from holdings, filtered by positive/negative)
        # Gainers: only stocks with positive gain_loss_pct
        gainers = [h for h in holdings_with_value if h['gain_loss_pct'] > 0]
        gainers_sorted = sorted(gainers, key=lambda x: x['gain_loss_pct'], reverse=True)
        top_gainers = gainers_sorted[:5]
        
        # Losers: only stocks with negative gain_loss_pct
        losers = [h for h in holdings_with_value if h['gain_loss_pct'] < 0]
        losers_sorted = sorted(losers, key=lambda x: x['gain_loss_pct'])
        top_losers = losers_sorted[:5]
        
        return jsonify({
            'portfolio_metrics': {
                'total_invested': round(total_invested, 2),
                'total_current_value': round(total_current_value, 2),
                'total_gain_loss': round(total_gain_loss, 2),
                'total_gain_loss_pct': round(total_gain_loss_pct, 2),
                'portfolio_day_change_pct': round(portfolio_day_change_pct, 2),
                'holdings_count': len(holdings_with_value)
            },
            'holdings': holdings_with_value,
            'action_items': action_items,
            'action_items_count': total_action_items,
            'top_gainers': top_gainers,
            'top_losers': top_losers,
            'stocks_tracked': len(stocks),
            'total_transactions': len(transactions)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/health/dashboard', methods=['GET'])
@api_login_required
def get_health_dashboard():
    """Get portfolio health metrics"""
    try:
        # Get all transactions and calculate holdings
        transactions = PortfolioTransaction.query.all()
        holdings_dict = calculate_holdings(transactions)
        
        # Get all stocks for additional info
        stocks = Stock.query.all()
        stocks_map = {}
        for stock in stocks:
            normalized = stock.symbol.replace('.NS', '').replace('.BO', '').upper()
            stocks_map[normalized] = stock
        
        # Build holdings list with full details
        holdings_list = []
        total_invested = 0
        
        for symbol, holding in holdings_dict.items():
            if holding['quantity'] > 0:
                normalized_symbol = symbol.replace('.NS', '').replace('.BO', '').upper()
                stock = stocks_map.get(normalized_symbol)
                
                holdings_list.append({
                    'symbol': symbol,
                    'name': stock.name if stock else '',
                    'sector': stock.sector if stock else None,
                    'market_cap': stock.market_cap if stock else None,
                    'invested_amount': holding['invested_amount'],
                    'quantity': holding['quantity'],
                    'current_price': stock.current_price if stock else None
                })
                
                total_invested += holding['invested_amount']
        
        # Calculate health metrics
        from utils import (
            calculate_concentration_risk,
            calculate_diversification_score,
            calculate_allocation_health,
            calculate_overall_health_score
        )
        
        concentration_risk = calculate_concentration_risk(holdings_list)
        diversification = calculate_diversification_score(holdings_list)
        allocation_health = calculate_allocation_health(holdings_list)
        overall_health_score = calculate_overall_health_score(
            concentration_risk,
            diversification,
            allocation_health
        )
        
        return jsonify({
            'overall_health_score': overall_health_score,
            'concentration_risk': concentration_risk,
            'diversification': diversification,
            'allocation_health': allocation_health,
            'total_invested': round(total_invested, 2),
            'holdings_count': len(holdings_list)
        })
    
    except Exception as e:
        print(f"ERROR in get_health_dashboard: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/health/financial-health', methods=['GET'])
@api_login_required
def get_financial_health():
    """Get comprehensive financial health metrics (Phase 3)"""
    try:
        from utils import (
            calculate_total_net_worth,
            get_asset_allocation,
            calculate_debt_to_income_ratio,
            calculate_emergency_fund_months,
            calculate_savings_rate
        )
        
        # Gather all assets
        all_assets = {
            'stocks': PortfolioTransaction.query.all(),
            'mutual_funds': MutualFundTransaction.query.all(),
            'fixed_deposits': FixedDeposit.query.all(),
            'epf': EPFAccount.query.all(),
            'nps': NPSAccount.query.all(),
            'savings': SavingsAccount.query.all(),
            'lending': LendingRecord.query.filter_by(status='active').all(),
            'other': OtherInvestment.query.all()
        }
        
        # Get income/expense transactions
        income_txns = IncomeTransaction.query.all()
        expense_txns = ExpenseTransaction.query.all()
        
        # Get global settings
        settings = GlobalSettings.query.first()
        if not settings:
            settings = GlobalSettings()
        
        # Calculate net worth
        net_worth = calculate_total_net_worth(all_assets)
        
        # Calculate asset allocation
        allocation = get_asset_allocation(all_assets)
        
        # Calculate savings rate
        savings_rate_data = calculate_savings_rate(income_txns, expense_txns, period='monthly')
        
        # Calculate emergency fund months
        savings_accounts = all_assets['savings']
        total_cash = sum(acc.current_balance for acc in savings_accounts)
        emergency_fund_months = calculate_emergency_fund_months(
            total_cash, 
            settings.monthly_expense_target if settings.monthly_expense_target > 0 else savings_rate_data['total_expense']
        )
        
        # Calculate debt-to-income ratio (for now, we don't track liabilities, so it's 0)
        # In future, can track credit card debt, loans, etc.
        debt_to_income = 0  # Placeholder
        
        # Calculate overall financial health score (0-100)
        # Based on multiple factors:
        # 1. Emergency fund status (25 points)
        emergency_fund_score = min((emergency_fund_months / settings.min_emergency_fund_months) * 25, 25) if settings.min_emergency_fund_months > 0 else 0
        
        # 2. Savings rate (25 points)
        target_savings_rate = 30  # 30% is considered healthy
        savings_rate_score = min((savings_rate_data['savings_rate'] / target_savings_rate) * 25, 25)
        
        # 3. Asset allocation balance (25 points)
        # Check if equity/debt allocation is within targets
        equity_target = settings.max_equity_allocation_pct
        debt_target = settings.max_debt_allocation_pct
        equity_diff = abs(allocation['equity'] - equity_target)
        debt_diff = abs(allocation['debt'] - debt_target)
        allocation_score = max(25 - (equity_diff + debt_diff) / 4, 0)
        
        # 4. Debt-to-income ratio (25 points)
        # Lower is better, 0% gets full points, >50% gets 0 points
        debt_score = max(25 - (debt_to_income / 2), 0)
        
        financial_health_score = int(emergency_fund_score + savings_rate_score + allocation_score + debt_score)
        
        return jsonify({
            'financial_health_score': financial_health_score,
            'net_worth': net_worth['total'],
            'emergency_fund': {
                'months_covered': emergency_fund_months,
                'target_months': settings.min_emergency_fund_months,
                'current_balance': round(total_cash, 2),
                'status': 'excellent' if emergency_fund_months >= settings.min_emergency_fund_months else 'needs_attention'
            },
            'savings_rate': {
                'current_rate': savings_rate_data['savings_rate'],
                'monthly_income': savings_rate_data['total_income'],
                'monthly_expense': savings_rate_data['total_expense'],
                'monthly_savings': savings_rate_data['net_savings'],
                'status': 'excellent' if savings_rate_data['savings_rate'] >= 30 else 'good' if savings_rate_data['savings_rate'] >= 20 else 'needs_improvement'
            },
            'debt_to_income': {
                'ratio': debt_to_income,
                'status': 'excellent' if debt_to_income < 20 else 'good' if debt_to_income < 35 else 'needs_attention'
            },
            'asset_allocation': {
                'equity': allocation['equity'],
                'debt': allocation['debt'],
                'cash': allocation['cash'],
                'alternative': allocation['alternative'],
                'equity_target': equity_target,
                'debt_target': debt_target
            },
            'score_breakdown': {
                'emergency_fund_score': round(emergency_fund_score, 1),
                'savings_rate_score': round(savings_rate_score, 1),
                'allocation_score': round(allocation_score, 1),
                'debt_score': round(debt_score, 1)
            }
        })
    
    except Exception as e:
        print(f"ERROR in get_financial_health: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/recommendations/dashboard', methods=['GET'])
@api_login_required
def get_recommendations_dashboard():
    """Get rebalancing recommendations and alert zones"""
    try:
        # Get all stocks and transactions
        stocks = Stock.query.all()
        transactions = PortfolioTransaction.query.all()
        
        # Calculate holdings
        holdings_dict = calculate_holdings(transactions)
        
        # Build holdings list with full details
        stocks_map = {}
        for stock in stocks:
            normalized = stock.symbol.replace('.NS', '').replace('.BO', '').upper()
            stocks_map[normalized] = stock
        
        holdings_list = []
        total_invested = 0
        
        for symbol, holding in holdings_dict.items():
            if holding['quantity'] > 0:
                normalized_symbol = symbol.replace('.NS', '').replace('.BO', '').upper()
                stock = stocks_map.get(normalized_symbol)
                
                holdings_list.append({
                    'symbol': symbol,
                    'name': stock.name if stock else '',
                    'sector': stock.sector if stock else None,
                    'market_cap': stock.market_cap if stock else None,
                    'invested_amount': holding['invested_amount'],
                    'quantity': holding['quantity'],
                    'current_price': stock.current_price if stock else None
                })
                
                total_invested += holding['invested_amount']
        
        # Get portfolio settings for thresholds
        settings = PortfolioSettings.query.first()
        
        # Get rebalancing suggestions
        from utils import get_rebalancing_suggestions
        rebalancing = get_rebalancing_suggestions(holdings_list, stocks, total_invested, settings)
        
        # Get alert zone action items (moved from analytics)
        holding_symbols_normalized = set(normalize_symbol(s) for s in holdings_dict.keys())
        
        action_items = {
            'in_buy_zone': [],
            'in_sell_zone': [],
            'in_average_zone': [],
            'near_buy_zone': [],
            'near_sell_zone': [],
            'near_average_zone': []
        }
        
        for stock in stocks:
            if not stock.current_price:
                continue
            
            normalized_symbol = normalize_symbol(stock.symbol)
            is_held = normalized_symbol in holding_symbols_normalized
            
            # Buy Zone - Only show if NOT held (watching stocks only)
            if stock.buy_zone_price and not is_held:
                buy_min, buy_max = parse_zone(stock.buy_zone_price)
                if buy_max and stock.current_price <= buy_max:
                    action_items['in_buy_zone'].append({
                        'symbol': stock.symbol,
                        'name': stock.name,
                        'sector': stock.sector,
                        'current_price': stock.current_price,
                        'zone': stock.buy_zone_price,
                        'is_held': is_held
                    })
                elif buy_max and stock.current_price <= buy_max * 1.03:
                    distance_pct = ((stock.current_price - buy_max) / buy_max) * 100
                    action_items['near_buy_zone'].append({
                        'symbol': stock.symbol,
                        'name': stock.name,
                        'sector': stock.sector,
                        'current_price': stock.current_price,
                        'zone': stock.buy_zone_price,
                        'distance_pct': distance_pct,
                        'distance_type': 'above',
                        'is_held': is_held
                    })
            
            # Sell Zone - Only show if held (holdings only)
            if stock.sell_zone_price and is_held:
                sell_min, sell_max = parse_zone(stock.sell_zone_price)
                if sell_min and stock.current_price >= sell_min:
                    action_items['in_sell_zone'].append({
                        'symbol': stock.symbol,
                        'name': stock.name,
                        'sector': stock.sector,
                        'current_price': stock.current_price,
                        'zone': stock.sell_zone_price,
                        'is_held': is_held
                    })
                elif sell_min and stock.current_price >= sell_min * 0.97:
                    distance_pct = ((sell_min - stock.current_price) / sell_min) * 100
                    action_items['near_sell_zone'].append({
                        'symbol': stock.symbol,
                        'name': stock.name,
                        'sector': stock.sector,
                        'current_price': stock.current_price,
                        'zone': stock.sell_zone_price,
                        'distance_pct': distance_pct,
                        'distance_type': 'below',
                        'is_held': is_held
                    })
            
            # Average Zone - Only show if held (holdings only)
            if stock.average_zone_price and is_held:
                avg_min, avg_max = parse_zone(stock.average_zone_price)
                if avg_min and avg_max and avg_min <= stock.current_price <= avg_max:
                    action_items['in_average_zone'].append({
                        'symbol': stock.symbol,
                        'name': stock.name,
                        'sector': stock.sector,
                        'current_price': stock.current_price,
                        'zone': stock.average_zone_price,
                        'is_held': is_held
                    })
                elif avg_max and stock.current_price <= avg_max * 1.03 and stock.current_price > avg_max:
                    distance_pct = ((stock.current_price - avg_max) / avg_max) * 100
                    action_items['near_average_zone'].append({
                        'symbol': stock.symbol,
                        'name': stock.name,
                        'sector': stock.sector,
                        'current_price': stock.current_price,
                        'zone': stock.average_zone_price,
                        'distance_pct': distance_pct,
                        'distance_type': 'above',
                        'is_held': is_held
                    })
                elif avg_min and stock.current_price >= avg_min * 0.97 and stock.current_price < avg_min:
                    distance_pct = ((avg_min - stock.current_price) / avg_min) * 100
                    action_items['near_average_zone'].append({
                        'symbol': stock.symbol,
                        'name': stock.name,
                        'sector': stock.sector,
                        'current_price': stock.current_price,
                        'zone': stock.average_zone_price,
                        'distance_pct': distance_pct,
                        'distance_type': 'below',
                        'is_held': is_held
                    })
        
        # Count action items
        total_action_items = sum(len(items) for items in action_items.values())
        
        return jsonify({
            'rebalancing': rebalancing,
            'action_items': action_items,
            'action_items_count': total_action_items
        })
    
    except Exception as e:
        print(f"ERROR in get_recommendations_dashboard: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============================================================================
# Data Management Routes (Auth required)
# ============================================================================

@app.route('/api/export/stocks', methods=['GET'])
@api_login_required
def export_stocks_csv():
    """Export all stocks to CSV"""
    try:
        stocks = Stock.query.all()
        
        # Return empty list if no stocks, not 404
        if not stocks:
            # Create empty CSV with headers
            df = pd.DataFrame(columns=['id', 'symbol', 'name', 'sector', 'market_cap', 'status'])
            filename = f'stocks_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            filepath = os.path.join('exports', filename)
            os.makedirs('exports', exist_ok=True)
            df.to_csv(filepath, index=False)
            return send_file(filepath, as_attachment=True, download_name=filename, mimetype='text/csv')
        
        # Convert to list of dicts
        data = [stock.to_dict() for stock in stocks]
        df = pd.DataFrame(data)
        
        # Save to CSV
        filename = f'stocks_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        filepath = os.path.join('exports', filename)
        
        # Create exports directory if it doesn't exist
        os.makedirs('exports', exist_ok=True)
        
        df.to_csv(filepath, index=False)
        
        return send_file(filepath, as_attachment=True, download_name=filename, mimetype='text/csv')
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/import/stocks', methods=['POST'])
@api_login_required
def import_stocks_csv():
    """Import stocks from CSV"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({'error': 'File must be a CSV'}), 400
        
        # Read CSV
        df = pd.read_csv(file)
        
        imported_count = 0
        skipped_count = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                # Check if stock already exists
                existing = Stock.query.filter_by(symbol=row['symbol']).first()
                if existing:
                    skipped_count += 1
                    continue
                
                # Create new stock
                stock = Stock(
                    symbol=row['symbol'],
                    name=row['name'],
                    group_name=row.get('group_name'),
                    sector=row.get('sector'),
                    market_cap=row.get('market_cap'),
                    buy_zone_price=row.get('buy_zone_price'),
                    sell_zone_price=row.get('sell_zone_price'),
                    average_zone_price=row.get('average_zone_price'),
                    status=row.get('status', 'WATCHING'),
                    current_price=row.get('current_price'),
                    notes=row.get('notes')
                )
                
                db.session.add(stock)
                imported_count += 1
            
            except Exception as e:
                errors.append(f"Row {index + 1}: {str(e)}")
        
        db.session.commit()
        
        return jsonify({
            'message': f'Import completed: {imported_count} imported, {skipped_count} skipped',
            'imported': imported_count,
            'skipped': skipped_count,
            'errors': errors
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/export/transactions', methods=['GET'])
@api_login_required
def export_transactions_csv():
    """Export all portfolio transactions to CSV"""
    try:
        transactions = PortfolioTransaction.query.all()
        
        # Return empty CSV if no transactions, not 404
        if not transactions:
            # Create empty CSV with headers
            df = pd.DataFrame(columns=['id', 'symbol', 'transaction_type', 'quantity', 'price', 'transaction_date'])
            filename = f'transactions_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            filepath = os.path.join('exports', filename)
            os.makedirs('exports', exist_ok=True)
            df.to_csv(filepath, index=False)
            return send_file(filepath, as_attachment=True, download_name=filename, mimetype='text/csv')
        
        # Convert to list of dicts
        data = [txn.to_dict() for txn in transactions]
        df = pd.DataFrame(data)
        
        # Save to CSV
        filename = f'transactions_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        filepath = os.path.join('exports', filename)
        
        os.makedirs('exports', exist_ok=True)
        
        df.to_csv(filepath, index=False)
        
        return send_file(filepath, as_attachment=True, download_name=filename, mimetype='text/csv')
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/import/transactions', methods=['POST'])
@api_login_required
def import_transactions_csv():
    """Import portfolio transactions from CSV"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({'error': 'File must be a CSV'}), 400
        
        # Read CSV
        df = pd.read_csv(file)
        
        imported_count = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                # Parse date
                txn_date = pd.to_datetime(row['transaction_date'])
                
                # Create new transaction
                transaction = PortfolioTransaction(
                    stock_symbol=row['stock_symbol'],
                    stock_name=row['stock_name'],
                    transaction_type=row['transaction_type'],
                    quantity=float(row['quantity']),
                    price=float(row['price']),
                    transaction_date=txn_date,
                    reason=row.get('reason'),
                    notes=row.get('notes')
                )
                
                db.session.add(transaction)
                imported_count += 1
            
            except Exception as e:
                errors.append(f"Row {index + 1}: {str(e)}")
        
        db.session.commit()
        
        return jsonify({
            'message': f'Import completed: {imported_count} transactions imported',
            'imported': imported_count,
            'errors': errors
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/backup/database', methods=['GET'])
@api_login_required
def backup_database():
    """Download database backup"""
    try:
        # Database is in instance/ folder
        db_path = os.path.join('instance', 'investment_manager.db')
        
        if not os.path.exists(db_path):
            # Try without instance folder (for tests or different setup)
            db_path = 'investment_manager.db'
            if not os.path.exists(db_path):
                return jsonify({'error': 'Database file not found'}), 404
        
        # Create backups directory
        os.makedirs('backups', exist_ok=True)
        
        # Create backup with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f'investment_manager_backup_{timestamp}.db'
        backup_path = os.path.join('backups', backup_filename)
        
        # Copy database file
        shutil.copy2(db_path, backup_path)
        
        return send_file(backup_path, as_attachment=True, download_name=backup_filename, mimetype='application/x-sqlite3')
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/restore/database', methods=['POST'])
@api_login_required
def restore_database():
    """Restore database from backup"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.endswith('.db'):
            return jsonify({'error': 'File must be a .db file'}), 400
        
        db_path = 'investment_manager.db'
        
        # Create backup of current database before restoring
        if os.path.exists(db_path):
            backup_current = f'investment_manager_before_restore_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
            shutil.copy2(db_path, os.path.join('backups', backup_current))
        
        # Save uploaded file as new database
        file.save(db_path)
        
        return jsonify({
            'message': 'Database restored successfully. Please restart the application.',
            'backup_created': backup_current if os.path.exists(os.path.join('backups', backup_current)) else None
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# Personal Finance API Routes - Multi-Asset Tracking
# ============================================================================

# Mutual Funds Routes
@app.route('/api/mutual-funds/schemes', methods=['GET'])
@api_login_required
def get_mutual_fund_schemes():
    """Get all tracked mutual fund schemes"""
    try:
        schemes = MutualFund.query.all()
        return jsonify([scheme.to_dict() for scheme in schemes])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/mutual-funds/schemes', methods=['POST'])
@api_login_required
def add_mutual_fund_scheme():
    """Add new mutual fund scheme to track"""
    try:
        data = request.json
        
        if not data or not data.get('scheme_code') or not data.get('scheme_name'):
            return jsonify({'error': 'Scheme code and name are required'}), 400
        
        # Check if scheme already exists
        existing = MutualFund.query.filter_by(scheme_code=data['scheme_code']).first()
        if existing:
            return jsonify({'error': 'Scheme already exists'}), 400
        
        scheme = MutualFund(
            scheme_code=data['scheme_code'],
            scheme_name=data['scheme_name'],
            fund_house=data.get('fund_house'),
            category=data.get('category'),
            sub_category=data.get('sub_category'),
            current_nav=data.get('current_nav'),
            expense_ratio=data.get('expense_ratio'),
            notes=data.get('notes')
        )
        
        db.session.add(scheme)
        db.session.commit()
        
        return jsonify(scheme.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/mutual-funds/schemes/<int:scheme_id>', methods=['PUT'])
@api_login_required
def update_mutual_fund_scheme(scheme_id):
    """Update mutual fund scheme details"""
    try:
        scheme = MutualFund.query.get_or_404(scheme_id)
        data = request.json
        
        if data.get('scheme_name'):
            scheme.scheme_name = data['scheme_name']
        if data.get('fund_house'):
            scheme.fund_house = data['fund_house']
        if data.get('category'):
            scheme.category = data['category']
        if data.get('sub_category'):
            scheme.sub_category = data['sub_category']
        if data.get('current_nav') is not None:
            scheme.current_nav = data['current_nav']
        if data.get('day_change_pct') is not None:
            scheme.day_change_pct = data['day_change_pct']
        if data.get('expense_ratio') is not None:
            scheme.expense_ratio = data['expense_ratio']
        if 'notes' in data:
            scheme.notes = data['notes']
        
        scheme.last_updated = datetime.now(timezone.utc)
        db.session.commit()
        
        return jsonify(scheme.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/mutual-funds/schemes/<int:scheme_id>', methods=['DELETE'])
@api_login_required
def delete_mutual_fund_scheme(scheme_id):
    """Delete mutual fund scheme"""
    try:
        scheme = MutualFund.query.get_or_404(scheme_id)
        db.session.delete(scheme)
        db.session.commit()
        return jsonify({'message': 'Scheme deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/mutual-funds/transactions', methods=['GET'])
@api_login_required
def get_mutual_fund_transactions():
    """Get all mutual fund transactions"""
    try:
        transactions = MutualFundTransaction.query.order_by(MutualFundTransaction.transaction_date.desc()).all()
        return jsonify([txn.to_dict() for txn in transactions])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/mutual-funds/transactions', methods=['POST'])
@api_login_required
def add_mutual_fund_transaction():
    """Add mutual fund transaction"""
    try:
        data = request.json
        
        required_fields = ['scheme_code', 'scheme_name', 'transaction_type', 'units', 'nav', 'amount', 'transaction_date']
        for field in required_fields:
            if not data or field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Parse transaction date
        try:
            if 'T' in data['transaction_date']:
                txn_date = datetime.fromisoformat(data['transaction_date'].replace('Z', '+00:00'))
            else:
                txn_date = datetime.strptime(data['transaction_date'], '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400
        
        transaction = MutualFundTransaction(
            scheme_code=data['scheme_code'],
            scheme_name=data['scheme_name'],
            transaction_type=data['transaction_type'].upper(),
            units=float(data['units']),
            nav=float(data['nav']),
            amount=float(data['amount']),
            transaction_date=txn_date,
            is_sip=data.get('is_sip', False),
            sip_id=data.get('sip_id'),
            reason=data.get('reason'),
            notes=data.get('notes')
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        return jsonify(transaction.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/mutual-funds/transactions/<int:txn_id>', methods=['PUT'])
@api_login_required
def update_mutual_fund_transaction(txn_id):
    """Update mutual fund transaction"""
    try:
        transaction = MutualFundTransaction.query.get_or_404(txn_id)
        data = request.json
        
        if data.get('scheme_code'):
            transaction.scheme_code = data['scheme_code']
        if data.get('scheme_name'):
            transaction.scheme_name = data['scheme_name']
        if data.get('transaction_type'):
            transaction.transaction_type = data['transaction_type'].upper()
        if data.get('units') is not None:
            transaction.units = float(data['units'])
        if data.get('nav') is not None:
            transaction.nav = float(data['nav'])
        if data.get('amount') is not None:
            transaction.amount = float(data['amount'])
        if data.get('transaction_date'):
            if 'T' in data['transaction_date']:
                transaction.transaction_date = datetime.fromisoformat(data['transaction_date'].replace('Z', '+00:00'))
            else:
                transaction.transaction_date = datetime.strptime(data['transaction_date'], '%Y-%m-%d')
        if 'is_sip' in data:
            transaction.is_sip = data['is_sip']
        if 'sip_id' in data:
            transaction.sip_id = data['sip_id']
        if 'reason' in data:
            transaction.reason = data['reason']
        if 'notes' in data:
            transaction.notes = data['notes']
        
        db.session.commit()
        return jsonify(transaction.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/mutual-funds/transactions/<int:txn_id>', methods=['DELETE'])
@api_login_required
def delete_mutual_fund_transaction(txn_id):
    """Delete mutual fund transaction"""
    try:
        transaction = MutualFundTransaction.query.get_or_404(txn_id)
        db.session.delete(transaction)
        db.session.commit()
        return jsonify({'message': 'Transaction deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/mutual-funds/holdings', methods=['GET'])
@api_login_required
def get_mutual_fund_holdings():
    """Calculate and return mutual fund holdings using FIFO"""
    try:
        transactions = MutualFundTransaction.query.order_by(MutualFundTransaction.transaction_date).all()
        
        from utils.mutual_funds import calculate_mf_holdings
        holdings_dict = calculate_mf_holdings(transactions)
        
        # Get scheme details
        schemes = MutualFund.query.all()
        schemes_map = {scheme.scheme_code: scheme for scheme in schemes}
        
        holdings_list = []
        for scheme_code, holding in holdings_dict.items():
            if holding['units'] > 0:
                scheme = schemes_map.get(scheme_code)
                holdings_list.append({
                    'scheme_code': scheme_code,
                    'scheme_name': holding['scheme_name'],
                    'units': holding['units'],
                    'invested_amount': holding['invested_amount'],
                    'current_nav': scheme.current_nav if scheme else None,
                    'current_value': (scheme.current_nav * holding['units']) if scheme and scheme.current_nav else None,
                    'realized_pnl': holding['realized_pnl'],
                    'unrealized_pnl': ((scheme.current_nav * holding['units']) - holding['invested_amount']) if scheme and scheme.current_nav else None
                })
        
        return jsonify(holdings_list)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Fixed Deposits Routes
@app.route('/api/fixed-deposits', methods=['GET'])
@api_login_required
def get_fixed_deposits():
    """Get all fixed deposits"""
    try:
        fds = FixedDeposit.query.all()
        return jsonify([fd.to_dict() for fd in fds])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/fixed-deposits', methods=['POST'])
@api_login_required
def add_fixed_deposit():
    """Add new fixed deposit"""
    try:
        data = request.json
        
        required_fields = ['bank_name', 'principal_amount', 'interest_rate', 'start_date', 'maturity_date']
        for field in required_fields:
            if not data or field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Parse dates
        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        maturity_date = datetime.strptime(data['maturity_date'], '%Y-%m-%d').date()
        
        fd = FixedDeposit(
            bank_name=data['bank_name'],
            account_number=data.get('account_number'),
            principal_amount=float(data['principal_amount']),
            interest_rate=float(data['interest_rate']),
            start_date=start_date,
            maturity_date=maturity_date,
            interest_frequency=data.get('interest_frequency', 'at_maturity'),
            maturity_amount=data.get('maturity_amount'),
            status=data.get('status', 'active'),
            notes=data.get('notes')
        )
        
        db.session.add(fd)
        db.session.commit()
        
        return jsonify(fd.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/fixed-deposits/<int:fd_id>', methods=['PUT'])
@api_login_required
def update_fixed_deposit(fd_id):
    """Update fixed deposit"""
    try:
        fd = FixedDeposit.query.get_or_404(fd_id)
        data = request.json
        
        if data.get('bank_name'):
            fd.bank_name = data['bank_name']
        if 'account_number' in data:
            fd.account_number = data['account_number']
        if data.get('principal_amount') is not None:
            fd.principal_amount = float(data['principal_amount'])
        if data.get('interest_rate') is not None:
            fd.interest_rate = float(data['interest_rate'])
        if data.get('start_date'):
            fd.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        if data.get('maturity_date'):
            fd.maturity_date = datetime.strptime(data['maturity_date'], '%Y-%m-%d').date()
        if data.get('interest_frequency'):
            fd.interest_frequency = data['interest_frequency']
        if data.get('maturity_amount') is not None:
            fd.maturity_amount = float(data['maturity_amount'])
        if data.get('status'):
            fd.status = data['status']
        if 'notes' in data:
            fd.notes = data['notes']
        
        db.session.commit()
        return jsonify(fd.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/fixed-deposits/<int:fd_id>', methods=['DELETE'])
@api_login_required
def delete_fixed_deposit(fd_id):
    """Delete fixed deposit"""
    try:
        fd = FixedDeposit.query.get_or_404(fd_id)
        db.session.delete(fd)
        db.session.commit()
        return jsonify({'message': 'Fixed deposit deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/fixed-deposits/matured', methods=['GET'])
@api_login_required
def get_matured_fixed_deposits():
    """Get matured fixed deposits"""
    try:
        today = datetime.now().date()
        matured_fds = FixedDeposit.query.filter(FixedDeposit.maturity_date <= today).all()
        return jsonify([fd.to_dict() for fd in matured_fds])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/fixed-deposits/upcoming-maturity', methods=['GET'])
@api_login_required
def get_upcoming_maturity_fds():
    """Get FDs maturing in next 90 days"""
    try:
        today = datetime.now().date()
        ninety_days_later = today + pd.Timedelta(days=90)
        
        upcoming_fds = FixedDeposit.query.filter(
            FixedDeposit.maturity_date > today,
            FixedDeposit.maturity_date <= ninety_days_later,
            FixedDeposit.status == 'active'
        ).all()
        
        return jsonify([fd.to_dict() for fd in upcoming_fds])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# EPF Routes
@app.route('/api/epf/accounts', methods=['GET'])
@api_login_required
def get_epf_accounts():
    """Get all EPF accounts"""
    try:
        accounts = EPFAccount.query.all()
        return jsonify([acc.to_dict() for acc in accounts])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/epf/accounts', methods=['POST'])
@api_login_required
def add_epf_account():
    """Add new EPF account"""
    try:
        data = request.json
        
        if not data or not data.get('employer_name'):
            return jsonify({'error': 'Employer name is required'}), 400
        
        opening_date = None
        if data.get('opening_date'):
            opening_date = datetime.strptime(data['opening_date'], '%Y-%m-%d').date()
        
        account = EPFAccount(
            employer_name=data['employer_name'],
            uan_number=data.get('uan_number'),
            opening_balance=data.get('opening_balance', 0.0),
            opening_date=opening_date,
            current_balance=data.get('current_balance', 0.0),
            interest_rate=data.get('interest_rate'),
            notes=data.get('notes')
        )
        
        db.session.add(account)
        db.session.commit()
        
        return jsonify(account.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/epf/accounts/<int:account_id>', methods=['PUT'])
@api_login_required
def update_epf_account(account_id):
    """Update EPF account"""
    try:
        account = EPFAccount.query.get_or_404(account_id)
        data = request.json
        
        if data.get('employer_name'):
            account.employer_name = data['employer_name']
        if 'uan_number' in data:
            account.uan_number = data['uan_number']
        if data.get('opening_balance') is not None:
            account.opening_balance = float(data['opening_balance'])
        if data.get('opening_date'):
            account.opening_date = datetime.strptime(data['opening_date'], '%Y-%m-%d').date()
        if data.get('current_balance') is not None:
            account.current_balance = float(data['current_balance'])
        if data.get('interest_rate') is not None:
            account.interest_rate = float(data['interest_rate'])
        if 'notes' in data:
            account.notes = data['notes']
        
        account.last_updated = datetime.now(timezone.utc)
        db.session.commit()
        
        return jsonify(account.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/epf/contributions', methods=['GET'])
@api_login_required
def get_epf_contributions():
    """Get all EPF contributions"""
    try:
        contributions = EPFContribution.query.order_by(EPFContribution.transaction_date.desc()).all()
        return jsonify([cont.to_dict() for cont in contributions])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/epf/contributions', methods=['POST'])
@api_login_required
def add_epf_contribution():
    """Add EPF contribution"""
    try:
        data = request.json
        
        required_fields = ['epf_account_id', 'month_year', 'transaction_date']
        for field in required_fields:
            if not data or field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        txn_date = datetime.strptime(data['transaction_date'], '%Y-%m-%d').date()
        
        contribution = EPFContribution(
            epf_account_id=data['epf_account_id'],
            month_year=data['month_year'],
            employee_contribution=data.get('employee_contribution', 0.0),
            employer_contribution=data.get('employer_contribution', 0.0),
            interest_earned=data.get('interest_earned', 0.0),
            transaction_date=txn_date,
            notes=data.get('notes')
        )
        
        db.session.add(contribution)
        
        # Update account current balance
        account = EPFAccount.query.get(data['epf_account_id'])
        if account:
            account.current_balance += (
                data.get('employee_contribution', 0.0) + 
                data.get('employer_contribution', 0.0) + 
                data.get('interest_earned', 0.0)
            )
            account.last_updated = datetime.now(timezone.utc)
        
        db.session.commit()
        
        return jsonify(contribution.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/epf/summary', methods=['GET'])
@api_login_required
def get_epf_summary():
    """Get EPF summary"""
    try:
        accounts = EPFAccount.query.all()
        total_balance = sum(acc.current_balance for acc in accounts)
        
        return jsonify({
            'total_accounts': len(accounts),
            'total_balance': total_balance,
            'accounts': [acc.to_dict() for acc in accounts]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# NPS Routes - Similar structure to EPF
@app.route('/api/nps/accounts', methods=['GET'])
@api_login_required
def get_nps_accounts():
    """Get all NPS accounts"""
    try:
        accounts = NPSAccount.query.all()
        return jsonify([acc.to_dict() for acc in accounts])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/nps/accounts', methods=['POST'])
@api_login_required
def add_nps_account():
    """Add new NPS account"""
    try:
        data = request.json
        
        if not data or not data.get('pran_number'):
            return jsonify({'error': 'PRAN number is required'}), 400
        
        # Check if PRAN already exists
        existing = NPSAccount.query.filter_by(pran_number=data['pran_number']).first()
        if existing:
            return jsonify({'error': 'PRAN already exists'}), 400
        
        account = NPSAccount(
            pran_number=data['pran_number'],
            scheme_type=data.get('scheme_type', 'tier1'),
            current_value=data.get('current_value', 0.0),
            units=data.get('units', 0.0),
            nav=data.get('nav'),
            notes=data.get('notes')
        )
        
        db.session.add(account)
        db.session.commit()
        
        return jsonify(account.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/nps/contributions', methods=['GET'])
@api_login_required
def get_nps_contributions():
    """Get all NPS contributions"""
    try:
        contributions = NPSContribution.query.order_by(NPSContribution.transaction_date.desc()).all()
        return jsonify([cont.to_dict() for cont in contributions])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/nps/contributions', methods=['POST'])
@api_login_required
def add_nps_contribution():
    """Add NPS contribution"""
    try:
        data = request.json
        
        required_fields = ['nps_account_id', 'amount', 'transaction_date']
        for field in required_fields:
            if not data or field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        txn_date = datetime.strptime(data['transaction_date'], '%Y-%m-%d').date()
        
        contribution = NPSContribution(
            nps_account_id=data['nps_account_id'],
            amount=float(data['amount']),
            nav=data.get('nav'),
            units=data.get('units'),
            transaction_date=txn_date,
            contribution_type=data.get('contribution_type', 'self'),
            notes=data.get('notes')
        )
        
        db.session.add(contribution)
        
        # Update account
        account = NPSAccount.query.get(data['nps_account_id'])
        if account:
            account.current_value += float(data['amount'])
            if data.get('units'):
                account.units += float(data['units'])
            if data.get('nav'):
                account.nav = float(data['nav'])
            account.last_updated = datetime.now(timezone.utc)
        
        db.session.commit()
        
        return jsonify(contribution.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/nps/summary', methods=['GET'])
@api_login_required
def get_nps_summary():
    """Get NPS summary"""
    try:
        accounts = NPSAccount.query.all()
        total_value = sum(acc.current_value for acc in accounts)
        
        return jsonify({
            'total_accounts': len(accounts),
            'total_value': total_value,
            'accounts': [acc.to_dict() for acc in accounts]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Savings Account Routes
@app.route('/api/savings/accounts', methods=['GET'])
@api_login_required
def get_savings_accounts():
    """Get all savings accounts"""
    try:
        accounts = SavingsAccount.query.all()
        return jsonify([acc.to_dict() for acc in accounts])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/savings/accounts', methods=['POST'])
@api_login_required
def add_savings_account():
    """Add new savings account"""
    try:
        data = request.json
        
        required_fields = ['bank_name', 'account_number']
        for field in required_fields:
            if not data or field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        account = SavingsAccount(
            bank_name=data['bank_name'],
            account_number=data['account_number'],
            account_type=data.get('account_type', 'savings'),
            current_balance=data.get('current_balance', 0.0),
            interest_rate=data.get('interest_rate'),
            notes=data.get('notes')
        )
        
        db.session.add(account)
        db.session.commit()
        
        return jsonify(account.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/savings/accounts/<int:account_id>', methods=['PUT'])
@api_login_required
def update_savings_account(account_id):
    """Update savings account"""
    try:
        account = SavingsAccount.query.get_or_404(account_id)
        data = request.json
        
        if data.get('bank_name'):
            account.bank_name = data['bank_name']
        if data.get('account_number'):
            account.account_number = data['account_number']
        if data.get('account_type'):
            account.account_type = data['account_type']
        if data.get('current_balance') is not None:
            account.current_balance = float(data['current_balance'])
        if data.get('interest_rate') is not None:
            account.interest_rate = float(data['interest_rate'])
        if 'notes' in data:
            account.notes = data['notes']
        
        account.last_updated = datetime.now(timezone.utc)
        db.session.commit()
        
        return jsonify(account.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/savings/transactions', methods=['GET'])
@api_login_required
def get_savings_transactions():
    """Get all savings transactions"""
    try:
        transactions = SavingsTransaction.query.order_by(SavingsTransaction.transaction_date.desc()).all()
        return jsonify([txn.to_dict() for txn in transactions])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/savings/transactions', methods=['POST'])
@api_login_required
def add_savings_transaction():
    """Add savings transaction"""
    try:
        data = request.json
        
        required_fields = ['account_id', 'transaction_type', 'amount', 'transaction_date']
        for field in required_fields:
            if not data or field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        txn_date = datetime.strptime(data['transaction_date'], '%Y-%m-%d').date()
        
        transaction = SavingsTransaction(
            account_id=data['account_id'],
            transaction_type=data['transaction_type'],
            amount=float(data['amount']),
            balance_after=data.get('balance_after'),
            transaction_date=txn_date,
            description=data.get('description'),
            notes=data.get('notes')
        )
        
        db.session.add(transaction)
        
        # Update account balance
        account = SavingsAccount.query.get(data['account_id'])
        if account:
            if data['transaction_type'] == 'deposit':
                account.current_balance += float(data['amount'])
            elif data['transaction_type'] == 'withdrawal':
                account.current_balance -= float(data['amount'])
            account.last_updated = datetime.now(timezone.utc)
        
        db.session.commit()
        
        return jsonify(transaction.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/savings/summary', methods=['GET'])
@api_login_required
def get_savings_summary():
    """Get savings summary"""
    try:
        accounts = SavingsAccount.query.all()
        total_balance = sum(acc.current_balance for acc in accounts)
        
        return jsonify({
            'total_accounts': len(accounts),
            'total_balance': total_balance,
            'accounts': [acc.to_dict() for acc in accounts]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Lending Routes
@app.route('/api/lending', methods=['GET'])
@api_login_required
def get_lending_records():
    """Get all lending records"""
    try:
        records = LendingRecord.query.all()
        return jsonify([rec.to_dict() for rec in records])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/lending', methods=['POST'])
@api_login_required
def add_lending_record():
    """Add new lending record"""
    try:
        data = request.json
        
        required_fields = ['borrower_name', 'principal_amount', 'start_date']
        for field in required_fields:
            if not data or field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        
        record = LendingRecord(
            borrower_name=data['borrower_name'],
            principal_amount=float(data['principal_amount']),
            interest_rate=data.get('interest_rate', 0.0),
            start_date=start_date,
            tenure_months=data.get('tenure_months'),
            monthly_emi=data.get('monthly_emi'),
            total_repaid=data.get('total_repaid', 0.0),
            outstanding_amount=data.get('outstanding_amount', data['principal_amount']),
            status=data.get('status', 'active'),
            notes=data.get('notes')
        )
        
        db.session.add(record)
        db.session.commit()
        
        return jsonify(record.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/lending/<int:record_id>', methods=['PUT'])
@api_login_required
def update_lending_record(record_id):
    """Update lending record"""
    try:
        record = LendingRecord.query.get_or_404(record_id)
        data = request.json
        
        if data.get('borrower_name'):
            record.borrower_name = data['borrower_name']
        if data.get('total_repaid') is not None:
            record.total_repaid = float(data['total_repaid'])
        if data.get('outstanding_amount') is not None:
            record.outstanding_amount = float(data['outstanding_amount'])
        if data.get('status'):
            record.status = data['status']
        if 'notes' in data:
            record.notes = data['notes']
        
        db.session.commit()
        return jsonify(record.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/lending/summary', methods=['GET'])
@api_login_required
def get_lending_summary():
    """Get lending summary"""
    try:
        records = LendingRecord.query.all()
        total_outstanding = sum(rec.outstanding_amount or 0 for rec in records if rec.status == 'active')
        
        return jsonify({
            'total_records': len(records),
            'active_records': len([r for r in records if r.status == 'active']),
            'total_outstanding': total_outstanding,
            'records': [rec.to_dict() for rec in records]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Other Investments Routes
@app.route('/api/other-investments', methods=['GET'])
@api_login_required
def get_other_investments():
    """Get all other investments"""
    try:
        investments = OtherInvestment.query.all()
        return jsonify([inv.to_dict() for inv in investments])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/other-investments', methods=['POST'])
@api_login_required
def add_other_investment():
    """Add new other investment"""
    try:
        data = request.json
        
        required_fields = ['investment_type', 'description', 'purchase_value']
        for field in required_fields:
            if not data or field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        purchase_date = None
        if data.get('purchase_date'):
            purchase_date = datetime.strptime(data['purchase_date'], '%Y-%m-%d').date()
        
        investment = OtherInvestment(
            investment_type=data['investment_type'],
            description=data['description'],
            purchase_value=float(data['purchase_value']),
            current_value=data.get('current_value'),
            purchase_date=purchase_date,
            notes=data.get('notes')
        )
        
        db.session.add(investment)
        db.session.commit()
        
        return jsonify(investment.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/other-investments/<int:inv_id>', methods=['PUT'])
@api_login_required
def update_other_investment(inv_id):
    """Update other investment"""
    try:
        investment = OtherInvestment.query.get_or_404(inv_id)
        data = request.json
        
        if data.get('investment_type'):
            investment.investment_type = data['investment_type']
        if data.get('description'):
            investment.description = data['description']
        if data.get('purchase_value') is not None:
            investment.purchase_value = float(data['purchase_value'])
        if data.get('current_value') is not None:
            investment.current_value = float(data['current_value'])
        if data.get('purchase_date'):
            investment.purchase_date = datetime.strptime(data['purchase_date'], '%Y-%m-%d').date()
        if 'notes' in data:
            investment.notes = data['notes']
        
        investment.last_updated = datetime.now(timezone.utc)
        db.session.commit()
        
        return jsonify(investment.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/other-investments/<int:inv_id>', methods=['DELETE'])
@api_login_required
def delete_other_investment(inv_id):
    """Delete other investment"""
    try:
        investment = OtherInvestment.query.get_or_404(inv_id)
        db.session.delete(investment)
        db.session.commit()
        return jsonify({'message': 'Investment deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# Income & Expense Routes
@app.route('/api/income/transactions', methods=['GET'])
@api_login_required
def get_income_transactions():
    """Get all income transactions"""
    try:
        transactions = IncomeTransaction.query.order_by(IncomeTransaction.transaction_date.desc()).all()
        return jsonify([txn.to_dict() for txn in transactions])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/income/transactions', methods=['POST'])
@api_login_required
def add_income_transaction():
    """Add income transaction"""
    try:
        data = request.json
        
        required_fields = ['source', 'amount', 'transaction_date']
        for field in required_fields:
            if not data or field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        txn_date = datetime.strptime(data['transaction_date'], '%Y-%m-%d').date()
        
        transaction = IncomeTransaction(
            source=data['source'],
            category=data.get('category'),
            amount=float(data['amount']),
            transaction_date=txn_date,
            is_recurring=data.get('is_recurring', False),
            description=data.get('description'),
            notes=data.get('notes')
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        return jsonify(transaction.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/income/transactions/<int:txn_id>', methods=['PUT'])
@api_login_required
def update_income_transaction(txn_id):
    """Update income transaction"""
    try:
        transaction = IncomeTransaction.query.get_or_404(txn_id)
        data = request.json
        
        if data.get('source'):
            transaction.source = data['source']
        if 'category' in data:
            transaction.category = data['category']
        if data.get('amount') is not None:
            transaction.amount = float(data['amount'])
        if data.get('transaction_date'):
            transaction.transaction_date = datetime.strptime(data['transaction_date'], '%Y-%m-%d').date()
        if 'is_recurring' in data:
            transaction.is_recurring = data['is_recurring']
        if 'description' in data:
            transaction.description = data['description']
        if 'notes' in data:
            transaction.notes = data['notes']
        
        db.session.commit()
        return jsonify(transaction.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/income/transactions/<int:txn_id>', methods=['DELETE'])
@api_login_required
def delete_income_transaction(txn_id):
    """Delete income transaction"""
    try:
        transaction = IncomeTransaction.query.get_or_404(txn_id)
        db.session.delete(transaction)
        db.session.commit()
        return jsonify({'message': 'Transaction deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/income/summary', methods=['GET'])
@api_login_required
def get_income_summary():
    """Get income summary (monthly/yearly)"""
    try:
        from utils.cash_flow import calculate_monthly_cash_flow
        
        transactions = IncomeTransaction.query.all()
        total_income = sum(txn.amount for txn in transactions)
        
        # Group by source
        by_source = {}
        for txn in transactions:
            source = txn.source
            if source not in by_source:
                by_source[source] = 0
            by_source[source] += txn.amount
        
        return jsonify({
            'total_income': total_income,
            'by_source': by_source,
            'transaction_count': len(transactions)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/income/categories', methods=['GET'])
@api_login_required
def get_income_categories():
    """Get income breakdown by category"""
    try:
        transactions = IncomeTransaction.query.all()
        
        by_category = {}
        for txn in transactions:
            category = txn.category or 'Uncategorized'
            if category not in by_category:
                by_category[category] = 0
            by_category[category] += txn.amount
        
        return jsonify(by_category)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Expense Routes
@app.route('/api/expenses/transactions', methods=['GET'])
@api_login_required
def get_expense_transactions():
    """Get all expense transactions"""
    try:
        transactions = ExpenseTransaction.query.order_by(ExpenseTransaction.transaction_date.desc()).all()
        return jsonify([txn.to_dict() for txn in transactions])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/expenses/transactions', methods=['POST'])
@api_login_required
def add_expense_transaction():
    """Add expense transaction"""
    try:
        data = request.json
        
        required_fields = ['category', 'amount', 'transaction_date']
        for field in required_fields:
            if not data or field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        txn_date = datetime.strptime(data['transaction_date'], '%Y-%m-%d').date()
        
        transaction = ExpenseTransaction(
            category=data['category'],
            subcategory=data.get('subcategory'),
            amount=float(data['amount']),
            transaction_date=txn_date,
            payment_method=data.get('payment_method'),
            is_recurring=data.get('is_recurring', False),
            description=data.get('description'),
            notes=data.get('notes')
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        return jsonify(transaction.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/expenses/transactions/<int:txn_id>', methods=['PUT'])
@api_login_required
def update_expense_transaction(txn_id):
    """Update expense transaction"""
    try:
        transaction = ExpenseTransaction.query.get_or_404(txn_id)
        data = request.json
        
        if data.get('category'):
            transaction.category = data['category']
        if 'subcategory' in data:
            transaction.subcategory = data['subcategory']
        if data.get('amount') is not None:
            transaction.amount = float(data['amount'])
        if data.get('transaction_date'):
            transaction.transaction_date = datetime.strptime(data['transaction_date'], '%Y-%m-%d').date()
        if 'payment_method' in data:
            transaction.payment_method = data['payment_method']
        if 'is_recurring' in data:
            transaction.is_recurring = data['is_recurring']
        if 'description' in data:
            transaction.description = data['description']
        if 'notes' in data:
            transaction.notes = data['notes']
        
        db.session.commit()
        return jsonify(transaction.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/expenses/transactions/<int:txn_id>', methods=['DELETE'])
@api_login_required
def delete_expense_transaction(txn_id):
    """Delete expense transaction"""
    try:
        transaction = ExpenseTransaction.query.get_or_404(txn_id)
        db.session.delete(transaction)
        db.session.commit()
        return jsonify({'message': 'Transaction deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/expenses/summary', methods=['GET'])
@api_login_required
def get_expense_summary():
    """Get expense summary (monthly/yearly)"""
    try:
        transactions = ExpenseTransaction.query.all()
        total_expense = sum(txn.amount for txn in transactions)
        
        # Group by category
        by_category = {}
        for txn in transactions:
            category = txn.category
            if category not in by_category:
                by_category[category] = 0
            by_category[category] += txn.amount
        
        return jsonify({
            'total_expense': total_expense,
            'by_category': by_category,
            'transaction_count': len(transactions)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/expenses/categories', methods=['GET'])
@api_login_required
def get_expense_by_category():
    """Get expense breakdown by category"""
    try:
        transactions = ExpenseTransaction.query.all()
        
        by_category = {}
        for txn in transactions:
            category = txn.category
            if category not in by_category:
                by_category[category] = {'total': 0, 'count': 0}
            by_category[category]['total'] += txn.amount
            by_category[category]['count'] += 1
        
        return jsonify(by_category)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/expenses/trends', methods=['GET'])
@api_login_required
def get_expense_trends():
    """Get monthly expense trends"""
    try:
        from utils.cash_flow import get_expense_trends
        
        transactions = ExpenseTransaction.query.all()
        trends = get_expense_trends(transactions, months=12)
        
        return jsonify(trends)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Budget Routes
@app.route('/api/budgets', methods=['GET'])
@api_login_required
def get_budgets():
    """Get all budgets"""
    try:
        budgets = Budget.query.all()
        return jsonify([budget.to_dict() for budget in budgets])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/budgets', methods=['POST'])
@api_login_required
def add_budget():
    """Create new budget"""
    try:
        data = request.json
        
        if not data or not data.get('category'):
            return jsonify({'error': 'Category is required'}), 400
        
        start_date = None
        end_date = None
        if data.get('start_date'):
            start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        if data.get('end_date'):
            end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        
        budget = Budget(
            category=data['category'],
            monthly_limit=data.get('monthly_limit'),
            annual_limit=data.get('annual_limit'),
            start_date=start_date,
            end_date=end_date,
            is_active=data.get('is_active', True),
            notes=data.get('notes')
        )
        
        db.session.add(budget)
        db.session.commit()
        
        return jsonify(budget.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/budgets/<int:budget_id>', methods=['PUT'])
@api_login_required
def update_budget(budget_id):
    """Update budget"""
    try:
        budget = Budget.query.get_or_404(budget_id)
        data = request.json
        
        if data.get('category'):
            budget.category = data['category']
        if data.get('monthly_limit') is not None:
            budget.monthly_limit = float(data['monthly_limit'])
        if data.get('annual_limit') is not None:
            budget.annual_limit = float(data['annual_limit'])
        if data.get('start_date'):
            budget.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        if data.get('end_date'):
            budget.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        if 'is_active' in data:
            budget.is_active = data['is_active']
        if 'notes' in data:
            budget.notes = data['notes']
        
        db.session.commit()
        return jsonify(budget.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/budgets/<int:budget_id>', methods=['DELETE'])
@api_login_required
def delete_budget(budget_id):
    """Delete budget"""
    try:
        budget = Budget.query.get_or_404(budget_id)
        db.session.delete(budget)
        db.session.commit()
        return jsonify({'message': 'Budget deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/budgets/status', methods=['GET'])
@api_login_required
def get_budget_status():
    """Get budget vs actual comparison"""
    try:
        budgets = Budget.query.filter_by(is_active=True).all()
        expenses = ExpenseTransaction.query.all()
        
        # Get current month expenses
        from datetime import date
        today = date.today()
        current_month_expenses = [e for e in expenses if e.transaction_date.month == today.month and e.transaction_date.year == today.year]
        
        # Group expenses by category
        expenses_by_category = {}
        for expense in current_month_expenses:
            cat = expense.category
            if cat not in expenses_by_category:
                expenses_by_category[cat] = 0
            expenses_by_category[cat] += expense.amount
        
        # Compare with budgets
        budget_status = []
        for budget in budgets:
            actual = expenses_by_category.get(budget.category, 0)
            limit = budget.monthly_limit or 0
            
            percentage = (actual / limit * 100) if limit > 0 else 0
            status = 'over' if actual > limit else ('warning' if percentage >= 80 else 'ok')
            
            budget_status.append({
                'category': budget.category,
                'limit': limit,
                'actual': actual,
                'remaining': limit - actual,
                'percentage': round(percentage, 2),
                'status': status
            })
        
        return jsonify(budget_status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Dashboard Routes
@app.route('/api/dashboard/net-worth', methods=['GET'])
@api_login_required
def get_net_worth():
    """Get total net worth across all assets"""
    try:
        from utils.net_worth import calculate_total_net_worth
        
        # Get all assets
        all_assets = {
            'stocks': PortfolioTransaction.query.all(),
            'mutual_funds': MutualFundTransaction.query.all(),
            'fixed_deposits': FixedDeposit.query.all(),
            'epf': EPFAccount.query.all(),
            'nps': NPSAccount.query.all(),
            'savings': SavingsAccount.query.all(),
            'lending': LendingRecord.query.filter_by(status='active').all(),
            'other': OtherInvestment.query.all()
        }
        
        net_worth_data = calculate_total_net_worth(all_assets)
        
        return jsonify(net_worth_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/dashboard/asset-allocation', methods=['GET'])
@api_login_required
def get_asset_allocation():
    """Get asset allocation (equity/debt/cash/other)"""
    try:
        from utils.net_worth import get_asset_allocation
        
        all_assets = {
            'stocks': PortfolioTransaction.query.all(),
            'mutual_funds': MutualFundTransaction.query.all(),
            'fixed_deposits': FixedDeposit.query.all(),
            'epf': EPFAccount.query.all(),
            'nps': NPSAccount.query.all(),
            'savings': SavingsAccount.query.all(),
            'lending': LendingRecord.query.filter_by(status='active').all(),
            'other': OtherInvestment.query.all()
        }
        
        allocation = get_asset_allocation(all_assets)
        
        return jsonify(allocation)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/dashboard/cash-flow', methods=['GET'])
@api_login_required
def get_cash_flow():
    """Get income vs expenses (monthly)"""
    try:
        from utils.cash_flow import calculate_monthly_cash_flow
        
        income = IncomeTransaction.query.all()
        expenses = ExpenseTransaction.query.all()
        
        # Get date range (last 12 months)
        from datetime import date, timedelta
        end_date = date.today()
        start_date = end_date - timedelta(days=365)
        
        cash_flow = calculate_monthly_cash_flow(income, expenses, start_date, end_date)
        
        return jsonify(cash_flow)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/dashboard/summary', methods=['GET'])
@api_login_required
def get_dashboard_summary():
    """Get unified dashboard summary"""
    try:
        # Count holdings across all assets
        stock_holdings = len([h for h in calculate_holdings(PortfolioTransaction.query.all()).values() if h['quantity'] > 0])
        mf_count = MutualFund.query.count()
        fd_count = FixedDeposit.query.filter_by(status='active').count()
        savings_count = SavingsAccount.query.count()
        
        # Calculate total invested
        stock_invested = sum(h['invested_amount'] for h in calculate_holdings(PortfolioTransaction.query.all()).values())
        fd_invested = sum(fd.principal_amount for fd in FixedDeposit.query.filter_by(status='active').all())
        epf_balance = sum(acc.current_balance for acc in EPFAccount.query.all())
        nps_value = sum(acc.current_value for acc in NPSAccount.query.all())
        savings_balance = sum(acc.current_balance for acc in SavingsAccount.query.all())
        
        total_invested = stock_invested + fd_invested + epf_balance + nps_value + savings_balance
        
        return jsonify({
            'total_holdings': stock_holdings + mf_count + fd_count + savings_count,
            'stock_holdings': stock_holdings,
            'mf_holdings': mf_count,
            'fd_count': fd_count,
            'savings_accounts': savings_count,
            'total_invested': round(total_invested, 2)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/dashboard/unified-xirr', methods=['GET'])
@api_login_required
def get_unified_xirr():
    """Get unified XIRR across all asset types (Phase 3)"""
    try:
        from utils import calculate_unified_portfolio_xirr
        
        # Gather all assets
        all_assets = {
            'stocks': PortfolioTransaction.query.all(),
            'mutual_funds': MutualFundTransaction.query.all(),
            'fixed_deposits': FixedDeposit.query.all(),
            'epf': EPFAccount.query.all(),
            'nps': NPSAccount.query.all(),
            'savings': SavingsAccount.query.all(),
            'lending': LendingRecord.query.filter_by(status='active').all(),
            'other': OtherInvestment.query.all()
        }
        
        xirr_data = calculate_unified_portfolio_xirr(all_assets)
        
        return jsonify(xirr_data)
    except Exception as e:
        print(f"ERROR in get_unified_xirr: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# Global Settings Routes
@app.route('/api/settings/global', methods=['GET'])
@api_login_required
def get_global_settings():
    """Get global settings"""
    try:
        settings = GlobalSettings.query.first()
        if not settings:
            # Create default settings
            settings = GlobalSettings()
            db.session.add(settings)
            db.session.commit()
        
        return jsonify(settings.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/settings/global', methods=['PUT'])
@api_login_required
def update_global_settings():
    """Update global settings"""
    try:
        settings = GlobalSettings.query.first()
        if not settings:
            settings = GlobalSettings()
            db.session.add(settings)
        
        data = request.json
        
        if data.get('max_equity_allocation_pct') is not None:
            settings.max_equity_allocation_pct = float(data['max_equity_allocation_pct'])
        if data.get('max_debt_allocation_pct') is not None:
            settings.max_debt_allocation_pct = float(data['max_debt_allocation_pct'])
        if data.get('min_emergency_fund_months') is not None:
            settings.min_emergency_fund_months = int(data['min_emergency_fund_months'])
        if data.get('monthly_income_target') is not None:
            settings.monthly_income_target = float(data['monthly_income_target'])
        if data.get('monthly_expense_target') is not None:
            settings.monthly_expense_target = float(data['monthly_expense_target'])
        if data.get('currency'):
            settings.currency = data['currency']
        
        settings.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        return jsonify(settings.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)

