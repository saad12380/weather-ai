# weather-anomaly-predictor/backend/auth.py
from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
import sqlite3
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
import os

# ============ UPDATED: Database path ============
# Use relative path to backend directory
current_dir = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(current_dir, 'weather_anomaly_users.db')

# ============ UPDATED: JWT Configuration ============
# Make sure these match your main.py
from dotenv import load_dotenv
import os

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret-only-for-dev")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ============ UPDATED: Database setup ============
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create users table with all columns
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
    
    conn.commit()
    conn.close()

def add_missing_columns():
    """Add missing columns to existing users table"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check which columns exist
        cursor.execute("PRAGMA table_info(users)")
        existing_cols = [col[1] for col in cursor.fetchall()]
        print(f"📊 Existing columns: {existing_cols}")
        
        # Add missing columns
        if 'profile_picture' not in existing_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN profile_picture TEXT")
            print("✅ Added profile_picture column")
        
        if 'phone_number' not in existing_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN phone_number TEXT")
            print("✅ Added phone_number column")
        
        if 'location' not in existing_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN location TEXT")
            print("✅ Added location column")
        
        if 'bio' not in existing_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN bio TEXT")
            print("✅ Added bio column")
        
        conn.commit()
        conn.close()
        print("✅ Database migration complete")
    except Exception as e:
        print(f"⚠️ Error adding columns: {e}")


# Initialize database
init_db()
add_missing_columns()

# ============ Pydantic Models ============
class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    
    @field_validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password cannot be longer than 72 bytes')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one number')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(char.islower() for char in v):
            raise ValueError('Password must contain at least one lowercase letter')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False

class UserInDB(BaseModel):
    id: int
    email: str
    full_name: str
    created_at: datetime
    last_login: Optional[datetime] = None
    account_type: str

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: dict

# ============ Authentication Functions ============
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
def get_user_by_email(email: str):
    """Get user by email with case-insensitive search and whitespace trimming"""
    if not email:
        return None
    
    # Clean the email
    email = email.lower().strip()
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Use case-insensitive comparison and trim
    cursor.execute("SELECT * FROM users WHERE LOWER(TRIM(email)) = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        user_dict = dict(user)
        # Parse datetime strings
        if user_dict['created_at']:
            try:
                user_dict['created_at'] = datetime.strptime(user_dict['created_at'], '%Y-%m-%d %H:%M:%S')
            except:
                user_dict['created_at'] = None
        
        if user_dict['last_login']:
            try:
                user_dict['last_login'] = datetime.strptime(user_dict['last_login'], '%Y-%m-%d %H:%M:%S')
            except:
                user_dict['last_login'] = None
        return user_dict
    return None
def truncate_password(password: str, max_bytes: int = 72) -> str:
    encoded = password.encode('utf-8')
    if len(encoded) <= max_bytes:
        return password
    truncated = encoded[:max_bytes]
    # Remove incomplete UTF-8 sequences from the end
    while truncated and (truncated[-1] & 0x80) and not (truncated[-1] & 0x40):
        truncated = truncated[:-1]
    return truncated.decode('utf-8', errors='ignore')

# In backend/auth.py, find this function and update it:

def create_user(email: str, full_name: str, password: str, account_type: str = "personal"):
    # Normalize email
    email = email.lower().strip()
    
    password = truncate_password(password)
    hashed_password = get_password_hash(password)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO users (email, full_name, hashed_password, account_type)
            VALUES (?, ?, ?, ?)
        ''', (email, full_name, hashed_password, account_type))
        
        user_id = cursor.lastrowid
        
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        
        # Parse datetime strings - adjust indices based on your table structure
        created_at = datetime.strptime(user[4], '%Y-%m-%d %H:%M:%S') if user[4] else None
        last_login = datetime.strptime(user[5], '%Y-%m-%d %H:%M:%S') if user[5] else None
        
        conn.commit()
        
        return {
            "id": user[0],
            "email": user[1],
            "full_name": user[2],
            "created_at": created_at,
            "last_login": last_login,
            "account_type": user[7] if len(user) > 7 else "personal",
            "profile_picture": None
        }
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    finally:
        conn.close()

def authenticate_user(email: str, password: str):
    print(f"🔐 Authenticating user: {email}")
    user = get_user_by_email(email)
    if not user:
        print(f"❌ User not found: {email}")
        return None
    
    print(f"✅ User found: {user['email']}")
    password = truncate_password(password)
    
    if not verify_password(password, user["hashed_password"]):
        print(f"❌ Password verification failed for: {email}")
        return None
    
    print(f"✅ Password verified for: {email}")
    return user
def update_user_last_login(email: str):
    """Update user's last login timestamp"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE users SET last_login = ? WHERE email = ?",
            (datetime.now().isoformat(), email)
        )
        conn.commit()
    finally:
        conn.close()

