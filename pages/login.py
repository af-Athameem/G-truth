import streamlit as st

from utils.sharepoint import get_access_token, get_site_id

st.set_page_config(initial_sidebar_state="collapsed")

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

#Authenticate & Store Credentials in Session
def authentication():
    """Authenticate using Microsoft Graph API"""
    try:
        TENANT_ID = st.secrets["azure"]["TENANT_ID"]
        CLIENT_ID = st.secrets["azure"]["CLIENT_ID"]
        CLIENT_SECRET = st.secrets["azure"]["CLIENT_SECRET"]
        
        token = get_access_token(TENANT_ID, CLIENT_ID, CLIENT_SECRET)
        if not token:
            return None

        site_id = get_site_id(token)
        if not site_id:
            return None

        st.session_state["token"] = token
        st.session_state["site_id"] = site_id
        return True
    except Exception as e:
        st.error(f"Authentication Failed: {str(e)}")
        return False

# Check if user is authenticated in main.py first
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.warning("Please log in first.")
    st.switch_page("main.py") 
else:
    if "token" not in st.session_state or "site_id" not in st.session_state:
        with st.spinner("Authenticating with SharePoint..."):
            if authentication():
                st.switch_page("pages/app.py")
            else:
                st.error("SharePoint Authentication Failed!")
    else:
        st.switch_page("pages/app.py")
