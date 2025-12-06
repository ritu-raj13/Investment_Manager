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
import json
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
    auto_backup_on_startup
)
from services import get_nse_price, get_scraped_price, get_stock_details
from services.mf_api import fetch_mf_nav_by_name, fetch_mf_nav, get_mf_scheme_details

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
    buy_step = db.Column(db.Integer, nullable=True)  # 1, 2, or 3 for multi-step buying
    sell_step = db.Column(db.Integer, nullable=True)  # 1 or 2 for multi-step selling
    avg_price_after = db.Column(db.Float, nullable=True)  # Average price after this transaction
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
            'buy_step': self.buy_step,
            'sell_step': self.sell_step,
            'avg_price_after': self.avg_price_after,
            'transaction_date': self.transaction_date.isoformat(),
            'reason': self.reason,
            'notes': self.notes,
            'created_at': self.created_at.isoformat()
        }


class PortfolioSettings(db.Model):
    __tablename__ = 'portfolio_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    projected_portfolio_amount = db.Column(db.Float, default=0.0)  # Projected portfolio target amount for % calculation
    target_date = db.Column(db.Date, nullable=True)  # Target date for projected portfolio amount
    
    # Per-stock allocation limits (% of projected portfolio per individual stock)
    max_large_cap_pct = db.Column(db.Float, default=5.0)  # Max % per stock for Large Cap (actual: 5%, display: 5.5%)
    max_mid_cap_pct = db.Column(db.Float, default=3.0)  # Max % per stock for Mid Cap (actual: 3%, display: 3.5%)
    max_small_cap_pct = db.Column(db.Float, default=2.5)  # Max % per stock for Small Cap (actual: 2.5%, display: 3%)
    max_micro_cap_pct = db.Column(db.Float, default=2.0)  # Max % per stock for Micro Cap (actual: 2%, display: 2.5%)
    
    # Market cap stock count limits (max number of stocks per market cap category)
    max_large_cap_stocks = db.Column(db.Integer, default=15)  # Max stocks in Large Cap
    max_mid_cap_stocks = db.Column(db.Integer, default=8)  # Max stocks in Mid Cap
    max_small_cap_stocks = db.Column(db.Integer, default=7)  # Max stocks in Small Cap
    max_micro_cap_stocks = db.Column(db.Integer, default=3)  # Max stocks in Micro Cap
    
    # Market cap portfolio allocation limits (total % of portfolio per market cap category)
    max_large_cap_portfolio_pct = db.Column(db.Float, default=50.0)  # Max total % in Large Cap
    max_mid_cap_portfolio_pct = db.Column(db.Float, default=30.0)  # Max total % in Mid Cap
    max_small_cap_portfolio_pct = db.Column(db.Float, default=25.0)  # Max total % in Small Cap
    max_micro_cap_portfolio_pct = db.Column(db.Float, default=10.0)  # Max total % in Micro Cap
    
    # Overall limits
    max_stocks_per_sector = db.Column(db.Integer, default=2)  # Max number of stocks per parent sector
    max_total_stocks = db.Column(db.Integer, default=30)  # Max total stocks in portfolio
    
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    def to_dict(self):
        return {
            'id': self.id,
            'projected_portfolio_amount': self.projected_portfolio_amount,
            'target_date': self.target_date.isoformat() if self.target_date else None,
            # Per-stock limits
            'max_large_cap_pct': self.max_large_cap_pct,
            'max_mid_cap_pct': self.max_mid_cap_pct,
            'max_small_cap_pct': self.max_small_cap_pct,
            'max_micro_cap_pct': self.max_micro_cap_pct,
            # Stock count limits per market cap
            'max_large_cap_stocks': self.max_large_cap_stocks,
            'max_mid_cap_stocks': self.max_mid_cap_stocks,
            'max_small_cap_stocks': self.max_small_cap_stocks,
            'max_micro_cap_stocks': self.max_micro_cap_stocks,
            # Portfolio % limits per market cap
            'max_large_cap_portfolio_pct': self.max_large_cap_portfolio_pct,
            'max_mid_cap_portfolio_pct': self.max_mid_cap_portfolio_pct,
            'max_small_cap_portfolio_pct': self.max_small_cap_portfolio_pct,
            'max_micro_cap_portfolio_pct': self.max_micro_cap_portfolio_pct,
            # Overall limits
            'max_stocks_per_sector': self.max_stocks_per_sector,
            'max_total_stocks': self.max_total_stocks,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class ParentSectorMapping(db.Model):
    __tablename__ = 'parent_sector_mappings'
    
    id = db.Column(db.Integer, primary_key=True)
    sector_name = db.Column(db.String(100), nullable=False, unique=True, index=True)  # Child sector (e.g., "Auto Components")
    parent_sector = db.Column(db.String(100), nullable=False, index=True)  # Parent sector (e.g., "Auto")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    def to_dict(self):
        return {
            'id': self.id,
            'sector_name': self.sector_name,
            'parent_sector': self.parent_sector,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# ============================================================================
# Personal Finance Models - Multi-Asset Tracking
# ============================================================================

class MutualFund(db.Model):
    __tablename__ = 'mutual_funds'
    
    id = db.Column(db.Integer, primary_key=True)
    scheme_code = db.Column(db.String(20), unique=True, nullable=True)
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
            'name': self.scheme_name,  # Frontend expects 'name'
            'fund_house': self.fund_house,
            'amc': self.fund_house,  # Frontend expects 'amc'
            'category': self.category,
            'sub_category': self.sub_category,
            'current_nav': self.current_nav,
            'nav': self.current_nav,  # Frontend expects 'nav'
            'day_change_pct': self.day_change_pct,
            'expense_ratio': self.expense_ratio,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'notes': self.notes
        }


class MutualFundTransaction(db.Model):
    __tablename__ = 'mutual_fund_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    scheme_id = db.Column(db.Integer)  # Link to MutualFund table
    scheme_code = db.Column(db.String(20))
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
            'scheme_id': self.scheme_id,  # Frontend needs this
            'scheme_code': self.scheme_code,
            'scheme_name': self.scheme_name,
            'transaction_type': self.transaction_type,
            'units': self.units,
            'nav': self.nav,
            'amount': self.amount,
            'transaction_date': self.transaction_date.strftime('%Y-%m-%d') if self.transaction_date else None,  # Backend format
            'date': self.transaction_date.strftime('%Y-%m-%d') if self.transaction_date else None,  # Frontend format
            'is_sip': self.is_sip,
            'sip_id': self.sip_id,
            'reason': self.reason,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
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


class KnowledgeDocument(db.Model):
    __tablename__ = 'knowledge_documents'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)  # Size in bytes
    total_pages = db.Column(db.Integer)
    version = db.Column(db.Integer, default=1)
    status = db.Column(db.String(50), default='processing')  # processing, organized, ready
    upload_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_updated = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    notes = db.Column(db.Text)
    
    # Relationships
    sections = db.relationship('KnowledgeSection', backref='document', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'total_pages': self.total_pages,
            'version': self.version,
            'status': self.status,
            'upload_date': self.upload_date.isoformat() if self.upload_date else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'notes': self.notes,
            'sections_count': len(self.sections) if self.sections else 0
        }


class KnowledgeBook(db.Model):
    __tablename__ = 'knowledge_books'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationship
    sections = db.relationship('KnowledgeSection', backref='book', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'section_count': len(self.sections) if self.sections else 0
        }