def get_user_by_id(user_id: int):
    """Get user by ID"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return dict(user)
    return None

def delete_user(email: str):
    """Delete a user (admin function)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM users WHERE email = ?", (email,))
        conn.commit()
        return True
    except Exception as e:
        return False
    finally:
        conn.close()

def get_all_users():
    """Get all users (admin function)"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, full_name, created_at, last_login, account_type FROM users")
    users = cursor.fetchall()
    conn.close()
    
    return [dict(user) for user in users]

# ============ Session Management Functions ============
def create_session(user_id: int, token: str, expires_at: datetime):
    """Create a user session"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO user_sessions (user_id, token, expires_at)
            VALUES (?, ?, ?)
        ''', (user_id, token, expires_at.isoformat()))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error creating session: {e}")
        return False
    finally:
        conn.close()

def get_session(token: str):
    """Get session by token"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_sessions WHERE token = ?", (token,))
    session = cursor.fetchone()
    conn.close()
    
    if session:
        session_dict = dict(session)
        # Parse datetime
        if session_dict['expires_at']:
            try:
                session_dict['expires_at'] = datetime.fromisoformat(session_dict['expires_at'])
            except:
                session_dict['expires_at'] = None
        return session_dict
    return None

def delete_session(token: str):
    """Delete a session"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM user_sessions WHERE token = ?", (token,))
        conn.commit()
        return True
    except Exception as e:
        return False
    finally:
        conn.close()

def cleanup_expired_sessions():
    """Clean up expired sessions"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM user_sessions WHERE expires_at < ?", 
                      (datetime.now().isoformat(),))
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()

# ============ Account Session Functions ============
def verify_account_session(session_token: str):
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
            return None
        
        # session columns: id, user_id, account_id, session_token, created_at, expires_at, account_email, account_name
        return {
            "valid": True,
            "email": session[6],  # account_email
            "full_name": session[7],  # account_name
            "is_switched": True,
            "account_id": session[2]  # account_id
        }
    except Exception as e:
        print(f"Error verifying account session: {e}")
        return None

# ============ Activity Log Functions ============
def log_activity(user_id: int, activity_type: str, city: str, status: str, is_anomaly: bool = False):
    """Log user activity"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO activity_log (user_id, activity_type, city, status, is_anomaly)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, activity_type, city, status, is_anomaly))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error logging activity: {e}")
        return False
    finally:
        conn.close()

def get_user_activities(user_id: int, limit: int = 10):
    """Get user activities"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM activity_log 
        WHERE user_id = ? 
        ORDER BY timestamp DESC 
        LIMIT ?
    ''', (user_id, limit))
    activities = cursor.fetchall()
    conn.close()
    
    return [dict(activity) for activity in activities]

def get_recent_activities(limit: int = 10):
    """Get recent activities for all users"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('''
        SELECT al.*, u.email, u.full_name 
        FROM activity_log al
        JOIN users u ON al.user_id = u.id
        ORDER BY al.timestamp DESC 
        LIMIT ?
    ''', (limit,))
    activities = cursor.fetchall()
    conn.close()
    
    return [dict(activity) for activity in activities]