import streamlit as st
import time
import datetime
import bcrypt
import logging
from utils.s3 import read_json_from_s3, write_json_to_s3

# Configure logging
logger = logging.getLogger('auth')

# Rate limiting storage
failed_attempts = {}
RATE_LIMIT_MAX_ATTEMPTS = 5
RATE_LIMIT_WINDOW = 300  # 5 minutes
SESSION_TIMEOUT = 1800  # 30 minutes

# Load user database from S3
def get_json_db():
    """Retrieve the user database from S3."""
    try:
        data = read_json_from_s3("users.json")
        if not data:
            # Initialize with empty users structure if no data found
            return {"users": {}}
        if "users" not in data:
            # Ensure the expected structure is present
            data = {"users": data} if isinstance(data, dict) else {"users": {}}
        return data
    except Exception as e:
        logger.error(f"Error retrieving user database: {str(e)}")
        return {"users": {}}

# Rate Limiting Functions
def check_rate_limit(username):
    """Check if the user has exceeded the allowed login attempts."""
    current_time = time.time()
    
    # Clear old failed attempts
    for user in list(failed_attempts.keys()):
        if current_time - failed_attempts[user]["timestamp"] > RATE_LIMIT_WINDOW:
            del failed_attempts[user]
    
    # Check if the user is rate limited
    if username in failed_attempts:
        attempts = failed_attempts[username]
        if attempts["count"] >= RATE_LIMIT_MAX_ATTEMPTS:
            if current_time - attempts["timestamp"] < RATE_LIMIT_WINDOW:
                minutes_left = int((attempts['timestamp'] + RATE_LIMIT_WINDOW - current_time) / 60)
                return False, f"Too many failed attempts. Try again in {minutes_left} minutes."
            else:
                failed_attempts[username] = {"count": 0, "timestamp": current_time}
    
    return True, ""

def record_failed_attempt(username):
    """Record a failed login attempt."""
    current_time = time.time()
    if username in failed_attempts:
        failed_attempts[username]["count"] += 1
        failed_attempts[username]["timestamp"] = current_time
    else:
        failed_attempts[username] = {"count": 1, "timestamp": current_time}

# Session Timeout Check
def check_session_timeout():
    """Log the user out if the session has been inactive for too long."""
    if "last_activity" in st.session_state and st.session_state.get("authenticated", False):
        current_time = time.time()
        if current_time - st.session_state["last_activity"] > SESSION_TIMEOUT:
            st.session_state["authenticated"] = False
            st.session_state["username"] = None
            st.warning("Your session has expired due to inactivity. Please log in again.")
            return True
    
    st.session_state["last_activity"] = time.time()
    return False

# Check Login Status
def check_login():
    """Redirects users to the login page if they are not authenticated."""
    if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
        st.warning("Please log in first.")
        st.switch_page("main.py")

# User Authentication Function
def authenticate_user(username, password):
    """Authenticate a user by checking stored credentials in S3."""
    if not username or not password:
        st.error("Username and password are required.")
        return False
        
    can_attempt, message = check_rate_limit(username)
    if not can_attempt:
        st.error(message)
        return False
    
    try:
        json_db = get_json_db()
        
        # Check if user exists
        if username not in json_db["users"]:
            record_failed_attempt(username)
            return False
        
        user_data = json_db["users"][username]
        
        if "password_hash" not in user_data:
            logger.error(f"User {username} exists but has no password hash")
            record_failed_attempt(username)
            return False
            
        stored_password = user_data["password_hash"]
        
        # Verify password
        try:
            if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
                # Update last login time
                st.session_state["authenticated"] = True
                st.session_state["username"] = username
                
                return True
            else:
                record_failed_attempt(username)
                return False
        except Exception as e:
            logger.error(f"Password verification error for user {username}: {str(e)}")
            record_failed_attempt(username)
            return False
            
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        return False

# Logout Function
def logout():
    """Logs the user out and clears session data."""
    st.session_state.clear()
    st.switch_page("main.py")
