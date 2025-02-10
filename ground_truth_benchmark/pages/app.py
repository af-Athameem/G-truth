import streamlit as st
from sqlalchemy.orm import joinedload
from models_copy import TestCase, Document, Tag, TestCaseHasTag, TestCaseRefersToDocument, SessionLocal
from streamlit_option_menu import option_menu
from utils import logout
import pandas as pd
import requests

st.set_page_config(page_title="Ground Truth Benchmark", layout="wide", initial_sidebar_state="expanded")

GRAPH_API_BASE_URL = "https://graph.microsoft.com/v1.0"

if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.warning("🔒 Please log in first.")
    st.switch_page("pages/login.py")  # Redirect to login

# Streamlit UI
st.markdown("""
    <style>
        .main {
            background-color: #f4f4f9;
        }
        .stButton>button {
            width: 100%;
            margin-bottom: 10px;
            background-color: #4CAF50;
            color: white;
            font-weight: bold;
        }
        .stButton>button:hover {
            background-color: #45a049;
        }
        .css-1aumxhk {
            padding: 2rem;
        }
        .stTable {
            background-color: white;
            border-radius: 10px;
            box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.1);
            font-size: 14px;
        }
        .dataframe th, .dataframe td {
            padding: 10px;
            text-align: left;
        }
        .dataframe thead th {
            background-color: #4CAF50;
            color: white;
        }
        .dataframe tbody tr:nth-child(odd) {
            background-color: #f9f9f9;
        }
        .dataframe tbody tr:hover {
            background-color: #f1f1f1;
        }
        h1, h2, h3, h4 {
            color: #333;
        }
        .remove-btn>button {
            background-color: #FF4B4B;
            color: white;
            font-weight: bold;
        }
        .remove-btn>button:hover {
            background-color: #D43F3F;
        }
        [data-testid="stSidebarNav"] {
            display: none;
        }
    </style>
""", unsafe_allow_html=True)

# st.title("GROUND TRUTH BENCHMARK")

# Sidebar for navigation
with st.sidebar:
    if st.button("Add New Question"):
        st.session_state['option'] = "Add New Question"
    if st.button("View Questions"):
        st.session_state['option'] = "View Questions"
    if st.button("View and Upload Documents"):
        st.session_state['option'] = "View and Upload Documents"
    if st.sidebar.button("Logout"):
        logout()
           
option = st.session_state.get('option', "Add New Question")

# Fetch token and site ID
TOKEN = st.session_state.get("token")
SITE_ID = st.session_state.get("site_id")

if not TOKEN or not SITE_ID:
    st.error("🔑 Authentication required. Please log in.")
else:
    headers = {"Authorization": f"Bearer {TOKEN}"}

    # Fetch document libraries
    def get_document_libraries():
        """Fetch SharePoint document libraries"""
        url = f"https://graph.microsoft.com/v1.0/sites/{SITE_ID}/drives"
        response = requests.get(url, headers=headers)
        libraries = response.json()

        if "value" not in libraries:
            st.error(f"❌ Failed to fetch document libraries: {libraries}")
            return None

        return libraries["value"]

    # Fetch files in a selected document library
    def get_files_in_library(drive_id):
        """Fetch files from the selected document library"""
        url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root/children"
        response = requests.get(url, headers=headers)
        files = response.json()

        if "value" not in files:
            st.error(f"❌ Failed to fetch files: {files}")
            return None

        return files["value"]

    # Upload a file to the selected document library
    def upload_file(drive_id, file_name, file_content):
        """Upload a file to SharePoint"""
        upload_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:/{file_name}:/content"
        upload_headers = {
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/octet-stream"
        }

        response = requests.put(upload_url, headers=upload_headers, data=file_content)

        if response.status_code == 201:
            st.success(f"✅ File '{file_name}' uploaded successfully!")
        else:
            st.error(f"❌ File upload failed: {response.json()}")


def get_document_libraries():
    """Fetch SharePoint document libraries"""
    token = st.session_state.get("token")
    site_id = st.session_state.get("site_id")

    if not token or not site_id:
        st.error("🔑 Authentication required. Please log in.")
        return None

    headers = {"Authorization": f"Bearer {token}"}
    url = f"{GRAPH_API_BASE_URL}/sites/{site_id}/drives"
    response = requests.get(url, headers=headers)
    libraries = response.json()

    if "value" not in libraries:
        st.error(f"❌ Failed to fetch document libraries: {libraries}")
        return None

    return libraries["value"]

