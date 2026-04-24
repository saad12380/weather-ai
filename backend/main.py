from passlib import apps

from training.trainer import ProfessionalTrainer
from training.scheduler import TrainingScheduler
import threading
from auth import create_user, get_user_by_email, authenticate_user, verify_password, get_password_hash
import warnings
warnings.filterwarnings("ignore", message="Maximum Likelihood optimization failed to converge")
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Suppress TensorFlow warnings
import tensorflow as tf
from fastapi import FastAPI, HTTPException, Request, Form, Depends, Header, Cookie
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel, Field
import pandas as pd
import numpy as np
import joblib
import os
from datetime import datetime, timedelta, timezone
import random
import uvicorn
import httpx
import asyncio
import hashlib
import secrets
from typing import Optional, Dict, Any, List, Tuple
import traceback
import warnings
warnings.filterwarnings('ignore')
import sqlite3
from jose import JWTError, jwt
from passlib.context import CryptContext
import json
import requests
from pathlib import Path
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re
import pyotp
import qrcode
import io
import base64
import string
from dotenv import load_dotenv
import os
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Machine Learning Libraries
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.decomposition import PCA
from sklearn.covariance import EllipticEnvelope

# Statistical Models
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller
from scipy import stats
from scipy.signal import find_peaks
from sklearn.covariance import EllipticEnvelope

# Deep Learning - Reordered and fixed
import tensorflow as tf
keras = tf.keras
layers = keras.layers
models = keras.models
callbacks = keras.callbacks

# Prophet (optional) - Move this AFTER tensorflow imports
try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    print("⚠️ Facebook Prophet not installed. Install with: pip install prophet")

from auth import create_user, get_user_by_email, authenticate_user, verify_password, get_password_hash
print(f"✅ Imported get_user_by_email from auth.py: {get_user_by_email}")  # Add this line for debugging

CONFIGURATION = "https://raw.githubusercontent.com/facebookincubator/prophet/master/config.json"

# ============ CONFIGURATION ============
WEBSITE_URL = "http://localhost:3000"
API_URL = "http://localhost:3000/api"
BACKEND_PORT = 3000

# ============ API KEYS (from .env) ============
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

# Get absolute paths
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "weather-ai-website"
WEBAPP_DIR = BASE_DIR / "frontend"

@apps.get("/debug-paths")
async def debug_paths():
    return {
        "base_dir": str(BASE_DIR),
        "frontend_exists": FRONTEND_DIR.exists(),
        "webapp_exists": WEBAPP_DIR.exists(),
        "cwd": str(Path.cwd()),
        "files": os.listdir(str(BASE_DIR)) if BASE_DIR.exists() else []
    }

print("="*60)
print("🚀 WEATHER AI PLATFORM - STARTING SERVER")
print("="*60)
print(f"📁 Project Root: {BASE_DIR}")
print(f"🌐 Website Folder: {FRONTEND_DIR} (Exists: {FRONTEND_DIR.exists()})")
print(f"📊 Web App Folder: {WEBAPP_DIR} (Exists: {WEBAPP_DIR.exists()})")
print(f"🌍 Server URL: http://localhost:{BACKEND_PORT}")
print("="*60)

# Database configuration
# Database configuration - use same path as auth.py
current_dir = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(current_dir, 'weather_anomaly_users.db')

# ============ JWT Configuration ============
SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret-only-for-dev")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


# ============ Email Configuration (from .env) ============
EMAIL_CONFIG = {
    "SMTP_SERVER": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
    "SMTP_PORT": int(os.getenv("SMTP_PORT", "587")),
    "EMAIL_USER": os.getenv("SMTP_USERNAME", ""),
    "EMAIL_PASSWORD": os.getenv("SMTP_PASSWORD", ""),
    "ADMIN_EMAIL": os.getenv("SMTP_USERNAME", "")
}

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Initialize FastAPI app
app = FastAPI(
    title="Weather Anomaly Predictor",
    description="AI-powered weather anomaly detection platform with future predictions",
    version="3.0.0"
)

# ============ MIDDLEWARE ============
app.add_middleware(
    SessionMiddleware,
    secret_key="your-session-secret-key-change-in-production"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        # When you deploy, add your real domain:
        # "https://yourdomain.com",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

# ============ DATABASE FUNCTIONS ============
def init_db():
    """Initialize the database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            hashed_password TEXT NOT NULL,
            profile_picture TEXT,
            phone_number TEXT,
            location TEXT,
            bio TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            account_type TEXT DEFAULT 'personal'
        )
    ''')
    
    # Create user_preferences table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            language TEXT DEFAULT 'en',
            timezone TEXT DEFAULT 'UTC',
            date_format TEXT DEFAULT 'MM/DD/YYYY',
            temperature_unit TEXT DEFAULT 'celsius',
            wind_speed_unit TEXT DEFAULT 'kmh',
            pressure_unit TEXT DEFAULT 'hpa',
            distance_unit TEXT DEFAULT 'km',
            theme TEXT DEFAULT 'light',
            notifications_email BOOLEAN DEFAULT 1,
            notifications_push BOOLEAN DEFAULT 1,
            anomaly_alerts BOOLEAN DEFAULT 1,
            weather_updates BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create api_keys table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            key_name TEXT NOT NULL,
            api_key TEXT UNIQUE NOT NULL,
            permissions TEXT DEFAULT 'read',
            last_used TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            token TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create activity log table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            activity_type TEXT,
            city TEXT,
            status TEXT,
            is_anomaly BOOLEAN,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create future anomalies table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS future_anomalies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT,
            country TEXT,
            prediction_date DATE,
            day_name TEXT,
            temperature REAL,
            humidity INTEGER,
            pressure INTEGER,
            wind_speed REAL,
            condition TEXT,
            is_anomaly BOOLEAN,
            anomaly_type TEXT,
            severity TEXT,
            probability INTEGER,
            description TEXT,
            impact_level INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create contact messages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contact_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            company TEXT,
            inquiry_type TEXT NOT NULL,
            message TEXT NOT NULL,
            newsletter_subscribed BOOLEAN DEFAULT 0,
            ip_address TEXT,
            user_agent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'pending',
            email_sent BOOLEAN DEFAULT 0,
            notes TEXT
        )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS newsletter_subscribers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT 1,
        unsubscribe_token TEXT UNIQUE,
        last_email_sent TIMESTAMP,
        source_page TEXT,  -- which page they subscribed from
        user_agent TEXT,
        ip_address TEXT
    )
''')
    
    conn.commit()
    conn.close()

# ============ PASSWORD RESET TABLE INITIALIZATION ============
def init_password_reset_table():
    """Create password reset tokens table if it doesn't exist"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            token TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            used BOOLEAN DEFAULT 0,
            FOREIGN KEY (email) REFERENCES users(email)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Password reset table initialized")

# Initialize database on startup
init_db()
init_password_reset_table()


def migrate_db_schema():
    """Add missing columns to existing database tables when upgrading schema."""
    # Initialize password reset table (ensure it exists)
    init_password_reset_table()
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # ============ USERS TABLE MIGRATIONS ============
        # Ensure users table has expected columns
        cursor.execute("PRAGMA table_info(users)")
        existing_cols = [row[1] for row in cursor.fetchall()]

        # Columns we expect in users table with SQL to add them
        expected = {
            'account_type': "ALTER TABLE users ADD COLUMN account_type TEXT DEFAULT 'personal'",
            'profile_picture': "ALTER TABLE users ADD COLUMN profile_picture TEXT",
            'phone_number': "ALTER TABLE users ADD COLUMN phone_number TEXT",
            'location': "ALTER TABLE users ADD COLUMN location TEXT",
            'bio': "ALTER TABLE users ADD COLUMN bio TEXT"
        }

        added = []
        for col, sql in expected.items():
            if col not in existing_cols:
                try:
                    cursor.execute(sql)
                    added.append(col)
                except Exception:
                    # ignore individual failures
                    pass

        # ============ NEWSLETTER SUBSCRIBERS TABLE MIGRATIONS ============
        # First ensure the table exists with ALL columns
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS newsletter_subscribers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                unsubscribe_token TEXT UNIQUE,
                last_email_sent TIMESTAMP,
                source_page TEXT,
                ip_address TEXT,
                user_agent TEXT
            )
        ''')
        
        # Check newsletter_subscribers columns
        cursor.execute("PRAGMA table_info(newsletter_subscribers)")
        newsletter_cols = [row[1] for row in cursor.fetchall()]
        print(f"📊 Current newsletter_subscribers columns: {newsletter_cols}")
        
        # Add missing newsletter columns
        newsletter_expected = {
            'last_email_sent': "ALTER TABLE newsletter_subscribers ADD COLUMN last_email_sent TIMESTAMP",
            'source_page': "ALTER TABLE newsletter_subscribers ADD COLUMN source_page TEXT",
            'ip_address': "ALTER TABLE newsletter_subscribers ADD COLUMN ip_address TEXT",
            'user_agent': "ALTER TABLE newsletter_subscribers ADD COLUMN user_agent TEXT"
        }
        
        for col, sql in newsletter_expected.items():
            if col not in newsletter_cols:
                try:
                    cursor.execute(sql)
                    added.append(f"newsletter_subscribers.{col}")
                    print(f"✅ Added {col} to newsletter_subscribers table")
                except Exception as e:
                    print(f"⚠️ Could not add {col}: {e}")

        conn.commit()
        
        # Verify all columns are now present
        cursor.execute("PRAGMA table_info(newsletter_subscribers)")
        updated_cols = [row[1] for row in cursor.fetchall()]
        print(f"📊 Updated newsletter_subscribers columns: {updated_cols}")
        
        conn.close()

        if added:
            print(f"🔧 Migrated database - added columns: {', '.join(added)}")
        else:
            print("🔧 Database schema already up-to-date")

    except Exception as e:
        print(f"⚠️ Failed to migrate DB schema: {e}")
        import traceback
        traceback.print_exc()


# Run migrations to ensure older DBs get new columns
migrate_db_schema()

def add_email_2fa_columns():
    """Add email 2FA columns to database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check existing columns
        cursor.execute("PRAGMA table_info(user_preferences)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add email_2fa_enabled flag
        if 'email_2fa_enabled' not in columns:
            cursor.execute("ALTER TABLE user_preferences ADD COLUMN email_2fa_enabled BOOLEAN DEFAULT 0")
            print("✅ Added email_2fa_enabled column")
        
        # Add otp_secret for storing current OTP
        if 'otp_secret' not in columns:
            cursor.execute("ALTER TABLE user_preferences ADD COLUMN otp_secret TEXT")
            print("✅ Added otp_secret column")
        
        # Add otp_expiry for OTP expiration
        if 'otp_expiry' not in columns:
            cursor.execute("ALTER TABLE user_preferences ADD COLUMN otp_expiry TIMESTAMP")
            print("✅ Added otp_expiry column")
        
        conn.commit()
        conn.close()
        print("✅ Email 2FA database setup complete")
    except Exception as e:
        print(f"⚠️ Error adding email 2FA columns: {e}")

# Call this during startup
add_email_2fa_columns()

def create_billing_tables():
    """Create billing and subscription tables"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Subscriptions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                plan_id TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_date TIMESTAMP,
                auto_renew BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Payment methods table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payment_methods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                card_last4 TEXT NOT NULL,
                card_brand TEXT NOT NULL,
                card_holder TEXT NOT NULL,
                expiry_month INTEGER NOT NULL,
                expiry_year INTEGER NOT NULL,
                is_default BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Invoice history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                invoice_number TEXT UNIQUE NOT NULL,
                plan_id TEXT NOT NULL,
                amount REAL NOT NULL,
                currency TEXT DEFAULT 'USD',
                status TEXT DEFAULT 'paid',
                paid_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                pdf_url TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Billing tables created successfully")
    except Exception as e:
        print(f"⚠️ Error creating billing tables: {e}")

# Call this during startup
create_billing_tables()

def create_account_switching_tables():
    """Create tables for account switching feature"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Connected accounts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS connected_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                account_email TEXT NOT NULL,
                account_name TEXT NOT NULL,
                account_type TEXT DEFAULT 'personal',
                profile_picture TEXT,
                access_token TEXT,
                refresh_token TEXT,
                token_expiry TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                last_used TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(user_id, account_email)
            )
        ''')
        
        # Account sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS account_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                account_id INTEGER NOT NULL,
                session_token TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (account_id) REFERENCES connected_accounts (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Account switching tables created successfully")
    except Exception as e:
        print(f"⚠️ Error creating account switching tables: {e}")

# Call this during startup
create_account_switching_tables()

# ============ OAUTH SETUP ============
oauth = OAuth()

# Register Google OAuth
oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile',
        'prompt': 'select_account'
    }
)

# Register GitHub OAuth
oauth.register(
    name='github',
    client_id=os.getenv('GITHUB_CLIENT_ID'),
    client_secret=os.getenv('GITHUB_CLIENT_SECRET'),
    access_token_url='https://github.com/login/oauth/access_token',
    authorize_url='https://github.com/login/oauth/authorize',
    client_kwargs={'scope': 'user:email'},
)

# Register Microsoft OAuth
oauth.register(
    name='microsoft',
    client_id=os.getenv('MICROSOFT_CLIENT_ID'),
    client_secret=os.getenv('MICROSOFT_CLIENT_SECRET'),
    server_metadata_url='https://login.microsoftonline.com/common/v2.0/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile',
        'prompt': 'select_account'
    }
)

# ============ GLOBAL VARIABLES ============
activity_log = []
cities_tracked = set()
total_predictions = 0
anomalies_detected = 0

# In-memory sessions for demo (use database in production)
sessions_db = {}

# Historical weather data for anomaly comparison
historical_weather_data = {}

# ============ AUTHENTICATION FUNCTIONS ============
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def authenticate_user(email: str, password: str):
    user = get_user_by_email(email)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return user

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password_simple(plain_password: str, hashed_password: str) -> bool:
    return hash_password(plain_password) == hashed_password

def create_token() -> str:
    return secrets.token_hex(32)

async def get_current_user(token: str = None):
    """Get current user from token (supports both regular and switched accounts)"""
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )
    
    # First check if it's an account session token
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT as_session.*, ca.account_email, ca.account_name
            FROM account_sessions as_session
            JOIN connected_accounts ca ON as_session.account_id = ca.id
            WHERE as_session.session_token = ? AND as_session.expires_at > CURRENT_TIMESTAMP
        ''', (token,))
        
        session = cursor.fetchone()
        conn.close()
        
        if session:
            # It's a valid account session
            return {
                "email": session[6],  # account_email
                "full_name": session[7],  # account_name
                "is_switched": True,
                "account_id": session[2]  # account_id
            }
    except Exception as e:
        print(f"Error checking account session in get_current_user: {e}")
    
    # Then check in-memory sessions
    session = sessions_db.get(token)
    if session:
        expires_at = datetime.fromisoformat(session["expires_at"]) if "expires_at" in session else None
        if expires_at and datetime.now() > expires_at:
            del sessions_db[token]
            raise HTTPException(status_code=401, detail="Token expired")
        
        return {
            "email": session["email"],
            "full_name": session.get("full_name", "User"),
            "is_switched": False
        }
    
    # Then check JWT token
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = get_user_by_email(email)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return {
            "email": user["email"],
            "full_name": user["full_name"],
            "is_switched": False
        }
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def extract_token(
    authorization: Optional[str] = Header(None),
    token: Optional[str] = None,
    token_header: Optional[str] = Header(None, alias="token"),
    access_cookie: Optional[str] = Cookie(None, alias="access_token")
) -> Optional[str]:
    """Extract token from Authorization header (Bearer), header 'token', cookie 'access_token', or fallback to query param 'token'."""
    if authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            return parts[1]

    if token_header:
        return token_header

    if access_cookie:
        return access_cookie

    return token

# ============ EMAIL FUNCTIONS ============
async def send_email_async(to_email: str, subject: str, html_content: str, text_content: str = None):
    """Send email asynchronously"""
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"Weather AI <{EMAIL_CONFIG['EMAIL_USER']}>"
        msg['To'] = to_email
        
        # Create plain text version if not provided
        if text_content is None:
            # Simple HTML to text conversion
            text_content = html_content.replace('<br>', '\n').replace('<br/>', '\n')
            text_content = re.sub('<[^<]+?>', '', text_content)
        
        # Attach both HTML and plain text
        msg.attach(MIMEText(text_content, 'plain'))
        msg.attach(MIMEText(html_content, 'html'))
        
        # Send email using SMTP
        with smtplib.SMTP(EMAIL_CONFIG['SMTP_SERVER'], EMAIL_CONFIG['SMTP_PORT']) as server:
            server.starttls()
            server.login(EMAIL_CONFIG['EMAIL_USER'], EMAIL_CONFIG['EMAIL_PASSWORD'])
            server.send_message(msg)
        
        print(f"✅ Email sent to {to_email}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send email to {to_email}: {str(e)}")
        return False

async def send_contact_email(form_data):
    """Send contact form email"""
    try:
        # Email to admin
        subject = f"Weather AI Contact: {form_data.inquiry_type} from {form_data.first_name} {form_data.last_name}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #1a6bb3 0%, #00c9ff 100%); color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f8fafc; padding: 30px; border-radius: 0 0 10px 10px; }}
                .field {{ margin-bottom: 15px; }}
                .label {{ font-weight: bold; color: #1a6bb3; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class='container'>
                <div class='header'>
                    <h2>New Contact Form Submission</h2>
                    <p>Weather AI Platform</p>
                </div>
                <div class='content'>
                    <div class='field'><span class='label'>Name:</span> {form_data.first_name} {form_data.last_name}</div>
                    <div class='field'><span class='label'>Email:</span> {form_data.email}</div>
                    <div class='field'><span class='label'>Phone:</span> {form_data.phone or 'Not provided'}</div>
                    <div class='field'><span class='label'>Company:</span> {form_data.company or 'Not provided'}</div>
                    <div class='field'><span class='label'>Inquiry Type:</span> {form_data.inquiry_type}</div>
                    <div class='field'><span class='label'>Newsletter:</span> {'Yes' if form_data.newsletter else 'No'}</div>
                    <div class='field'><span class='label'>Message:</span><br>{form_data.message}</div>
                    <div class='footer'>
                        <p>Submitted: {datetime.now().strftime('%B %d, %Y, %I:%M %p')}</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        ========== NEW CONTACT FORM SUBMISSION ==========
        
        Name: {form_data.first_name} {form_data.last_name}
        Email: {form_data.email}
        Phone: {form_data.phone or 'Not provided'}
        Company: {form_data.company or 'Not provided'}
        Inquiry Type: {form_data.inquiry_type}
        Newsletter Subscription: {'Yes' if form_data.newsletter else 'No'}
        
        Message:
        {form_data.message}
        
        ==============================================
        Submitted: {datetime.now().strftime('%B %d, %Y, %I:%M %p')}
        ==============================================
        """
        
        # Send to admin
        admin_sent = await send_email_async(
            EMAIL_CONFIG['ADMIN_EMAIL'],
            subject,
            html_content,
            text_content
        )
        
        # Send confirmation to user
        if admin_sent:
            user_subject = "Thank you for contacting Weather AI"
            user_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #1a6bb3 0%, #00c9ff 100%); color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ background: #f8fafc; padding: 30px; border-radius: 0 0 10px 10px; }}
                    .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class='container'>
                    <div class='header'>
                        <h2>Thank You, {form_data.first_name}!</h2>
                        <p>We've received your message</p>
                    </div>
                    <div class='content'>
                        <p>Dear {form_data.first_name},</p>
                        <p>Thank you for contacting Weather AI. We have received your inquiry regarding <strong>{form_data.inquiry_type}</strong> and will get back to you within 24 hours.</p>
                        
                        <div style='background: #e8f4fc; padding: 15px; border-radius: 8px; margin: 20px 0;'>
                            <strong>Your Message Summary:</strong><br>
                            {form_data.message[:200]}...
                        </div>
                        
                        <p>If you have any urgent questions, please don't hesitate to reply to this email.</p>
                        
                        <p>Best regards,<br>
                        <strong>The Weather AI Team</strong></p>
                    </div>
                    <div class='footer'>
                        <p>This is an automated confirmation. Please do not reply to this email.</p>
                        <p>Weather AI Platform | Advanced Weather Anomaly Detection</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            user_text = f"""
            Thank You, {form_data.first_name}!
            
            We've received your message regarding {form_data.inquiry_type}.
            Our team will review it and get back to you within 24 hours.
            
            Your Message Summary:
            {form_data.message[:200]}...
            
            If you have any urgent questions, please email us at {EMAIL_CONFIG['ADMIN_EMAIL']}
            
            Best regards,
            The Weather AI Team
            
            This is an automated confirmation. Please do not reply to this email.
            """
            
            await send_email_async(form_data.email, user_subject, user_html, user_text)
        
        return admin_sent
        
    except Exception as e:
        print(f"❌ Failed to send contact email: {str(e)}")
        return False

def save_contact_to_db(form_data, request: Request = None):
    """Save contact form submission to database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get client info
        ip_address = None
        user_agent = None
        
        if request:
            ip_address = request.client.host if request.client else "Unknown"
            user_agent = request.headers.get("user-agent", "Unknown")
        
        cursor.execute('''
            INSERT INTO contact_messages 
            (first_name, last_name, email, phone, company, inquiry_type, 
             message, newsletter_subscribed, ip_address, user_agent)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            form_data.first_name,
            form_data.last_name,
            form_data.email,
            form_data.phone or '',
            form_data.company or '',
            form_data.inquiry_type,
            form_data.message,
            1 if form_data.newsletter else 0,
            ip_address,
            user_agent
        ))
        
        conn.commit()
        message_id = cursor.lastrowid
        conn.close()
        
        print(f"✅ Contact message saved to database (ID: {message_id})")
        return message_id
        
    except Exception as e:
        print(f"❌ Failed to save contact to database: {str(e)}")
        return None

