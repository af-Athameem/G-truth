import streamlit as st
from utils import authenticate_user, get_db  # Import helper functions

# Hide sidebar
st.markdown(
    """
    <style>
        [data-testid="stSidebarNav"] {
            display: none;
        }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("Login")

# Initialize session state for authentication
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
    st.session_state["username"] = None

# Redirect if already logged in
if st.session_state["authenticated"]:
    st.success(f"Welcome back, {st.session_state['username']}!")
    st.switch_page("pages/app.py")  # Redirect to a protected page


else:
    # Login Form
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if authenticate_user(username, password):  # Check database
            st.session_state["authenticated"] = True
            st.session_state["username"] = username
            st.success(f"🎉 Welcome, {username}!")
            st.rerun() 
        else:
            st.error("❌ Invalid username or password.")

# Logout button (only shows after login)
if st.session_state["authenticated"]:
    st.sidebar.header(f"Welcome, {st.session_state['username']}!")
    if st.sidebar.button("Logout"):
        st.session_state["authenticated"] = False
        st.session_state["username"] = None
        st.rerun() 