def get_files_in_library(drive_id):
    """Fetch files in a selected document library"""
    token = st.session_state.get("token")

    if not token:
        st.error("🔑 Authentication required. Please log in.")
        return None

    headers = {"Authorization": f"Bearer {token}"}
    url = f"{GRAPH_API_BASE_URL}/drives/{drive_id}/root/children"
    response = requests.get(url, headers=headers)
    files = response.json()

    if "value" not in files:
        st.error(f"❌ Failed to fetch files: {files}")
        return None

    return files["value"]

def upload_file(drive_id, file_name, file_content):
    """Upload a file to a selected document library"""
    token = st.session_state.get("token")

    if not token:
        st.error("🔑 Authentication required. Please log in.")
        return None

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/octet-stream"
    }

    url = f"{GRAPH_API_BASE_URL}/drives/{drive_id}/root:/{file_name}:/content"
    response = requests.put(url, headers=headers, data=file_content)

    if response.status_code == 201:
        st.success(f"✅ File '{file_name}' uploaded successfully!")
    else:
        st.error(f"❌ File upload failed: {response.json()}")

# Fetch questions from the database
def get_questions():
    db = SessionLocal()
    try:
        questions = db.query(TestCase).options(
            joinedload(TestCase.documents),
            joinedload(TestCase.tags)
        ).all()

        return questions
    except Exception as e:
        st.error(f"⚠️ Failed to fetch questions: {str(e)}")
        return []
    finally:
        db.close()

def get_documents():
    db = SessionLocal()
    documents = db.query(Document).all()
    db.close()
    return documents

if option == "Add New Question":
    st.header("Add a New Question")

    # Input for question details
    question = st.text_area("Question", help="Enter the question text", key="question_input")
    ideal_answer = st.text_area("Ideal Answer", help="Enter the expected answer", key="ideal_answer_input")
    agent_name = st.text_input("Agent Name", help="Enter the agent name", key="agent_name_input")

    # Fetch document libraries from SharePoint
    libraries = get_document_libraries()

    if not libraries:
        st.error("⚠️ No document libraries found in SharePoint. Check your permissions.")
    else:
        # Select a document library
        drive_options = {lib["id"]: lib["name"] for lib in libraries}
        drive_id = st.selectbox("Select Document Library", options=drive_options.keys(), format_func=lambda x: drive_options[x])

        # Fetch files from the selected SharePoint library
        sharepoint_files = []
        if drive_id:
            files = get_files_in_library(drive_id)
            if files:
                sharepoint_files = [file["name"] for file in files]

    # Reference Documents Dropdown (Using SharePoint Files Instead of DB)
    if not sharepoint_files:
        st.warning("⚠️ No files found in the selected SharePoint document library.")
    
    if 'reference_docs' not in st.session_state:
        st.session_state['reference_docs'] = ["Reference Document 1"]

    to_remove = []

    for idx, doc in enumerate(st.session_state['reference_docs']):
        cols = st.columns([4, 1])

        with cols[0]:
            selected_doc = st.selectbox(
                f"{doc} (Select from SharePoint)",
                options=[""] + sharepoint_files,
                key=f'doc_{idx}'
            )

            st.text_input(f"Page Numbers for {doc} (comma-separated)", key=f'pages_{idx}')

        with cols[1]:
            if st.button("-", key=f'remove_{idx}', help="Remove this document"):
                to_remove.append(idx)

    # Remove documents marked for deletion
    for idx in sorted(to_remove, reverse=True):
        st.session_state['reference_docs'].pop(idx)
        for key_prefix in ['doc_', 'pages_']:
            if f'{key_prefix}{idx}' in st.session_state:
                del st.session_state[f'{key_prefix}{idx}']

    # Add new document field
    if st.button("+ ADD DOCUMENT", key="add_doc_btn"):
        st.session_state['reference_docs'].append(f"Reference Document {len(st.session_state['reference_docs']) + 1}")

    # Select Tags
    db = SessionLocal()
    existing_tags = [tag.tag_name for tag in db.query(Tag).all()]
    selected_tags = st.multiselect("Select Tags", options=existing_tags)

    # Allow user to create a new tag
    new_tag = st.text_input(" Add New Tag (Optional)", help="Enter a new tag name if needed")
    if new_tag and new_tag not in selected_tags:
        selected_tags.append(new_tag)

    db.close()

    # Submit button
    if st.button("Submit", key="submit_btn"):
        if not question.strip():
            st.error("⚠️ Question is required.")
        elif not ideal_answer.strip():
            st.error("⚠️ Ideal Answer is required.")
        elif not agent_name.strip():
            st.error("⚠️ Agent Name is required.")
        else:
            # Save question in the database
            db = SessionLocal()
            try:
                new_question = TestCase(
                    question=question,
                    ideal_answer=ideal_answer,
                    agent_name=agent_name
                )
                db.add(new_question)
                db.flush()

                # Check and insert document if not exists before referencing it
                for idx, _ in enumerate(st.session_state['reference_docs']):
                    file_name = st.session_state.get(f'doc_{idx}')
                    pages = st.session_state.get(f'pages_{idx}', "")

                    if file_name:
                         # **Ensure document exists in the database before referencing**
                        document = db.query(Document).filter_by(name=file_name).first()  # <-- Adjust column name if needed
                        if not document:
                            document = Document(name=file_name)  # <-- Adjust column name if needed
                            db.add(document)
                            db.flush()  # Ensure it is saved before referencing

                        db.add(TestCaseRefersToDocument(
                            test_case_id=new_question.test_case_id,
                            document_name=document.name,  # <-- Adjust column reference if needed
                            pages=pages
                        ))

                # Attach tags to the question
                for tag_name in selected_tags:
                    tag = db.query(Tag).filter_by(tag_name=tag_name).first()
                    if not tag:
                        tag = Tag(tag_name=tag_name)
                        db.add(tag)
                        db.flush()

                    db.add(TestCaseHasTag(
                        test_case_id=new_question.test_case_id,
                        tag_name=tag.tag_name
                    ))

                db.commit()
                st.success("✅ Question added successfully!")

                # Clear session state after submission
                st.session_state['reference_docs'] = ["Reference Document 1"]
                for key in list(st.session_state.keys()):
                    if key.startswith(('doc_', 'pages_', 'question_input', 'ideal_answer_input', 'agent_name_input')):
                        del st.session_state[key]

            except Exception as e:
                db.rollback()
                st.error(f"⚠️ An error occurred: {str(e)}")

            finally:
                db.close()

