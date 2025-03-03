import streamlit as st
import time
import datetime
import json
import os
import bcrypt


# Rate limiting storage
failed_attempts = {}
RATE_LIMIT_MAX_ATTEMPTS = 5
RATE_LIMIT_WINDOW = 300  # 5 minutes
SESSION_TIMEOUT = 1800  # 30 minutes

CREDS = st.secrets["database"]["CREDS"]

# Make sure the directory exists
if not os.path.exists('json-db'):
    os.makedirs('json-db', exist_ok=True)

# Database functions for JSON user storage
def get_json_db():
    """Create or connect to the JSON database for user authentication"""
    if os.path.exists(CREDS):
        with open(CREDS, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                # File exists but is not valid JSON
                return {"users": {}}
    else:
        # Create new database
        db = {"users": {}}
        save_json_db(db)
        return db

def save_json_db(db):
    """Save the database to JSON file"""
    with open(CREDS, 'w') as f:
        json.dump(db, f, indent=2, default=str)

# Password Hashing
def hash_password(password):
    """Securely hash password using bcrypt"""
    if isinstance(password, str):
        password = password.encode('utf-8')
    
    # Use bcrypt for passwords
    hashed = bcrypt.hashpw(password, bcrypt.gensalt())
    return hashed.decode('utf-8')

# Check Login Status
def check_login():
    """Redirects users to the login page if they are not authenticated."""
    if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
        st.warning("Please log in first.")
        st.switch_page("main.py")

def logout():
    """Clears session and redirects to login page."""
    st.session_state.clear()
    st.switch_page("main.py")

def check_rate_limit(username):
    """Check if user has exceeded failed login attempts"""
    current_time = time.time()
    
    # Clear old entries
    for user in list(failed_attempts.keys()):
        if current_time - failed_attempts[user]["timestamp"] > RATE_LIMIT_WINDOW:
            del failed_attempts[user]
    
    # Check if user is rate limited
    if username in failed_attempts:
        attempts = failed_attempts[username]
        if attempts["count"] >= RATE_LIMIT_MAX_ATTEMPTS:
            if current_time - attempts["timestamp"] < RATE_LIMIT_WINDOW:
                return False, f"Too many failed attempts. Try again in {int((attempts['timestamp'] + RATE_LIMIT_WINDOW - current_time) / 60)} minutes."
            else:
                failed_attempts[username] = {"count": 0, "timestamp": current_time}
    
    return True, ""

def record_failed_attempt(username):
    """Record a failed login attempt"""
    current_time = time.time()
    
    if username in failed_attempts:
        failed_attempts[username]["count"] += 1
        failed_attempts[username]["timestamp"] = current_time
    else:
        failed_attempts[username] = {"count": 1, "timestamp": current_time}

def check_session_timeout():
    """Check if the session has timed out due to inactivity"""
    if "last_activity" in st.session_state and st.session_state["authenticated"]:
        current_time = time.time()
        if current_time - st.session_state["last_activity"] > SESSION_TIMEOUT:
            # Session timed out, log the user out
            st.session_state["authenticated"] = False
            st.session_state["username"] = None
            if "token" in st.session_state:
                del st.session_state["token"]
            if "site_id" in st.session_state:
                del st.session_state["site_id"]
            st.warning("Your session has expired due to inactivity. Please log in again.")
            return True
    
    # Update last activity time
    st.session_state["last_activity"] = time.time()
    return False

# User Authentication Functions
def authenticate_user(username, password):
    """Authenticate a user with their username and password"""
    # First, check rate limiting
    can_attempt, message = check_rate_limit(username)
    if not can_attempt:
        st.error(message)
        return False
    
    # Get JSON DB
    json_db = get_json_db()
    
    # Check if user exists
    if username not in json_db["users"]:
        record_failed_attempt(username)
        return False
    
    user_data = json_db["users"][username]
    
    # Check password
    stored_password = user_data["password_hash"]
    if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
        # Update last activity
        json_db["users"][username]["last_activity"] = str(datetime.datetime.now())
        save_json_db(json_db)
        
        # Clear failed attempts on successful login
        if username in failed_attempts:
            del failed_attempts[username]
            
        return True
    else:
        record_failed_attempt(username)
        return False