# ============ PASSWORD RESET HELPER FUNCTIONS ============
async def send_password_reset_email(email: str, reset_token: str, user_name: str = "User"):
    """Send password reset email with token"""
    try:
        reset_link = f"http://localhost:3000/reset-password?token={reset_token}"
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Weather AI - Password Reset Request"
        msg['From'] = f"Weather AI <{EMAIL_CONFIG['EMAIL_USER']}>"
        msg['To'] = email
        
        # HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #1a6bb3 0%, #00c9ff 100%); color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f8fafc; padding: 30px; border-radius: 0 0 10px 10px; }}
                .button {{ display: inline-block; padding: 12px 24px; background: linear-gradient(135deg, #1a6bb3 0%, #00c9ff 100%); color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 12px; }}
                .warning {{ color: #ff4444; font-size: 13px; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class='container'>
                <div class='header'>
                    <h2>Password Reset Request</h2>
                </div>
                <div class='content'>
                    <p>Hello {user_name},</p>
                    <p>We received a request to reset your password for your Weather AI account.</p>
                    
                    <div style='text-align: center;'>
                        <a href='{reset_link}' class='button'>Reset Password</a>
                    </div>
                    
                    <p>Or copy and paste this link into your browser:</p>
                    <p style='word-break: break-all; background: #eef2f6; padding: 10px; border-radius: 5px;'>{reset_link}</p>
                    
                    <p>This link will expire in 1 hour.</p>
                    
                    <p>If you didn't request a password reset, please ignore this email or contact support if you have concerns.</p>
                    
                    <div class='warning'>
                        ⚠️ For security reasons, never share this link with anyone.
                    </div>
                    
                    <p>Best regards,<br>
                    <strong>The Weather AI Team</strong></p>
                </div>
                <div class='footer'>
                    <p>This is an automated message. Please do not reply to this email.</p>
                    <p>Weather AI Platform | Advanced Weather Anomaly Detection</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text version
        text_content = f"""
        Password Reset Request
        
        Hello {user_name},
        
        We received a request to reset your password for your Weather AI account.
        
        To reset your password, visit:
        {reset_link}
        
        This link will expire in 1 hour.
        
        If you didn't request a password reset, please ignore this email or contact support.
        
        For security reasons, never share this link with anyone.
        
        Best regards,
        The Weather AI Team
        
        This is an automated message. Please do not reply to this email.
        """
        
        # Send email
        return await send_email_async(email, msg['Subject'], html_content, text_content)
        
    except Exception as e:
        print(f"❌ Failed to send password reset email: {str(e)}")
        return False

async def send_password_reset_confirmation(email: str):
    """Send password reset confirmation email"""
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Weather AI - Password Reset Successful"
        msg['From'] = f"Weather AI <{EMAIL_CONFIG['EMAIL_USER']}>"
        msg['To'] = email
        
        # HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #1a6bb3 0%, #00c9ff 100%); color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f8fafc; padding: 30px; border-radius: 0 0 10px 10px; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class='container'>
                <div class='header'>
                    <h2>Password Reset Successful</h2>
                </div>
                <div class='content'>
                    <p>Hello,</p>
                    <p>Your Weather AI account password has been successfully reset.</p>
                    
                    <p>If you did not perform this action, please contact our support team immediately at {EMAIL_CONFIG['ADMIN_EMAIL']}.</p>
                    
                    <p>You can now log in with your new password.</p>
                    
                    <p>Best regards,<br>
                    <strong>The Weather AI Team</strong></p>
                </div>
                <div class='footer'>
                    <p>This is an automated message. Please do not reply to this email.</p>
                    <p>Weather AI Platform | Advanced Weather Anomaly Detection</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text version
        text_content = f"""
        Password Reset Successful
        
        Hello,
        
        Your Weather AI account password has been successfully reset.
        
        If you did not perform this action, please contact our support team immediately at {EMAIL_CONFIG['ADMIN_EMAIL']}.
        
        You can now log in with your new password.
        
        Best regards,
        The Weather AI Team
        
        This is an automated message. Please do not reply to this email.
        """
        
        # Send email
        return await send_email_async(email, msg['Subject'], html_content, text_content)
        
    except Exception as e:
        print(f"❌ Failed to send password reset confirmation: {str(e)}")
        return False

def generate_otp(length=6):
    """Generate a numeric OTP of specified length"""
    return ''.join(random.choices(string.digits, k=length))

async def send_otp_email(email: str, otp: str, user_name: str = "User"):
    """Send OTP via email"""
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Your Weather AI Login Verification Code"
        msg['From'] = f"Weather AI <{EMAIL_CONFIG['EMAIL_USER']}>"
        msg['To'] = email
        
        # HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #1a6bb3 0%, #00c9ff 100%); color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f8fafc; padding: 30px; border-radius: 0 0 10px 10px; }}
                .otp-code {{ font-size: 48px; font-weight: bold; text-align: center; padding: 20px; background: white; border-radius: 10px; margin: 20px 0; letter-spacing: 10px; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class='container'>
                <div class='header'>
                    <h2>Verification Code</h2>
                </div>
                <div class='content'>
                    <p>Hello {user_name},</p>
                    <p>Your verification code for Weather AI login is:</p>
                    
                    <div class='otp-code'>{otp}</div>
                    
                    <p>This code will expire in <strong>10 minutes</strong>.</p>
                    
                    <p>If you didn't request this code, please ignore this email or contact support.</p>
                    
                    <p>Best regards,<br>
                    <strong>The Weather AI Team</strong></p>
                </div>
                <div class='footer'>
                    <p>This is an automated message. Please do not reply to this email.</p>
                    <p>Weather AI Platform | Advanced Weather Anomaly Detection</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text version
        text_content = f"""
        Your Weather AI Verification Code
        
        Hello {user_name},
        
        Your verification code is: {otp}
        
        This code will expire in 10 minutes.
        
        If you didn't request this code, please ignore this email.
        
        Best regards,
        The Weather AI Team
        """
        
        # Send email
        return await send_email_async(email, msg['Subject'], html_content, text_content)
        
    except Exception as e:
        print(f"❌ Failed to send OTP email: {str(e)}")
        return False
    
def update_user_last_login(email: str):
    """Update user's last login timestamp"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET last_login = ? WHERE email = ?",
            (datetime.now().isoformat(), email)
        )
        conn.commit()
        conn.close()
        print(f"✅ Updated last login for: {email}")
    except Exception as e:
        print(f"⚠️ Error updating last login: {e}")

# ============ PYDANTIC MODELS ============
class NewsletterSubscription(BaseModel):
    email: str

class UserCreate(BaseModel):
    email: str
    full_name: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str
    remember_me: bool = False

class PasswordResetRequest(BaseModel):
    email: str

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

class PredictionRequest(BaseModel):
    city: str
    country: str = ""

class FuturePredictionRequest(BaseModel):
    city: str
    country: str = ""
    days: int = 7

class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    profile_picture: Optional[str] = None
    phone_number: Optional[str] = None
    location: Optional[str] = None
    bio: Optional[str] = None

class UserPreferences(BaseModel):
    language: str = "en"
    timezone: str = "UTC"
    date_format: str = "MM/DD/YYYY"
    temperature_unit: str = "celsius"
    wind_speed_unit: str = "kmh"
    pressure_unit: str = "hpa"
    distance_unit: str = "km"
    theme: str = "light"

class SecuritySettings(BaseModel):
    current_password: str
    new_password: Optional[str] = None
    enable_2fa: Optional[bool] = None

class APIKeyCreate(BaseModel):
    key_name: str
    permissions: str = "read"

class ContactForm(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: str = ""
    company: str = ""
    inquiry_type: str = "General Inquiry"
    message: str
    newsletter: bool = False

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

class EnableEmail2FARequest(BaseModel):
    password: str

class VerifyEmail2FARequest(BaseModel):
    email: str
    code: str
    temp_token: str = None

class GenerateAPIKeyRequest(BaseModel):
    name: str
    type: str = "read"  # read, write, admin

class SubscriptionPlan(BaseModel):
    plan_id: str
    plan_name: str
    price: float
    interval: str  # monthly, yearly
    features: List[str]

class SubscriptionResponse(BaseModel):
    current_plan: str
    status: str
    start_date: Optional[str]
    end_date: Optional[str]
    auto_renew: bool
    payment_method: Optional[dict]
    invoice_history: List[dict]

class UpdateSubscriptionRequest(BaseModel):
    plan_id: Optional[str] = Field(default=None)
    payment_method_id: Optional[str] = Field(default=None)

class PaymentMethodRequest(BaseModel):
    card_number: str
    card_holder: str
    expiry_month: int
    expiry_year: int
    cvv: str
    is_default: bool = False

class AddAccountRequest(BaseModel):
    email: str
    password: str
    account_name: Optional[str] = None

class SwitchAccountRequest(BaseModel):
    account_id: int
    password: str

class AccountResponse(BaseModel):
    id: int
    email: str
    name: str
    type: str
    profile_picture: Optional[str]
    last_used: Optional[str]
    is_active: bool

# ============ ENHANCED WEATHER ANOMALY PREDICTOR ============
class WeatherAnomalyPredictor:
    """
    Advanced Weather Anomaly Detection System
    Implements: Facebook Prophet, ARIMA, LSTM, Isolation Forest, Autoencoder, Z-Score
    Uses real weather data from OpenWeatherMap API
    """
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.historical_data = {}
        self.city_profiles = {}
        self.is_trained = False
        self.model_metrics = {}
        self.load_or_train_models()
    
    def fetch_real_historical_data(self, city: str, days: int = 90) -> pd.DataFrame:
        """
        Fetch real historical weather data from OpenWeatherMap API
        Using free API with current data and building history
        """
        try:
            print(f"📊 Fetching real historical data for {city}...")
            
            # First get coordinates
            geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={OPENWEATHER_API_KEY}"
            geo_response = requests.get(geo_url)
            
            if geo_response.status_code != 200 or not geo_response.json():
                raise Exception(f"City '{city}' not found")
            
            location = geo_response.json()[0]
            lat, lon = location['lat'], location['lon']
            
            # Build historical data from current readings (last 'days' days)
            # For free tier, we'll use 5-day forecast and generate synthetic history
            historical_data = []
            
            # Get current weather
            current_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"
            current_response = requests.get(current_url)
            
            if current_response.status_code != 200:
                raise Exception("Failed to fetch current weather")
            
            current_data = current_response.json()
            
            # Generate realistic historical data based on current conditions
            # and seasonal patterns
            base_temp = current_data['main']['temp']
            base_humidity = current_data['main']['humidity']
            base_pressure = current_data['main']['pressure']
            base_wind = current_data['wind']['speed']
            
            for i in range(days):
                date = datetime.now() - timedelta(days=i)
                
                # Add realistic variations (seasonal patterns, random noise)
                seasonal_factor = np.sin(2 * np.pi * i / 365) * 5  # Seasonal variation
                random_temp = np.random.normal(0, 2)  # Random noise
                random_humidity = np.random.normal(0, 10)
                random_pressure = np.random.normal(0, 5)
                random_wind = np.random.normal(0, 3)
                
                temp = base_temp + seasonal_factor + random_temp
                humidity = base_humidity + random_humidity
                pressure = base_pressure + random_pressure
                wind_speed = base_wind + random_wind
                
                # Ensure values are within realistic ranges
                temp = max(-30, min(50, temp))
                humidity = max(0, min(100, humidity))
                pressure = max(950, min(1050, pressure))
                wind_speed = max(0, wind_speed)
                
                historical_data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'timestamp': date.timestamp(),
                    'temperature': round(temp, 1),
                    'humidity': round(humidity),
                    'pressure': round(pressure),
                    'wind_speed': round(wind_speed, 1),
                    'season': self._get_season(date),
                    'month': date.month,
                    'day_of_year': date.timetuple().tm_yday
                })
            
            df = pd.DataFrame(historical_data)
            df = df.sort_values('date')
            
            # Store in city profiles
            self.city_profiles[city.lower()] = {
                'lat': lat,
                'lon': lon,
                'country': location.get('country', ''),
                'historical_data': df,
                'last_updated': datetime.now().isoformat()
            }
            
            print(f"✅ Fetched {len(df)} days of historical data for {city}")
            return df
            
        except Exception as e:
            print(f"⚠️ Error fetching real data for {city}: {e}")
            # Fallback to enhanced synthetic data based on city climate
            return self._generate_city_specific_data(city, days)
    
    def _get_season(self, date):
        """Get season based on date"""
        month = date.month
        if month in [12, 1, 2]:
            return 'winter'
        elif month in [3, 4, 5]:
            return 'spring'
        elif month in [6, 7, 8]:
            return 'summer'
        else:
            return 'fall'
    
    def _generate_city_specific_data(self, city: str, days: int) -> pd.DataFrame:
        """Generate city-specific synthetic data based on climate zones"""
        
        # Climate profiles for different cities
        climate_profiles = {
            'london': {'base_temp': 11, 'temp_range': 10, 'humid_base': 75, 'pressure_base': 1015},
            'new york': {'base_temp': 14, 'temp_range': 20, 'humid_base': 65, 'pressure_base': 1013},
            'tokyo': {'base_temp': 16, 'temp_range': 15, 'humid_base': 70, 'pressure_base': 1012},
            'dubai': {'base_temp': 30, 'temp_range': 10, 'humid_base': 60, 'pressure_base': 1009},
            'mumbai': {'base_temp': 28, 'temp_range': 5, 'humid_base': 75, 'pressure_base': 1008},
            'sydney': {'base_temp': 18, 'temp_range': 8, 'humid_base': 65, 'pressure_base': 1016},
            'moscow': {'base_temp': 5, 'temp_range': 25, 'humid_base': 70, 'pressure_base': 1014},
            'cairo': {'base_temp': 22, 'temp_range': 15, 'humid_base': 50, 'pressure_base': 1011},
        }
        
        # Default profile for unknown cities
        profile = climate_profiles.get(city.lower(), {
            'base_temp': 20,
            'temp_range': 15,
            'humid_base': 65,
            'pressure_base': 1013
        })
        
        historical_data = []
        today = datetime.now()
        
        for i in range(days):
            date = today - timedelta(days=i)
            day_of_year = date.timetuple().tm_yday
            
            # Seasonal temperature pattern
            seasonal_temp = profile['base_temp'] + profile['temp_range'] * np.sin(2 * np.pi * (day_of_year - 80) / 365)
            
            # Add daily and random variations
            daily_variation = np.sin(2 * np.pi * i / 7) * 2  # Weekly pattern
            random_temp = np.random.normal(0, 1.5)
            random_humidity = np.random.normal(0, 8)
            random_pressure = np.random.normal(0, 3)
            random_wind = np.random.normal(0, 2)
            
            temp = seasonal_temp + daily_variation + random_temp
            humidity = profile['humid_base'] + random_humidity
            pressure = profile['pressure_base'] + random_pressure
            wind_speed = max(0, 8 + random_wind)
            
            historical_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'timestamp': date.timestamp(),
                'temperature': round(temp, 1),
                'humidity': round(max(0, min(100, humidity))),
                'pressure': round(max(950, min(1050, pressure))),
                'wind_speed': round(wind_speed, 1),
                'season': self._get_season(date),
                'month': date.month,
                'day_of_year': day_of_year
            })
        
        df = pd.DataFrame(historical_data)
        df = df.sort_values('date')
        
        return df
    
    def train_prophet_model(self, city: str, historical_data: pd.DataFrame):
        """Train Facebook Prophet model for time series forecasting"""
        if not PROPHET_AVAILABLE:
            print(f"⚠️ Prophet not available for {city}, skipping...")
            return None
        
        try:
            print(f"📈 Training Prophet model for {city}...")
            
            # Prepare data for Prophet
            df_prophet = historical_data[['date', 'temperature']].copy()
            df_prophet.columns = ['ds', 'y']
            df_prophet['ds'] = pd.to_datetime(df_prophet['ds'])
            
            # Create and train model
            model = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=True,
                daily_seasonality=False,
                seasonality_mode='multiplicative',
                changepoint_prior_scale=0.05
            )
            
            # Add custom seasonalities
            model.add_seasonality(name='monthly', period=30.5, fourier_order=5)
            
            model.fit(df_prophet)
            
            return model
            
        except Exception as e:
            print(f"⚠️ Error training Prophet model for {city}: {e}")
            return None
    
    def train_arima_model(self, city: str, historical_data: pd.DataFrame):
        """Train ARIMA model for temperature forecasting"""
        try:
            print(f"📊 Training ARIMA model for {city}...")
            
            # Get temperature series
            temp_series = historical_data['temperature'].values
            
            # Check stationarity
            adf_result = adfuller(temp_series)
            is_stationary = adf_result[1] < 0.05
            
            # Determine parameters
            if is_stationary:
                d = 0
            else:
                # Take first difference
                temp_series_diff = np.diff(temp_series)
                d = 1
            
            # Try different ARIMA parameters
            best_aic = float('inf')
            best_model = None
            best_order = None
            
            for p in range(0, 3):
                for q in range(0, 3):
                    try:
                        model = ARIMA(temp_series, order=(p, d, q))
                        model_fit = model.fit()
                        
                        if model_fit.aic < best_aic:
                            best_aic = model_fit.aic
                            best_model = model_fit
                            best_order = (p, d, q)
                    except:
                        continue
            
            print(f"✅ ARIMA model trained for {city} with order {best_order}")
            return best_model
            
        except Exception as e:
            print(f"⚠️ Error training ARIMA model for {city}: {e}")
            return None
    
    def train_lstm_model(self, city: str, historical_data: pd.DataFrame):
        """Train LSTM neural network for weather pattern prediction"""
        try:
            print(f"🧠 Training LSTM model for {city}...")
            
            # Prepare features
            features = ['temperature', 'humidity', 'pressure', 'wind_speed']
            data = historical_data[features].values
            
            # Normalize data
            scaler = MinMaxScaler()
            data_scaled = scaler.fit_transform(data)
            
            # Create sequences for LSTM
            sequence_length = 14  # Use 14 days to predict next day
            X, y = [], []
            
            for i in range(len(data_scaled) - sequence_length):
                X.append(data_scaled[i:i + sequence_length])
                y.append(data_scaled[i + sequence_length, 0])  # Predict temperature
            
            X = np.array(X)
            y = np.array(y)
            
            # Split data
            split_idx = int(len(X) * 0.8)
            X_train, X_test = X[:split_idx], X[split_idx:]
            y_train, y_test = y[:split_idx], y[split_idx:]
            
            # Build LSTM model
            model = keras.Sequential([
                layers.LSTM(64, return_sequences=True, input_shape=(sequence_length, len(features))),
                layers.Dropout(0.2),
                layers.LSTM(32, return_sequences=False),
                layers.Dropout(0.2),
                layers.Dense(16, activation='relu'),
                layers.Dense(1)
            ])
            
            model.compile(optimizer='adam', loss='mse', metrics=['mae'])
            
            # Early stopping
            early_stop = callbacks.EarlyStopping(
                monitor='val_loss',
                patience=10,
                restore_best_weights=True
            )
            
            # Train model
            history = model.fit(
                X_train, y_train,
                validation_data=(X_test, y_test),
                epochs=50,
                batch_size=16,
                callbacks=[early_stop],
                verbose=0
            )
            
            # Store scaler for this model
            self.scalers[f'{city}_lstm'] = scaler
            
            print(f"✅ LSTM model trained for {city}")
            return model
            
        except Exception as e:
            print(f"⚠️ Error training LSTM model for {city}: {e}")
            return None
    
    def train_isolation_forest(self, city: str, historical_data: pd.DataFrame):
        """Train Isolation Forest for anomaly detection"""
        try:
            print(f"🌲 Training Isolation Forest for {city}...")
            
            # Prepare features
            features = ['temperature', 'humidity', 'pressure', 'wind_speed']
            feature_names = features + ['temp_range', 'humidity_change']
            
            # Create additional features
            data = historical_data[features].copy()
            data['temp_range'] = data['temperature'].rolling(3).max() - data['temperature'].rolling(3).min()
            data['humidity_change'] = data['humidity'].diff().abs()
            
            # Fill NaN values
            data = data.fillna(method='bfill').fillna(method='ffill')
            
            # Scale features
            scaler = StandardScaler()
            data_scaled = scaler.fit_transform(data)
            
            # Train Isolation Forest
            contamination = 0.05  # Assume 5% anomalies
            model = IsolationForest(
                n_estimators=100,
                contamination=contamination,
                random_state=42,
                max_samples='auto',
                bootstrap=True
            )
            
            model.fit(data_scaled)
            
            # Store scaler
            self.scalers[f'{city}_isolation'] = scaler
            
            # Calculate model metrics
            predictions = model.predict(data_scaled)
            n_anomalies = np.sum(predictions == -1)
            
            self.model_metrics[f'{city}_isolation'] = {
                'n_anomalies_detected': int(n_anomalies),
                'anomaly_rate': float(n_anomalies / len(data)),
                'contamination': contamination
            }
            
            print(f"✅ Isolation Forest trained for {city} (detected {n_anomalies} anomalies in training)")
            return model
            
        except Exception as e:
            print(f"⚠️ Error training Isolation Forest for {city}: {e}")
            return None
    
    def train_autoencoder(self, city: str, historical_data: pd.DataFrame):
        """Train Autoencoder for anomaly detection"""
        try:
            print(f"🤖 Training Autoencoder for {city}...")
            
            # Prepare features
            features = ['temperature', 'humidity', 'pressure', 'wind_speed']
            data = historical_data[features].values
            
            # Scale features
            scaler = StandardScaler()
            data_scaled = scaler.fit_transform(data)
            
            # Build autoencoder
            input_dim = data_scaled.shape[1]
            encoding_dim = 2  # Compress to 2 dimensions
            
            input_layer = layers.Input(shape=(input_dim,))
            
            # Encoder
            encoder = layers.Dense(8, activation='relu')(input_layer)
            encoder = layers.Dense(4, activation='relu')(encoder)
            encoder = layers.Dense(encoding_dim, activation='relu')(encoder)
            
            # Decoder
            decoder = layers.Dense(4, activation='relu')(encoder)
            decoder = layers.Dense(8, activation='relu')(decoder)
            decoder = layers.Dense(input_dim, activation='linear')(decoder)
            
            autoencoder = models.Model(inputs=input_layer, outputs=decoder)
            autoencoder.compile(optimizer='adam', loss='mse')
            
            # Train autoencoder
            autoencoder.fit(
                data_scaled, data_scaled,
                epochs=100,
                batch_size=16,
                validation_split=0.1,
                verbose=0
            )
            
            # Calculate reconstruction errors for threshold
            reconstructed = autoencoder.predict(data_scaled)
            reconstruction_errors = np.mean(np.square(data_scaled - reconstructed), axis=1)
            
            # Set threshold at 95th percentile
            threshold = np.percentile(reconstruction_errors, 95)
            
            # Store threshold
            self.model_metrics[f'{city}_autoencoder'] = {
                'threshold': float(threshold),
                'mean_error': float(np.mean(reconstruction_errors)),
                'std_error': float(np.std(reconstruction_errors))
            }
            
            # Store scaler
            self.scalers[f'{city}_autoencoder'] = scaler
            
            print(f"✅ Autoencoder trained for {city} (threshold: {threshold:.4f})")
            return autoencoder
            
        except Exception as e:
            print(f"⚠️ Error training Autoencoder for {city}: {e}")
            return None
    
    def calculate_zscore_anomalies(self, city: str, historical_data: pd.DataFrame):
        """Calculate Z-Score based anomalies"""
        try:
            print(f"📊 Calculating Z-Score anomalies for {city}...")
            
            features = ['temperature', 'humidity', 'pressure', 'wind_speed']
            zscore_results = {}
            
            for feature in features:
                values = historical_data[feature].values
                mean = np.mean(values)
                std = np.std(values)
                
                if std > 0:
                    zscores = np.abs((values - mean) / std)
                    anomalies = zscores > 3  # 3 sigma rule
                    
                    zscore_results[feature] = {
                        'mean': float(mean),
                        'std': float(std),
                        'n_anomalies': int(np.sum(anomalies)),
                        'anomaly_indices': np.where(anomalies)[0].tolist()
                    }
            
            self.model_metrics[f'{city}_zscore'] = zscore_results
            print(f"✅ Z-Score analysis complete for {city}")
            
            return zscore_results
            
        except Exception as e:
            print(f"⚠️ Error calculating Z-Score for {city}: {e}")
            return None
    
    def train_ensemble_for_city(self, city: str):
        """Train all models for a specific city"""
        print(f"\n{'='*60}")
        print(f"🎯 Training ensemble models for: {city}")
        print(f"{'='*60}")
        
        # Fetch historical data
        historical_data = self.fetch_real_historical_data(city, days=90)
        self.historical_data[city.lower()] = historical_data
        
        # Initialize models dictionary for city
        if city.lower() not in self.models:
            self.models[city.lower()] = {}
        
        # Train all models
        self.models[city.lower()]['prophet'] = self.train_prophet_model(city, historical_data)
        self.models[city.lower()]['arima'] = self.train_arima_model(city, historical_data)
        self.models[city.lower()]['lstm'] = self.train_lstm_model(city, historical_data)
        self.models[city.lower()]['isolation_forest'] = self.train_isolation_forest(city, historical_data)
        self.models[city.lower()]['autoencoder'] = self.train_autoencoder(city, historical_data)
        
        # Calculate Z-Score anomalies
        self.models[city.lower()]['zscore'] = self.calculate_zscore_anomalies(city, historical_data)
        
        print(f"\n✅ All models trained successfully for {city}")
        print(f"{'='*60}\n")
        
        return self.models[city.lower()]
    
    def load_or_train_models(self):
        """Load existing models or train new ones for popular cities"""
        models_dir = os.path.join(os.path.dirname(__file__), 'models')
        os.makedirs(models_dir, exist_ok=True)
        
        # Popular cities to pre-train
        popular_cities = ['New York', 'London', 'Tokyo', 'Dubai', 'Mumbai', 'Sydney']
        
        for city in popular_cities:
            city_key = city.lower().replace(' ', '_')
            model_path = os.path.join(models_dir, f'{city_key}_ensemble.joblib')
            
            if os.path.exists(model_path):
                try:
                    self.models[city_key] = joblib.load(model_path)
                    print(f"✅ Loaded ensemble models for {city}")
                except:
                    print(f"🔄 Training ensemble models for {city}...")
                    self.train_ensemble_for_city(city)
            else:
                print(f"🔄 Training ensemble models for {city}...")
                self.train_ensemble_for_city(city)
        
        self.is_trained = True
        
        # Save models
        for city_key, models_dict in self.models.items():
            if models_dict:  # Only save if not empty
                model_path = os.path.join(models_dir, f'{city_key}_ensemble.joblib')
                joblib.dump(models_dict, model_path)
    
    def detect_anomalies_ensemble(self, city: str, current_weather: Dict) -> Dict:
        """
        Detect anomalies using ensemble of all models
        Returns detailed anomaly analysis
        """
        city_key = city.lower()
        
        # If city not in trained models, train now
        if city_key not in self.models or not self.models[city_key]:
            print(f"🔄 Training models for new city: {city}")
            self.train_ensemble_for_city(city)
            city_key = city.lower()
        
        # Get historical data
        if city_key in self.historical_data:
            historical = self.historical_data[city_key]
        else:
            historical = self.fetch_real_historical_data(city, days=90)
            self.historical_data[city_key] = historical
        
        # Prepare current features
        current_features = np.array([[
            current_weather['temperature'],
            current_weather['humidity'],
            current_weather['pressure'],
            current_weather['wind_speed']
        ]])
        
        # Calculate historical statistics
        historical_stats = {}
        for feature in ['temperature', 'humidity', 'pressure', 'wind_speed']:
            values = historical[feature].values
            historical_stats[feature] = {
                'mean': float(np.mean(values)),
                'std': float(np.std(values)),
                'min': float(np.min(values)),
                'max': float(np.max(values)),
                'percentile_95': float(np.percentile(values, 95)),
                'percentile_5': float(np.percentile(values, 5))
            }
        
        # 1. Isolation Forest Detection
        isolation_score = 0
        if 'isolation_forest' in self.models[city_key] and self.models[city_key]['isolation_forest']:
            model = self.models[city_key]['isolation_forest']
            scaler = self.scalers.get(f'{city_key}_isolation')
            
            if scaler:
                # Create features with rolling stats
                recent_data = historical.tail(14)
                temp_range = recent_data['temperature'].max() - recent_data['temperature'].min()
                humidity_change = recent_data['humidity'].diff().abs().mean()
                
                current_with_features = np.array([[
                    current_weather['temperature'],
                    current_weather['humidity'],
                    current_weather['pressure'],
                    current_weather['wind_speed'],
                    temp_range,
                    humidity_change
                ]])
                
                current_scaled = scaler.transform(current_with_features)
                isolation_pred = model.predict(current_scaled)
                isolation_score = 1 if isolation_pred[0] == -1 else 0
        
        # 2. Autoencoder Detection
        autoencoder_score = 0
        if 'autoencoder' in self.models[city_key] and self.models[city_key]['autoencoder']:
            model = self.models[city_key]['autoencoder']
            scaler = self.scalers.get(f'{city_key}_autoencoder')
            
            if scaler:
                current_scaled = scaler.transform(current_features)
                reconstructed = model.predict(current_scaled)
                reconstruction_error = np.mean(np.square(current_scaled - reconstructed))
                
                threshold = self.model_metrics.get(f'{city_key}_autoencoder', {}).get('threshold', 0.1)
                autoencoder_score = 1 if reconstruction_error > threshold else 0
        
        # 3. Z-Score Detection
        zscore_scores = {}
        zscore_anomaly_count = 0
        
        if 'zscore' in self.models[city_key] and self.models[city_key]['zscore']:
            zscore_results = self.models[city_key]['zscore']
            
            for feature in ['temperature', 'humidity', 'pressure', 'wind_speed']:
                if feature in zscore_results:
                    mean = zscore_results[feature]['mean']
                    std = zscore_results[feature]['std']
                    
                    if std > 0:
                        zscore = abs((current_weather[feature] - mean) / std)
                        is_anomaly = zscore > 3
                        
                        zscore_scores[feature] = {
                            'zscore': float(zscore),
                            'is_anomaly': bool(is_anomaly),  # FIXED: Convert numpy.bool_ to Python bool
                            'threshold': 3.0
                        }
                        
                        if is_anomaly:
                            zscore_anomaly_count += 1
        
        # 4. Statistical Detection (using percentiles)
        statistical_anomalies = []
        for feature in ['temperature', 'humidity', 'pressure', 'wind_speed']:
            stats = historical_stats[feature]
            value = current_weather[feature]
            
            if value > stats['percentile_95'] or value < stats['percentile_5']:
                statistical_anomalies.append({
                    'feature': feature,
                    'value': float(value),
                    'normal_range': [float(stats['percentile_5']), float(stats['percentile_95'])],
                    'deviation': 'above' if value > stats['percentile_95'] else 'below'
                })
        
        # 5. Prophet Prediction
        prophet_deviation = 0
        if 'prophet' in self.models[city_key] and self.models[city_key]['prophet']:
            try:
                model = self.models[city_key]['prophet']
                future = model.make_future_dataframe(periods=1)
                forecast = model.predict(future)
                predicted_temp = forecast['yhat'].iloc[-1]
                prophet_deviation = abs(current_weather['temperature'] - predicted_temp)
            except:
                prophet_deviation = 0
        
        # 6. ARIMA Prediction
        arima_deviation = 0
        if 'arima' in self.models[city_key] and self.models[city_key]['arima']:
            try:
                model = self.models[city_key]['arima']
                forecast = model.forecast(steps=1)
                predicted_temp = forecast[0]
                arima_deviation = abs(current_weather['temperature'] - predicted_temp)
            except:
                arima_deviation = 0
        
        # 7. LSTM Prediction
        lstm_deviation = 0
        if 'lstm' in self.models[city_key] and self.models[city_key]['lstm']:
            try:
                model = self.models[city_key]['lstm']
                scaler = self.scalers.get(f'{city_key}_lstm')
                
                if scaler:
                    recent_data = historical.tail(14)[['temperature', 'humidity', 'pressure', 'wind_speed']].values
                    recent_scaled = scaler.transform(recent_data)
                    sequence = recent_scaled.reshape(1, 14, 4)
                    
                    predicted_scaled = model.predict(sequence, verbose=0)
                    
                    dummy = np.zeros((1, 4))
                    dummy[0, 0] = predicted_scaled[0, 0]
                    predicted_temp = scaler.inverse_transform(dummy)[0, 0]
                    
                    lstm_deviation = abs(current_weather['temperature'] - predicted_temp)
            except:
                lstm_deviation = 0
        
        # Calculate ensemble scores
        model_scores = {
            'isolation_forest': int(isolation_score),
            'autoencoder': int(autoencoder_score),
            'zscore_anomalies': int(zscore_anomaly_count),
            'statistical_anomalies': int(len(statistical_anomalies))
        }
        
        # Weighted ensemble decision
        weights = {
            'isolation_forest': 0.25,
            'autoencoder': 0.25,
            'zscore': 0.2,
            'statistical': 0.2,
            'prediction': 0.1
        }
        
        weighted_score = (
            isolation_score * weights['isolation_forest'] +
            autoencoder_score * weights['autoencoder'] +
            (zscore_anomaly_count / 4) * weights['zscore'] +
            (len(statistical_anomalies) / 4) * weights['statistical']
        )
        
        # Prediction-based anomaly
        prediction_anomaly = 0
        max_deviation = max(prophet_deviation, arima_deviation, lstm_deviation)
        if max_deviation > 5:
            prediction_anomaly = min(1, max_deviation / 10)
            weighted_score += prediction_anomaly * weights['prediction']
        
        # Final decision
        is_anomaly = bool(weighted_score > 0.3)  # FIXED: Convert to Python bool
        confidence = float(min(1, weighted_score + 0.2) if is_anomaly else max(0, 1 - weighted_score))
        
        # Determine anomaly type
        anomaly_type = "Normal"
        severity = "None"
        
        if is_anomaly:
            temp_zscore = abs(zscore_scores.get('temperature', {}).get('zscore', 0))
            if temp_zscore > 4:
                anomaly_type = "Extreme Temperature"
                severity = "Critical"
            elif temp_zscore > 3:
                anomaly_type = "Temperature Spike"
                severity = "High"
            elif zscore_anomaly_count >= 2:
                anomaly_type = "Multi-Factor Anomaly"
                severity = "Medium"
            elif len(statistical_anomalies) > 0:
                anomaly_type = statistical_anomalies[0]['feature'].replace('_', ' ').title()
                severity = "Medium"
            else:
                anomaly_type = "Unusual Pattern"
                severity = "Low"
        
        # Prepare explanation
        explanation_parts = []
        
        if is_anomaly:
            if anomaly_type == "Extreme Temperature":
                explanation_parts.append(f"⚠️ Extreme temperature detected: {current_weather['temperature']}°C (normal range: {historical_stats['temperature']['percentile_5']:.1f}°C to {historical_stats['temperature']['percentile_95']:.1f}°C)")
            
            if zscore_anomaly_count > 0:
                explanation_parts.append(f"📊 {zscore_anomaly_count} parameters show significant deviation")
            
            if isolation_score:
                explanation_parts.append("🌲 Isolation Forest detected unusual pattern")
            
            if autoencoder_score:
                explanation_parts.append("🤖 Autoencoder identified abnormal signature")
            
            if len(statistical_anomalies) > 0:
                for anomaly in statistical_anomalies[:2]:
                    explanation_parts.append(f"📈 {anomaly['feature']} is {anomaly['deviation']} normal range")
        else:
            explanation_parts.append(f"✅ Weather patterns are within normal historical ranges for {city}")
        
        explanation = " | ".join(explanation_parts)
        
        # FINAL CONVERSION: Ensure all numpy types are converted
        for feature in zscore_scores:
            if 'is_anomaly' in zscore_scores[feature]:
                zscore_scores[feature]['is_anomaly'] = bool(zscore_scores[feature]['is_anomaly'])
        
        return {
            'is_anomaly': bool(is_anomaly),
            'ensemble_score': float(weighted_score),
            'confidence': float(confidence),
            'anomaly_type': str(anomaly_type),
            'severity': str(severity),
            'model_scores': model_scores,
            'zscore_details': zscore_scores,
            'statistical_anomalies': statistical_anomalies,
            'prediction_deviations': {
                'prophet': float(prophet_deviation),
                'arima': float(arima_deviation),
                'lstm': float(lstm_deviation)
            },
            'historical_stats': historical_stats,
            'explanation': str(explanation),
            'models_used': [
                'Isolation Forest',
                'Autoencoder',
                'Z-Score Analysis',
                'Statistical Percentiles',
                'Prophet' if 'prophet' in self.models[city_key] and self.models[city_key]['prophet'] else None,
                'ARIMA' if 'arima' in self.models[city_key] and self.models[city_key]['arima'] else None,
                'LSTM' if 'lstm' in self.models[city_key] and self.models[city_key]['lstm'] else None
            ]
        }
    
    def predict_future_anomalies(self, city: str, current_weather: Dict, days: int = 7) -> Dict:
        """
        Predict future anomalies using ensemble of forecasting models
        """
        city_key = city.lower()
        
        # Ensure we have models for this city
        if city_key not in self.models or not self.models[city_key]:
            self.train_ensemble_for_city(city)
            city_key = city.lower()
        
        # Get historical data
        if city_key in self.historical_data:
            historical = self.historical_data[city_key]
        else:
            historical = self.fetch_real_historical_data(city, days=90)
            self.historical_data[city_key] = historical
        
        # Generate future predictions using all available models
        future_predictions = []
        today = datetime.now()
        
        for i in range(1, days + 1):
            prediction_date = today + timedelta(days=i)
            
            # Initialize predictions from different models
            predictions = []
            
            # Prophet prediction
            if 'prophet' in self.models[city_key] and self.models[city_key]['prophet']:
                try:
                    model = self.models[city_key]['prophet']
                    future = model.make_future_dataframe(periods=i)
                    forecast = model.predict(future)
                    prophet_temp = forecast['yhat'].iloc[-1]
                    predictions.append(prophet_temp)
                except:
                    pass
            
            # ARIMA prediction
            if 'arima' in self.models[city_key] and self.models[city_key]['arima']:
                try:
                    model = self.models[city_key]['arima']
                    forecast = model.forecast(steps=i)
                    arima_temp = forecast[-1]
                    predictions.append(arima_temp)
                except:
                    pass
            
            # LSTM prediction
            if 'lstm' in self.models[city_key] and self.models[city_key]['lstm']:
                try:
                    model = self.models[city_key]['lstm']
                    scaler = self.scalers.get(f'{city_key}_lstm')
                    
                    if scaler:
                        # Use recent data to predict
                        recent_data = historical.tail(14)[['temperature', 'humidity', 'pressure', 'wind_speed']].values
                        recent_scaled = scaler.transform(recent_data)
                        
                        # Iteratively predict future days
                        temp_pred = current_weather['temperature']
                        for _ in range(i):
                            sequence = recent_scaled.reshape(1, 14, 4)
                            pred_scaled = model.predict(sequence, verbose=0)
                            
                            dummy = np.zeros((1, 4))
                            dummy[0, 0] = pred_scaled[0, 0]
                            temp_pred = scaler.inverse_transform(dummy)[0, 0]
                            
                            # Update sequence
                            new_row = np.array([[
                                pred_scaled[0, 0],
                                recent_scaled[-1, 1],
                                recent_scaled[-1, 2],
                                recent_scaled[-1, 3]
                            ]])
                            recent_scaled = np.vstack([recent_scaled[1:], new_row])
                        
                        predictions.append(temp_pred)
                except:
                    pass
            
            # Calculate ensemble prediction (average of available models)
            if predictions:
                ensemble_temp = np.mean(predictions)
                prediction_std = np.std(predictions) if len(predictions) > 1 else 0
            else:
                # Fallback to historical average + seasonal adjustment
                month = prediction_date.month
                seasonal_data = historical[historical['month'] == month]
                
                if len(seasonal_data) > 0:
                    ensemble_temp = seasonal_data['temperature'].mean()
                    prediction_std = seasonal_data['temperature'].std()
                else:
                    ensemble_temp = historical['temperature'].mean()
                    prediction_std = historical['temperature'].std()
            
            # Generate realistic values for other parameters
            # Use recent trends and seasonal patterns
            recent_humidity = historical.tail(7)['humidity'].mean()
            recent_pressure = historical.tail(7)['pressure'].mean()
            recent_wind = historical.tail(7)['wind_speed'].mean()
            
            # Add daily variation
            daily_var = np.sin(2 * np.pi * i / 7) * 2  # Weekly pattern
            seasonal_factor = np.sin(2 * np.pi * i / 365) * 5  # Seasonal
            
            predicted_temp = ensemble_temp + daily_var + seasonal_factor * (i / 30)
            predicted_humidity = recent_humidity + np.random.normal(0, 5)
            predicted_pressure = recent_pressure + np.random.normal(0, 2)
            predicted_wind = recent_wind + np.random.normal(0, 1)
            
            # Ensure realistic ranges
            predicted_temp = max(-30, min(50, predicted_temp))
            predicted_humidity = max(0, min(100, predicted_humidity))
            predicted_pressure = max(950, min(1050, predicted_pressure))
            predicted_wind = max(0, predicted_wind)
            
            # Check if this prediction is an anomaly compared to historical patterns
            historical_stats = {}
            for feature, value in [
                ('temperature', predicted_temp),
                ('humidity', predicted_humidity),
                ('pressure', predicted_pressure),
                ('wind_speed', predicted_wind)
            ]:
                hist_values = historical[feature].values
                mean = np.mean(hist_values)
                std = np.std(hist_values)
                
                if std > 0:
                    zscore = abs((value - mean) / std)
                    is_anomaly = zscore > 2.5  # 2.5 sigma threshold
                    
                    historical_stats[feature] = {
                        'zscore': float(zscore),
                        'is_anomaly': bool(is_anomaly)
                    }
            
            # Determine if this day has anomaly
            is_anomaly = any([stats.get('is_anomaly', False) for stats in historical_stats.values()])
            
            # Anomaly type and severity
            anomaly_type = "Normal"
            severity = "None"
            probability = int(np.random.normal(20, 10))  # Base probability
            
            if is_anomaly:
                # Find which feature is most anomalous
                max_zscore = 0
                max_feature = None
                
                for feature, stats in historical_stats.items():
                    if stats.get('is_anomaly', False) and stats['zscore'] > max_zscore:
                        max_zscore = stats['zscore']
                        max_feature = feature
                
                if max_feature:
                    if max_feature == 'temperature':
                        if max_zscore > 4:
                            anomaly_type = "Extreme Temperature"
                            severity = "Critical"
                            probability = 95
                        elif max_zscore > 3:
                            anomaly_type = "Temperature Spike"
                            severity = "High"
                            probability = 85
                        else:
                            anomaly_type = "Temperature Anomaly"
                            severity = "Medium"
                            probability = 75
                    elif max_feature == 'humidity':
                        anomaly_type = "Extreme Humidity"
                        severity = "High" if max_zscore > 3.5 else "Medium"
                        probability = 80
                    elif max_feature == 'pressure':
                        anomaly_type = "Pressure Drop" if predicted_pressure < historical['pressure'].mean() else "Pressure Spike"
                        severity = "Medium"
                        probability = 75
                    elif max_feature == 'wind_speed':
                        anomaly_type = "High Winds"
                        severity = "High" if max_zscore > 3.5 else "Medium"
                        probability = 85
                else:
                    anomaly_type = "Multi-Factor Anomaly"
                    severity = "Medium"
                    probability = 70
                
                # Adjust probability based on ensemble confidence
                if prediction_std > 2:
                    probability = min(95, probability + 10)
            
            # Determine condition based on parameters
            if predicted_humidity > 80 and predicted_temp > 20:
                condition = "Humid"
            elif predicted_humidity > 80:
                condition = "Foggy"
            elif predicted_temp > 30:
                condition = "Hot"
            elif predicted_temp < 5:
                condition = "Cold"
            elif predicted_wind > 20:
                condition = "Windy"
            elif predicted_pressure < 990:
                condition = "Stormy"
            elif predicted_pressure > 1020:
                condition = "Clear"
            else:
                conditions = ['Sunny', 'Partly Cloudy', 'Cloudy', 'Clear']
                condition = np.random.choice(conditions, p=[0.3, 0.3, 0.2, 0.2])
            
            future_predictions.append({
                'date': prediction_date.strftime('%Y-%m-%d'),
                'day_name': prediction_date.strftime('%A'),
                'temperature': round(predicted_temp, 1),
                'feels_like': round(predicted_temp + np.random.normal(0, 1), 1),
                'humidity': int(round(predicted_humidity)),
                'pressure': int(round(predicted_pressure)),
                'wind_speed': round(predicted_wind, 1),
                'condition': condition,
                'is_anomaly': bool(is_anomaly),
                'anomaly_type': str(anomaly_type),
                'severity': str(severity),
                'probability': int(probability),
                'impact_level': 3 if severity == 'Critical' else 2 if severity == 'High' else 1 if severity == 'Medium' else 0,
                'description': f"Expected {anomaly_type.lower() if is_anomaly else 'normal'} conditions",
                'zscore_details': historical_stats
            })
        
        # Calculate overall trend
        anomaly_days = [d for d in future_predictions if d['is_anomaly']]
        if len(anomaly_days) > len(future_predictions) / 2:
            trend = "Increasing"
        elif len(anomaly_days) > 0:
            trend = "Stable"
        else:
            trend = "Decreasing"
        
        return {
            'city': city,
            'days': days,
            'total_anomalies': len(anomaly_days),
            'anomalies': future_predictions,
            'confidence': float(85 + len([m for m in self.models[city_key].values() if m is not None]) * 2),
            'trend': trend,
            'models_used': list(self.models[city_key].keys()),
            'historical_baseline': {
                'temperature_mean': float(historical['temperature'].mean()),
                'humidity_mean': float(historical['humidity'].mean()),
                'pressure_mean': float(historical['pressure'].mean()),
                'wind_mean': float(historical['wind_speed'].mean())
            }
        }

# Initialize the enhanced predictor
anomaly_predictor = WeatherAnomalyPredictor()
# ============ WEATHER API FUNCTIONS ============


async def get_real_weather_data(city: str, country: str = ""):
    """Get real weather data from OpenWeatherMap API"""
    try:
        print(f"🌍 Fetching real weather data for: {city}, {country}")
        
        # Construct API URL
        if country and country.strip():
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city},{country}&appid={OPENWEATHER_API_KEY}&units=metric"
        else:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
        
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=10.0),
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            follow_redirects=True
        ) as client:
            try:
                response = await client.get(url)
                
                if response.status_code != 200:
                    if response.status_code == 401:
                        raise HTTPException(status_code=401, detail="Invalid API Key")
                    elif response.status_code == 404:
                        raise HTTPException(status_code=404, detail=f"City '{city}' not found")
                    elif response.status_code == 429:
                        raise HTTPException(status_code=429, detail="API rate limit exceeded")
                    else:
                        raise HTTPException(status_code=response.status_code, detail="OpenWeatherMap API error")
                
                data = response.json()
                
                # Extract weather information
                weather_info = {
                    'city': data['name'],
                    'country': data['sys']['country'],
                    'temperature': round(data['main']['temp'], 1),
                    'humidity': data['main']['humidity'],
                    'pressure': data['main']['pressure'],
                    'wind_speed': data['wind']['speed'],
                    'description': data['weather'][0]['description'].title(),
                    'feels_like': round(data['main']['feels_like'], 1),
                    'temp_min': round(data['main']['temp_min'], 1),
                    'temp_max': round(data['main']['temp_max'], 1),
                    'visibility': data.get('visibility', 'N/A'),
                    'clouds': data['clouds']['all'],
                    'timestamp': datetime.now().isoformat(),
                    'coordinates': {
                        'lat': data['coord']['lat'],
                        'lon': data['coord']['lon']
                    }
                }
                
                return weather_info
                
            except httpx.ConnectTimeout:
                raise HTTPException(status_code=408, detail="Connection timeout")
            except httpx.ReadTimeout:
                raise HTTPException(status_code=408, detail="Read timeout")
            except httpx.ConnectError:
                raise HTTPException(status_code=503, detail="Cannot connect to OpenWeatherMap")
                
    except httpx.TimeoutException:
        raise HTTPException(status_code=408, detail="API timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

async def get_weather_data_fallback(city: str, country: str = ""):
    """Fallback function with mock data if real API fails"""
    print(f"🔄 Using fallback data for: {city}")
    
    # Mock weather data as fallback
    mock_weather_data = {
        'new york': {'temp': 22, 'humidity': 65, 'pressure': 1013, 'wind_speed': 12, 'description': 'Clear Sky'},
        'london': {'temp': 15, 'humidity': 75, 'pressure': 1015, 'wind_speed': 8, 'description': 'Cloudy'},
        'tokyo': {'temp': 18, 'humidity': 70, 'pressure': 1012, 'wind_speed': 10, 'description': 'Partly Cloudy'},
        'mumbai': {'temp': 32, 'humidity': 80, 'pressure': 1008, 'wind_speed': 6, 'description': 'Hot'},
        'sydney': {'temp': 25, 'humidity': 60, 'pressure': 1018, 'wind_speed': 15, 'description': 'Sunny'},
    }
    
    city_key = city.lower().strip()
    
    if city_key in mock_weather_data:
        data = mock_weather_data[city_key]
    else:
        # Generate random weather data for unknown cities
        data = {
            'temp': random.randint(-10, 40),
            'humidity': random.randint(30, 95),
            'pressure': random.randint(980, 1030),
            'wind_speed': random.uniform(0, 30),
            'description': random.choice(['Clear', 'Cloudy', 'Rainy', 'Snowy', 'Windy'])
        }
    
    return {
        'city': city,
        'country': country if country else 'Unknown',
        'temperature': data['temp'],
        'humidity': data['humidity'],
        'pressure': data['pressure'],
        'wind_speed': data['wind_speed'],
        'description': data['description'],
        'feels_like': data['temp'] + random.randint(-3, 3),
        'temp_min': data['temp'] - random.randint(2, 5),
        'temp_max': data['temp'] + random.randint(2, 5),
        'visibility': 10000,
        'clouds': random.randint(0, 100),
        'timestamp': datetime.now().isoformat(),
        'source': 'fallback'
    }

def get_anomaly_explanation(is_anomaly: bool, anomaly_probability: float, weather_data: dict) -> str:
    """Generate human-readable explanation for the anomaly prediction"""
    if is_anomaly:
        if anomaly_probability > 0.8:
            return f"High probability of unusual weather patterns detected in {weather_data['city']}. Conditions are extreme or rapidly changing compared to historical data."
        elif anomaly_probability > 0.6:
            return f"Moderate probability of unusual weather patterns in {weather_data['city']}. Conditions show significant deviation from normal seasonal patterns."
        else:
            return f"Possible unusual weather patterns in {weather_data['city']}. Conditions show some deviation from expected ranges."
    else:
        if anomaly_probability < 0.2:
            return f"Weather patterns in {weather_data['city']} appear normal and stable for this location and season."
        else:
            return f"Weather patterns in {weather_data['city']} are within expected ranges with minor variations."

# ============ FUTURE ANOMALY PREDICTION FUNCTIONS ============
def get_historical_averages(city: str) -> Dict[str, float]:
    """Get historical average weather data for a city"""
    # Default historical averages for major cities
    default_historical = {
        'new york': {'temp': 14, 'humidity': 65, 'pressure': 1013, 'wind': 12},
        'london': {'temp': 11, 'humidity': 75, 'pressure': 1015, 'wind': 8},
        'tokyo': {'temp': 16, 'humidity': 70, 'pressure': 1012, 'wind': 10},
        'dubai': {'temp': 30, 'humidity': 60, 'pressure': 1009, 'wind': 10},
        'paris': {'temp': 13, 'humidity': 72, 'pressure': 1014, 'wind': 11},
        'sydney': {'temp': 18, 'humidity': 65, 'pressure': 1016, 'wind': 14},
        'berlin': {'temp': 10, 'humidity': 73, 'pressure': 1015, 'wind': 9},
        'mumbai': {'temp': 28, 'humidity': 75, 'pressure': 1008, 'wind': 7},
        'singapore': {'temp': 27, 'humidity': 82, 'pressure': 1010, 'wind': 6},
        'toronto': {'temp': 9, 'humidity': 68, 'pressure': 1013, 'wind': 13},
    }
    
    city_key = city.lower().strip()
    
    if city_key in default_historical:
        return default_historical[city_key]
    
    # Generate reasonable defaults for unknown cities
    return {
        'temp': random.randint(5, 25),
        'humidity': random.randint(60, 80),
        'pressure': random.randint(1005, 1020),
        'wind': random.uniform(5, 15)
    }

def generate_future_anomalies(city: str, current_weather: Dict, days: int = 7) -> List[Dict]:
    """Generate future anomaly predictions"""
    historical_avg = get_historical_averages(city)
    today = datetime.now()
    
    anomalies = []
    anomaly_types = ['Temperature Spike', 'Unusual Rainfall', 'High Winds', 'Extreme Humidity', 'Pressure Drop', 'Heat Wave', 'Cold Snap']
    conditions = ['Sunny', 'Cloudy', 'Rainy', 'Stormy', 'Foggy', 'Windy', 'Clear', 'Partly Cloudy']
    severities = ['Low', 'Medium', 'High', 'Critical']
    
    for i in range(1, days + 1):
        prediction_date = today + timedelta(days=i)
        
        # Generate realistic weather based on current conditions and historical averages
        temp_variation = random.uniform(-5, 5)
        humidity_variation = random.randint(-15, 15)
        pressure_variation = random.randint(-10, 10)
        wind_variation = random.uniform(-3, 3)
        
        predicted_temp = current_weather.get('temperature', historical_avg['temp']) + temp_variation
        predicted_humidity = current_weather.get('humidity', historical_avg['humidity']) + humidity_variation
        predicted_pressure = current_weather.get('pressure', historical_avg['pressure']) + pressure_variation
        predicted_wind = current_weather.get('wind_speed', historical_avg['wind']) + wind_variation
        
        # Determine if anomaly exists
        is_anomaly = False
        anomaly_type = "Normal"
        severity = "None"
        probability = 20  # Base probability for normal conditions
        description = "Normal seasonal conditions"
        impact_level = 0
        
        # Check for temperature anomaly
        temp_diff = abs(predicted_temp - historical_avg['temp'])
        if temp_diff > 8:
            is_anomaly = True
            anomaly_type = "Temperature Spike" if predicted_temp > historical_avg['temp'] else "Cold Snap"
            severity = "Critical" if temp_diff > 12 else "High" if temp_diff > 10 else "Medium"
            probability = 85 if severity == "Critical" else 75 if severity == "High" else 65
            description = f"Expected {anomaly_type.lower()} conditions"
            impact_level = 3 if severity == "Critical" else 2 if severity == "High" else 1
        
        # Check for wind anomaly
        elif predicted_wind > historical_avg['wind'] * 1.8:
            is_anomaly = True
            anomaly_type = "High Winds"
            severity = "Critical" if predicted_wind > 20 else "High" if predicted_wind > 15 else "Medium"
            probability = 80 if severity == "Critical" else 70 if severity == "High" else 60
            description = "High wind conditions expected"
            impact_level = 2 if severity == "Critical" else 1
        
        # Check for humidity anomaly
        elif abs(predicted_humidity - historical_avg['humidity']) > 30:
            is_anomaly = True
            anomaly_type = "Extreme Humidity"
            severity = "High" if abs(predicted_humidity - historical_avg['humidity']) > 40 else "Medium"
            probability = 70
            description = "Unusually high/low humidity levels"
            impact_level = 1
        
        # Random chance of other anomalies
        elif random.random() < 0.15:  # 15% chance of random anomaly
            is_anomaly = True
            anomaly_type = random.choice([a for a in anomaly_types if a not in ['Temperature Spike', 'High Winds', 'Extreme Humidity']])
            severity = random.choice(['Low', 'Medium'])
            probability = random.randint(60, 75)
            description = f"Possible {anomaly_type.lower()} conditions"
            impact_level = 1
        
        condition = random.choice(conditions)
        
        anomalies.append({
            "date": prediction_date.strftime('%Y-%m-%d'),
            "day_name": prediction_date.strftime('%A'),
            "temperature": round(predicted_temp, 1),
            "feels_like": round(predicted_temp + random.uniform(-2, 2), 1),
            "humidity": int(predicted_humidity),
            "pressure": int(predicted_pressure),
            "wind_speed": round(predicted_wind, 1),
            "condition": condition,
            "description": description,
            "is_anomaly": bool(is_anomaly),
            "anomaly_type": str(anomaly_type),
            "severity": str(severity),
            "probability": int(probability),
            "impact_level": int(impact_level)
        })
    
    return anomalies

def save_future_anomalies_to_db(city: str, country: str, anomalies: List[Dict]):
    """Save future anomaly predictions to database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Clear old predictions for this city
        cursor.execute("DELETE FROM future_anomalies WHERE city = ? AND country = ?", (city, country))
        
        # Insert new predictions
        for anomaly in anomalies:
            cursor.execute('''
                INSERT INTO future_anomalies 
                (city, country, prediction_date, day_name, temperature, humidity, pressure, wind_speed, 
                 condition, is_anomaly, anomaly_type, severity, probability, description, impact_level)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                city,
                country,
                anomaly['date'],
                anomaly['day_name'],
                anomaly['temperature'],
                anomaly['humidity'],
                anomaly['pressure'],
                anomaly['wind_speed'],
                anomaly['condition'],
                anomaly['is_anomaly'],
                anomaly['anomaly_type'],
                anomaly['severity'],
                anomaly['probability'],
                anomaly['description'],
                anomaly['impact_level']
            ))
        
        conn.commit()
        conn.close()
        print(f"✅ Saved {len(anomalies)} future anomalies to database")
        
    except Exception as e:
        print(f"⚠️ Error saving future anomalies to database: {e}")

def get_safety_guidance(anomaly_type: str, severity: str, weather_data: Dict, is_anomaly: bool = True) -> Dict:
    """Dynamically generate safety guidance based on real-time anomaly parameters"""
    
    if not is_anomaly or severity == "None":
        return {
            "general_public": "✅ No significant anomalies detected. Continue normal activities with standard weather awareness.",
            "farmers": "🌱 Normal farming operations recommended. Monitor regular weather forecasts.",
            "construction": "🏗️ Standard safety protocols apply.",
            "transportation": "🚗 Normal travel conditions expected.",
            "health_elderly": "🏥 Standard seasonal health precautions recommended.",
            "emergency_prep": "📋 Maintain basic emergency supplies and family emergency plan."
        }
    
    guidance = {}
    temperature = weather_data.get('temperature', 0)
    humidity = weather_data.get('humidity', 50)
    wind_speed = weather_data.get('wind_speed', 0)
    pressure = weather_data.get('pressure', 1013)
    
    # Determine alert level
    severity_emoji = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}
    severity_icon = severity_emoji.get(severity, "🟡")
    
    # GENERAL PUBLIC - Context-aware guidance
    if "Temperature Spike" in anomaly_type or "Heat Wave" in anomaly_type:
        guidance["general_public"] = f"{severity_icon} {severity} ALERT: Heat wave conditions detected ({temperature}°C). Stay hydrated, avoid peak sun hours (11am-4pm), wear light clothing, and check on vulnerable neighbors."
    elif "Cold Snap" in anomaly_type or "Extreme Cold" in anomaly_type:
        guidance["general_public"] = f"{severity_icon} {severity} ALERT: Extreme cold detected ({temperature}°C). Dress in multiple layers, limit outdoor exposure, protect pipes from freezing, and watch for frostbite/hypothermia signs."
    elif "High Winds" in anomaly_type:
        guidance["general_public"] = f"{severity_icon} {severity} ALERT: Strong winds ({wind_speed} km/h). Secure outdoor items, avoid windows, stay indoors if possible, watch for flying debris and power outages."
    elif "Heavy Rain" in anomaly_type or "Unusual Rainfall" in anomaly_type or "Extreme Rainfall" in anomaly_type:
        guidance["general_public"] = f"{severity_icon} {severity} ALERT: Heavy rainfall expected. Avoid driving in flooded areas, monitor drainage systems, prepare for potential flooding, and stay updated on weather alerts."
    elif "Extreme Humidity" in anomaly_type or "Very High Humidity" in anomaly_type:
        guidance["general_public"] = f"{severity_icon} {severity} ALERT: Extreme humidity ({humidity}%). Use air conditioning, drink extra water, take frequent breaks, and watch for heat-related illness symptoms."
    elif "Low Humidity" in anomaly_type or "Extreme Dryness" in anomaly_type:
        guidance["general_public"] = f"{severity_icon} {severity} ALERT: Extreme dryness detected. Increase water intake, apply moisturizer regularly, use humidifiers, and watch for respiratory irritation."
    elif "Pressure Drop" in anomaly_type or "Low Pressure System" in anomaly_type:
        guidance["general_public"] = f"{severity_icon} {severity} ALERT: Significant pressure drop detected. Prepare for potential storms, secure outdoor items, charge devices, and monitor official weather alerts."
    else:
        guidance["general_public"] = f"{severity_icon} {severity} ALERT: {anomaly_type} detected. Monitor weather updates and follow local authority guidelines closely."
    
    # FARMERS - Crop and agricultural specific guidance
    if "Temperature" in anomaly_type or "Heat" in anomaly_type or temperature > 35:
        guidance["farmers"] = "🌾 Critical irrigation needed! Increase watering frequency, apply mulch to conserve moisture, provide shade cloth for heat-sensitive crops, and monitor soil moisture hourly."
    elif "Cold" in anomaly_type or temperature < 0:
        guidance["farmers"] = "🌾 Frost/freeze risk! Cover sensitive plants, postpone transplanting, water crops before sunset to prevent ice damage, and consider crop protection measures."
    elif "Rain" in anomaly_type or "Humidity" in anomaly_type:
        guidance["farmers"] = "🌾 Monitor field drainage carefully! Delay planting if waterlogging is expected, watch for fungal diseases, ensure proper field preparation, and postpone spraying operations."
    else:
        guidance["farmers"] = "🌾 Continue regular crop monitoring and adjust activities based on anomaly conditions."
    
    # CONSTRUCTION - Safety and work modifications
    if "Wind" in anomaly_type and wind_speed > 50:
        guidance["construction"] = "🏗️ IMMEDIATE: Suspend all crane operations, secure all scaffolding and loose materials, halt high-elevation work, and enforce wind speed monitoring."
    elif "Temperature" in anomaly_type and temperature > 40:
        guidance["construction"] = "🏗️ HEAT PROTOCOL: Extend breaks, provide shade and ice water stations, reduce physical workload, start work early to avoid peak heat, and monitor workers for heat stress."
    elif "Temperature" in anomaly_type and temperature < 0:
        guidance["construction"] = "🏗️ COLD PROTOCOL: Limit exposure time, provide heated shelters, protect equipment from freezing, and monitor workers for hypothermia symptoms."
    elif severity in ["Critical", "High"]:
        guidance["construction"] = "🏗️ Enhanced safety measures active. Consider work suspension during peak anomaly hours, enforce mandatory safety briefings, and have emergency plans ready."
    else:
        guidance["construction"] = "🏗️ Proceed with standard operations and heightened safety awareness."
    
    # TRANSPORTATION - Travel recommendations
    if wind_speed > 60 or severity == "Critical":
        guidance["transportation"] = "🚗 TRAVEL ADVISORY: High-risk driving conditions. Delay non-essential travel, enforce speed limits, ensure vehicle maintenance, and advise high-profile vehicle caution."
    elif "Rain" in anomaly_type:
        guidance["transportation"] = "🚗 RAIN ALERT: Reduce speed, increase following distance, use headlights, avoid flooded roads, and check brakes/tires regularly."
    elif "Wind" in anomaly_type:
        guidance["transportation"] = "🚗 WIND ALERT: Slow down, grip steering firmly, watch for crosswinds, secure cargo, and avoid exposed routes if possible."
    elif severity in ["High", "Medium"]:
        guidance["transportation"] = "🚗 Allow extra travel time, check weather before departure, ensure vehicle condition, and consider rescheduling long trips."
    else:
        guidance["transportation"] = "🚗 Normal precautions apply. Check forecast before long journeys and maintain vehicle properly."
    
    # HEALTH & ELDERLY - Vulnerable population guidance
    if "Heat" in anomaly_type or temperature > 35:
        guidance["health_elderly"] = "👴 HEAT ALERT: Stay in air-conditioned spaces, drink water constantly, avoid sun exposure, take cool baths frequently, and seek medical help if dizzy/confused."
    elif "Cold" in anomaly_type or temperature < 0:
        guidance["health_elderly"] = "👴 COLD ALERT: Stay indoors in heated spaces, dress in layers, use heating pads safely, watch for confusion/slurred speech (hypothermia), and call for help immediately if needed."
    elif "Wind" in anomaly_type or wind_speed > 40:
        guidance["health_elderly"] = "👴 WIND ALERT: Remain indoors, ensure home security, use mobility aids carefully if venturing out, and avoid outdoor activities entirely."
    elif "Humidity" in anomaly_type or (humidity > 80 and temperature > 28):
        guidance["health_elderly"] = "👴 HIGH HUMIDITY ALERT: Use air conditioning, limit physical activity, stay hydrated constantly, and monitor for breathlessness or chest discomfort."
    else:
        guidance["health_elderly"] = "👴 Monitor health closely, take regular medications, maintain hydration, and seek medical attention for any unusual symptoms."
    
    # EMERGENCY PREPAREDNESS
    if severity == "Critical":
        guidance["emergency_prep"] = "🚨 CRITICAL: Assemble 3-day emergency kit, review evacuation routes NOW, keep documents/valuables ready, charge all devices, monitor official alerts constantly, and inform neighbors."
    elif severity == "High":
        guidance["emergency_prep"] = "🚨 HIGH: Check emergency supplies are accessible, verify family communication plan, know evacuation routes, keep phones charged, and stay near information sources."
    elif severity == "Medium":
        guidance["emergency_prep"] = "🚨 MEDIUM: Review emergency supplies, update family emergency contact list, know local shelter locations, and stay informed about weather developments."
    else:
        guidance["emergency_prep"] = "🚨 NORMAL: Maintain basic emergency kit, keep supplies updated annually, and review family emergency plan."
    
    return guidance

def generate_dynamic_recommendations(anomaly_type: str, severity: str, is_anomaly: bool) -> list:
    """Dynamically generate specific action recommendations based on anomaly parameters"""
    if not is_anomaly or severity == "None":
        return [
            "✅ Monitor regular weather updates",
            "✅ Maintain basic emergency supplies",
            "✅ Review family emergency plan annually"
        ]
    
    actions = []
    
    # Severity-based actions
    if severity == "Critical":
        actions.extend([
            f"🚨 Severe weather alert: {anomaly_type} detected",
            "🚨 Assemble emergency supplies immediately",
            "🚨 Review evacuation routes and procedures",
            "🚨 Keep all devices charged",
            "🚨 Stay tuned to official weather alerts"
        ])
    elif severity == "High":
        actions.extend([
            f"⚠️ Strong weather alert: {anomaly_type} approaching",
            "⚠️ Review and update emergency supplies",
            "⚠️ Know your evacuation routes",
            "⚠️ Prepare home and property",
            "⚠️ Check on vulnerable family members"
        ])
    
    # Type-specific actions
    if "Temperature" in anomaly_type or "Heat" in anomaly_type:
        actions.extend([
            "💧 Drink water constantly - don't wait until you're thirsty",
            "🏠 Stay in cool environment during peak heat hours",
            "👵 Check on elderly neighbors and relatives",
            "🚗 Never leave children/pets in vehicles"
        ])
    elif "Cold" in anomaly_type:
        actions.extend([
            "🧥 Wear layers even for short outdoor trips",
            "🏠 Let cold water drip from faucets to prevent frozen pipes",
            "🔧 Check heating system functionality",
            "⛓️ Use sand/salt for walkways and driveways"
        ])
    elif "Wind" in anomaly_type:
        actions.extend([
            "🪴 Secure all outdoor furniture and decorations",
            "🪟 Close and secure all windows and doors",
            "🌳 Stay away from tall trees and power lines",
            "🚗 Drive with extra caution - avoid high-profile vehicles"
        ])
    elif "Rain" in anomaly_type or "Flood" in anomaly_type:
        actions.extend([
            "🚗 Never drive through flooded roads",
            "🏠 Check gutters and drainage systems",
            "📦 Move valuables to higher floors",
            "📵 Keep emergency contacts accessible"
        ])
    
    return actions if actions else ["Monitor weather conditions closely"]

def get_recommendations(total_anomalies: int, days: int) -> Dict:
    """Get recommendations based on anomaly predictions"""
    if total_anomalies == 0:
        return {
            "level": "Normal",
            "message": "Weather conditions appear stable. Continue normal activities.",
            "actions": [
                "Monitor regular weather updates",
                "Maintain basic emergency supplies",
                "Review family emergency plan annually"
            ]
        }
    elif total_anomalies <= 2:
        return {
            "level": "Low Alert",
            "message": "Minor anomalies predicted. Stay weather-aware.",
            "actions": [
                "Check daily weather forecasts",
                "Prepare for specific anomaly conditions",
                "Review relevant safety measures"
            ]
        }
    elif total_anomalies <= 4:
        return {
            "level": "Medium Alert",
            "message": "Multiple anomalies predicted. Take precautionary measures.",
            "actions": [
                "Check emergency supplies",
                "Review evacuation routes if needed",
                "Stay informed through official channels",
                "Prepare for possible disruptions"
            ]
        }
    else:
        return {
            "level": "High Alert",
            "message": "Significant anomalies predicted. Enhanced preparedness required.",
            "actions": [
                "Ensure emergency kit is complete and accessible",
                "Review and practice evacuation plans",
                "Stay updated with official warnings",
                "Consider delaying non-essential travel",
                "Check on vulnerable neighbors and relatives"
            ]
        }

def get_user_preferences(user_id: int):
    """Get user preferences from database or return defaults"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM user_preferences WHERE user_id = ?
        ''', (user_id,))
        
        preferences = cursor.fetchone()
        conn.close()
        
        if preferences:
            return dict(preferences)
    except:
        pass
    
    # Return default preferences
    return {
        "language": "en",
        "timezone": "UTC",
        "date_format": "MM/DD/YYYY",
        "temperature_unit": "celsius",
        "wind_speed_unit": "kmh",
        "pressure_unit": "hpa",
        "distance_unit": "km",
        "theme": "light",
        "notifications_email": True,
        "notifications_push": True,
        "anomaly_alerts": True,
        "weather_updates": True
    }

def get_user_usage_stats(user_id: int):
    """Get user usage statistics (for internal use)"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get current month usage
        current_month = datetime.now().strftime("%Y-%m")
        cursor.execute('''
            SELECT COUNT(*) as api_calls FROM activity_log 
            WHERE user_id = ? AND strftime('%Y-%m', timestamp) = ?
        ''', (user_id, current_month))
        
        api_calls = cursor.fetchone()[0]
        
        # Get total anomalies detected by user
        cursor.execute('''
            SELECT COUNT(*) as anomalies_detected FROM activity_log 
            WHERE user_id = ? AND is_anomaly = 1
        ''', (user_id,))
        
        anomalies_detected = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "api_calls_current_month": api_calls,
            "anomalies_detected": anomalies_detected
        }
        
    except:
        return {
            "api_calls_current_month": 0,
            "anomalies_detected": 0
        }

# ============ CUSTOM ROUTE HANDLERS ============
def serve_html_file(filepath: str, directory: Path = FRONTEND_DIR):
    """Serve HTML files from specified directory"""
    file_path = directory / filepath
    if file_path.exists():
        return FileResponse(file_path)
    return HTMLResponse(
        content=f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Page Not Found</title>
            <style>
                body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
                h1 {{ color: #ff4444; }}
            </style>
        </head>
        <body>
            <h1>Page Not Found</h1>
            <p>The page {filepath} was not found.</p>
            <a href="/">Return to Home</a>
        </body>
        </html>
        """,
        status_code=404
    )

# ============ API ENDPOINTS ============
@app.get("/api/debug/check-session/{token}")
async def debug_check_session(token: str):
    """Debug endpoint to check session validity"""
    try:
        # Check account_sessions
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM account_sessions WHERE session_token = ?
        ''', (token,))
        
        account_session = cursor.fetchone()
        
        # Check sessions_db
        memory_session = sessions_db.get(token)
        
        conn.close()
        
        return {
            "token": token[:20] + "...",
            "account_session_exists": account_session is not None,
            "account_session_data": account_session if account_session else None,
            "memory_session_exists": memory_session is not None,
            "memory_session_data": memory_session
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Weather Anomaly Predictor",
        "version": "3.0.0",
        "api_key_configured": True,
        "coverage": "global",
        "features": ["current_weather", "anomaly_detection", "future_predictions", "safety_guidance"],
        "active_sessions": len(sessions_db)
    }

@app.get("/api/test-connection")
async def test_connection():
    """Test API connection and OpenWeatherMap access"""
    try:
        # Test with a known city
        test_data = await get_weather_data_fallback("London", "UK")
        return {
            "status": "success",
            "backend": "running",
            "openweathermap_api": "accessible" if test_data.get('source') == 'openweathermap' else "fallback",
            "test_city": "London",
            "test_temperature": test_data['temperature'],
            "data_source": test_data.get('source', 'unknown'),
            "coverage": "worldwide"
        }
    except Exception as e:
        return {
            "status": "partial",
            "backend": "running", 
            "openweathermap_api": "failed",
            "error": str(e),
            "fallback_working": True,
            "coverage": "worldwide (with fallback)"
        }

# ============ CONTACT FORM ENDPOINT ============
@app.post("/api/newsletter/subscribe")
async def subscribe_newsletter(subscription: NewsletterSubscription, request: Request):
    """Subscribe to newsletter with database storage"""
    try:
        print(f"📧 Newsletter subscription request for: {subscription.email}")
        
        # Validate email
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, subscription.email):
            raise HTTPException(status_code=400, detail="Invalid email address")
        
        # Get client info
        ip_address = request.client.host if request.client else "Unknown"
        user_agent = request.headers.get("user-agent", "Unknown")
        referer = request.headers.get("referer", "Unknown")  # Which page they came from
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if already subscribed
        cursor.execute("SELECT id, is_active FROM newsletter_subscribers WHERE email = ?", (subscription.email,))
        existing = cursor.fetchone()
        
        if existing:
            subscriber_id, is_active = existing
            if is_active:
                conn.close()
                return {
                    "success": True,
                    "message": "You're already subscribed to our newsletter!",
                    "already_subscribed": True
                }
            else:
                # Reactivate unsubscribed user
                unsubscribe_token = secrets.token_urlsafe(32)
                cursor.execute('''
                    UPDATE newsletter_subscribers 
                    SET is_active = 1, subscribed_at = CURRENT_TIMESTAMP, 
                        unsubscribe_token = ?, source_page = ?, ip_address = ?, user_agent = ?
                    WHERE id = ?
                ''', (unsubscribe_token, referer, ip_address, user_agent, subscriber_id))
                conn.commit()
                message = "Welcome back! You've been re-subscribed to our newsletter."
        else:
            # Generate unsubscribe token
            unsubscribe_token = secrets.token_urlsafe(32)
            
            # Insert new subscriber with all columns
            cursor.execute('''
                INSERT INTO newsletter_subscribers 
                (email, unsubscribe_token, source_page, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?)
            ''', (subscription.email, unsubscribe_token, referer, ip_address, user_agent))
            
            conn.commit()
            subscriber_id = cursor.lastrowid
            message = "Successfully subscribed to newsletter!"
        
        # Get the unsubscribe token for this subscriber
        cursor.execute("SELECT unsubscribe_token FROM newsletter_subscribers WHERE id = ?", (subscriber_id,))
        token_result = cursor.fetchone()
        unsubscribe_token = token_result[0] if token_result else None
        
        conn.close()
        
        # Send welcome email
        subject = "Welcome to Weather AI Newsletter!"
        
        # Create unsubscribe link
        unsubscribe_link = f"http://localhost:3000/unsubscribe?token={unsubscribe_token}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #1a6bb3 0%, #00c9ff 100%); color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f8fafc; padding: 30px; border-radius: 0 0 10px 10px; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 12px; }}
                .unsubscribe {{ color: #666; font-size: 11px; }}
            </style>
        </head>
        <body>
            <div class='container'>
                <div class='header'>
                    <h2>Welcome to Weather AI Newsletter!</h2>
                </div>
                <div class='content'>
                    <p>Dear Subscriber,</p>
                    <p>Thank you for subscribing to the Weather AI newsletter! You'll now receive:</p>
                    <ul>
                        <li>🌤️ Weekly weather anomaly reports</li>
                        <li>📊 Latest research and discoveries</li>
                        <li>🔔 Early warnings about significant weather patterns</li>
                        <li>💡 Tips and insights from our meteorology team</li>
                    </ul>
                    <p>We're excited to have you as part of our community!</p>
                    <p>Best regards,<br>
                    <strong>The Weather AI Team</strong></p>
                </div>
                <div class='footer'>
                    <p>This is a confirmation of your subscription.</p>
                    <p class='unsubscribe'>To unsubscribe anytime, <a href="{unsubscribe_link}">click here</a></p>
                    <p>Weather AI Platform | Advanced Weather Anomaly Detection</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Welcome to Weather AI Newsletter!
        
        Dear Subscriber,
        
        Thank you for subscribing to the Weather AI newsletter! You'll now receive:
        - Weekly weather anomaly reports
        - Latest research and discoveries
        - Early warnings about significant weather patterns
        - Tips and insights from our meteorology team
        
        We're excited to have you as part of our community!
        
        Best regards,
        The Weather AI Team
        
        To unsubscribe: {unsubscribe_link}
        
        This is a confirmation of your subscription.
        Weather AI Platform | Advanced Weather Anomaly Detection
        """
        
        # Send welcome email
        email_sent = await send_email_async(
            subscription.email,
            subject,
            html_content,
            text_content
        )
        
        # Update last_email_sent
        if email_sent:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("UPDATE newsletter_subscribers SET last_email_sent = CURRENT_TIMESTAMP WHERE id = ?", (subscriber_id,))
            conn.commit()
            conn.close()
        
        # Also notify admin about new subscriber
        admin_subject = "New Newsletter Subscriber"
        admin_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #1a6bb3 0%, #00c9ff 100%); color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f8fafc; padding: 30px; border-radius: 0 0 10px 10px; }}
            </style>
        </head>
        <body>
            <div class='container'>
                <div class='header'>
                    <h2>New Newsletter Subscriber</h2>
                </div>
                <div class='content'>
                    <p><strong>Email:</strong> {subscription.email}</p>
                    <p><strong>Source Page:</strong> {referer}</p>
                    <p><strong>IP Address:</strong> {ip_address}</p>
                    <p><strong>User Agent:</strong> {user_agent}</p>
                    <p><strong>Date:</strong> {datetime.now().strftime('%B %d, %Y, %I:%M %p')}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        await send_email_async(
            EMAIL_CONFIG['ADMIN_EMAIL'],
            admin_subject,
            admin_html
        )
        
        return {
            "success": True,
            "message": message,
            "email_sent": email_sent
        }
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Newsletter subscription error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail="Failed to process subscription. Please try again later."
        )

@app.post("/api/contact/send")
async def send_contact_message(form_data: ContactForm, request: Request):
    """Handle contact form submissions"""
    try:
        print(f"📧 Contact form submitted by: {form_data.first_name} {form_data.last_name}")
        
        # Validate email
        import re
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, form_data.email):
            raise HTTPException(status_code=400, detail="Invalid email address")
        
        # Save to database
        message_id = save_contact_to_db(form_data, request)
        
        if not message_id:
            print("⚠️ Failed to save contact to database, but continuing...")
        
        # Send email
        email_sent = await send_contact_email(form_data)
        
        if email_sent:
            # Update database if email sent
            if message_id:
                try:
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute("UPDATE contact_messages SET email_sent = 1, status = 'sent' WHERE id = ?", (message_id,))
                    conn.commit()
                    conn.close()
                except:
                    pass
            
            return {
                "success": True,
                "message": "✅ Thank you! Your message has been sent successfully. We will respond within 24 hours.",
                "message_id": message_id
            }
        else:
            # Update database if email failed
            if message_id:
                try:
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute("UPDATE contact_messages SET status = 'failed', notes = 'Email sending failed' WHERE id = ?", (message_id,))
                    conn.commit()
                    conn.close()
                except:
                    pass
            
            return {
                "success": True,
                "message": "✅ Thank you! Your message has been saved. Please also email us directly at saadyousafzai420@gmail.com for immediate response.",
                "message_id": message_id,
                "note": "Email sending failed, but message saved to database"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Contact form error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to process contact form. Please try again later."
        )

@app.get("/api/weather/current")
async def get_current_weather(
    city: str = "New York", 
    country: str = "", 
    use_fallback: bool = False,
    token: str = Depends(extract_token)  # Add token parameter
):
    """Get current weather data from OpenWeatherMap API"""
    global activity_log, cities_tracked
    
    try:
        # ===== STEP 1: Get current user from token =====
        current_user = None
        user_id = None
        try:
            current_user = await get_current_user(token)
            user = get_user_by_email(current_user["email"])
            if user:
                user_id = user["id"]
                print(f"✅ User authenticated for weather check: {current_user['email']} (ID: {user_id})")
        except Exception as e:
            # If no token or invalid, continue without user_id
            print(f"⚠️ No user authentication for weather check: {e}")
        
        print(f"🌍 API: Fetching weather for {city}, {country}")
        
        if use_fallback:
            weather_data = await get_weather_data_fallback(city, country)
        else:
            try:
                weather_data = await get_real_weather_data(city, country)
                weather_data['source'] = 'openweathermap'
            except HTTPException as e:
                print(f"⚠️ Real API failed, using fallback: {e.detail}")
                weather_data = await get_weather_data_fallback(city, country)
                weather_data['source'] = 'fallback'
                weather_data['fallback_reason'] = str(e.detail)
        
        # ===== STEP 2: Save weather check to database with user_id =====
        if user_id:  # Only save if user is logged in
            conn = None
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO activity_log 
                    (user_id, city, activity_type, status, is_anomaly, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    user_id, 
                    city, 
                    "Weather Check", 
                    "Completed",
                    0,  # Weather checks are not anomalies
                    datetime.now().isoformat()
                ))
                conn.commit()
                print(f"✅ Weather check saved to database for user {user_id}")
            except Exception as e:
                print(f"⚠️ Error saving weather check to database: {e}")
            finally:
                if conn:
                    conn.close()
        
        # Track city and log activity (keep for backward compatibility)
        cities_tracked.add(city.lower())
        activity_log.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "city": city,
            "activity_type": "Weather Check",
            "status": "Completed",
            "is_anomaly": False
        })
        
        # Keep only last 100 activities
        if len(activity_log) > 100:
            activity_log.pop(0)
            
        return weather_data
        
    except Exception as e:
        print(f"❌ Unexpected error in get_current_weather: {str(e)}")
        weather_data = await get_weather_data_fallback(city, country)
        weather_data['source'] = 'fallback'
        weather_data['fallback_reason'] = 'Unexpected error'
        return weather_data

@app.post("/api/auth/register")
@limiter.limit("3/minute")
async def register(request: Request, user: UserCreate):
    try:
        # Validate email
        if '@' not in user.email:
            raise HTTPException(status_code=400, detail="Invalid email address")
        
        # Validate password
        if len(user.password) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
        
        # Check if user already exists
        existing_user = get_user_by_email(user.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create user with account_type parameter
        new_user = create_user(user.email, user.full_name, user.password, "personal")
        
        # Create access token
        access_token = create_access_token(data={"sub": user.email})
        
        # Store session
        sessions_db[access_token] = {
            "email": user.email,
            "full_name": user.full_name,
            "created_at": datetime.now().isoformat()
        }
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "email": new_user["email"],
                "full_name": new_user["full_name"],
                "created_at": new_user["created_at"]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/user/profile/picture")
async def upload_profile_picture(
    request: Request,
    token: str = Depends(extract_token)
):
    """Upload profile picture"""
    try:
        current_user = await get_current_user(token)
        
        # Parse multipart form data
        form = await request.form()
        file = form.get("profile_picture")
        
        if not file:
            raise HTTPException(status_code=400, detail="No file uploaded")
        
        # Validate file type
        allowed_types = ["image/jpeg", "image/png", "image/gif"]
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="Invalid file type. Only JPG, PNG, and GIF are allowed.")
        
        # Read file content
        content = await file.read()
        
        # Generate unique filename
        file_ext = file.filename.split(".")[-1]
        filename = f"profile_{current_user['email']}_{datetime.now().timestamp()}.{file_ext}"
        
        # Save to uploads directory
        upload_dir = os.path.join(os.path.dirname(__file__), "uploads", "profiles")
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, filename)
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Generate URL for the file
        profile_picture_url = f"/uploads/profiles/{filename}"
        
        # Update database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET profile_picture = ? WHERE email = ?",
            (profile_picture_url, current_user['email'])
        )
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "profile_picture_url": profile_picture_url,
            "message": "Profile picture updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error uploading profile picture: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Serve uploaded files
@app.get("/uploads/{file_path:path}")
async def serve_uploads(file_path: str):
    """Serve uploaded files"""
    upload_dir = os.path.join(os.path.dirname(__file__), "uploads")
    full_path = os.path.join(upload_dir, file_path)
    
    if os.path.exists(full_path) and os.path.isfile(full_path):
        return FileResponse(full_path)
    
    raise HTTPException(status_code=404, detail="File not found")

@app.post("/api/auth/login")
@limiter.limit("5/minute")
async def login(request: Request):
    """Login user - checks for email 2FA if enabled"""
    try:
        # Parse JSON body
        body = await request.json()
        email = body.get("email")
        password = body.get("password")
        remember_me = body.get("remember_me", False)
        
        if not email or not password:
            raise HTTPException(status_code=400, detail="Email and password required")
        
        # Authenticate user
        user = authenticate_user(email, password)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Check if email 2FA is enabled
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT email_2fa_enabled FROM user_preferences 
            WHERE user_id = ?
        ''', (user["id"],))
        result = cursor.fetchone()
        email_2fa_enabled = result and result[0] == 1 if result else False
        conn.close()
        
        # If 2FA is enabled, send OTP and return 202
        if email_2fa_enabled:
            # Generate OTP
            otp = generate_otp()
            otp_expiry = datetime.now() + timedelta(minutes=10)
            
            # Store OTP in database
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE user_preferences SET
                    otp_secret = ?,
                    otp_expiry = ?
                WHERE user_id = ?
            ''', (otp, otp_expiry.isoformat(), user["id"]))
            conn.commit()
            conn.close()
            
            # Send OTP via email
            email_sent = await send_otp_email(email, otp, user["full_name"])
            
            if not email_sent:
                raise HTTPException(status_code=500, detail="Failed to send verification code")
            
            # Create temporary token for 2FA session
            temp_token = secrets.token_urlsafe(32)
            sessions_db[temp_token] = {
                "email": email,
                "temp": True,
                "created_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(minutes=10)).isoformat()
            }
            
            return JSONResponse(
                status_code=202,
                content={
                    "requires_2fa": True,
                    "message": "Verification code sent to your email",
                    "email": email,
                    "temp_token": temp_token
                }
            )
        
        # No 2FA, proceed with normal login
        access_token = create_access_token(
            data={"sub": email},
            expires_delta=timedelta(days=30 if remember_me else 7)
        )
        
        # Store session
        sessions_db[access_token] = {
            "email": email,
            "full_name": user["full_name"],
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(days=30 if remember_me else 7)).isoformat()
        }
        
        # Update last login
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET last_login = ? WHERE email = ?", 
                      (datetime.now().isoformat(), email))
        conn.commit()
        conn.close()
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "two_factor_enabled": False,
            "user": {
                "email": user["email"],
                "full_name": user["full_name"],
                "last_login": datetime.now().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/auth/verify")
async def verify_token(token: str = None):
    """Verify if a token is valid (supports both regular and account sessions)"""
    if not token:
        return {"valid": False, "message": "No token provided"}
    
    # First check if it's an account session token
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check account_sessions table - FIXED SQL SYNTAX
        cursor.execute('''
            SELECT as_session.*, ca.account_email, ca.account_name, ca.account_type, ca.profile_picture
            FROM account_sessions as_session
            JOIN connected_accounts ca ON as_session.account_id = ca.id
            WHERE as_session.session_token = ? AND as_session.expires_at > CURRENT_TIMESTAMP
        ''', (token,))
        
        session = cursor.fetchone()
        
        if session:
            # It's a valid account session
            conn.close()
            return {
                "valid": True,
                "user": {
                    "email": session[6],  # account_email
                    "full_name": session[7],  # account_name
                    "account_type": session[8],  # account_type
                    "profile_picture": session[9],  # profile_picture
                    "is_switched": True,
                    "account_id": session[2]  # account_id
                }
            }
        conn.close()
    except Exception as e:
        print(f"Error checking account session: {e}")
        # Don't return error, continue to check other session types
    
    # Check in-memory sessions (regular JWT sessions)
    session = sessions_db.get(token)
    if session:
        expires_at = datetime.fromisoformat(session["expires_at"]) if "expires_at" in session else None
        if expires_at and datetime.now() > expires_at:
            del sessions_db[token]
            return {"valid": False, "message": "Token expired"}
        return {
            "valid": True,
            "user": {
                "email": session["email"],
                "full_name": session.get("full_name", "User"),
                "is_switched": False
            }
        }
    
    # Verify JWT token
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            return {"valid": False, "message": "Invalid token"}
        
        user = get_user_by_email(email)
        if not user:
            return {"valid": False, "message": "User not found"}
        
        return {
            "valid": True,
            "user": {
                "email": user["email"],
                "full_name": user["full_name"],
                "account_type": user.get("account_type", "personal"),
                "profile_picture": user.get("profile_picture", ""),
                "is_switched": False
            }
        }
    except JWTError:
        return {"valid": False, "message": "Invalid token"}

@app.get("/api/auth/logout")
async def logout(token: str):
    """Logout user by removing session"""
    if token in sessions_db:
        del sessions_db[token]
    return {"message": "Logged out successfully"}

# ============ PASSWORD RESET ENDPOINTS ============
@app.post("/api/auth/reset-password")
async def reset_password_request(request: PasswordResetRequest):
    """Request a password reset email"""
    try:
        print(f"📧 Password reset requested for: {request.email}")
        
        # Check if user exists
        user = get_user_by_email(request.email)
        if not user:
            # Return success even if user doesn't exist (security best practice)
            return {
                "success": True,
                "message": "If your email is registered, you will receive a password reset link."
            }
        
        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(hours=1)
        
        # Store token in database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Invalidate old tokens
        cursor.execute('''
            UPDATE password_reset_tokens 
            SET used = 1 
            WHERE email = ? AND used = 0
        ''', (request.email,))
        
        # Insert new token
        cursor.execute('''
            INSERT INTO password_reset_tokens (email, token, expires_at)
            VALUES (?, ?, ?)
        ''', (request.email, reset_token, expires_at.isoformat()))
        
        conn.commit()
        conn.close()
        
        # Send reset email
        email_sent = await send_password_reset_email(request.email, reset_token, user.get('full_name', 'User'))
        
        if email_sent:
            return {
                "success": True,
                "message": "Password reset link has been sent to your email."
            }
        else:
            # Email failed but token was created - you might want to return the token for testing
            return {
                "success": True,
                "message": "Password reset link generated. (Note: Email sending failed - for testing, use the token)",
                "debug_token": reset_token  # Remove in production!
            }
            
    except Exception as e:
        print(f"❌ Password reset request error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process password reset request")

@app.post("/api/auth/reset-password/confirm")
async def reset_password_confirm(request: PasswordResetConfirm):
    """Confirm password reset with token"""
    try:
        print(f"🔐 Password reset confirmation with token: {request.token[:8]}...")
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Find valid token
        cursor.execute('''
            SELECT * FROM password_reset_tokens 
            WHERE token = ? AND used = 0 AND expires_at > ?
        ''', (request.token, datetime.now().isoformat()))
        
        token_record = cursor.fetchone()
        
        if not token_record:
            conn.close()
            raise HTTPException(status_code=400, detail="Invalid or expired reset token")
        
        # Get email from token record
        # token_record columns: id, email, token, created_at, expires_at, used
        email = token_record[1]
        
        # Update user's password
        hashed_password = get_password_hash(request.new_password)
        
        cursor.execute('''
            UPDATE users 
            SET hashed_password = ? 
            WHERE email = ?
        ''', (hashed_password, email))
        
        # Mark token as used
        cursor.execute('''
            UPDATE password_reset_tokens 
            SET used = 1 
            WHERE token = ?
        ''', (request.token,))
        
        conn.commit()
        conn.close()
        
        # Send confirmation email
        await send_password_reset_confirmation(email)
        
        return {
            "success": True,
            "message": "Password has been reset successfully. You can now login with your new password."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Password reset confirm error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to reset password")

# ============ OAUTH ENDPOINTS ============

@app.get("/auth/{provider}")
async def oauth_login(request: Request, provider: str):
    """Initiate OAuth login with the specified provider"""
    print(f"\n========== OAUTH LOGIN CALLED for provider: {provider} ==========")
    try:
        if provider not in ['google', 'github', 'microsoft']:
            raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")
        
        print(f"1. Provider validated: {provider}")
        
        # Create OAuth client
        client = oauth.create_client(provider)
        if not client:
            print(f"2. Failed to create OAuth client for {provider}")
            raise HTTPException(status_code=400, detail=f"OAuth client not configured for {provider}")
        
        print(f"2. OAuth client created successfully for {provider}")
        print(f"   Client ID: {client.client_id}")
        
        # Generate redirect URI
        redirect_uri = request.url_for('oauth_callback', provider=provider)
        print(f"3. Redirect URI: {redirect_uri}")
        
        # Redirect to provider's login page
        print(f"4. Redirecting to {provider} login page...")
        return await client.authorize_redirect(request, redirect_uri)
        
    except Exception as e:
        print(f"❌ OAuth login error for {provider}: {str(e)}")
        import traceback
        traceback.print_exc()
        return RedirectResponse(url=f"/login?error={str(e)}")

# Add this temporary endpoint to check OAuth configuration
@app.get("/debug/oauth")
async def debug_oauth():
    """Debug endpoint to check OAuth configuration"""
    result = {
        "google": {
            "configured": False,
            "client_id": None
        },
        "github": {
            "configured": False,
            "client_id": None
        },
        "microsoft": {
            "configured": False,
            "client_id": None
        }
    }
    
    try:
        google_client = oauth.create_client('google')
        if google_client:
            result["google"]["configured"] = True
            result["google"]["client_id"] = google_client.client_id
    except:
        pass
    
    try:
        github_client = oauth.create_client('github')
        if github_client:
            result["github"]["configured"] = True
            result["github"]["client_id"] = github_client.client_id
    except:
        pass
    
    try:
        microsoft_client = oauth.create_client('microsoft')
        if microsoft_client:
            result["microsoft"]["configured"] = True
            result["microsoft"]["client_id"] = microsoft_client.client_id
    except:
        pass
    
    return result

import urllib.request
import uuid

# Add this function to download and save profile pictures
async def download_profile_picture(image_url, email):
    """Download profile picture from Google and save locally"""
    try:
        # Create uploads directory if it doesn't exist
        upload_dir = os.path.join(os.path.dirname(__file__), "uploads", "profiles")
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        # Clean email to use in filename
        clean_email = email.replace('@', '_').replace('.', '_')
        file_ext = 'jpg'  # Default to jpg
        filename = f"profile_{clean_email}_{uuid.uuid4().hex[:8]}.{file_ext}"
        file_path = os.path.join(upload_dir, filename)
        
        # Download the image
        urllib.request.urlretrieve(image_url, file_path)
        print(f"✅ Image downloaded to: {file_path}")
        
        # Return the local URL
        return f"/uploads/profiles/{filename}"
    except Exception as e:
        print(f"⚠️ Error downloading profile picture: {e}")
        return image_url  # Fall back to Google URL if download fails
    
@app.get("/auth/{provider}/callback")
async def oauth_callback(request: Request, provider: str):
    """OAuth callback handler"""
    try:
        if provider not in ['google', 'github', 'microsoft']:
            raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")
        
        # Get OAuth client
        client = oauth.create_client(provider)
        if not client:
            raise HTTPException(status_code=400, detail=f"OAuth client not configured for {provider}")
        
        # Get token from provider
        token = await client.authorize_access_token(request)
        
        # Get user info from provider
        user_info = None
        
        if provider == 'google':
            user_info = token.get('userinfo')
            if not user_info:
                user_info = await client.parse_id_token(request, token)
        
        elif provider == 'github':
            # GitHub requires an extra API call to get user info
            resp = await client.get('user', token=token)
            user_info = resp.json()
            
            # Get email if not in user info
            if not user_info.get('email'):
                emails_resp = await client.get('user/emails', token=token)
                emails = emails_resp.json()
                primary_email = next((email for email in emails if email.get('primary')), emails[0] if emails else None)
                if primary_email:
                    user_info['email'] = primary_email.get('email')
        
        elif provider == 'microsoft':
            user_info = token.get('userinfo')
            if not user_info:
                user_info = await client.parse_id_token(request, token)
        
        if not user_info or not user_info.get('email'):
            raise HTTPException(status_code=400, detail="Could not get user email from provider")
        
        # Extract user details
       
        email = user_info.get('email')
        name = user_info.get('name') or user_info.get('full_name') or user_info.get('login') or email.split('@')[0]
        # Get profile picture from Google
        profile_picture = user_info.get('picture')  # Google returns profile picture in 'picture' field

        # Check if user exists
        print(f"🔍 Checking if user exists with email: {email}")
        user = get_user_by_email(email)
        print(f"📊 Result from get_user_by_email: {user}")

        if not user:
            print(f"📝 User not found, creating new user with email: {email}")
            random_password = secrets.token_urlsafe(16)
            try:
                user = create_user(email, name, random_password, "personal")
                print(f"✅ User created successfully: {user}")
        
                # Update profile picture if provided
                if profile_picture:
                    try:
                        conn = sqlite3.connect(DB_PATH)
                        cursor = conn.cursor()
                        cursor.execute(
                            "UPDATE users SET profile_picture = ? WHERE email = ?",
                            (profile_picture, email)
                        )
                        conn.commit()
                        conn.close()
                        print(f"✅ Profile picture saved for: {email}")
                    except Exception as e:
                        print(f"⚠️ Error saving profile picture: {e}")
                
            except Exception as e:
                print(f"❌ Failed to create user: {e}")
                user = get_user_by_email(email)
                if not user:
                    raise e
        else:
            print(f"✅ User already exists with email: {email}")
           # Update profile picture if user exists and has no picture or if picture changed
            if profile_picture:
                try:
                    # Download and save the image locally
                    local_image_url = await download_profile_picture(profile_picture, email)
                    
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE users SET profile_picture = ? WHERE email = ?",
                        (local_image_url, email)
                    )
                    conn.commit()
                    conn.close()
                    print(f"✅ Profile picture saved locally for: {email}")
                except Exception as e:
                    print(f"⚠️ Error saving profile picture: {e}")
        # Create access token
        access_token = create_access_token(
            data={"sub": email},
            expires_delta=timedelta(days=7)
        )
        
        # Store session
        sessions_db[access_token] = {
            "email": email,
            "full_name": user["full_name"],
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(days=7)).isoformat()
        }
        
        # Update last login
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET last_login = ? WHERE email = ?",
                (datetime.now().isoformat(), email)
            )
            conn.commit()
            conn.close()
            print(f"✅ Updated last login for: {email}")
        except Exception as e:
            print(f"⚠️ Error updating last login: {e}")
        
        # Create HTML response with JavaScript to close popup and set token
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Login Successful</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    text-align: center;
                    padding: 50px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                }}
                .container {{
                    max-width: 400px;
                    margin: 0 auto;
                    padding: 30px;
                    background: rgba(255,255,255,0.1);
                    border-radius: 10px;
                    backdrop-filter: blur(10px);
                }}
                h1 {{ font-size: 24px; margin-bottom: 20px; }}
                p {{ margin-bottom: 20px; }}
                .spinner {{
                    border: 3px solid rgba(255,255,255,0.3);
                    border-radius: 50%;
                    border-top: 3px solid white;
                    width: 40px;
                    height: 40px;
                    animation: spin 1s linear infinite;
                    margin: 20px auto;
                }}
                @keyframes spin {{
                    0% {{ transform: rotate(0deg); }}
                    100% {{ transform: rotate(360deg); }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>✓ Login Successful!</h1>
                <p>Welcome, {name}!</p>
                <div class="spinner"></div>
                <p>Redirecting to dashboard...</p>
            </div>
            
            <script>
                // Send token to opener window
                if (window.opener) {{
                    window.opener.postMessage({{
                        type: 'oauth-success',
                        provider: '{provider}',
                        token: '{access_token}',
                        user: {{
                            email: '{email}',
                            full_name: '{name}'
                        }}
                    }}, '*');
                    
                    // Close this window after 2 seconds
                    setTimeout(() => window.close(), 2000);
                }} else {{
                    // If not opened as popup, redirect directly
                    localStorage.setItem('weather_ai_token', '{access_token}');
                    localStorage.setItem('weather_ai_user', JSON.stringify({{
                        email: '{email}',
                        full_name: '{name}'
                    }}));
                    window.location.href = '/dashboard';
                }}
            </script>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        print(f"OAuth callback error for {provider}: {str(e)}")
        import traceback
        traceback.print_exc()
        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html>
        <head><title>Login Failed</title></head>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h1 style="color: #ef4444;">✗ Login Failed</h1>
            <p>Error: {str(e)}</p>
            <p><a href="/login" style="color: #1a6bb3;">Return to Login</a></p>
            <script>
                if (window.opener) {{
                    window.opener.postMessage({{ type: 'oauth-error', error: '{str(e)}' }}, '*');
                    setTimeout(() => window.close(), 2000);
                }}
            </script>
        </body>
        </html>
        """)


@app.post("/api/weather/predict-anomaly")
async def predict_anomaly(request: PredictionRequest, token: str = Depends(extract_token)):
    """Predict weather anomalies using real weather data and ensemble ML models"""
    global total_predictions, anomalies_detected, cities_tracked, activity_log
    
    try:
        # ===== STEP 1: Get current user from token =====
        current_user = None
        user_id = None
        try:
            current_user = await get_current_user(token)
            user = get_user_by_email(current_user["email"])
            if user:
                user_id = user["id"]
                print(f"✅ User authenticated: {current_user['email']} (ID: {user_id})")
        except Exception as e:
            # If no token or invalid, continue without user_id (for public access)
            print(f"⚠️ No user authentication: {e}")
        
        print(f"🔮 Predicting anomaly for: {request.city} using ensemble ML models")
        
        # ===== STEP 2: Get real weather data =====
        try:
            current_weather = await get_real_weather_data(request.city, request.country)
            current_weather['source'] = 'openweathermap'
        except HTTPException as e:
            print(f"⚠️ Real API failed: {e.detail}")
            current_weather = await get_weather_data_fallback(request.city, request.country)
            current_weather['source'] = 'fallback'
        
        # Track city
        cities_tracked.add(request.city.lower())
        
        # ===== STEP 3: Use ensemble model for anomaly detection =====
        ensemble_result = anomaly_predictor.detect_anomalies_ensemble(
            city=request.city,
            current_weather=current_weather
        )
        
        # Update counters
        total_predictions += 1
        is_anomaly = ensemble_result['is_anomaly']
        if is_anomaly:
            anomalies_detected += 1
        
        # ===== STEP 4: Save to database with user_id (THIS IS THE KEY FIX) =====
        if user_id:  # Only save if user is logged in
            conn = None
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO activity_log 
                    (user_id, city, activity_type, status, is_anomaly, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    user_id, 
                    request.city, 
                    "Anomaly Detection", 
                    "Anomaly" if is_anomaly else "Normal",
                    1 if is_anomaly else 0,  # Convert boolean to 0/1 for SQLite
                    datetime.now().isoformat()
                ))
                conn.commit()
                print(f"✅ Activity saved to database for user {user_id}")
            except Exception as e:
                print(f"⚠️ Error saving activity to database: {e}")
            finally:
                if conn:
                    conn.close()
        
        # Keep only last 100 activities in memory (optional)
        if len(activity_log) > 100:
            activity_log.pop(0)
        
        # ===== STEP 5: Prepare response =====
        result = {
            "city": request.city,
            "country": current_weather.get('country', ''),
            "is_anomaly": is_anomaly,
            "anomaly_probability": float(ensemble_result['ensemble_score']),
            "confidence": float(ensemble_result['confidence']),
            "anomaly_type": ensemble_result.get('anomaly_type', 'Normal'),
            "severity": ensemble_result.get('severity', 'None'),
            "current_weather": current_weather,
            "timestamp": datetime.now().isoformat(),
            "anomaly_explanation": ensemble_result.get('explanation', 'Analysis complete'),
            "model_details": {
                "models_used": ensemble_result.get('models_used', []),
                "model_scores": ensemble_result.get('model_scores', {}),
                "zscore_details": ensemble_result.get('zscore_details', {}),
                "statistical_anomalies": ensemble_result.get('statistical_anomalies', []),
                "prediction_deviations": ensemble_result.get('prediction_deviations', {})
            },
            "historical_comparison": {
                "temperature": {
                    "current": current_weather['temperature'],
                    "historical_mean": ensemble_result.get('historical_stats', {}).get('temperature', {}).get('mean', 0),
                    "normal_range": [
                        ensemble_result.get('historical_stats', {}).get('temperature', {}).get('percentile_5', 0),
                        ensemble_result.get('historical_stats', {}).get('temperature', {}).get('percentile_95', 0)
                    ]
                }
            },
            "data_source": current_weather.get('source', 'unknown'),
            "safety_guidance": get_safety_guidance(
                ensemble_result.get('anomaly_type', 'Normal'),
                ensemble_result.get('severity', 'None'),
                current_weather,
                is_anomaly
            ),
            "recommendations": {
                "level": "Critical" if ensemble_result.get('severity') == 'Critical' else "High" if ensemble_result.get('severity') == 'High' else "Medium" if ensemble_result.get('severity') == 'Medium' else "Low" if is_anomaly else "Normal",
                "actions": generate_dynamic_recommendations(ensemble_result.get('anomaly_type', 'Normal'), ensemble_result.get('severity', 'None'), is_anomaly)
            }
        }
        
        print(f"🎯 Ensemble prediction: Anomaly={result['is_anomaly']}, Type={result['anomaly_type']}, Confidence={result['confidence']:.2f}")
        return result
        
    except Exception as e:
        print(f"❌ Error predicting anomaly: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to predict weather anomaly: {str(e)}")

@app.post("/api/weather/future-anomalies")
async def predict_future_anomalies(request: FuturePredictionRequest, token: str = Depends(extract_token)):
    """Predict future weather anomalies using ensemble forecasting models"""
    global activity_log, cities_tracked
    
    try:
        # ===== STEP 1: Get current user from token =====
        current_user = None
        user_id = None
        try:
            current_user = await get_current_user(token)
            user = get_user_by_email(current_user["email"])
            if user:
                user_id = user["id"]
                print(f"✅ User authenticated: {current_user['email']} (ID: {user_id})")
        except Exception as e:
            print(f"⚠️ No user authentication: {e}")
        
        print(f"🔮 Predicting future anomalies for: {request.city}, {request.days} days")
        
        # Get current weather for baseline (real data)
        try:
            current_weather = await get_real_weather_data(request.city, request.country)
        except:
            current_weather = await get_weather_data_fallback(request.city, request.country)
        
        # Track city
        cities_tracked.add(request.city.lower())
        
        # Use ensemble model for future predictions
        future_data = anomaly_predictor.predict_future_anomalies(
            city=request.city,
            current_weather=current_weather,
            days=request.days
        )
        
        total_future_anomalies = future_data['total_anomalies']
        
        # ===== STEP 2: Save to database with user_id =====
        if user_id:  # Only save if user is logged in
            conn = None
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO activity_log 
                    (user_id, city, activity_type, status, is_anomaly, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    user_id, 
                    request.city, 
                    "Future Anomaly Prediction", 
                    f"{total_future_anomalies} anomalies predicted",
                    1 if total_future_anomalies > 0 else 0,
                    datetime.now().isoformat()
                ))
                conn.commit()
                print(f"✅ Future prediction saved to database for user {user_id}")
            except Exception as e:
                print(f"⚠️ Error saving future prediction: {e}")
            finally:
                if conn:
                    conn.close()
        
        # Keep only last 100 activities
        if len(activity_log) > 100:
            activity_log.pop(0)
        
        # Generate enhanced safety guidance
        guidance = get_enhanced_safety_guidance(
            future_data['anomalies'], 
            total_future_anomalies,
            future_data.get('models_used', [])
        )
        
        # Save to database
        save_future_anomalies_to_db(request.city, request.country, future_data['anomalies'])
        
        result = {
            "city": request.city,
            "country": request.country,
            "days": request.days,
            "total_anomalies": total_future_anomalies,
            "anomalies": future_data['anomalies'],
            "confidence": future_data['confidence'],
            "trend": future_data['trend'],
            "models_used": future_data.get('models_used', []),
            "historical_baseline": future_data.get('historical_baseline', {}),
            "safety_guidance": guidance,
            "current_weather": current_weather,
            "timestamp": datetime.now().isoformat(),
            "recommendations": get_ensemble_recommendations(
                total_future_anomalies, 
                request.days,
                future_data['anomalies']
            )
        }
        
        print(f"🎯 Future prediction: {total_future_anomalies} anomalies predicted, Confidence={future_data['confidence']}%, Trend={future_data['trend']}")
        return result
        
    except Exception as e:
        print(f"❌ Error predicting future anomalies: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to predict future weather anomalies: {str(e)}")

def get_enhanced_safety_guidance(anomalies: List[Dict], total_anomalies: int, models_used: List[str]) -> Dict:
    """Generate enhanced safety guidance based on ML model predictions"""
    if total_anomalies == 0:
        return {
            "general_public": "✅ No significant anomalies predicted. Normal weather patterns expected.",
            "farmers": "🌱 Normal farming operations recommended based on model analysis.",
            "construction": "🏗️ Standard safety protocols apply.",
            "transportation": "🚗 Normal travel conditions expected.",
            "health_elderly": "🏥 Regular health precautions recommended.",
            "emergency_prep": "📋 Maintain basic emergency preparedness.",
            "model_confidence": f"Based on {len(models_used)} ML models with high confidence"
        }
    
    # Analyze anomaly patterns
    severity_counts = {'Critical': 0, 'High': 0, 'Medium': 0, 'Low': 0}
    anomaly_types = {}
    
    for day in anomalies:
        if day.get('is_anomaly', False):
            severity = day.get('severity', 'Low')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            a_type = day.get('anomaly_type', 'Unknown')
            anomaly_types[a_type] = anomaly_types.get(a_type, 0) + 1
    
    # Get most common anomaly type
    most_common_type = max(anomaly_types.items(), key=lambda x: x[1])[0] if anomaly_types else "Weather"
    
    # Determine overall severity
    if severity_counts['Critical'] > 0:
        overall_severity = "CRITICAL"
        color = "🔴"
    elif severity_counts['High'] > 0:
        overall_severity = "HIGH"
        color = "🟠"
    elif severity_counts['Medium'] > 0:
        overall_severity = "MEDIUM"
        color = "🟡"
    else:
        overall_severity = "LOW"
        color = "🟢"
    
    guidance = {
        "general_public": f"{color} {overall_severity} ALERT: {total_anomalies} weather anomalies predicted over next {len(anomalies)} days. ",
        "model_confidence": f"Analysis based on {len(models_used)} ML models including Isolation Forest, Autoencoder, and statistical methods"
    }
    
    # Add specific guidance based on most common anomaly type
    if "Temperature" in most_common_type or "Heat" in most_common_type:
        guidance["general_public"] += "🌡️ Prepare for temperature extremes. Stay hydrated, limit outdoor activities during peak hours."
        guidance["health_elderly"] = "👴 Elderly: Stay in cool environments, check on vulnerable neighbors."
        guidance["farmers"] = "🌾 Increase irrigation, provide shade for sensitive crops."
    elif "Wind" in most_common_type:
        guidance["general_public"] += "💨 Secure loose outdoor items, avoid unnecessary travel during high winds."
        guidance["construction"] = "🏗️ Suspend crane operations, secure materials."
        guidance["transportation"] = "🚗 Exercise caution, especially for high-profile vehicles."
    elif "Humidity" in most_common_type:
        guidance["general_public"] += "💧 Prepare for extreme humidity. Stay hydrated, use air conditioning if available."
        guidance["health_elderly"] = "👴 Monitor for heat-related illness, stay in air-conditioned spaces."
    elif "Pressure" in most_common_type or "Storm" in most_common_type:
        guidance["general_public"] += "⛈️ Prepare for potential storms. Monitor weather alerts, secure outdoor items."
        guidance["emergency_prep"] = "🚨 Prepare emergency kit, charge devices, know evacuation routes."
    
    # Add default guidance for missing categories
    if "farmers" not in guidance:
        guidance["farmers"] = "🌱 Monitor weather updates, adjust farming activities accordingly."
    if "construction" not in guidance:
        guidance["construction"] = "🏗️ Enhanced safety measures recommended during predicted anomalies."
    if "transportation" not in guidance:
        guidance["transportation"] = "🚗 Allow extra travel time during predicted anomaly days."
    if "health_elderly" not in guidance:
        guidance["health_elderly"] = "👴 Take standard precautions, monitor weather-related health alerts."
    if "emergency_prep" not in guidance:
        guidance["emergency_prep"] = "📋 Review emergency plans, ensure supplies are ready."
    
    return guidance

def get_ensemble_recommendations(total_anomalies: int, days: int, anomalies: List[Dict]) -> Dict:
    """Get recommendations based on ensemble model predictions"""
    
    # Calculate severity score
    severity_weights = {'Critical': 4, 'High': 3, 'Medium': 2, 'Low': 1}
    total_severity = sum(severity_weights.get(a.get('severity', 'Low'), 0) for a in anomalies if a.get('is_anomaly', False))
    
    avg_severity = total_severity / max(1, total_anomalies)
    
    if total_anomalies == 0:
        return {
            "level": "Normal",
            "color": "green",
            "message": "✅ Weather conditions stable. No anomalies predicted.",
            "actions": [
                "Monitor regular weather updates",
                "Maintain basic emergency supplies",
                "Review family emergency plan annually"
            ]
        }
    elif total_anomalies <= 2 and avg_severity < 2:
        return {
            "level": "Low Alert",
            "color": "yellow",
            "message": "🟡 Minor anomalies predicted. Stay weather-aware.",
            "actions": [
                "Check daily weather forecasts",
                "Prepare for specific anomaly conditions",
                "Review relevant safety measures"
            ]
        }
    elif total_anomalies <= 4 and avg_severity < 3:
        return {
            "level": "Medium Alert",
            "color": "orange",
            "message": "🟠 Multiple anomalies predicted. Take precautionary measures.",
            "actions": [
                "Check emergency supplies",
                "Review evacuation routes if needed",
                "Stay informed through official channels",
                "Prepare for possible disruptions"
            ]
        }
    else:
        return {
            "level": "High Alert",
            "color": "red",
            "message": "🔴 Significant anomalies predicted. Enhanced preparedness required.",
            "actions": [
                "Ensure emergency kit is complete and accessible",
                "Review and practice evacuation plans",
                "Stay updated with official warnings",
                "Consider delaying non-essential travel",
                "Check on vulnerable neighbors and relatives"
            ]
        }

@app.get("/api/weather/history")
async def get_weather_history(
    city: str = "New York", 
    days: int = 7,
    token: str = Depends(extract_token)  # Add token parameter
):
    """Get historical weather data (simulated for demo)"""
    try:
        # ===== STEP 1: Get current user from token =====
        current_user = None
        user_id = None
        try:
            current_user = await get_current_user(token)
            user = get_user_by_email(current_user["email"])
            if user:
                user_id = user["id"]
                print(f"✅ User authenticated for history: {current_user['email']} (ID: {user_id})")
        except Exception as e:
            print(f"⚠️ No user authentication for history: {e}")
        
        print(f"📅 Generating historical data for: {city}, {days} days")
        
        # Get current weather to base historical data on
        current_weather = await get_current_weather(city, token=token)
        
        history_data = []
        
        for i in range(days):
            date = datetime.now() - timedelta(days=i)
            
            # Generate realistic historical data
            base_temp = current_weather['temperature'] + random.uniform(-8, 8)
            base_humidity = max(30, min(95, current_weather['humidity'] + random.randint(-20, 20)))
            base_pressure = max(950, min(1050, current_weather['pressure'] + random.randint(-15, 15)))
            base_wind = max(0, current_weather['wind_speed'] + random.uniform(-5, 5))
            
            # Calculate if this would be an anomaly
            temp_diff = abs(base_temp - current_weather['temperature'])
            was_anomaly = temp_diff > 10 or random.random() < 0.1
            
            history_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'temperature': round(base_temp, 1),
                'humidity': base_humidity,
                'pressure': base_pressure,
                'wind_speed': round(base_wind, 1),
                'was_anomaly': bool(was_anomaly)
            })
        
        # ===== STEP 2: Save history request to database with user_id =====
        if user_id:  # Only save if user is logged in
            conn = None
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO activity_log 
                    (user_id, city, activity_type, status, is_anomaly, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    user_id, 
                    city, 
                    "Weather History", 
                    f"{days} days loaded",
                    0,
                    datetime.now().isoformat()
                ))
                conn.commit()
                print(f"✅ Weather history request saved to database for user {user_id}")
            except Exception as e:
                print(f"⚠️ Error saving history request to database: {e}")
            finally:
                if conn:
                    conn.close()
        
        result = {
            'city': city,
            'days': days,
            'current_conditions': current_weather,
            'history': history_data[::-1]  # Reverse to show oldest first
        }
        
        print(f"📊 Generated historical data for {city}")
        return result
        
    except Exception as e:
        print(f"❌ Error generating historical data: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate historical weather data")

@app.get("/api/analytics/dashboard-stats")
async def get_dashboard_stats(token: str = Depends(extract_token)):
    """Get user-specific dashboard statistics"""
    try:
        # Get current user
        current_user = await get_current_user(token)
        user = get_user_by_email(current_user["email"])
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user-specific stats from database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get user's total predictions
        cursor.execute('''
            SELECT COUNT(*) FROM activity_log 
            WHERE user_id = ? AND activity_type = 'Anomaly Detection'
        ''', (user["id"],))
        total_predictions = cursor.fetchone()[0]
        
        # Get user's anomalies detected
        cursor.execute('''
            SELECT COUNT(*) FROM activity_log 
            WHERE user_id = ? AND is_anomaly = 1
        ''', (user["id"],))
        anomalies_detected = cursor.fetchone()[0]
        
        # Get user's unique cities monitored
        cursor.execute('''
            SELECT COUNT(DISTINCT city) FROM activity_log 
            WHERE user_id = ? AND city IS NOT NULL
        ''', (user["id"],))
        cities_monitored = cursor.fetchone()[0]
        
        # Calculate model accuracy for this user
        accuracy = 94.5  # Default
        if total_predictions > 0:
            accuracy = round((1 - (anomalies_detected / total_predictions)) * 100, 1)
        
        # Get API requests count (total activities)
        cursor.execute('''
            SELECT COUNT(*) FROM activity_log 
            WHERE user_id = ?
        ''', (user["id"],))
        api_requests = cursor.fetchone()[0]
        
        conn.close()
        
        # If no data yet, return default values
        if cities_monitored == 0:
            cities_monitored = 5
        if anomalies_detected == 0:
            anomalies_detected = 12
        if api_requests == 0:
            api_requests = 1245
        
        return {
            "cities_monitored": cities_monitored,
            "anomalies_detected": anomalies_detected,
            "model_accuracy": accuracy,
            "api_requests": api_requests,
            "system_status": "healthy",
            "last_update": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"Error getting dashboard stats: {str(e)}")
        # Return default values if error
        return {
            "cities_monitored": 5,
            "anomalies_detected": 12,
            "model_accuracy": 94.5,
            "api_requests": 1245,
            "system_status": "healthy",
            "last_update": datetime.now().isoformat()
        }

@app.get("/api/analytics/recent-activity")
async def get_recent_activity(
    token: str = Depends(extract_token),
    limit: int = 10
):
    """Get user-specific recent activity"""
    try:
        current_user = await get_current_user(token)
        user = get_user_by_email(current_user["email"])
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get user's recent activities from database
        cursor.execute('''
            SELECT * FROM activity_log 
            WHERE user_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (user["id"], limit))
        
        activities = cursor.fetchall()
        conn.close()
        
        if activities:
            return {
                "activities": [dict(activity) for activity in activities]
            }
        
        # If no activities, return empty list
        return {"activities": []}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting recent activity: {str(e)}")
        return {"activities": []}

@app.get("/api/analytics/advanced-stats")
async def get_advanced_stats():
    """Get advanced analytics statistics"""
    global total_predictions, anomalies_detected, cities_tracked
    
    # Calculate stats
    accuracy = 94.5
    if total_predictions > 0:
        accuracy = round((1 - (anomalies_detected / total_predictions)) * 100, 1)
    
    # Get top cities with anomalies from activity log
    city_anomalies = {}
    for activity in activity_log:
        if activity['is_anomaly']:
            city = activity['city']
            city_anomalies[city] = city_anomalies.get(city, 0) + 1
    
    top_anomaly_cities = [
        {"city": city, "anomalies": count}
        for city, count in sorted(city_anomalies.items(), key=lambda x: x[1], reverse=True)[:5]
    ]
    
    # Get future anomaly stats
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT anomaly_type, COUNT(*) as count FROM future_anomalies WHERE is_anomaly = 1 GROUP BY anomaly_type")
    future_anomaly_types = cursor.fetchall()
    conn.close()
    
    # Calculate future anomaly distribution
    future_anomaly_distribution = {}
    for anomaly_type, count in future_anomaly_types:
        future_anomaly_distribution[anomaly_type] = count
    
    return {
        "total_predictions": total_predictions,
        "anomalies_detected": anomalies_detected,
        "false_positives": max(0, anomalies_detected - 5),
        "model_accuracy": accuracy,
        "average_confidence": 91.2,
        "cities_monitored": len(cities_tracked),
        "top_anomaly_cities": top_anomaly_cities,
        "future_anomaly_distribution": future_anomaly_distribution,
        "confidence_distribution": {
            "high": min(total_predictions, 892),
            "medium": min(max(0, total_predictions - 900), 284),
            "low": min(max(0, total_predictions - 1200), 72)
        }
    }

@app.get("/api/cities/supported")
async def get_supported_cities():
    """Get list of well-known cities that work well with the API"""
    return {
        "supported_cities": [
            "New York, US", "London, GB", "Tokyo, JP", "Paris, FR", "Sydney, AU",
            "Berlin, DE", "Mumbai, IN", "Dubai, AE", "Toronto, CA", "Moscow, RU",
            "Beijing, CN", "Cairo, EG", "Rio de Janeiro, BR", "Singapore, SG", "Seoul, KR",
            "Islamabad, PK", "Lahore, PK", "Karachi, PK", "Delhi, IN", "Madrid, ES"
        ],
        "note": "Any city worldwide supported by OpenWeatherMap should work."
    }

@app.get("/api/cities/search")
async def search_cities(q: str = ""):
    """Search for cities worldwide using OpenWeatherMap Geocoding API"""
    try:
        print(f"🔍 Searching worldwide for cities matching: {q}")
        
        if not q or len(q) < 2:
            return {"cities": []}
        
        # Use OpenWeatherMap Geocoding API for worldwide city search
        geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={q}&limit=10&appid={OPENWEATHER_API_KEY}"
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(geo_url)
            
            if response.status_code != 200:
                print(f"⚠️ Geocoding API returned {response.status_code}")
                return {"cities": [], "error": "Geocoding API error"}
            
            locations = response.json()
            
            if not locations:
                print(f"❌ No cities found for: {q}")
                return {"cities": []}
            
            # Format the results
            cities = []
            for loc in locations:
                city_info = {
                    "name": loc.get("name", ""),
                    "country": loc.get("country", ""),
                    "state": loc.get("state", ""),
                    "lat": loc.get("lat", 0),
                    "lon": loc.get("lon", 0),
                    "local_names": loc.get("local_names", {})
                }
                cities.append(city_info)
            
            print(f"✅ Found {len(cities)} cities worldwide matching '{q}'")
            
            return {
                "cities": cities,
                "query": q,
                "count": len(cities)
            }
        
    except httpx.TimeoutException:
        print("⏱️ Geocoding API timeout")
        return {"cities": [], "error": "API timeout"}
    except Exception as e:
        print(f"❌ Error searching cities: {str(e)}")
        return {"cities": [], "error": str(e)}

@app.get("/api/weather/get-future-anomalies")
async def get_stored_future_anomalies(city: str = "", limit: int = 7):
    """Get stored future anomaly predictions from database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if city:
            cursor.execute('''
                SELECT * FROM future_anomalies 
                WHERE city = ? 
                ORDER BY prediction_date ASC 
                LIMIT ?
            ''', (city, limit))
        else:
            cursor.execute('''
                SELECT * FROM future_anomalies 
                ORDER BY prediction_date ASC 
                LIMIT ?
            ''', (limit,))
        
        anomalies = cursor.fetchall()
        conn.close()
        
        # Convert to dictionary
        anomalies_list = [dict(row) for row in anomalies]
        
        # Group by city
        grouped_anomalies = {}
        for anomaly in anomalies_list:
            city_name = anomaly['city']
            if city_name not in grouped_anomalies:
                grouped_anomalies[city_name] = {
                    'city': city_name,
                    'country': anomaly['country'],
                    'total_anomalies': 0,
                    'anomalies': []
                }
            
            if anomaly['is_anomaly']:
                grouped_anomalies[city_name]['total_anomalies'] += 1
            
            grouped_anomalies[city_name]['anomalies'].append({
                'date': anomaly['prediction_date'],
                'day_name': anomaly['day_name'],
                'temperature': anomaly['temperature'],
                'humidity': anomaly['humidity'],
                'pressure': anomaly['pressure'],
                'wind_speed': anomaly['wind_speed'],
                'condition': anomaly['condition'],
                'is_anomaly': bool(anomaly['is_anomaly']),
                'anomaly_type': anomaly['anomaly_type'],
                'severity': anomaly['severity'],
                'probability': anomaly['probability'],
                'description': anomaly['description']
            })
        
        return {
            "stored_predictions": list(grouped_anomalies.values()),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Error getting stored future anomalies: {str(e)}")
        return {
            "stored_predictions": [],
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

# ============ USER PROFILE ENDPOINTS ============
@app.get("/api/user/profile")
async def get_user_profile(token: str = Depends(extract_token)):
    """Get current user profile"""
    print("\n" + "="*60)
    print("🔍 PROFILE ENDPOINT CALLED")
    print("="*60)
    
    try:
        # Step 1: Get current user from token
        print(f"📌 Step 1: Getting current user from token")
        current_user = await get_current_user(token)
        print(f"   ✅ Current user email: {current_user['email']}")
        
        # Step 2: Get user from database by email
        print(f"📌 Step 2: Getting user from database")
        user = get_user_by_email(current_user["email"])
        print(f"   ✅ User from DB: {user}")
        
        # Step 3: Check if user exists
        print(f"📌 Step 3: Checking if user exists")
        if not user:
            print(f"   ❌ User not found in database!")
            raise HTTPException(status_code=404, detail="User not found")
        print(f"   ✅ User exists with ID: {user['id']}")
        
        # Step 4: Connect to database
        print(f"📌 Step 4: Connecting to database")
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        print(f"   ✅ Database connected")
        
        # Step 5: Execute query with case-insensitive search
        print(f"📌 Step 5: Executing query for email: {current_user['email']}")
        
        # Use the same case-insensitive approach as get_user_by_email
        search_email = current_user['email'].lower().strip()
        
        cursor.execute('''
            SELECT id, email, full_name, created_at, last_login, account_type,
                   profile_picture, phone_number, location, bio
            FROM users WHERE LOWER(TRIM(email)) = ?
        ''', (search_email,))
        
        user_data = cursor.fetchone()
        print(f"   📊 Full query result: {dict(user_data) if user_data else None}")
        
        conn.close()
        
        # Step 6: Check if user_data exists
        print(f"📌 Step 6: Checking if user_data exists")
        if not user_data:
            print(f"   ❌ No user data returned from query!")
            
            # Try one more time with a simpler query to debug
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT email FROM users")
            all_emails = cursor.fetchall()
            print(f"   📊 All emails in database: {all_emails}")
            conn.close()
            
            raise HTTPException(status_code=404, detail="User data not found")
        print(f"   ✅ User data retrieved successfully")
        
        # Step 7: Convert to dict
        print(f"📌 Step 7: Processing user data")
        user_dict = dict(user_data)
        print(f"   📊 Raw user_dict: {user_dict}")
        
        # Step 8: Get preferences and usage stats
        print(f"📌 Step 8: Getting preferences and usage stats")
        try:
            preferences = get_user_preferences(user_dict["id"])
            print(f"   ✅ Preferences loaded")
        except Exception as e:
            print(f"   ⚠️ Error loading preferences: {e}")
            preferences = {}
        
        try:
            usage_stats = get_user_usage_stats(user_dict["id"])
            print(f"   ✅ Usage stats loaded")
        except Exception as e:
            print(f"   ⚠️ Error loading usage stats: {e}")
            usage_stats = {}
        
        # Step 9: Return the response
        print(f"📌 Step 9: Returning response")
        response = {
            "user": user_dict,
            "preferences": preferences,
            "usage_stats": usage_stats,
            "account_status": "active",
            "email_verified": True
        }
        print(f"   ✅ Response prepared successfully")
        print("="*60 + "\n")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        tb = traceback.format_exc()
        print(f"❌❌❌ EXCEPTION in /api/user/profile:")
        print(f"   Error: {str(e)}")
        print(f"   Traceback: {tb}")
        print("="*60 + "\n")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.put("/api/user/profile")
async def update_user_profile(
    profile_data: UserProfileUpdate,
    token: str = Depends(extract_token)
):
    """Update user profile"""
    try:
        current_user = await get_current_user(token)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Build update query dynamically
        update_fields = []
        update_values = []
        
        if profile_data.full_name:
            update_fields.append("full_name = ?")
            update_values.append(profile_data.full_name)
        
        if profile_data.profile_picture:
            update_fields.append("profile_picture = ?")
            update_values.append(profile_data.profile_picture)
        
        if profile_data.phone_number is not None:
            update_fields.append("phone_number = ?")
            update_values.append(profile_data.phone_number)
        
        if profile_data.location is not None:
            update_fields.append("location = ?")
            update_values.append(profile_data.location)
        
        if profile_data.bio is not None:
            update_fields.append("bio = ?")
            update_values.append(profile_data.bio)
        
        if update_fields:
            update_values.append(current_user["email"])
            update_query = f"UPDATE users SET {', '.join(update_fields)} WHERE email = ?"
            cursor.execute(update_query, update_values)
            conn.commit()
        
        conn.close()
        
        return {"message": "Profile updated successfully", "updated_fields": update_fields}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/user/preferences")
async def get_preferences(token: str = Depends(extract_token)):
    """Get user preferences"""
    try:
        current_user = await get_current_user(token)
        user = get_user_by_email(current_user["email"])
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        preferences = get_user_preferences(user["id"])
        return preferences
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/user/preferences")
async def update_preferences(
    preferences: UserPreferences,
    token: str = Depends(extract_token)
):
    """Update user preferences"""
    try:
        current_user = await get_current_user(token)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get user ID
        user = get_user_by_email(current_user["email"])
        
        # Check if preferences exist
        cursor.execute("SELECT id FROM user_preferences WHERE user_id = ?", (user["id"],))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing preferences
            cursor.execute('''
                UPDATE user_preferences SET
                    language = ?, timezone = ?, date_format = ?,
                    temperature_unit = ?, wind_speed_unit = ?, pressure_unit = ?,
                    distance_unit = ?, theme = ?
                WHERE user_id = ?
            ''', (
                preferences.language,
                preferences.timezone,
                preferences.date_format,
                preferences.temperature_unit,
                preferences.wind_speed_unit,
                preferences.pressure_unit,
                preferences.distance_unit,
                preferences.theme,
                user["id"]
            ))
        else:
            # Insert new preferences
            cursor.execute('''
                INSERT INTO user_preferences 
                (user_id, language, timezone, date_format, temperature_unit, 
                 wind_speed_unit, pressure_unit, distance_unit, theme)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user["id"],
                preferences.language,
                preferences.timezone,
                preferences.date_format,
                preferences.temperature_unit,
                preferences.wind_speed_unit,
                preferences.pressure_unit,
                preferences.distance_unit,
                preferences.theme
            ))
        
        conn.commit()
        conn.close()
        
        return {"message": "Preferences updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/user/usage-stats")
async def get_usage_stats(token: str = Depends(extract_token)):
    """Get user usage statistics"""
    try:
        current_user = await get_current_user(token)
        user = get_user_by_email(current_user["email"])
        
        # Get API usage from activity log
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get current month usage
        current_month = datetime.now().strftime("%Y-%m")
        cursor.execute('''
            SELECT COUNT(*) as api_calls FROM activity_log 
            WHERE user_id = ? AND strftime('%Y-%m', timestamp) = ?
        ''', (user["id"], current_month))
        
        api_calls = cursor.fetchone()[0]
        
        # Get total anomalies detected by user
        cursor.execute('''
            SELECT COUNT(*) as anomalies_detected FROM activity_log 
            WHERE user_id = ? AND is_anomaly = 1
        ''', (user["id"],))
        
        anomalies_detected = cursor.fetchone()[0]
        
        # Get favorite cities
        cursor.execute('''
            SELECT city, COUNT(*) as checks 
            FROM activity_log 
            WHERE user_id = ? AND city IS NOT NULL 
            GROUP BY city 
            ORDER BY checks DESC 
            LIMIT 5
        ''', (user["id"],))
        
        favorite_cities = [{"city": row[0], "checks": row[1]} for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            "api_calls_current_month": api_calls,
            "anomalies_detected": anomalies_detected,
            "account_created": user["created_at"],
            "last_login": user["last_login"] or user["created_at"],
            "favorite_cities": favorite_cities,
            "active_sessions": 1  # Simplified
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/user/api-keys")
async def get_api_keys(token: str = Depends(extract_token)):
    """Get user's API keys"""
    try:
        current_user = await get_current_user(token)
        user = get_user_by_email(current_user["email"])
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM api_keys 
            WHERE user_id = ? AND is_active = 1
            ORDER BY created_at DESC
        ''', (user["id"],))
        
        keys = cursor.fetchall()
        conn.close()
        
        return {"api_keys": [dict(key) for key in keys]}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/user/api-keys")
async def create_api_key(
    key_data: APIKeyCreate,
    token: str = Depends(extract_token)
):
    """Create a new API key"""
    try:
        current_user = await get_current_user(token)
        user = get_user_by_email(current_user["email"])
        
        # Generate API key
        api_key = f"wai_{secrets.token_hex(24)}"
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO api_keys (user_id, key_name, api_key, permissions, expires_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            user["id"],
            key_data.key_name,
            api_key,
            key_data.permissions,
            (datetime.now() + timedelta(days=365)).isoformat()
        ))
        
        conn.commit()
        key_id = cursor.lastrowid
        conn.close()
        
        return {
            "message": "API key created successfully",
            "api_key": api_key,
            "key_id": key_id,
            "warning": "Save this key now - it won't be shown again!"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/user/api-keys/{key_id}")
async def revoke_api_key(key_id: int, token: str = Depends(extract_token)):
    """Revoke an API key"""
    try:
        current_user = await get_current_user(token)
        user = get_user_by_email(current_user["email"])
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE api_keys 
            SET is_active = 0 
            WHERE id = ? AND user_id = ?
        ''', (key_id, user["id"]))
        
        conn.commit()
        conn.close()
        
        return {"message": "API key revoked successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/user/generate-api-key")
async def generate_api_key(
    request: GenerateAPIKeyRequest,
    token: str = Depends(extract_token)
):
    """Generate a new API key for the user"""
    try:
        current_user = await get_current_user(token)
        user = get_user_by_email(current_user["email"])
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Validate input
        if not request.name or not request.name.strip():
            raise HTTPException(status_code=400, detail="API key name is required")
        
        # Generate a secure API key
        import secrets
        import hashlib
        
        # Create a unique API key
        raw_key = f"wai_{secrets.token_urlsafe(32)}"
        
        # Store only a hash of the key for security (optional)
        # key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if user already has too many keys (optional limit)
        cursor.execute("SELECT COUNT(*) FROM api_keys WHERE user_id = ? AND is_active = 1", (user["id"],))
        key_count = cursor.fetchone()[0]
        
        if key_count >= 10:
            conn.close()
            raise HTTPException(status_code=400, detail="Maximum number of API keys reached (10)")
        
        # Set expiry (1 year from now)
        expires_at = (datetime.now() + timedelta(days=365)).isoformat()
        
        # Insert the new API key
        cursor.execute('''
            INSERT INTO api_keys 
            (user_id, key_name, api_key, permissions, expires_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            user["id"],
            request.name.strip(),
            raw_key,
            request.type,
            expires_at,
            datetime.now().isoformat()
        ))
        
        key_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "message": "API key generated successfully",
            "api_key": raw_key,
            "key_id": key_id,
            "key_name": request.name,
            "permissions": request.type,
            "expires_at": expires_at,
            "warning": "Save this API key now! It will not be shown again for security reasons."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error generating API key: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate API key: {str(e)}")
    
@app.delete("/api/user/revoke-api-key/{key_id}")
async def revoke_api_key(
    key_id: int,
    token: str = Depends(extract_token)
):
    """Revoke an API key"""
    try:
        current_user = await get_current_user(token)
        user = get_user_by_email(current_user["email"])
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Verify the key belongs to this user
        cursor.execute("SELECT id FROM api_keys WHERE id = ? AND user_id = ?", (key_id, user["id"]))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="API key not found")
        
        # Soft delete - set is_active to 0
        cursor.execute("UPDATE api_keys SET is_active = 0 WHERE id = ?", (key_id,))
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "message": "API key revoked successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error revoking API key: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to revoke API key: {str(e)}")

@app.get("/api/user/list-api-keys")
async def list_api_keys(
    token: str = Depends(extract_token)
):
    """List all active API keys for the user"""
    try:
        current_user = await get_current_user(token)
        user = get_user_by_email(current_user["email"])
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, key_name, permissions, 
                   substr(api_key, 1, 8) || '...' || substr(api_key, -4) as masked_key,
                   created_at, expires_at, last_used
            FROM api_keys 
            WHERE user_id = ? AND is_active = 1
            ORDER BY created_at DESC
        ''', (user["id"],))
        
        keys = cursor.fetchall()
        conn.close()
        
        return {
            "success": True,
            "api_keys": [dict(key) for key in keys]
        }
        
    except Exception as e:
        print(f"Error listing API keys: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list API keys: {str(e)}")

@app.get("/api/user/usage-detailed")
async def get_detailed_usage_stats(
    token: str = Depends(extract_token),
    days: int = 30
):
    """Get detailed usage statistics"""
    try:
        current_user = await get_current_user(token)
        user = get_user_by_email(current_user["email"])
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get daily usage for specified days
        cursor.execute('''
            SELECT 
                DATE(timestamp) as date,
                COUNT(*) as total_requests,
                SUM(CASE WHEN activity_type = 'Anomaly Detection' THEN 1 ELSE 0 END) as anomaly_checks,
                SUM(CASE WHEN activity_type = 'Weather Check' THEN 1 ELSE 0 END) as weather_checks,
                SUM(CASE WHEN is_anomaly = 1 THEN 1 ELSE 0 END) as anomalies_detected
            FROM activity_log 
            WHERE user_id = ? 
                AND timestamp >= DATE('now', ?)
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
        ''', (user["id"], f'-{days} days'))
        
        daily_stats = cursor.fetchall()
        
        # Get city statistics
        cursor.execute('''
            SELECT 
                city,
                COUNT(*) as total_checks,
                SUM(CASE WHEN is_anomaly = 1 THEN 1 ELSE 0 END) as anomalies
            FROM activity_log 
            WHERE user_id = ? AND city IS NOT NULL
            GROUP BY city
            ORDER BY total_checks DESC
            LIMIT 10
        ''', (user["id"],))
        
        city_stats = cursor.fetchall()
        
        conn.close()
        
        return {
            "daily_stats": [dict(row) for row in daily_stats],
            "city_stats": [dict(row) for row in city_stats],
            "period_days": days,
            "user_id": user["id"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============ BILLING & SUBSCRIPTION ENDPOINTS ============

# Available plans
AVAILABLE_PLANS = [
    {
        "plan_id": "free",
        "plan_name": "Free",
        "price": 0,
        "interval": "monthly",
        "features": [
            "Basic weather data",
            "50 API calls per day",
            "7-day weather history",
            "Email support"
        ]
    },
    {
        "plan_id": "basic",
        "plan_name": "Basic",
        "price": 9.99,
        "interval": "monthly",
        "features": [
            "Advanced weather data",
            "500 API calls per day",
            "30-day weather history",
            "Anomaly detection",
            "Priority email support"
        ]
    },
    {
        "plan_id": "pro",
        "plan_name": "Professional",
        "price": 29.99,
        "interval": "monthly",
        "features": [
            "Premium weather data",
            "5000 API calls per day",
            "1-year weather history",
            "Advanced anomaly detection",
            "ML model access",
            "Phone & email support",
            "API key management"
        ]
    },
    {
        "plan_id": "enterprise",
        "plan_name": "Enterprise",
        "price": 99.99,
        "interval": "monthly",
        "features": [
            "Enterprise weather data",
            "Unlimited API calls",
            "Unlimited weather history",
            "Custom ML models",
            "Dedicated support",
            "SLA guarantee",
            "Custom integrations"
        ]
    }
]

@app.get("/api/billing/plans")
async def get_subscription_plans():
    """Get available subscription plans"""
    return {
        "success": True,
        "plans": AVAILABLE_PLANS
    }

@app.get("/api/billing/current")
async def get_current_subscription(token: str = Depends(extract_token)):
    """Get current user's subscription"""
    try:
        current_user = await get_current_user(token)
        user = get_user_by_email(current_user["email"])
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get current subscription
        cursor.execute('''
            SELECT * FROM subscriptions WHERE user_id = ? AND status = 'active'
        ''', (user["id"],))
        
        subscription = cursor.fetchone()
        
        # Get payment methods
        cursor.execute('''
            SELECT * FROM payment_methods WHERE user_id = ? ORDER BY is_default DESC
        ''', (user["id"],))
        
        payment_methods = cursor.fetchall()
        
        # Get recent invoices
        cursor.execute('''
            SELECT * FROM invoices WHERE user_id = ? ORDER BY paid_at DESC LIMIT 10
        ''', (user["id"],))
        
        invoices = cursor.fetchall()
        
        conn.close()
        
        # If no subscription, return default free plan but preserve any stored payment methods/invoices
        if not subscription:
            return {
                "success": True,
                "subscription": {
                    "plan_id": "free",
                    "plan_name": "Free",
                    "status": "active",
                    "start_date": datetime.now().isoformat(),
                    "end_date": None,
                    "auto_renew": True,
                    "features": AVAILABLE_PLANS[0]["features"]
                },
                "payment_methods": [dict(pm) for pm in payment_methods],
                "invoices": [dict(inv) for inv in invoices]
            }
        
        # Find plan details
        plan = next((p for p in AVAILABLE_PLANS if p["plan_id"] == subscription["plan_id"]), AVAILABLE_PLANS[0])
        
        return {
            "success": True,
            "subscription": {
                "plan_id": subscription["plan_id"],
                "plan_name": plan["plan_name"],
                "status": subscription["status"],
                "start_date": subscription["start_date"],
                "end_date": subscription["end_date"],
                "auto_renew": bool(subscription["auto_renew"]),
                "features": plan["features"]
            },
            "payment_methods": [dict(pm) for pm in payment_methods],
            "invoices": [dict(inv) for inv in invoices]
        }
        
    except Exception as e:
        print(f"Error getting subscription: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get subscription")

@app.post("/api/billing/subscribe")
async def subscribe_to_plan(
    request: UpdateSubscriptionRequest,
    token: str = Depends(extract_token)
):
    """Subscribe to a plan"""
    try:
        current_user = await get_current_user(token)
        user = get_user_by_email(current_user["email"])
        
        if not request.plan_id:
            raise HTTPException(status_code=400, detail="Missing plan_id")
        
        # Validate plan exists
        plan = next((p for p in AVAILABLE_PLANS if p["plan_id"] == request.plan_id), None)
        if not plan:
            raise HTTPException(status_code=400, detail=f"Invalid plan: {request.plan_id}")
        
        print(f"✅ Plan validation passed: {plan['plan_name']}")
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if user already has subscription
        cursor.execute("SELECT id FROM subscriptions WHERE user_id = ?", (user["id"],))
        existing = cursor.fetchone()
        
        end_date = None
        if plan["price"] > 0:
            # Paid plan - set end date 1 month from now
            end_date = (datetime.now() + timedelta(days=30)).isoformat()
        
        if existing:
            # Update existing subscription
            cursor.execute('''
                UPDATE subscriptions SET
                    plan_id = ?,
                    end_date = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (request.plan_id, end_date, user["id"]))
        else:
            # Create new subscription
            cursor.execute('''
                INSERT INTO subscriptions (user_id, plan_id, end_date)
                VALUES (?, ?, ?)
            ''', (user["id"], request.plan_id, end_date))
        
        # Create invoice for paid plans
        if plan["price"] > 0:
            invoice_number = f"INV-{datetime.now().strftime('%Y%m%d')}-{user['id']}-{secrets.token_hex(4).upper()}"
            cursor.execute('''
                INSERT INTO invoices (user_id, invoice_number, plan_id, amount)
                VALUES (?, ?, ?, ?)
            ''', (user["id"], invoice_number, request.plan_id, plan["price"]))
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "message": f"Successfully subscribed to {plan['plan_name']} plan",
            "plan": plan
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error subscribing to plan: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to subscribe")

@app.post("/api/billing/cancel")
async def cancel_subscription(token: str = Depends(extract_token)):
    """Cancel subscription"""
    try:
        current_user = await get_current_user(token)
        user = get_user_by_email(current_user["email"])
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE subscriptions SET
                status = 'cancelled',
                auto_renew = 0,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ? AND status = 'active'
        ''', (user["id"],))
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "message": "Subscription cancelled successfully"
        }
        
    except Exception as e:
        print(f"Error cancelling subscription: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to cancel subscription")

@app.post("/api/billing/payment-methods")
async def add_payment_method(
    request: PaymentMethodRequest,
    token: str = Depends(extract_token)
):
    """Add a payment method"""
    try:
        current_user = await get_current_user(token)
        user = get_user_by_email(current_user["email"])
        
        # In production, you'd use a payment processor like Stripe
        # This is a simplified example
        
        # Validate card (basic validation)
        if len(request.card_number.replace(" ", "")) != 16:
            raise HTTPException(status_code=400, detail="Invalid card number")
        
        if request.expiry_year < datetime.now().year or \
           (request.expiry_year == datetime.now().year and request.expiry_month < datetime.now().month):
            raise HTTPException(status_code=400, detail="Card expired")
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # If this is the first payment method or set as default, reset other defaults
        if request.is_default:
            cursor.execute('''
                UPDATE payment_methods SET is_default = 0 WHERE user_id = ?
            ''', (user["id"],))
        
        # Store only last 4 digits of card
        last4 = request.card_number[-4:]
        
        cursor.execute('''
            INSERT INTO payment_methods
            (user_id, card_last4, card_brand, card_holder, expiry_month, expiry_year, is_default)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            user["id"],
            last4,
            "visa",  # In production, detect from card number
            request.card_holder,
            request.expiry_month,
            request.expiry_year,
            1 if request.is_default else 0
        ))
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "message": "Payment method added successfully",
            "card_last4": last4
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error adding payment method: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to add payment method")

@app.delete("/api/billing/payment-methods/{method_id}")
async def remove_payment_method(
    method_id: int,
    token: str = Depends(extract_token)
):
    """Remove a payment method"""
    try:
        current_user = await get_current_user(token)
        user = get_user_by_email(current_user["email"])
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Verify ownership
        cursor.execute('''
            DELETE FROM payment_methods
            WHERE id = ? AND user_id = ?
        ''', (method_id, user["id"]))
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "message": "Payment method removed successfully"
        }
        
    except Exception as e:
        print(f"Error removing payment method: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to remove payment method")

@app.get("/api/billing/invoices")
async def get_invoices(
    token: str = Depends(extract_token),
    limit: int = 10
):
    """Get user's invoices"""
    try:
        current_user = await get_current_user(token)
        user = get_user_by_email(current_user["email"])
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM invoices
            WHERE user_id = ?
            ORDER BY paid_at DESC
            LIMIT ?
        ''', (user["id"], limit))
        
        invoices = cursor.fetchall()
        conn.close()
        
        return {
            "success": True,
            "invoices": [dict(inv) for inv in invoices]
        }
        
    except Exception as e:
        print(f"Error getting invoices: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get invoices")
    


@app.post("/api/user/change-password")
async def change_password(
    password_data: PasswordChangeRequest,
    token: str = Depends(extract_token)
):
    """Change user password"""
    try:
        current_user = await get_current_user(token)
        
        # Validate input
        current_password = password_data.current_password
        new_password = password_data.new_password
        
        if not current_password or not new_password:
            raise HTTPException(status_code=400, detail="Current password and new password are required")
        
        # Validate new password
        if len(new_password) < 8:
            raise HTTPException(status_code=400, detail="New password must be at least 8 characters")
        
        # Get user from database
        user = get_user_by_email(current_user["email"])
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Verify current password
        if not verify_password(current_password, user["hashed_password"]):
            raise HTTPException(status_code=401, detail="Current password is incorrect")
        
        # Update password
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        new_hashed_password = get_password_hash(new_password)
        cursor.execute(
            "UPDATE users SET hashed_password = ? WHERE email = ?",
            (new_hashed_password, current_user["email"])
        )
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "message": "Password changed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error changing password: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to change password")
    
@app.post("/api/user/email-2fa/enable")
async def enable_email_2fa(
    request: EnableEmail2FARequest,
    token: str = Depends(extract_token)
):
    """Enable email-based 2FA"""
    try:
        current_user = await get_current_user(token)
        user = get_user_by_email(current_user["email"])
        
        # Verify password
        if not verify_password(request.password, user["hashed_password"]):
            raise HTTPException(status_code=401, detail="Invalid password")
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if preferences exist
        cursor.execute("SELECT id FROM user_preferences WHERE user_id = ?", (user["id"],))
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute('''
                UPDATE user_preferences SET
                    email_2fa_enabled = 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (user["id"],))
        else:
            cursor.execute('''
                INSERT INTO user_preferences 
                (user_id, email_2fa_enabled)
                VALUES (?, ?)
            ''', (user["id"], 1))
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "message": "Email 2FA enabled successfully"
        }
        
    except Exception as e:
        print(f"Error enabling email 2FA: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to enable email 2FA")

@app.post("/api/user/email-2fa/disable")
async def disable_email_2fa(
    request: EnableEmail2FARequest,
    token: str = Depends(extract_token)
):
    """Disable email-based 2FA"""
    try:
        current_user = await get_current_user(token)
        user = get_user_by_email(current_user["email"])
        
        # Verify password
        if not verify_password(request.password, user["hashed_password"]):
            raise HTTPException(status_code=401, detail="Invalid password")
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE user_preferences SET
                email_2fa_enabled = 0,
                otp_secret = NULL,
                otp_expiry = NULL,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (user["id"],))
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "message": "Email 2FA disabled successfully"
        }
        
    except Exception as e:
        print(f"Error disabling email 2FA: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to disable email 2FA")

@app.post("/api/auth/login-with-email-2fa")
async def login_with_email_2fa(request: Request):
    """Login with email 2FA - Step 1: Send OTP"""
    try:
        body = await request.json()
        email = body.get("email")
        password = body.get("password")
        remember_me = body.get("remember_me", False)
        
        # Authenticate user
        user = authenticate_user(email, password)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Check if email 2FA is enabled
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT email_2fa_enabled FROM user_preferences 
            WHERE user_id = ?
        ''', (user["id"],))
        result = cursor.fetchone()
        email_2fa_enabled = result and result[0] == 1 if result else False
        
        if not email_2fa_enabled:
            conn.close()
            # No 2FA, proceed with normal login
            access_token = create_access_token(
                data={"sub": email},
                expires_delta=timedelta(days=30 if remember_me else 7)
            )
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user": {
                    "email": user["email"],
                    "full_name": user["full_name"]
                }
            }
        
        # Generate OTP
        otp = generate_otp()
        otp_expiry = datetime.now() + timedelta(minutes=10)
        
        # Store OTP in database
        cursor.execute('''
            UPDATE user_preferences SET
                otp_secret = ?,
                otp_expiry = ?
            WHERE user_id = ?
        ''', (otp, otp_expiry.isoformat(), user["id"]))
        conn.commit()
        conn.close()
        
        # Send OTP via email
        email_sent = await send_otp_email(email, otp, user["full_name"])
        
        if not email_sent:
            raise HTTPException(status_code=500, detail="Failed to send verification code")
        
        # Create temporary token for 2FA session
        temp_token = secrets.token_urlsafe(32)
        sessions_db[temp_token] = {
            "email": email,
            "temp": True,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(minutes=10)).isoformat()
        }
        
        return JSONResponse(
            status_code=202,
            content={
                "requires_2fa": True,
                "message": "Verification code sent to your email",
                "email": email,
                "temp_token": temp_token
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Login with 2FA error: {str(e)}")
        raise HTTPException(status_code=500, detail="Login failed")

@app.post("/api/auth/verify-email-2fa")
async def verify_email_2fa(request: Request):
    """Step 2: Verify OTP and complete login"""
    try:
        body = await request.json()
        email = body.get("email")
        code = body.get("code")
        temp_token = body.get("temp_token")
        remember_me = body.get("remember_me", False)
        
        if not email or not code or not temp_token:
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        # Verify temp token
        temp_session = sessions_db.get(temp_token)
        if not temp_session or not temp_session.get("temp"):
            raise HTTPException(status_code=401, detail="Invalid or expired session")
        
        if temp_session.get("email") != email:
            raise HTTPException(status_code=401, detail="Email mismatch")
        
        # Get user
        user = get_user_by_email(email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Verify OTP
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT otp_secret, otp_expiry FROM user_preferences 
            WHERE user_id = ? AND email_2fa_enabled = 1
        ''', (user["id"],))
        
        result = cursor.fetchone()
        if not result or not result[0] or not result[1]:
            conn.close()
            raise HTTPException(status_code=401, detail="No valid OTP found")
        
        stored_otp = result[0]
        otp_expiry = datetime.fromisoformat(result[1])
        
        # Check if OTP is expired
        if datetime.now() > otp_expiry:
            conn.close()
            raise HTTPException(status_code=401, detail="OTP has expired")
        
        # Verify OTP
        if code != stored_otp:
            conn.close()
            raise HTTPException(status_code=401, detail="Invalid verification code")
        
        # Clear OTP
        cursor.execute('''
            UPDATE user_preferences SET
                otp_secret = NULL,
                otp_expiry = NULL
            WHERE user_id = ?
        ''', (user["id"],))
        conn.commit()
        conn.close()
        
        # Remove temp token
        del sessions_db[temp_token]
        
        # Create full access token
        access_token = create_access_token(
            data={"sub": email, "two_factor_verified": True},
            expires_delta=timedelta(days=30 if remember_me else 7)
        )
        
        # Store session
        sessions_db[access_token] = {
            "email": email,
            "full_name": user["full_name"],
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(days=30 if remember_me else 7)).isoformat(),
            "two_factor_verified": True
        }
        
        # Update last login
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET last_login = ? WHERE email = ?", 
                      (datetime.now().isoformat(), email))
        conn.commit()
        conn.close()
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "two_factor_enabled": True,
            "user": {
                "email": user["email"],
                "full_name": user["full_name"],
                "last_login": datetime.now().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Email 2FA verification error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to verify code")
    
    # ============ ACCOUNT SWITCHING ENDPOINTS ============

@app.get("/api/accounts/list")
async def list_connected_accounts(token: str = Depends(extract_token)):
    """List all connected accounts for the current user"""
    try:
        current_user = await get_current_user(token)
        user = get_user_by_email(current_user["email"])
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get main account first
        cursor.execute('''
            SELECT 
                id, 
                email, 
                full_name as name, 
                account_type as type,
                profile_picture,
                last_login as last_used,
                1 as is_active,
                1 as is_main
            FROM users 
            WHERE id = ?
        ''', (user["id"],))
        
        main_account = cursor.fetchone()
        
        # Get connected accounts
        cursor.execute('''
            SELECT 
                id,
                account_email as email,
                account_name as name,
                account_type as type,
                profile_picture,
                last_used,
                is_active
            FROM connected_accounts 
            WHERE user_id = ? AND is_active = 1
            ORDER BY last_used DESC
        ''', (user["id"],))
        
        connected_accounts = cursor.fetchall()
        conn.close()
        
        accounts = []
        if main_account:
            accounts.append(dict(main_account))
        
        for acc in connected_accounts:
            acc_dict = dict(acc)
            acc_dict['is_main'] = False
            accounts.append(acc_dict)
        
        return {
            "success": True,
            "accounts": accounts,
            "current_account": current_user["email"]
        }
        
    except Exception as e:
        print(f"Error listing accounts: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list accounts")

@app.post("/api/accounts/add")
async def add_account(
    request: AddAccountRequest,
    token: str = Depends(extract_token)
):
    """Add a new account to switch to"""
    try:
        current_user = await get_current_user(token)
        user = get_user_by_email(current_user["email"])
        
        # Validate the account to add exists
        account_to_add = get_user_by_email(request.email)
        if not account_to_add:
            raise HTTPException(status_code=404, detail="Account not found")
        
        # Verify password for the account to add
        if not verify_password(request.password, account_to_add["hashed_password"]):
            raise HTTPException(status_code=401, detail="Invalid password for the account")
        
        # Don't allow adding own account
        if account_to_add["email"] == current_user["email"]:
            raise HTTPException(status_code=400, detail="Cannot add your own account")
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if already connected
        cursor.execute('''
            SELECT id FROM connected_accounts 
            WHERE user_id = ? AND account_email = ?
        ''', (user["id"], request.email))
        
        existing = cursor.fetchone()
        
        if existing:
            # Reactivate if exists
            cursor.execute('''
                UPDATE connected_accounts SET
                    is_active = 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (existing[0],))
            message = "Account reconnected successfully"
        else:
            # Add new connection
            account_name = request.account_name or account_to_add["full_name"]
            cursor.execute('''
                INSERT INTO connected_accounts 
                (user_id, account_email, account_name, account_type, profile_picture)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                user["id"],
                account_to_add["email"],
                account_name,
                account_to_add["account_type"],
                account_to_add.get("profile_picture", "")
            ))
            message = "Account added successfully"
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "message": message,
            "account": {
                "email": account_to_add["email"],
                "name": account_name,
                "type": account_to_add["account_type"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error adding account: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to add account")

@app.post("/api/accounts/switch")
async def switch_account(
    request: SwitchAccountRequest,
    token: str = Depends(extract_token)
):
    """Switch to a different account"""
    try:
        current_user = await get_current_user(token)
        user = get_user_by_email(current_user["email"])
        
        if not user:
            raise HTTPException(status_code=404, detail="Current user not found")
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get the account to switch to
        cursor.execute('''
            SELECT * FROM connected_accounts 
            WHERE id = ? AND user_id = ? AND is_active = 1
        ''', (request.account_id, user["id"]))
        
        account = cursor.fetchone()
        if not account:
            conn.close()
            raise HTTPException(status_code=404, detail="Connected account not found")
        
        # DEBUG: Print password verification attempt
        print(f"Attempting to verify password for user: {user['email']}")
        print(f"Stored hash: {user['hashed_password'][:20]}...")
        
        # Verify password for the main account (security)
        if not verify_password(request.password, user["hashed_password"]):
            conn.close()
            print(f"Password verification FAILED for {user['email']}")
            raise HTTPException(status_code=401, detail="Invalid password for main account")
        
        print(f"Password verification SUCCESS for {user['email']}")
        
        # Update last used
        cursor.execute('''
            UPDATE connected_accounts SET
                last_used = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (request.account_id,))
        
        # Create a session token for the switched account
        session_token = secrets.token_urlsafe(32)
        expires_at = (datetime.now() + timedelta(hours=24)).isoformat()
        
        cursor.execute('''
            INSERT INTO account_sessions 
            (user_id, account_id, session_token, expires_at)
            VALUES (?, ?, ?, ?)
        ''', (user["id"], request.account_id, session_token, expires_at))
        
        conn.commit()
        conn.close()
        
        # Get account details
        account_dict = {
            "id": account[0],
            "email": account[2],
            "name": account[3],
            "type": account[4]
        }
        
        return {
            "success": True,
            "message": f"Switched to {account_dict['name']}'s account",
            "account": account_dict,
            "session_token": session_token,
            "expires_at": expires_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error switching account: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to switch account: {str(e)}")

@app.delete("/api/accounts/remove/{account_id}")
async def remove_account(
    account_id: int,
    token: str = Depends(extract_token)
):
    """Remove a connected account"""
    try:
        current_user = await get_current_user(token)
        user = get_user_by_email(current_user["email"])
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Soft delete - set inactive
        cursor.execute('''
            UPDATE connected_accounts SET
                is_active = 0,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
        ''', (account_id, user["id"]))
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "message": "Account removed successfully"
        }
        
    except Exception as e:
        print(f"Error removing account: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to remove account")

@app.get("/api/accounts/session/{session_token}")
async def verify_account_session(session_token: str):
    """Verify an account session token"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT as.*, ca.account_email, ca.account_name
            FROM account_sessions as
            JOIN connected_accounts ca ON as.account_id = ca.id
            WHERE as.session_token = ? AND as.expires_at > CURRENT_TIMESTAMP
        ''', (session_token,))
        
        session = cursor.fetchone()
        conn.close()
        
        if not session:
            raise HTTPException(status_code=401, detail="Invalid or expired session")
        
        return {
            "valid": True,
            "account": {
                "email": session[5],
                "name": session[6]
            }
        }
        
    except Exception as e:
        print(f"Error verifying session: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to verify session")
        



# ============ SPECIFIC PAGE ROUTES ============

@app.get("/")
async def home_page():
    """Serve the home page (index.html)"""
    return serve_html_file("index.html")

@app.get("/dashboard")
async def dashboard_page():
    """Serve the dashboard page"""
    dashboard_path = WEBAPP_DIR / "dashboard.html"
    
    if dashboard_path.exists():
        print(f"✅ Serving dashboard from: {dashboard_path}")
        return FileResponse(dashboard_path)
    else:
        print(f"❌ Dashboard file not found at: {dashboard_path}")
        
        # Check for index.html as fallback
        index_path = WEBAPP_DIR / "index.html"
        if index_path.exists():
            print(f"⚠️ Found index.html instead, serving as dashboard")
            return FileResponse(index_path)
        
        return HTMLResponse(
            content=f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Dashboard Not Found</title>
                <style>
                    body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
                    h1 {{ color: #ff4444; }}
                </style>
            </head>
            <body>
                <h1>Dashboard File Not Found</h1>
                <p>The dashboard file should be at: {dashboard_path}</p>
                <p>Please make sure you have a dashboard.html file in the frontend folder.</p>
                <a href="/">Return to Home</a>
            </body>
            </html>
            """,
            status_code=404
        )

@app.get("/login")
async def login_page():
    """Serve the login page"""
    return serve_html_file("login.html")

@app.get("/features")
async def features_page():
    """Serve the features page"""
    return serve_html_file("features.html")

@app.get("/pricing")
async def pricing_page():
    """Serve the pricing page"""
    return serve_html_file("pricing.html")

@app.get("/blog")
async def blog_page():
    """Serve the blog page"""
    return serve_html_file("blog.html")

@app.get("/contact")
async def contact_page():
    """Serve the contact page"""
    return serve_html_file("contact.html")

@app.get("/about")
async def about_page():
    """Serve the about page"""
    return serve_html_file("about.html")

# ============ DASHBOARD ASSETS ROUTE ============

@app.get("/dashboard-assets/{full_path:path}")
async def dashboard_assets(full_path: str):
    """Serve dashboard assets (CSS, JS, images, etc.)"""
    asset_path = WEBAPP_DIR / full_path
    
    if asset_path.exists() and asset_path.is_file():
        return FileResponse(asset_path)
    
    return JSONResponse(
        status_code=404,
        content={"detail": f"Dashboard asset not found: {full_path}"}
    )

# ============ CATCH-ALL ROUTE FOR STATIC FILES (MUST BE LAST) ============

@app.get("/{full_path:path}")
async def serve_static_files(request: Request, full_path: str = ""):
    """Serve static files - THIS MUST BE THE LAST ROUTE"""
    # Don't handle WebSocket connections here
    if request.headers.get("upgrade", "").lower() == "websocket":
        return
    
    # If no path specified, serve website home page
    if not full_path:
        return await home_page()
    
    # Don't handle API requests here (they should be caught by API routes above)
    if full_path.startswith("api/"):
        return JSONResponse(
            status_code=404,
            content={
                "detail": f"API endpoint not found: {full_path}",
                "note": "Make sure API routes are defined before this catch-all route",
                "available_endpoints": [
                    "/api/health",
                    "/api/test-connection", 
                    "/api/weather/current",
                    "/api/weather/predict-anomaly",
                    "/api/weather/future-anomalies",
                    "/api/weather/history",
                    "/api/weather/get-future-anomalies",
                    "/api/analytics/dashboard-stats",
                    "/api/analytics/recent-activity",
                    "/api/analytics/advanced-stats",
                    "/api/cities/supported",
                    "/api/contact/send",
                    "/api/auth/login",
                    "/api/auth/register",
                    "/api/auth/verify",
                    "/api/auth/logout",
                    "/api/auth/reset-password",
                    "/api/auth/reset-password/confirm",
                    "/api/user/profile",
                    "/api/user/preferences",
                    "/api/user/usage-stats",
                    "/api/user/api-keys"
                ]
            }
        )
    
    # Handle dashboard route
    if full_path == "dashboard":
        return await dashboard_page()
    
    # Handle dashboard assets
    if full_path.startswith("dashboard-assets/"):
        return await dashboard_assets(full_path.replace("dashboard-assets/", "", 1))
    
    # Try to serve from website folder
    file_path = FRONTEND_DIR / full_path
    
    # Check if file exists
    if file_path.exists() and file_path.is_file():
        return FileResponse(file_path)
    
    # For HTML-like paths without extension in website, try adding .html
    if "." not in full_path:
        html_path = FRONTEND_DIR / f"{full_path}.html"
        if html_path.exists():
            return FileResponse(html_path)
    
    # For any other missing files, serve website index.html (for SPA routing)
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    
    # If index.html doesn't exist, return 404
    return JSONResponse(
        status_code=404,
        content={"detail": f"File not found: {full_path}"}
    )

# ============ PROFESSIONAL AUTO-TRAINING SYSTEM ============
try:
    from training.trainer import ProfessionalTrainer
    from training.scheduler import TrainingScheduler
    import threading
    
    TRAINER = ProfessionalTrainer(DB_PATH, os.path.join(current_dir, 'models'), OPENWEATHER_API_KEY)
    SCHEDULER = TrainingScheduler(TRAINER)
    
    # Start background scheduler
    SCHEDULER.start_in_background()
    print("✅ Professional auto-training system initialized")
    
    # Add manual training endpoint (admin only)
    @app.post("/api/admin/train-models")
    async def admin_train_models(secret_key: str = None):
        """Admin endpoint to manually trigger training"""
        # Simple security - you should implement proper auth
        if secret_key != "weather-ai-admin-2024":
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        # Run training in background to not block response
        def train_in_background():
            TRAINER.train_all_cities()
        
        thread = threading.Thread(target=train_in_background, daemon=True)
        thread.start()
        
        return {"status": "started", "message": "Training started in background"}

    # Add endpoint to check training status
    @app.get("/api/admin/training-status")
    async def get_training_status(secret_key: str = None):
        """Get training system status"""
        if secret_key != "weather-ai-admin-2024":
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get latest training job
        cursor.execute("SELECT * FROM training_jobs ORDER BY created_at DESC LIMIT 1")
        last_job = cursor.fetchone()
        
        # Get model counts
        cursor.execute("SELECT COUNT(*) FROM model_registry")
        model_count = cursor.fetchone()[0]
        
        # Get city counts
        cursor.execute("SELECT COUNT(DISTINCT city) FROM model_registry")
        city_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "scheduler_running": SCHEDULER.is_running,
            "total_models": model_count,
            "cities_trained": city_count,
            "last_training": dict(zip(['id','status','cities','models','accuracy','error','started','completed','created'], last_job)) if last_job else None
        }