# View Questions
elif option == "View Questions":
    st.header("Ground Truth Library")

    questions = get_questions()
    
    if questions:
        data = {
            "Question": [q.question for q in questions],
            "Ideal Answer": [q.ideal_answer for q in questions],
            "Reference Documents": [
                "\n" .join([
                    f"- {doc.document_name} (Pages {doc.pages})"
                    for doc in q.documents
                ]) for q in questions
            ],
            "Agent Name": [q.agent_name for q in questions],
            "Tags": [", ".join([tag.tag_name for tag in q.tags]) for q in questions],
            "Created On": [q.created_on.strftime("%Y-%m-%d") for q in questions]
        }
        df = pd.DataFrame(data)
        st.dataframe(df.style.set_table_styles([
            {'selector': 'thead th', 'props': [('background-color', '#4CAF50'), ('color', 'white')]},
            {'selector': 'tbody tr:nth-child(odd)', 'props': [('background-color', '#f9f9f9')]},
            {'selector': 'tbody tr:hover', 'props': [('background-color', '#f1f1f1')]},
        ]), width=3000, height=500)
    else:
        st.warning("No questions found.")
        

# View and Upload Documents Page
elif option == "View and Upload Documents":
    st.header("SharePoint Document Management")
        # Navigation menu
    selected_page = option_menu(
            menu_title="",
            options=["📂 File List", "📤 Upload New File"],
            default_index=0,
            orientation="horizontal"
        )

        # Fetch document libraries
    libraries = get_document_libraries()

    if libraries:
            drive_options = {lib["id"]: lib["name"] for lib in libraries}
            drive_id = st.selectbox(" Select Document Library", options=drive_options.keys(), format_func=lambda x: drive_options[x])

            if drive_id:
                if selected_page == "📂 File List":
                    # File List Page
                    st.write(" Files in Selected Library")
                    files = get_files_in_library(drive_id)

                    if files:
                        file_data = [{"📄 File Name": file["name"], "📅 Last Modified": file["lastModifiedDateTime"]} for file in files]
                        df = pd.DataFrame(file_data)
                        st.table(df)
                    else:
                        st.warning("⚠️ No files found in the selected library.")

                elif selected_page == "📤 Upload New File":
                    # Upload File Page
                    uploaded_file = st.file_uploader("📂 Choose a file to upload", type=None)

                    if uploaded_file:
                        st.write(f"✅ **File Ready to Upload:** `{uploaded_file.name}` ({len(uploaded_file.read())} bytes)")

                        if st.button("📤 Upload File"):
                            upload_file(drive_id, uploaded_file.name, uploaded_file.read())

    else:
        st.error("⚠️ No document libraries found in SharePoint. Please check your permissions.")

