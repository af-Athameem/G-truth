import requests
import streamlit as st

# Hide default Streamlit sidebar
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

# Microsoft Graph API Credentials
SHAREPOINT_URL = "https://thameema.sharepoint.com/sites/Test"
CLIENT_ID = "4a9e0273-dbbf-4bf7-b999-accd993df5a4"
CLIENT_SECRET = "WqH8Q~5RFlvA0amtkLbWeFg7azcp6pRoDwe77aB-"
TENANT_ID = "cf907539-ab94-4499-b96f-6bbac1b7cf0c"
GRAPH_API_BASE_URL = "https://graph.microsoft.com/v1.0"
TOKEN_URL = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"

# Step 1: Get OAuth Token
def get_access_token():
    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "https://graph.microsoft.com/.default"
    }
    response = requests.post(TOKEN_URL, data=data)
    token_json = response.json()

    if "access_token" not in token_json:
        st.error(f"❌ Failed to get access token: {token_json}")
        return None

    return token_json["access_token"]



# Step 2: Get SharePoint Site ID
def get_site_id(token):
    headers = {"Authorization": f"Bearer {token}"}
    site_url = f"{GRAPH_API_BASE_URL}/sites/thameema.sharepoint.com:/sites/Test"

    response = requests.get(site_url, headers=headers)
    site_info = response.json()

    if "id" not in site_info:
        st.error(f"❌ Failed to fetch Site ID: {site_info}")
        return None

    return site_info["id"]

# Step 3: Authenticate & Store Credentials in Session
def authentication():
    """Authenticate using Microsoft Graph API"""
    try:
        token = get_access_token()
        if not token:
            return None

        site_id = get_site_id(token)
        if not site_id:
            return None

        st.session_state["authenticated"] = True
        st.session_state["token"] = token
        st.session_state["site_id"] = site_id
        st.success(f"✅ Authentication Successful! Site ID: {site_id}")
        st.switch_page("pages/app.py")
        return True
    except Exception as e:
        st.error(f"❌ Authentication Failed: {str(e)}")
        return False

# Authenticate if user is not logged in
if "authenticated" not in st.session_state:
    authentication()
