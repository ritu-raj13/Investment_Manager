from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_login import login_user, logout_user, current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime
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
    clean_symbol
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
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
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
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'total_amount': self.total_amount,
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
                    stock.last_updated = datetime.utcnow()
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
                        stock.last_updated = datetime.utcnow()
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
                    stock.last_updated = datetime.utcnow()
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
                    stock.last_updated = datetime.utcnow()
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
                        stock.last_updated = datetime.utcnow()
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
                    stock.last_updated = datetime.utcnow()
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
    transactions = PortfolioTransaction.query.all()
    
    # Calculate holdings using utility function
    holdings = calculate_holdings(transactions)
    
    # Get current prices and calculate gains/losses
    summary = []
    total_invested = 0
    total_current_value = 0
    
    for symbol, holding in holdings.items():
        if holding['quantity'] > 0:  # Only include current holdings
            avg_price = holding['invested_amount'] / holding['quantity'] if holding['quantity'] > 0 else 0
            
            # Get current price from stocks table (flexible matching for .NS/.BO suffix)
            current_price = 0
            stock = find_stock_by_symbol(symbol)
            if stock and stock.current_price:
                current_price = stock.current_price
            
            current_value = holding['quantity'] * current_price
            gain_loss = current_value - holding['invested_amount']
            gain_loss_pct = (gain_loss / holding['invested_amount'] * 100) if holding['invested_amount'] > 0 else 0
            
            summary.append({
                'symbol': symbol,
                'name': holding['name'],
                'quantity': holding['quantity'],
                'avg_price': round(avg_price, 2),
                'current_price': current_price,
                'invested_amount': round(holding['invested_amount'], 2),
                'current_value': round(current_value, 2),
                'gain_loss': round(gain_loss, 2),
                'gain_loss_pct': round(gain_loss_pct, 2),
                'day_change_pct': stock.day_change_pct if stock else None
            })
            
            total_invested += holding['invested_amount']
            total_current_value += current_value
    
    total_gain_loss = total_current_value - total_invested
    total_gain_loss_pct = (total_gain_loss / total_invested * 100) if total_invested > 0 else 0
    
    # Calculate portfolio 1-day change (weighted average)
    portfolio_day_change_pct = 0
    if total_current_value > 0:
        weighted_change = 0
        for holding in summary:
            if holding['day_change_pct'] is not None:
                weight = holding['current_value'] / total_current_value
                weighted_change += holding['day_change_pct'] * weight
        portfolio_day_change_pct = weighted_change
    
    return jsonify({
        'holdings': summary,
        'total_invested': round(total_invested, 2),
        'total_current_value': round(total_current_value, 2),
        'total_gain_loss': round(total_gain_loss, 2),
        'total_gain_loss_pct': round(total_gain_loss_pct, 2),
        'portfolio_day_change_pct': round(portfolio_day_change_pct, 2)
    })


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
    """Update portfolio settings (total amount)"""
    data = request.get_json()
    settings = PortfolioSettings.query.first()
    
    if not settings:
        settings = PortfolioSettings()
        db.session.add(settings)
    
    if 'total_amount' in data:
        settings.total_amount = float(data['total_amount'])
        settings.updated_at = datetime.utcnow()
    
    db.session.commit()
    return jsonify(settings.to_dict())


# Initialize database
@app.before_request
def create_tables():
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


# ============================================================================
# Data Management Routes (Auth required)
# ============================================================================

@app.route('/api/export/stocks', methods=['GET'])
@api_login_required
def export_stocks_csv():
    """Export all stocks to CSV"""
    try:
        stocks = Stock.query.all()
        
        if not stocks:
            return jsonify({'error': 'No stocks to export'}), 404
        
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
        
        if not transactions:
            return jsonify({'error': 'No transactions to export'}), 404
        
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


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)