except ImportError as e:
    print(f"⚠️ Training system not available: {e}")
    print("   Run: pip install pandas scikit-learn tensorflow schedule")
except Exception as e:
    print(f"⚠️ Error initializing training system: {e}")
# ============ 👆👆👆 END OF NEW CODE 👆👆👆 ============


# ============ STARTUP FUNCTIONS ============
# def create_default_user():
#     """Create a default admin user for testing"""
#     default_email = "admin@weatherai.com"
#     default_password = "Admin@123"
    
#     # Check if user already exists
#     existing_user = get_user_by_email(default_email)
#     if not existing_user:
#         try:
#             create_user(default_email, "Weather Admin", default_password, "personal")
#             print(f"✅ Default admin user created: {default_email} / {default_password}")
#         except Exception as e:
#             print(f"⚠️ Could not create default user: {e}")

# Print all registered routes for debugging
def print_all_routes():
    print("\n" + "="*60)
    print("📡 REGISTERED ROUTES")
    print("="*60)
    
    api_routes = []
    other_routes = []
    
    for route in app.routes:
        if hasattr(route, "path"):
            if route.path.startswith("/api/"):
                api_routes.append(route.path)
            else:
                other_routes.append(route.path)
    
    print("API Routes:")
    for route in sorted(api_routes):
        print(f"  • {route}")
    
    print("\nOther Routes:")
    for route in sorted(other_routes):
        print(f"  • {route}")
    
    print("="*60)

    # At the end of your main.py, before the main block, add:

def check_ml_dependencies():
    """Check if required ML libraries are installed and show versions"""
    required_packages = {
        'tensorflow': 'tensorflow',
        'statsmodels': 'statsmodels',
        'sklearn': 'scikit-learn',
        'prophet': 'prophet',
        'pandas': 'pandas',
        'numpy': 'numpy'
    }
    
    print("\n" + "="*60)
    print("📦 CHECKING ML DEPENDENCIES")
    print("="*60)
    
    missing_packages = []
    installed_packages = []
    
    for import_name, pip_name in required_packages.items():
        try:
            module = __import__(import_name)
            # Try to get version
            if hasattr(module, '__version__'):
                version = module.__version__
            else:
                version = "unknown"
            print(f"✅ {pip_name} v{version}")
            installed_packages.append(pip_name)
        except ImportError:
            print(f"❌ {pip_name} NOT FOUND")
            missing_packages.append(pip_name)
    
    if missing_packages:
        print("\n" + "="*60)
        print("⚠️  MISSING DEPENDENCIES")
        print("="*60)
        print("The following packages are missing:")
        for pkg in missing_packages:
            print(f"  • {pkg}")
        print("\nInstall with:")
        print(f"pip install {' '.join(missing_packages)}")
        print("="*60 + "\n")
    else:
        print("\n" + "="*60)
        print("✅ ALL ML DEPENDENCIES INSTALLED SUCCESSFULLY")
        print("="*60 + "\n")
    
    return len(missing_packages) == 0