class KnowledgeSection(db.Model):
    __tablename__ = 'knowledge_sections'
    
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('knowledge_documents.id'), nullable=True)
    book_id = db.Column(db.Integer, db.ForeignKey('knowledge_books.id'), nullable=True)
    parent_section_id = db.Column(db.Integer, db.ForeignKey('knowledge_sections.id'), nullable=True)
    
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    content_markdown = db.Column(db.Text)  # Markdown version for editing
    page_numbers = db.Column(db.String(100))  # e.g., "5,12,23" for pages where this topic appears
    section_order = db.Column(db.Integer, default=0)
    section_type = db.Column(db.String(50), default='section')  # 'chapter', 'section', 'subsection'
    section_metadata = db.Column(db.Text)  # JSON string for additional metadata
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    images = db.relationship('KnowledgeSectionImage', backref='section', lazy=True, cascade='all, delete-orphan')
    subsections = db.relationship('KnowledgeSection', backref=db.backref('parent_section', remote_side=[id]), lazy=True)
    
    def to_dict(self, include_images=False, include_subsections=False):
        result = {
            'id': self.id,
            'document_id': self.document_id,
            'book_id': self.book_id,
            'parent_section_id': self.parent_section_id,
            'title': self.title,
            'content': self.content,
            'content_markdown': self.content_markdown,
            'page_numbers': self.page_numbers,
            'section_order': self.section_order,
            'section_type': self.section_type,
            'metadata': self.section_metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_images and self.images:
            result['images'] = [img.to_dict() for img in self.images]
        
        if include_subsections and self.subsections:
            result['subsections'] = [sub.to_dict() for sub in self.subsections]
        
        return result


class KnowledgeSectionImage(db.Model):
    __tablename__ = 'knowledge_section_images'
    
    id = db.Column(db.Integer, primary_key=True)
    section_id = db.Column(db.Integer, db.ForeignKey('knowledge_sections.id'), nullable=False)
    image_path = db.Column(db.String(500), nullable=False)
    caption = db.Column(db.String(500))
    position = db.Column(db.Integer, default=0)  # Order within section
    source_page = db.Column(db.Integer)  # Original PDF page number
    width = db.Column(db.Integer)
    height = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    def to_dict(self):
        return {
            'id': self.id,
            'section_id': self.section_id,
            'image_path': self.image_path,
            'caption': self.caption,
            'position': self.position,
            'source_page': self.source_page,
            'width': self.width,
            'height': self.height,
            'created_at': self.created_at.isoformat()
        }


class ContentOrganizationProposal(db.Model):
    __tablename__ = 'content_organization_proposals'
    
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('knowledge_documents.id'), nullable=False)
    proposal_type = db.Column(db.String(50), nullable=False)  # 'merge', 'split', 'reorganize'
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    affected_pages = db.Column(db.String(200))  # Pages affected by this proposal
    proposed_content = db.Column(db.Text)  # JSON string with the proposed changes
    status = db.Column(db.String(50), default='pending')  # pending, approved, rejected
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    reviewed_at = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'document_id': self.document_id,
            'proposal_type': self.proposal_type,
            'title': self.title,
            'description': self.description,
            'affected_pages': self.affected_pages,
            'proposed_content': self.proposed_content,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None
        }


