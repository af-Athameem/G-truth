import streamlit as st
import yaml
import hashlib
from sqlalchemy.orm import Session
from models_copy import Document, Tag, TestCase, Users, SessionLocal
import bcrypt

# Create a new database session
def get_db():
    """Returns a new database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Load Configuration (e.g., SharePoint credentials)
def load_config():
    """Loads configuration from config.yaml."""
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)

# Password Hashing
def hash_password(password):
    """Returns SHA-256 hashed password."""
    return hashlib.sha256(password.encode()).hexdigest()

# Check Login Status
def check_login():
    """Redirects users to the login page if they are not authenticated."""
    if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
        st.warning("🔒 Please log in first.")
        st.switch_page("login")

# Logout User
def logout():
    """Clears session and redirects to login page."""
    st.session_state.clear()
    st.switch_page("main.py")

# Fetch All Documents
def get_documents(db: Session):
    """Returns a list of available documents from the database."""
    return db.query(Document).all()

# Fetch All Tags
def get_tags(db: Session):
    """Returns a list of available tags from the database."""
    return [tag.tag_name for tag in db.query(Tag).all()]

# Fetch All Questions
def get_questions(db: Session, search_query=None):
    """
    Returns a list of questions, with optional filtering.
    
    :param db: SQLAlchemy session
    :param search_query: Optional search term
    """
    query = db.query(TestCase)

    if search_query:
        query = query.filter(TestCase.question.ilike(f"%{search_query}%"))

    return query.all()


#Hash password using bcrypt
def hash_password(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

# Verify user credentials
def authenticate_user(username, password):
    db = SessionLocal()
    user = db.query(Users).filter(Users.username == username).first()
    db.close()

    if user and bcrypt.checkpw(password.encode("utf-8"), user.password.encode("utf-8")):
        return True
    return False

# Register a new user (for testing purposes)
def add_user(username, password):
    db = SessionLocal()
    hashed_password = hash_password(password)

    new_user = Users(username=username, password=hashed_password)
    db.add(new_user)
    db.commit()
    db.close()
    return f"User {username} registered successfully!"