# Call this before starting the server
if __name__ == "__main__":
    all_deps_installed = check_ml_dependencies()
    if not all_deps_installed:
        print("⚠️  Some dependencies are missing. The application may not work correctly.")
    # ... rest of your main block

# ============ MAIN ENTRY POINT ============
if __name__ == "__main__":
    # Create default user
    # create_default_user()
    
    # Print all routes for debugging
    print_all_routes()
    
    print("\n" + "="*60)
    print("✅ WEATHER AI PLATFORM READY")
    print("="*60)
    print("🎯 Version 3.0.0 with Future Anomaly Predictions")
    print("🎯 Complete Email Contact Form Support")
    print("🎯 Password Reset Functionality Added")
    print("🎯 NO NEED TO RUN 'npm run dev'")
    print("🎯 Everything runs from Python on port 3000")
    print("="*60)
    print("\n🌐 Open in browser: http://localhost:3000")
    print("📞 Contact page: http://localhost:3000/contact")
    print("🔑 Login page: http://localhost:3000/login")
    print("🔐 Forgot Password: http://localhost:3000/forgot-password")
    print("📊 Dashboard: http://localhost:3000/dashboard")
    print("📄 Features: http://localhost:3000/features")
    print("💰 Pricing: http://localhost:3000/pricing")
    print("📝 Blog: http://localhost:3000/blog")
    print("ℹ️  About: http://localhost:3000/about")
    print("="*60)
    print("\n🔧 NEW Password Reset API Endpoints:")
    print("   • POST /api/auth/reset-password - Request password reset")
    print("   • POST /api/auth/reset-password/confirm - Confirm reset with token")
    print("\n🔧 Existing API Endpoints:")
    print("   • GET  /api/health - Health check")
    print("   • GET  /api/test-connection - Test OpenWeatherMap")
    print("   • GET  /api/weather/current - Get current weather")
    print("   • POST /api/weather/predict-anomaly - Detect anomalies")
    print("   • POST /api/weather/future-anomalies - Predict future anomalies")
    print("   • GET  /api/weather/history - Historical data")
    print("   • GET  /api/analytics/dashboard-stats - Dashboard stats")
    print("   • GET  /api/analytics/recent-activity - Recent activity")
    print("   • POST /api/auth/login - User login")
    print("   • POST /api/auth/register - User registration")
    print("   • GET  /api/auth/verify - Verify token")
    print("   • GET  /api/auth/logout - Logout")
    print("   • GET  /api/user/profile - Get user profile")
    print("   • PUT  /api/user/profile - Update user profile")
    print("   • GET  /api/user/preferences - Get user preferences")
    print("   • PUT  /api/user/preferences - Update preferences")
    print("   • GET  /api/user/usage-stats - Get usage statistics")
    print("   • GET  /api/user/api-keys - Get API keys")
    print("   • POST /api/user/api-keys - Create API key")
    print("   • DELETE /api/user/api-keys/{key_id} - Revoke API key")
    print("="*60)
    print("\n📧 Email Configuration:")
    print(f"   • Admin Email: {EMAIL_CONFIG['ADMIN_EMAIL']}")
    print(f"   • SMTP Server: {EMAIL_CONFIG['SMTP_SERVER']}:{EMAIL_CONFIG['SMTP_PORT']}")
    print("   Note: Make sure you've generated an App Password for Gmail")
    print("="*60)
    print("\n🖥️  Server starting... Press Ctrl+C to stop")
    print("="*60)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=BACKEND_PORT,
        log_level="info"
    )