class ChatHistory(db.Model):
    __tablename__ = 'chat_history'
    
    id = db.Column(db.Integer, primary_key=True)
    query = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    sources = db.Column(db.Text)  # JSON string with source references
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    response_time = db.Column(db.Float)  # Time taken to generate response in seconds
    
    def to_dict(self):
        return {
            'id': self.id,
            'query': self.query,
            'response': self.response,
            'sources': self.sources,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'response_time': self.response_time
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
                ticker = yf.Ticker(stock.symbol)
                info = ticker.history(period='1d')
                if not info.empty:
                    stock.current_price = round(info['Close'].iloc[-1], 2)
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
# Parent Sector Mapping Routes (Auth required)
# ============================================================================

@app.route('/api/sectors/parent-mappings', methods=['GET'])
@api_login_required
def get_parent_sector_mappings():
    """Get all parent sector mappings"""
    mappings = ParentSectorMapping.query.order_by(ParentSectorMapping.parent_sector, ParentSectorMapping.sector_name).all()
    return jsonify([m.to_dict() for m in mappings])


@app.route('/api/sectors/parent-mappings', methods=['POST'])
@api_login_required
def create_parent_sector_mapping():
    """Create or update a parent sector mapping"""
    data = request.json
    
    sector_name = data.get('sector_name', '').strip()
    parent_sector = data.get('parent_sector', '').strip()
    
    if not sector_name or not parent_sector:
        return jsonify({'error': 'sector_name and parent_sector are required'}), 400
    
    # Check if mapping already exists
    existing = ParentSectorMapping.query.filter_by(sector_name=sector_name).first()
    
    if existing:
        # Update existing mapping
        existing.parent_sector = parent_sector
        existing.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        return jsonify(existing.to_dict())
    else:
        # Create new mapping
        mapping = ParentSectorMapping(
            sector_name=sector_name,
            parent_sector=parent_sector
        )
        db.session.add(mapping)
        db.session.commit()
        return jsonify(mapping.to_dict()), 201


@app.route('/api/sectors/parent-mappings/<int:mapping_id>', methods=['DELETE'])
@api_login_required
def delete_parent_sector_mapping(mapping_id):
    """Delete a parent sector mapping"""
    mapping = ParentSectorMapping.query.get_or_404(mapping_id)
    db.session.delete(mapping)
    db.session.commit()
    return jsonify({'message': 'Parent sector mapping deleted successfully'})


@app.route('/api/sectors/parent/<parent_name>/stocks', methods=['GET'])
@api_login_required
def get_stocks_by_parent_sector(parent_name):
    """Get all stocks belonging to a parent sector"""
    # Get all child sectors for this parent
    mappings = ParentSectorMapping.query.filter_by(parent_sector=parent_name).all()
    child_sectors = [m.sector_name for m in mappings]
    
    # Also include stocks with the exact parent sector name
    child_sectors.append(parent_name)
    
    # Get stocks in these sectors
    stocks = Stock.query.filter(Stock.sector.in_(child_sectors)).all()
    return jsonify([s.to_dict() for s in stocks])


@app.route('/api/sectors/parent-list', methods=['GET'])
@api_login_required
def get_parent_sectors_list():
    """Get list of unique parent sectors"""
    parents = db.session.query(ParentSectorMapping.parent_sector).distinct().all()
    return jsonify([p[0] for p in parents if p[0]])


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
    
    # Validate buy/sell steps if provided
    buy_step = data.get('buy_step')
    sell_step = data.get('sell_step')
    
    # Handle empty strings and None
    if buy_step is not None and buy_step != '':
        try:
            buy_step = int(buy_step)
            if buy_step < 1 or buy_step > 3:
                return jsonify({'error': 'buy_step must be between 1 and 3'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'buy_step must be a valid number'}), 400
    else:
        buy_step = None
    
    if sell_step is not None and sell_step != '':
        try:
            sell_step = int(sell_step)
            if sell_step < 1 or sell_step > 2:
                return jsonify({'error': 'sell_step must be between 1 and 2'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'sell_step must be a valid number'}), 400
    else:
        sell_step = None
    
    # Calculate average price after this transaction (for BUY transactions)
    avg_price_after = None
    if data['transaction_type'].upper() == 'BUY':
        symbol = clean_symbol(data['stock_symbol'])
        # Get all previous BUY transactions for this stock
        previous_buys = PortfolioTransaction.query.filter_by(
            stock_symbol=symbol,
            transaction_type='BUY'
        ).all()
        
        total_qty = float(data['quantity'])
        total_value = float(data['quantity']) * float(data['price'])
        
        for prev_tx in previous_buys:
            total_qty += prev_tx.quantity
            total_value += prev_tx.quantity * prev_tx.price
        
        if total_qty > 0:
            avg_price_after = total_value / total_qty
    
    # Create transaction
    transaction = PortfolioTransaction(
        stock_symbol=clean_symbol(data['stock_symbol']),
        stock_name=data['stock_name'].strip(),
        transaction_type=data['transaction_type'].upper(),
        quantity=float(data['quantity']),
        price=float(data['price']),
        buy_step=buy_step,
        sell_step=sell_step,
        avg_price_after=avg_price_after,
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
    
    # Update buy/sell steps if provided
    if 'buy_step' in data:
        buy_step = data['buy_step']
        if buy_step is not None and buy_step != '':
            try:
                buy_step = int(buy_step)
                if buy_step < 1 or buy_step > 3:
                    return jsonify({'error': 'buy_step must be between 1 and 3'}), 400
            except (ValueError, TypeError):
                return jsonify({'error': 'buy_step must be a valid number'}), 400
        else:
            buy_step = None
        transaction.buy_step = buy_step
    
    if 'sell_step' in data:
        sell_step = data['sell_step']
        if sell_step is not None and sell_step != '':
            try:
                sell_step = int(sell_step)
                if sell_step < 1 or sell_step > 2:
                    return jsonify({'error': 'sell_step must be between 1 and 2'}), 400
            except (ValueError, TypeError):
                return jsonify({'error': 'sell_step must be a valid number'}), 400
        else:
            sell_step = None
        transaction.sell_step = sell_step
    
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
    """Get portfolio settings (projected portfolio amount for % calculation)"""
    settings = PortfolioSettings.query.first()
    if not settings:
        # Create default settings if none exist
        settings = PortfolioSettings(projected_portfolio_amount=0.0)
        db.session.add(settings)
        db.session.commit()
    return jsonify(settings.to_dict())


@app.route('/api/portfolio/settings', methods=['PUT'])
@api_login_required
def update_portfolio_settings():
    """Update portfolio settings (projected portfolio amount and allocation thresholds)"""
    data = request.get_json()
    settings = PortfolioSettings.query.first()
    
    if not settings:
        settings = PortfolioSettings()
        db.session.add(settings)
    
    # Update all configurable fields
    if 'projected_portfolio_amount' in data:
        settings.projected_portfolio_amount = float(data['projected_portfolio_amount'])
    # Support old field name for backward compatibility
    if 'total_amount' in data:
        settings.projected_portfolio_amount = float(data['total_amount'])
    
    if 'target_date' in data:
        if data['target_date']:
            # Parse date string to date object
            from datetime import date
            if isinstance(data['target_date'], str):
                settings.target_date = date.fromisoformat(data['target_date'])
            else:
                settings.target_date = data['target_date']
        else:
            settings.target_date = None
    
    if 'max_large_cap_pct' in data:
        settings.max_large_cap_pct = float(data['max_large_cap_pct'])
    if 'max_mid_cap_pct' in data:
        settings.max_mid_cap_pct = float(data['max_mid_cap_pct'])
    if 'max_small_cap_pct' in data:
        settings.max_small_cap_pct = float(data['max_small_cap_pct'])
    if 'max_micro_cap_pct' in data:
        settings.max_micro_cap_pct = float(data['max_micro_cap_pct'])
    
    # Stock count limits per market cap
    if 'max_large_cap_stocks' in data:
        settings.max_large_cap_stocks = int(data['max_large_cap_stocks'])
    if 'max_mid_cap_stocks' in data:
        settings.max_mid_cap_stocks = int(data['max_mid_cap_stocks'])
    if 'max_small_cap_stocks' in data:
        settings.max_small_cap_stocks = int(data['max_small_cap_stocks'])
    if 'max_micro_cap_stocks' in data:
        settings.max_micro_cap_stocks = int(data['max_micro_cap_stocks'])
    
    # Portfolio % limits per market cap
    if 'max_large_cap_portfolio_pct' in data:
        settings.max_large_cap_portfolio_pct = float(data['max_large_cap_portfolio_pct'])
    if 'max_mid_cap_portfolio_pct' in data:
        settings.max_mid_cap_portfolio_pct = float(data['max_mid_cap_portfolio_pct'])
    if 'max_small_cap_portfolio_pct' in data:
        settings.max_small_cap_portfolio_pct = float(data['max_small_cap_portfolio_pct'])
    if 'max_micro_cap_portfolio_pct' in data:
        settings.max_micro_cap_portfolio_pct = float(data['max_micro_cap_portfolio_pct'])
    
    # Overall limits
    if 'max_stocks_per_sector' in data:
        settings.max_stocks_per_sector = int(data['max_stocks_per_sector'])
    if 'max_total_stocks' in data:
        settings.max_total_stocks = int(data['max_total_stocks'])
    
    settings.updated_at = datetime.now(timezone.utc)
    
    db.session.commit()
    return jsonify(settings.to_dict())


# Initialize database tables on startup
with app.app_context():
    db.create_all()


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
        total_current_value = 0
        
        for symbol, holding in holdings_dict.items():
            if holding['quantity'] > 0:
                normalized_symbol = symbol.replace('.NS', '').replace('.BO', '').upper()
                stock = stocks_map.get(normalized_symbol)
                
                current_value = (holding['quantity'] * stock.current_price) if (stock and stock.current_price) else 0
                
                holdings_list.append({
                    'symbol': symbol,
                    'name': stock.name if stock else '',
                    'sector': stock.sector if stock else None,
                    'market_cap': stock.market_cap if stock else None,
                    'invested_amount': holding['invested_amount'],
                    'quantity': holding['quantity'],
                    'current_price': stock.current_price if stock else None,
                    'current_value': current_value
                })
                
                total_invested += holding['invested_amount']
                total_current_value += current_value
        
        # Get portfolio settings for thresholds and total amount
        settings = PortfolioSettings.query.first()
        
        # Use settings.projected_portfolio_amount for percentage calculations (same as Holdings screen)
        # This ensures % of Total matches between Holdings and Recommendations
        total_target_amount = settings.projected_portfolio_amount if settings and settings.projected_portfolio_amount > 0 else total_current_value
        
        # Get parent sector mappings
        parent_mappings_list = ParentSectorMapping.query.all()
        parent_sector_mappings = {m.sector_name: m.parent_sector for m in parent_mappings_list}
        
        # Get rebalancing suggestions
        from utils import get_rebalancing_suggestions
        rebalancing = get_rebalancing_suggestions(holdings_list, stocks, total_target_amount, settings, parent_sector_mappings)
        
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
        
        # Map frontend field names to backend field names
        # Use 'name' from frontend, fallback to 'scheme_name'
        scheme_name = data.get('name') if 'name' in data else data.get('scheme_name')
        if scheme_name == '':
            scheme_name = None
        
        scheme_code = data.get('scheme_code')
        if scheme_code == '':
            scheme_code = None
            
        fund_house = data.get('amc') if 'amc' in data else data.get('fund_house')
        if fund_house == '':
            fund_house = None
        
        # Handle numeric fields - convert empty strings to None
        current_nav = data.get('nav') if 'nav' in data else data.get('current_nav')
        if current_nav == '' or current_nav is None:
            current_nav = None
        else:
            current_nav = float(current_nav)
        
        expense_ratio = data.get('expense_ratio')
        if expense_ratio == '' or expense_ratio is None:
            expense_ratio = None
        else:
            expense_ratio = float(expense_ratio)
        
        # Auto-fetch NAV by scheme name if NAV is missing
        if scheme_name and not current_nav:
            try:
                nav_data = fetch_mf_nav_by_name(scheme_name)
                if nav_data:
                    if not current_nav and nav_data.get('nav'):
                        current_nav = float(nav_data['nav'])
                    print(f"[OK] Auto-fetched NAV for {scheme_name}: Rs.{current_nav}")
            except Exception as e:
                print(f"[WARN] Could not auto-fetch NAV: {str(e)}")
        
        if not data or not scheme_name:
            return jsonify({'error': 'Scheme name is required'}), 400
        
        # Check if scheme already exists by name
        existing = MutualFund.query.filter_by(scheme_name=scheme_name).first()
        if existing:
            return jsonify({'error': 'Scheme with this name already exists'}), 400
        
        scheme = MutualFund(
            scheme_code=scheme_code,
            scheme_name=scheme_name,
            fund_house=fund_house,
            category=data.get('category') if data.get('category') else None,
            sub_category=data.get('sub_category') if data.get('sub_category') else None,
            current_nav=current_nav,
            expense_ratio=expense_ratio,
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
        
        # Map frontend field names to backend field names
        scheme_name = data.get('name') if 'name' in data else data.get('scheme_name')
        if scheme_name == '':
            scheme_name = None
            
        fund_house = data.get('amc') if 'amc' in data else data.get('fund_house')
        if fund_house == '':
            fund_house = None
        
        if scheme_name:
            scheme.scheme_name = scheme_name
        if fund_house:
            scheme.fund_house = fund_house
        if 'category' in data:
            scheme.category = data['category']
        if 'sub_category' in data:
            scheme.sub_category = data['sub_category']
        
        # Handle numeric fields - convert empty strings to None
        if 'nav' in data or 'current_nav' in data:
            current_nav = data.get('nav') if 'nav' in data else data.get('current_nav')
            if current_nav == '' or current_nav is None:
                scheme.current_nav = None
            else:
                scheme.current_nav = float(current_nav)
        
        if 'day_change_pct' in data:
            day_change_pct = data.get('day_change_pct')
            if day_change_pct == '' or day_change_pct is None:
                scheme.day_change_pct = None
            else:
                scheme.day_change_pct = float(day_change_pct)
        
        if 'expense_ratio' in data:
            expense_ratio = data.get('expense_ratio')
            if expense_ratio == '' or expense_ratio is None:
                scheme.expense_ratio = None
            else:
                scheme.expense_ratio = float(expense_ratio)
        
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


@app.route('/api/mutual-funds/fetch-nav/<scheme_name>', methods=['GET'])
@api_login_required
def fetch_mutual_fund_nav_by_name(scheme_name):
    """
    Fetch current NAV by scheme name using web search
    """
    try:
        # Fetch NAV data by searching scheme name
        nav_data = fetch_mf_nav_by_name(scheme_name)
        
        if not nav_data or not nav_data.get('nav'):
            return jsonify({
                'error': 'Could not fetch NAV. Please enter manually.',
                'scheme_name': scheme_name
            }), 404
        
        return jsonify({
            'scheme_name': nav_data.get('scheme_name'),
            'nav': nav_data.get('nav'),
            'current_nav': nav_data.get('nav'),  # For frontend compatibility
            'date': nav_data.get('date'),
            'last_updated': nav_data.get('date'),
            'source': nav_data.get('source', 'Web Search')
        })
    
    except Exception as e:
        print(f"[ERROR] fetch_mutual_fund_nav_by_name failed: {str(e)}")
        return jsonify({
            'error': 'Failed to fetch NAV',
            'message': str(e)
        }), 500


@app.route('/api/mutual-funds/refresh-navs', methods=['POST'])
@api_login_required
def refresh_mutual_fund_navs():
    """
    Refresh NAVs for all tracked mutual fund schemes using scheme names
    """
    try:
        schemes = MutualFund.query.all()
        updated_count = 0
        failed_count = 0
        
        print(f"\n[REFRESH] Starting NAV refresh for {len(schemes)} schemes...")
        
        for scheme in schemes:
            try:
                old_nav = scheme.current_nav
                print(f"[REFRESH] Fetching NAV for: {scheme.scheme_name} (current: {old_nav})")
                
                # Fetch NAV by scheme name (not code)
                nav_data = fetch_mf_nav_by_name(scheme.scheme_name)
                if nav_data and nav_data.get('nav'):
                    new_nav = float(nav_data['nav'])
                    scheme.current_nav = new_nav
                    scheme.last_updated = datetime.now(timezone.utc)
                    
                    updated_count += 1
                    print(f"[REFRESH] ✓ Updated {scheme.scheme_name}: {old_nav} → {new_nav}")
                else:
                    failed_count += 1
                    print(f"[REFRESH] ✗ Could not fetch NAV for {scheme.scheme_name}")
            except Exception as e:
                failed_count += 1
                print(f"[REFRESH] ✗ Error for {scheme.scheme_name}: {str(e)}")
        
        db.session.commit()
        print(f"[REFRESH] Committed changes to database")
        
        return jsonify({
            'message': f'Updated {updated_count} of {len(schemes)} schemes',
            'updated_count': updated_count,
            'failed_count': failed_count,
            'total_count': len(schemes)
        })
    
    except Exception as e:
        db.session.rollback()
        print(f"[REFRESH] ✗ Error during refresh: {str(e)}")
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
        
        # Accept either scheme_id or scheme_code/scheme_name
        scheme_id = data.get('scheme_id')
        transaction_date = data.get('date') or data.get('transaction_date')
        
        # Required fields check
        if not data or not data.get('transaction_type') or not data.get('units') or not data.get('nav') or not data.get('amount') or not transaction_date:
            return jsonify({'error': 'transaction_type, units, nav, amount, and date are required'}), 400
        
        # If scheme_id is provided, look up the scheme
        if scheme_id:
            scheme = MutualFund.query.get(scheme_id)
            if not scheme:
                return jsonify({'error': 'Scheme not found'}), 404
            scheme_code = scheme.scheme_code or ''
            scheme_name = scheme.scheme_name
        else:
            # Fallback to old method (scheme_code and scheme_name directly)
            scheme_code = data.get('scheme_code', '')
            scheme_name = data.get('scheme_name')
            if not scheme_name:
                return jsonify({'error': 'scheme_id or scheme_name is required'}), 400
        
        # Parse transaction date
        try:
            if 'T' in transaction_date:
                txn_date = datetime.fromisoformat(transaction_date.replace('Z', '+00:00'))
            else:
                txn_date = datetime.strptime(transaction_date, '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400
        
        transaction = MutualFundTransaction(
            scheme_id=scheme_id if scheme_id else None,
            scheme_code=scheme_code,
            scheme_name=scheme_name,
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
        
        # Handle scheme_id - lookup scheme if provided
        if data.get('scheme_id'):
            scheme = MutualFund.query.get(data['scheme_id'])
            if scheme:
                transaction.scheme_id = data['scheme_id']
                transaction.scheme_code = scheme.scheme_code or ''
                transaction.scheme_name = scheme.scheme_name
        
        # Fallback to direct scheme_code/scheme_name
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
            
        # Handle date field (frontend sends 'date', backend stores 'transaction_date')
        date_value = data.get('date') or data.get('transaction_date')
        if date_value:
            if 'T' in date_value:
                transaction.transaction_date = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
            else:
                transaction.transaction_date = datetime.strptime(date_value, '%Y-%m-%d')
                
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
        
        from utils.mutual_funds import calculate_mf_holdings, calculate_mf_xirr
        holdings_dict = calculate_mf_holdings(transactions)
        
        # Get scheme details - create maps by both ID and code
        schemes = MutualFund.query.all()
        schemes_by_id = {scheme.id: scheme for scheme in schemes}
        schemes_by_code = {scheme.scheme_code: scheme for scheme in schemes if scheme.scheme_code}
        
        holdings_list = []
        total_invested = 0
        total_current_value = 0
        total_unrealized_pl = 0
        
        for key, holding in holdings_dict.items():
            if holding['units'] > 0:
                # Try to find scheme by ID first, then by code
                scheme = None
                scheme_id = holding.get('scheme_id')
                
                if scheme_id:
                    scheme = schemes_by_id.get(scheme_id)
                
                if not scheme and holding.get('scheme_code'):
                    scheme = schemes_by_code.get(holding['scheme_code'])
                
                # Calculate current value first
                current_value = (scheme.current_nav * holding['units']) if scheme and scheme.current_nav else 0
                invested_amount = holding['invested_amount']
                
                # Calculate XIRR for this holding
                scheme_transactions = [t for t in transactions if (t.scheme_id == scheme_id or t.scheme_name == holding['scheme_name'])]
                
                # Calculate XIRR with current value
                if scheme_transactions and current_value > 0:
                    from utils.xirr import xirr
                    from datetime import date
                    cash_flows = []
                    for txn in scheme_transactions:
                        txn_date = txn.transaction_date
                        if isinstance(txn_date, datetime):
                            txn_date = txn_date.date()
                        if txn.transaction_type == 'BUY':
                            cash_flows.append((txn_date, -txn.amount))
                        elif txn.transaction_type == 'SELL':
                            cash_flows.append((txn_date, txn.amount))
                    # Add current value as final inflow
                    cash_flows.append((date.today(), current_value))
                    try:
                        xirr_value = xirr(cash_flows)
                        if xirr_value is not None:
                            xirr_value = round(xirr_value * 100, 2)  # Convert to percentage and round to 2 decimals
                    except:
                        xirr_value = None
                else:
                    xirr_value = None
                unrealized_pl = current_value - invested_amount if current_value else 0
                return_percent = (unrealized_pl / invested_amount * 100) if invested_amount > 0 else 0
                
                total_invested += invested_amount
                total_current_value += current_value
                total_unrealized_pl += unrealized_pl
                
                holdings_list.append({
                    'id': len(holdings_list) + 1,  # Temporary ID for frontend
                    'scheme_id': scheme_id,
                    'scheme_code': holding.get('scheme_code', ''),
                    'scheme_name': holding['scheme_name'],
                    'category': scheme.category if scheme else None,
                    'units': holding['units'],
                    'avg_nav': invested_amount / holding['units'] if holding['units'] > 0 else 0,
                    'invested': invested_amount,
                    'invested_amount': invested_amount,
                    'current_nav': scheme.current_nav if scheme else None,
                    'current_value': current_value,
                    'realized_pnl': holding['realized_pnl'],
                    'unrealized_pl': unrealized_pl,
                    'return_percent': return_percent,
                    'xirr': xirr_value
                })
        
        # Calculate overall portfolio XIRR
        if transactions and total_current_value > 0:
            from utils.xirr import xirr
            from datetime import date
            cash_flows = []
            for txn in transactions:
                txn_date = txn.transaction_date
                if isinstance(txn_date, datetime):
                    txn_date = txn_date.date()
                if txn.transaction_type == 'BUY':
                    cash_flows.append((txn_date, -txn.amount))
                elif txn.transaction_type == 'SELL':
                    cash_flows.append((txn_date, txn.amount))
            # Add current portfolio value as final inflow
            cash_flows.append((date.today(), total_current_value))
            try:
                overall_xirr = xirr(cash_flows)
                if overall_xirr is not None:
                    overall_xirr = round(overall_xirr * 100, 2)  # Convert to percentage and round to 2 decimals
            except:
                overall_xirr = None
        else:
            overall_xirr = None
        
        return jsonify({
            'holdings': holdings_list,
            'summary': {
                'total_invested': round(total_invested, 2),
                'current_value': round(total_current_value, 2),
                'unrealized_pl': round(total_unrealized_pl, 2),
                'return_percent': round((total_unrealized_pl / total_invested * 100) if total_invested > 0 else 0, 2),
                'xirr': overall_xirr
            }
        })
    except Exception as e:
        print(f"ERROR in get_mutual_fund_holdings: {str(e)}")
        import traceback
        traceback.print_exc()
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


# ============================================================================
# Knowledge Base / Trading Notes Chatbot Routes
# ============================================================================

def _process_single_pdf(file, kb_service, skip_organization=False):
    """
    Process a single PDF file
    
    Args:
        file: File object from request
        kb_service: Knowledge base service instance
        skip_organization: If True, skip content organization (faster upload)
        
    Returns:
        Dict with processing results or error
    """
    filename = file.filename
    try:
        print(f"[INFO] Starting processing: {filename}")
        
        # Create document record
        doc = KnowledgeDocument(
            filename=secure_filename(filename),
            original_filename=filename,
            file_path='',
            status='uploading'
        )
        db.session.add(doc)
        db.session.commit()
        
        print(f"[INFO] Saving file: {filename}")
        # Save file
        try:
            file.seek(0)
        except:
            pass
        file_path = kb_service.save_uploaded_file(file, doc.id)
        
        # Update document with file info
        doc.file_path = file_path
        file_size = os.path.getsize(file_path)
        doc.file_size = file_size
        doc.status = 'extracting'
        db.session.commit()
        
        print(f"[INFO] Extracting text from: {filename}")
        # Extract text, images and metadata
        full_text, total_pages, pages_data = kb_service.extract_text_from_pdf(file_path, doc.id)
        doc.total_pages = total_pages
        doc.status = 'indexing'
        db.session.commit()
        
        print(f"[INFO] Chunking text: {filename}")
        # Chunk text
        chunks = kb_service.chunk_text(full_text, pages_data)
        
        print(f"[INFO] Adding to vector store: {filename}")
        # Add to vector store
        result = kb_service.add_to_vector_store(chunks, doc.id, doc.filename)
        
        if result['status'] != 'success':
            doc.status = 'error'
            db.session.commit()
            return {
                'status': 'error',
                'filename': filename,
                'document_id': doc.id,
                'message': result.get('message', 'Failed to index PDF')
            }
        
        # Update status to indexed
        doc.status = 'indexed'
        db.session.commit()
        
        print(f"[SUCCESS] Completed processing: {filename}")
        
        return {
            'status': 'success',
            'filename': filename,
            'document_id': doc.id,
            'total_pages': total_pages,
            'chunks_processed': result['chunks_added']
        }
        
    except Exception as e:
        error_msg = str(e)
        print(f"[ERROR] Failed processing {filename}: {error_msg}")
        db.session.rollback()
        return {
            'status': 'error',
            'filename': filename,
            'message': error_msg
        }


@app.route('/api/knowledge/upload', methods=['POST'])
@api_login_required
def upload_knowledge_pdf():
    """Upload single PDF for knowledge base"""
    try:
        from services.knowledge_base import get_knowledge_base_service
        from services.content_organizer import get_content_organizer
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'error': 'Only PDF files are allowed'}), 400
        
        kb_service = get_knowledge_base_service()
        
        result = _process_single_pdf(file, kb_service, skip_organization=False)
        
        if result['status'] == 'error':
            return jsonify({'error': result['message']}), 500
        
        return jsonify(result), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/knowledge/upload-multiple', methods=['POST'])
@api_login_required
def upload_multiple_pdfs():
    """Upload multiple PDFs and process them sequentially"""
    try:
        from services.knowledge_base import get_knowledge_base_service
        from services.content_organizer import get_content_organizer
        
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        
        if not files or len(files) == 0:
            return jsonify({'error': 'No files selected'}), 400
        
        # Validate all files are PDFs
        invalid_files = [f.filename for f in files if not f.filename.lower().endswith('.pdf')]
        if invalid_files:
            return jsonify({
                'error': f'Only PDF files are allowed. Invalid files: {", ".join(invalid_files)}'
            }), 400
        
        kb_service = get_knowledge_base_service()
        
        results = {
            'total_files': len(files),
            'successful': 0,
            'failed': 0,
            'results': []
        }
        
        print(f"\n[INFO] ========== Processing {len(files)} PDFs ==========")
        
        # Process each file sequentially (SKIP organization for now)
        for idx, file in enumerate(files, 1):
            if file.filename == '':
                continue
            
            print(f"\n[INFO] Processing file {idx}/{len(files)}: {file.filename}")
            
            try:
                # Reset file pointer before processing
                file.seek(0)
            except:
                pass
            
            result = _process_single_pdf(file, kb_service, skip_organization=True)
            results['results'].append(result)
            
            if result['status'] == 'success':
                results['successful'] += 1
                print(f"[SUCCESS] {idx}/{len(files)} completed: {file.filename}")
            else:
                results['failed'] += 1
                print(f"[ERROR] {idx}/{len(files)} failed: {file.filename} - {result.get('message', 'Unknown error')}")
        
        print(f"\n[INFO] ========== Upload Complete: {results['successful']} success, {results['failed']} failed ==========")
        
        # Overall status
        if results['successful'] == len(files):
            status_code = 201
            results['status'] = 'success'
            results['message'] = f'All {len(files)} PDFs processed successfully'
        elif results['successful'] > 0:
            status_code = 207  # Multi-Status
            results['status'] = 'partial'
            results['message'] = f'{results["successful"]} of {len(files)} PDFs processed successfully'
        else:
            status_code = 500
            results['status'] = 'error'
            results['message'] = 'All PDF processing failed'
        
        return jsonify(results), status_code
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/knowledge/documents', methods=['GET'])
@api_login_required
def get_knowledge_documents():
    """Get all uploaded knowledge documents"""
    try:
        documents = KnowledgeDocument.query.order_by(KnowledgeDocument.upload_date.desc()).all()
        return jsonify({
            'status': 'success',
            'documents': [doc.to_dict() for doc in documents],
            'total': len(documents)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/knowledge/documents/<int:doc_id>', methods=['DELETE'])
@api_login_required
def delete_knowledge_document(doc_id):
    """Delete a knowledge document"""
    try:
        from services.knowledge_base import get_knowledge_base_service
        
        doc = KnowledgeDocument.query.get_or_404(doc_id)
        
        # Delete from vector store
        kb_service = get_knowledge_base_service()
        kb_service.delete_document_from_store(doc_id)
        
        # Delete file
        if os.path.exists(doc.file_path):
            os.remove(doc.file_path)
        
        # Delete from database (cascade will delete sections and proposals)
        db.session.delete(doc)
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': 'Document deleted'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/knowledge/proposals', methods=['GET'])
@api_login_required
def get_organization_proposals():
    """Get pending organization proposals"""
    try:
        document_id = request.args.get('document_id', type=int)
        
        query = ContentOrganizationProposal.query
        if document_id:
            query = query.filter_by(document_id=document_id)
        
        proposals = query.filter_by(status='pending').order_by(
            ContentOrganizationProposal.created_at.desc()
        ).all()
        
        return jsonify([p.to_dict() for p in proposals])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/knowledge/proposals/generate', methods=['POST'])
@api_login_required
def generate_proposals_for_all():
    """Generate organization proposals for new/unorganized documents only"""
    try:
        from services.content_organizer import get_content_organizer
        from services.knowledge_base import get_knowledge_base_service
        
        print("\n[INFO] ========== Starting Proposal Generation ==========")
        
        kb_service = get_knowledge_base_service()
        organizer = get_content_organizer()
        
        # Get ONLY indexed documents (skip already organized ones)
        docs = KnowledgeDocument.query.filter_by(status='indexed').all()
        
        if not docs:
            print("[INFO] No new documents to organize (all already organized)")
            return jsonify({
                'status': 'success',
                'message': 'No new documents to organize',
                'processed': 0
            })
        
        if not docs:
            print("[INFO] No indexed documents found")
            return jsonify({
                'status': 'success',
                'message': 'No documents need proposal generation',
                'processed': 0
            })
        
        print(f"[INFO] Found {len(docs)} indexed documents")
        
        total_proposals = 0
        processed_docs = 0
        errors = []
        
        for idx, doc in enumerate(docs, 1):
            try:
                print(f"\n[{idx}/{len(docs)}] Processing: {doc.filename}")
                
                # Extract pages for analysis
                _, _, pages_data = kb_service.extract_text_from_pdf(doc.file_path, doc.id)
                print(f"    Extracted {len(pages_data)} pages")
                
                # Analyze content with LLM intelligence
                use_llm = request.json.get('use_llm', True) if request.json else True
                analysis = organizer.analyze_content_structure(pages_data, doc.filename, use_llm=use_llm)
                
                # Save proposals
                if analysis['status'] == 'success':
                    proposals_count = 0
                    for proposal in analysis.get('proposals', []):
                        org_proposal = ContentOrganizationProposal(
                            document_id=doc.id,
                            proposal_type=proposal.get('type', 'section'),
                            title=proposal.get('title', ''),
                            description=proposal.get('description', ''),
                            affected_pages=proposal.get('affected_pages', ''),
                            proposed_content=json.dumps(proposal),
                            status='pending'
                        )
                        db.session.add(org_proposal)
                        proposals_count += 1
                        total_proposals += 1
                    
                    doc.status = 'organized'
                    processed_docs += 1
                    db.session.commit()
                    print(f"    ✓ Generated {proposals_count} proposal(s)")
                else:
                    errors.append(f"{doc.filename}: {analysis.get('message', 'Unknown error')}")
                
            except Exception as doc_error:
                error_msg = f"{doc.filename}: {str(doc_error)}"
                print(f"    ✗ Error: {str(doc_error)}")
                errors.append(error_msg)
                continue
        
        print(f"\n[INFO] ========== Proposal Generation Complete ==========")
        print(f"[INFO] Processed: {processed_docs}/{len(docs)} documents")
        print(f"[INFO] Total proposals: {total_proposals}")
        if errors:
            print(f"[WARN] Errors: {len(errors)}")
        
        return jsonify({
            'status': 'success',
            'message': f'Generated {total_proposals} proposals from {processed_docs} documents',
            'proposals_generated': total_proposals,
            'documents_processed': processed_docs,
            'errors': errors if errors else None
        })
        
    except Exception as e:
        error_msg = str(e)
        print(f"\n[ERROR] Proposal generation failed: {error_msg}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'error': error_msg}), 500


@app.route('/api/knowledge/proposals/approve-all', methods=['POST'])
@api_login_required
def approve_all_proposals():
    """Auto-approve all pending proposals and add to book in logical order"""
    try:
        from services.content_organizer import get_content_organizer
        from services.knowledge_base import get_knowledge_base_service
        
        data = request.json or {}
        book_id = data.get('book_id')
        
        if not book_id:
            return jsonify({'error': 'book_id required'}), 400
        
        book = KnowledgeBook.query.get(book_id)
        if not book:
            return jsonify({'error': 'Book not found'}), 404
        
        # Get all pending proposals
        proposals = ContentOrganizationProposal.query.filter_by(status='pending').order_by(
            ContentOrganizationProposal.document_id,
            ContentOrganizationProposal.created_at
        ).all()
        
        if not proposals:
            return jsonify({
                'status': 'success',
                'message': 'No pending proposals',
                'sections_created': 0
            })
        
        print(f"\n[INFO] Auto-approving {len(proposals)} proposals to '{book.title}'")
        
        kb_service = get_knowledge_base_service()
        organizer = get_content_organizer()
        
        sections_created = 0
        errors = []
        
        # Get current max section order
        current_max_order = db.session.query(db.func.max(KnowledgeSection.section_order)).filter_by(book_id=book.id).scalar() or -1
        next_order = current_max_order + 1
        
        for proposal in proposals:
            try:
                doc = KnowledgeDocument.query.get(proposal.document_id)
                
                # Extract pages
                _, _, pages_data = kb_service.extract_text_from_pdf(doc.file_path, doc.id)
                
                # Apply organization
                proposal_dict = json.loads(proposal.proposed_content)
                result = organizer.apply_organization(proposal_dict, pages_data)
                
                if result['status'] == 'success':
                    # Create section
                    section = KnowledgeSection(
                        document_id=doc.id,
                        book_id=book.id,
                        title=result['title'],
                        content=result['content'],
                        content_markdown=result.get('content', ''),
                        page_numbers=result['pages'],
                        section_order=next_order,
                        section_type='chapter'
                    )
                    db.session.add(section)
                    next_order += 1
                    
                    # Mark proposal as approved
                    proposal.status = 'approved'
                    proposal.reviewed_at = datetime.now(timezone.utc)
                    
                    sections_created += 1
                    print(f"[SUCCESS] Created section: {result['title']}")
                
            except Exception as e:
                error_msg = f"Failed to process proposal {proposal.id}: {str(e)}"
                print(f"[ERROR] {error_msg}")
                errors.append(error_msg)
                continue
        
        db.session.commit()
        
        print(f"[INFO] Auto-approval complete: {sections_created} sections created")
        
        return jsonify({
            'status': 'success',
            'message': f'Created {sections_created} sections in {book.title}',
            'sections_created': sections_created,
            'errors': errors if errors else None
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/knowledge/proposals/<int:proposal_id>/approve', methods=['POST'])
@api_login_required
def approve_organization_proposal(proposal_id):
    """Approve single organization proposal to a book"""
    try:
        from services.content_organizer import get_content_organizer
        from services.knowledge_base import get_knowledge_base_service
        
        data = request.json or {}
        
        proposal = ContentOrganizationProposal.query.get_or_404(proposal_id)
        
        if proposal.status != 'pending':
            return jsonify({'error': 'Proposal already processed'}), 400
        
        # Get book selection from request
        book_id = data.get('book_id')
        create_new_book = data.get('create_new_book', False)
        new_book_title = data.get('new_book_title', '')
        
        # Get document and pages
        doc = KnowledgeDocument.query.get(proposal.document_id)
        kb_service = get_knowledge_base_service()
        
        # Extract pages again
        _, _, pages_data = kb_service.extract_text_from_pdf(doc.file_path, doc.id)
        
        # Apply organization
        organizer = get_content_organizer()
        proposal_dict = json.loads(proposal.proposed_content)
        result = organizer.apply_organization(proposal_dict, pages_data)
        
        if result['status'] == 'success':
            # Determine which book to use
            if create_new_book:
                # Create new book
                book = KnowledgeBook(
                    title=new_book_title or f"Trading Notes - {doc.original_filename.replace('.pdf', '')}",
                    description=f"Organized content from {doc.original_filename}"
                )
                db.session.add(book)
                db.session.flush()
            elif book_id:
                # Use existing book
                book = KnowledgeBook.query.get(book_id)
                if not book:
                    return jsonify({'error': 'Selected book not found'}), 404
            else:
                return jsonify({'error': 'Must specify either book_id or create_new_book'}), 400
            
            # Get next section order
            current_max_order = db.session.query(db.func.max(KnowledgeSection.section_order)).filter_by(book_id=book.id).scalar() or -1
            
            # Create knowledge section linked to book
            section = KnowledgeSection(
                document_id=doc.id,
                book_id=book.id,
                title=result['title'],
                content=result['content'],
                content_markdown=result.get('content', ''),
                page_numbers=result['pages'],
                section_order=current_max_order + 1,
                section_type='chapter'
            )
            db.session.add(section)
            
            # Update proposal status
            proposal.status = 'approved'
            proposal.reviewed_at = datetime.now(timezone.utc)
            
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'section': section.to_dict(),
                'book': book.to_dict(),
                'message': f'Section added to book: {book.title}'
            })
        else:
            return jsonify({'error': 'Failed to apply organization'}), 500
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/knowledge/proposals/<int:proposal_id>/reject', methods=['POST'])
@api_login_required
def reject_organization_proposal(proposal_id):
    """Reject organization proposal"""
    try:
        proposal = ContentOrganizationProposal.query.get_or_404(proposal_id)
        
        proposal.status = 'rejected'
        proposal.reviewed_at = datetime.now(timezone.utc)
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': 'Proposal rejected'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/knowledge/chat', methods=['POST'])
@api_login_required
def knowledge_chat():
    """Chat with knowledge base"""
    try:
        from services.rag_chatbot import get_rag_chatbot
        
        data = request.json
        
        if not data or not data.get('query'):
            return jsonify({'error': 'Query is required'}), 400
        
        query = data['query'].strip()
        
        if len(query) < 3:
            return jsonify({'error': 'Query too short'}), 400
        
        print(f"\n[INFO] ========== Chat Query ==========")
        print(f"[INFO] Query: {query}")
        
        # Get chatbot response
        print("[INFO] Initializing RAG chatbot...")
        chatbot = get_rag_chatbot()
        
        print("[INFO] Processing query...")
        print("[INFO] Step 1: Searching vector database for relevant chunks...")
        
        result = chatbot.query(query, include_sources=True)
        
        if result['status'] == 'success':
            print(f"[INFO] Step 2: Found {len(result.get('sources', []))} relevant sources")
            print(f"[INFO] Step 3: Generating response with LLM (gpt-oss:20b)...")
            print(f"[SUCCESS] Response generated in {result.get('response_time', 0):.2f}s")
            print(f"[INFO] Response length: {len(result['response'])} characters")
            
            # Save to chat history
            chat_entry = ChatHistory(
                query=query,
                response=result['response'],
                sources=json.dumps(result.get('sources', [])),
                response_time=result.get('response_time')
            )
            db.session.add(chat_entry)
            db.session.commit()
            
            print("[INFO] Chat history saved")
            print("[INFO] ========== Chat Complete ==========\n")
            
            return jsonify(result)
        else:
            print(f"[ERROR] Chat failed: {result.get('error', 'Unknown error')}")
            print("[INFO] ========== Chat Failed ==========\n")
            return jsonify(result), 500
            
    except Exception as e:
        print(f"[ERROR] Chat endpoint failed: {str(e)}")
        import traceback
        traceback.print_exc()
        print("[INFO] ========== Chat Error ==========\n")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/knowledge/chat/history', methods=['GET'])
@api_login_required
def get_chat_history():
    """Get chat history"""
    try:
        limit = request.args.get('limit', 50, type=int)
        
        history = ChatHistory.query.order_by(
            ChatHistory.timestamp.desc()
        ).limit(limit).all()
        
        return jsonify([h.to_dict() for h in history])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/knowledge/chat/history', methods=['DELETE'])
@api_login_required
def clear_chat_history():
    """Clear all chat history"""
    try:
        ChatHistory.query.delete()
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': 'Chat history cleared'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/knowledge/reindex', methods=['POST'])
@api_login_required
def reindex_knowledge_base():
    """Rebuild vector database from all documents"""
    try:
        from services.knowledge_base import get_knowledge_base_service
        
        # Get all documents
        documents = KnowledgeDocument.query.all()
        
        if not documents:
            return jsonify({'error': 'No documents to reindex'}), 400
        
        documents_data = [
            {
                'id': doc.id,
                'filename': doc.filename,
                'file_path': doc.file_path
            }
            for doc in documents
        ]
        
        kb_service = get_knowledge_base_service()
        result = kb_service.reindex_all(documents_data)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/knowledge/sections', methods=['GET'])
@api_login_required
def get_knowledge_sections():
    """Get organized knowledge sections"""
    try:
        document_id = request.args.get('document_id', type=int)
        
        query = KnowledgeSection.query
        if document_id:
            query = query.filter_by(document_id=document_id)
        
        sections = query.order_by(KnowledgeSection.section_order).all()
        
        return jsonify([s.to_dict() for s in sections])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/knowledge/stats', methods=['GET'])
@api_login_required
def get_knowledge_stats():
    """Get knowledge base statistics"""
    try:
        from services.knowledge_base import get_knowledge_base_service
        
        kb_service = get_knowledge_base_service()
        vector_stats = kb_service.get_collection_stats()
        
        stats = {
            'total_documents': KnowledgeDocument.query.count(),
            'total_sections': KnowledgeSection.query.count(),
            'pending_proposals': ContentOrganizationProposal.query.filter_by(status='pending').count(),
            'total_pages': db.session.query(db.func.sum(KnowledgeDocument.total_pages)).scalar() or 0,
            'vector_store': vector_stats
        }
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/knowledge/config', methods=['GET'])
@api_login_required
def get_knowledge_config():
    """Get knowledge base configuration"""
    try:
        from config.knowledge_base import config
        
        return jsonify(config.get_config_summary())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/knowledge/config/validate', methods=['GET'])
@api_login_required
def validate_knowledge_config():
    """Validate knowledge base configuration and check model availability"""
    try:
        from config.knowledge_base import config
        
        validation_result = config.validate_config()
        
        return jsonify(validation_result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# Book Management Endpoints
# ============================================================================

@app.route('/api/knowledge/books', methods=['GET'])
@api_login_required
def get_books():
    """List all books"""
    try:
        books = KnowledgeBook.query.order_by(KnowledgeBook.created_at.desc()).all()
        return jsonify({
            'status': 'success',
            'books': [book.to_dict() for book in books]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/knowledge/books', methods=['POST'])
@api_login_required
def create_book():
    """Create a new book"""
    try:
        data = request.json
        
        if not data or not data.get('title'):
            return jsonify({'error': 'Title is required'}), 400
        
        book = KnowledgeBook(
            title=data['title'],
            description=data.get('description', '')
        )
        
        db.session.add(book)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'book': book.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/knowledge/books/<int:book_id>', methods=['GET'])
@api_login_required
def get_book(book_id):
    """Get a book with all sections"""
    try:
        book = KnowledgeBook.query.get_or_404(book_id)
        
        # Get sections ordered hierarchically
        sections = KnowledgeSection.query.filter_by(
            book_id=book_id,
            parent_section_id=None
        ).order_by(KnowledgeSection.section_order).all()
        
        result = book.to_dict()
        result['sections'] = [s.to_dict(include_images=True, include_subsections=True) for s in sections]
        
        return jsonify({
            'status': 'success',
            'book': result
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/knowledge/books/<int:book_id>', methods=['PUT'])
@api_login_required
def update_book(book_id):
    """Update book metadata"""
    try:
        book = KnowledgeBook.query.get_or_404(book_id)
        data = request.json
        
        if 'title' in data:
            book.title = data['title']
        if 'description' in data:
            book.description = data['description']
        
        book.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'book': book.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/knowledge/books/<int:book_id>', methods=['DELETE'])
@api_login_required
def delete_book(book_id):
    """Delete a book and all its sections"""
    try:
        book = KnowledgeBook.query.get_or_404(book_id)
        db.session.delete(book)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Book deleted successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ============================================================================
# Section CRUD Endpoints
# ============================================================================

@app.route('/api/knowledge/sections', methods=['POST'])
@api_login_required
def create_section():
    """Create new section manually"""
    try:
        data = request.json
        
        if not data or not data.get('title'):
            return jsonify({'error': 'Title is required'}), 400
        
        section = KnowledgeSection(
            book_id=data.get('book_id'),
            parent_section_id=data.get('parent_section_id'),
            title=data['title'],
            content=data.get('content', ''),
            content_markdown=data.get('content_markdown', ''),
            section_type=data.get('section_type', 'section'),
            section_order=data.get('section_order', 0),
            page_numbers=data.get('page_numbers', '')
        )
        
        db.session.add(section)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'section': section.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/knowledge/sections/<int:section_id>', methods=['PUT'])
@api_login_required
def update_section(section_id):
    """Update section content/metadata"""
    try:
        section = KnowledgeSection.query.get_or_404(section_id)
        data = request.json
        
        # Update allowed fields
        if 'title' in data:
            section.title = data['title']
        if 'content' in data:
            section.content = data['content']
        if 'content_markdown' in data:
            section.content_markdown = data['content_markdown']
        if 'section_type' in data:
            section.section_type = data['section_type']
        if 'section_order' in data:
            section.section_order = data['section_order']
        if 'parent_section_id' in data:
            section.parent_section_id = data['parent_section_id']
        if 'page_numbers' in data:
            section.page_numbers = data['page_numbers']
        
        section.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'section': section.to_dict(include_images=True)
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/knowledge/sections/<int:section_id>', methods=['DELETE'])
@api_login_required
def delete_section(section_id):
    """Delete section"""
    try:
        section = KnowledgeSection.query.get_or_404(section_id)
        db.session.delete(section)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Section deleted successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/knowledge/sections/reorder', methods=['POST'])
@api_login_required
def reorder_sections():
    """Reorder sections"""
    try:
        data = request.json
        
        if not data or 'section_ids' not in data:
            return jsonify({'error': 'section_ids array is required'}), 400
        
        section_ids = data['section_ids']
        
        # Update order for each section
        for order, section_id in enumerate(section_ids):
            section = KnowledgeSection.query.get(section_id)
            if section:
                section.section_order = order
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'Reordered {len(section_ids)} sections'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/knowledge/sections/<int:section_id>/images', methods=['POST'])
@api_login_required
def add_section_image(section_id):
    """Add image to section"""
    try:
        section = KnowledgeSection.query.get_or_404(section_id)
        data = request.json
        
        if not data or not data.get('image_path'):
            return jsonify({'error': 'image_path is required'}), 400
        
        image = KnowledgeSectionImage(
            section_id=section_id,
            image_path=data['image_path'],
            caption=data.get('caption', ''),
            position=data.get('position', 0),
            source_page=data.get('source_page'),
            width=data.get('width'),
            height=data.get('height')
        )
        
        db.session.add(image)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'image': image.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ============================================================================
# Book Export Endpoints
# ============================================================================

@app.route('/api/knowledge/books/<int:book_id>/reorganize', methods=['POST'])
@api_login_required
def reorganize_book(book_id):
    """Analyze and reorganize book into logical chapter hierarchy"""
    try:
        from services.book_organizer import get_book_organizer
        
        print(f"\n[INFO] ========== Book Reorganization ==========")
        print(f"[INFO] Book ID: {book_id}")
        
        book = KnowledgeBook.query.get_or_404(book_id)
        print(f"[INFO] Book: {book.title}")
        
        # Get all sections
        sections = KnowledgeSection.query.filter_by(
            book_id=book_id,
            parent_section_id=None
        ).order_by(KnowledgeSection.section_order).all()
        
        print(f"[INFO] Found {len(sections)} sections to organize")
        
        if not sections:
            return jsonify({'error': 'No sections to organize'}), 400
        
        # Analyze and get organization proposal
        organizer = get_book_organizer()
        sections_data = [s.to_dict() for s in sections]
        
        result = organizer.analyze_and_organize_book(book.title, sections_data)
        
        if result['status'] == 'success':
            organization = result['organization']
            chapters = organization['chapters']
            
            print(f"[INFO] Proposed {len(chapters)} chapters")
            
            # Apply organization (create chapter structure)
            new_order = 0
            created_chapters = []
            
            for chapter_def in chapters:
                print(f"[INFO] Creating chapter: {chapter_def['title']}")
                
                # Create parent chapter
                parent_chapter = KnowledgeSection(
                    book_id=book_id,
                    title=chapter_def['title'],
                    content=f"# {chapter_def['title']}\n\nThis chapter covers essential concepts in {chapter_def['title'].lower()}.",
                    content_markdown=f"# {chapter_def['title']}\n\nThis chapter covers essential concepts.",
                    section_type='chapter',
                    section_order=new_order,
                    parent_section_id=None
                )
                db.session.add(parent_chapter)
                db.session.flush()  # Get ID
                
                new_order += 1
                subsection_count = 0
                
                # Move matching sections under this chapter
                for section_idx in chapter_def['section_ids']:
                    if 0 <= section_idx - 1 < len(sections):
                        section = sections[section_idx - 1]
                        section.parent_section_id = parent_chapter.id
                        section.section_order = new_order
                        section.section_type = 'section'
                        new_order += 1
                        subsection_count += 1
                
                created_chapters.append({
                    'id': parent_chapter.id,
                    'title': parent_chapter.title,
                    'sections_count': subsection_count
                })
                
                print(f"[SUCCESS] Created '{parent_chapter.title}' with {subsection_count} sections")
            
            db.session.commit()
            
            print(f"[INFO] ========== Reorganization Complete ==========\n")
            
            return jsonify({
                'status': 'success',
                'message': f'Organized into {len(created_chapters)} chapters',
                'chapters': created_chapters,
                'method': organization.get('method', 'unknown')
            })
        else:
            return jsonify({'error': 'Organization failed'}), 500
            
    except Exception as e:
        print(f"[ERROR] Reorganization failed: {str(e)}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/knowledge/books/<int:book_id>/synthesize', methods=['POST'])
@api_login_required
def synthesize_book_content(book_id):
    """Synthesize raw content into clean educational prose"""
    try:
        from services.content_synthesizer import get_content_synthesizer
        
        print(f"\n[INFO] ========== Content Synthesis ==========")
        print(f"[INFO] Book ID: {book_id}")
        
        book = KnowledgeBook.query.get_or_404(book_id)
        print(f"[INFO] Book: {book.title}")
        
        # Get all parent chapters
        chapters = KnowledgeSection.query.filter_by(
            book_id=book_id,
            parent_section_id=None,
            section_type='chapter'
        ).order_by(KnowledgeSection.section_order).all()
        
        print(f"[INFO] Found {len(chapters)} chapters to synthesize")
        
        if not chapters:
            return jsonify({'error': 'No chapters found. Run reorganize first.'}), 400
        
        synthesizer = get_content_synthesizer()
        processed_chapters = []
        
        for chapter in chapters:
            print(f"\n[INFO] Processing chapter: {chapter.title}")
            
            # Get child sections
            child_sections = KnowledgeSection.query.filter_by(
                parent_section_id=chapter.id
            ).order_by(KnowledgeSection.section_order).all()
            
            if not child_sections:
                continue
            
            sections_data = [s.to_dict() for s in child_sections]
            
            # Synthesize chapter content
            result = synthesizer.synthesize_chapter_content(
                chapter_title=chapter.title,
                sections_data=sections_data
            )
            
            # Update chapter introduction
            chapter.content = f"# {result['chapter_title']}\n\n{result['introduction']}"
            chapter.content_markdown = chapter.content
            
            # Update each section with synthesized content
            for idx, synth_section in enumerate(result['sections']):
                if idx < len(child_sections):
                    section = child_sections[idx]
                    section.title = synth_section['title']
                    section.content = synth_section['content']
                    section.content_markdown = synth_section['content']
                    
                    print(f"[SUCCESS] Updated section: {section.title}")
            
            processed_chapters.append({
                'id': chapter.id,
                'title': chapter.title,
                'sections_updated': len(result['sections'])
            })
        
        db.session.commit()
        
        print(f"\n[INFO] ========== Synthesis Complete ==========\n")
        
        return jsonify({
            'status': 'success',
            'message': f'Synthesized {len(processed_chapters)} chapters',
            'chapters': processed_chapters
        })
        
    except Exception as e:
        print(f"[ERROR] Synthesis failed: {str(e)}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/knowledge/books/<int:book_id>/export', methods=['GET'])
@api_login_required
def export_book(book_id):
    """Export book to PDF or HTML"""
    try:
        print(f"\n[INFO] Export request for book {book_id}")
        
        export_format = request.args.get('format', 'html').lower()
        print(f"[INFO] Export format: {export_format}")
        
        if export_format not in ['html', 'pdf']:
            return jsonify({'error': 'Invalid format. Use html or pdf'}), 400
        
        # Get book and sections
        book = KnowledgeBook.query.get_or_404(book_id)
        print(f"[INFO] Found book: {book.title}")
        
        sections = KnowledgeSection.query.filter_by(
            book_id=book_id,
            parent_section_id=None
        ).order_by(KnowledgeSection.section_order).all()
        print(f"[INFO] Found {len(sections)} sections")
        
        if not sections:
            return jsonify({
                'error': 'No sections in this book. Add content before exporting.',
                'book_title': book.title
            }), 400
        
        try:
            from services.book_exporter import get_book_exporter
            exporter = get_book_exporter()
            print("[INFO] Book exporter initialized")
        except ImportError as ie:
            print(f"[ERROR] Failed to import book_exporter: {str(ie)}")
            return jsonify({
                'error': 'Export service not available',
                'details': str(ie)
            }), 500
        
        book_data = book.to_dict()
        sections_data = [s.to_dict(include_images=True, include_subsections=True) for s in sections]
        base_path = os.path.abspath('.')
        
        if export_format == 'html':
            try:
                print("[INFO] Generating HTML...")
                html_content = exporter.export_to_html(book_data, sections_data, base_path)
                print(f"[INFO] HTML generated ({len(html_content)} bytes)")
                
                # Create response with HTML file
                from flask import make_response
                response = make_response(html_content)
                response.headers['Content-Type'] = 'text/html; charset=utf-8'
                response.headers['Content-Disposition'] = f'attachment; filename="{book.title}.html"'
                return response
            except Exception as html_error:
                print(f"[ERROR] HTML export failed: {str(html_error)}")
                import traceback
                traceback.print_exc()
                return jsonify({
                    'error': f'HTML export failed: {str(html_error)}',
                    'type': type(html_error).__name__
                }), 500
            
        else:  # pdf
            try:
                print("[INFO] Generating PDF...")
                pdf_bytes = exporter.export_to_pdf(book_data, sections_data, base_path)
                print(f"[INFO] PDF generated ({len(pdf_bytes)} bytes)")
                
                from flask import make_response
                response = make_response(pdf_bytes)
                response.headers['Content-Type'] = 'application/pdf'
                response.headers['Content-Disposition'] = f'attachment; filename="{book.title}.pdf"'
                return response
                
            except Exception as pdf_error:
                print(f"[ERROR] PDF export failed: {str(pdf_error)}")
                import traceback
                traceback.print_exc()
                return jsonify({
                    'error': f'PDF export failed: {str(pdf_error)}',
                    'suggestion': 'Install weasyprint or reportlab: pip install weasyprint',
                    'type': type(pdf_error).__name__
                }), 500
                
    except Exception as e:
        print(f"[ERROR] Export endpoint failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'type': type(e).__name__}), 500


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    # Auto-backup on startup (daily basis, keeps last 5 backups)
    try:
        from utils.backup import auto_backup_on_startup
        
        # Get database path from config
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
        if db_uri.startswith('sqlite:///'):
            db_path = db_uri.replace('sqlite:///', '')
            
            # Make path absolute if it's relative
            if not os.path.isabs(db_path):
                db_path = os.path.join(os.path.dirname(__file__), db_path)
            
            # Run auto-backup
            backup_dir = os.path.join(os.path.dirname(__file__), 'backups')
            backup_result = auto_backup_on_startup(db_path, backup_dir, keep_count=5)
            
            if backup_result['status'] == 'success':
                print(f"[STARTUP] ✓ Backup created! Total: {backup_result.get('total_backups', 0)}")
                if backup_result.get('backups_deleted', 0) > 0:
                    print(f"[STARTUP] ✓ Cleaned up {backup_result['backups_deleted']} old backup(s)")
            elif backup_result['status'] == 'skipped':
                reason = backup_result.get('reason', 'unknown')
                if reason == 'backup_already_exists_for_today':
                    print(f"[STARTUP] ✓ Backup up-to-date (Total: {backup_result.get('total_backups', 0)} backups)")
        else:
            print("[STARTUP] Auto-backup only supported for SQLite databases")
            
    except Exception as e:
        print(f"[STARTUP] Auto-backup warning: {str(e)}")
        # Don't stop the app if backup fails
    
    app.run(debug=True, port=5000)

