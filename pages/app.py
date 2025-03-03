import streamlit as st
import pandas as pd
import os
import tempfile

from streamlit_option_menu import option_menu
from utils import (
    logout, get_document_libraries, get_files_in_eval_benchmark, get_file_item,
    upload_to_eval_benchmark, get_all_tags_from_list, 
    add_document, remove_document, handle_new_tag
)
from utils.s3 import upload_file, list_files, read_json_from_s3, write_json_to_s3

# Page configuration
st.set_page_config(page_title="Ground Truth Benchmark", layout="wide", initial_sidebar_state="expanded")

# Load questions from S3
try:
    QUESTIONS = read_json_from_s3("submitted_questions.json")
    if QUESTIONS is None or not isinstance(QUESTIONS, list):
        QUESTIONS = []
        write_json_to_s3("submitted_questions.json", [])
except Exception:
    QUESTIONS = []
    write_json_to_s3("submitted_questions.json", [])

# Authentication check
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.warning("Please log in first.")
    st.switch_page("pages/login.py")

# CSS
st.markdown("""
    <style>
        .main { background-color: #f4f4f9; }
        .stButton>button {
            width: 100%;
            margin-bottom: 10px;
            background-color: #4CAF50;
            color: white;
        }
        .stButton>button:hover { background-color: #45a049; }
        .dataframe th, .dataframe td { padding: 10px; text-align: left; }
        .dataframe thead th { background-color: #4CAF50; color: white; }
        .dataframe tbody tr:nth-child(odd) { background-color: #f9f9f9; }
        .dataframe tbody tr:hover { background-color: #f1f1f1; }
        h1, h2, h3, h4 { color: #333; }
        .remove-btn>button { background-color: #FF4B4B; color: white; font-weight: bold; }
        .remove-btn>button:hover { background-color: #D43F3F; }
        [data-testid="stSidebarNav"] { display: none; }
    </style>
""", unsafe_allow_html=True)

# Need to moves these to functions 
def get_files_from_storage():
    """Get files from both SharePoint and S3 storage."""
    files = []
    
    # Get SharePoint files
    TOKEN = st.session_state.get("token")
    SITE_ID = st.session_state.get("site_id")
    if TOKEN and SITE_ID:
        drive_id = st.session_state.get("document_drive_id")
        if drive_id:
            sharepoint_files = get_files_in_eval_benchmark(TOKEN, drive_id)
            if sharepoint_files:
                for file in sharepoint_files:
                    if "folder" not in file:
                        files.append({
                            "name": file["name"],
                            "source": "SharePoint",
                            "lastModified": file.get("lastModifiedDateTime", ""),
                            "createdBy": file.get("createdBy", {}).get("user", {}).get("displayName", "Unknown")
                        })

    # Get S3 files
    s3_files = list_files()
    for file_name in s3_files:
        files.append({
            "name": file_name,
            "source": "S3",
            "lastModified": pd.Timestamp.now().strftime("%Y-%m-%d"),
            "createdBy": "Unknown"
        })

    return files

def upload_to_storage(file_name, file_bytes):
    results = []
    TOKEN = st.session_state.get("token")
    SITE_ID = st.session_state.get("site_id")
    
    if TOKEN and SITE_ID:
        try:
            sharepoint_result = upload_to_eval_benchmark(TOKEN, SITE_ID, file_name, file_bytes)
            results.append(("SharePoint", sharepoint_result))
        except Exception:
            results.append(("SharePoint", False))

    try:
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file_path = temp_file.name
            temp_file.write(file_bytes)
        
        s3_result = upload_file(temp_file_path, target_filename=file_name)  
        results.append(("S3", s3_result))
    except Exception:
        results.append(("S3", False))
    finally:
        try:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        except Exception:
            pass

    return results

def get_unique_filename(original_filename):
    """Generate unique filename to avoid overwriting existing files."""
    existing_filenames = {file["name"] for file in get_files_from_storage()}
    
    if original_filename not in existing_filenames:
        return original_filename
        
    name_parts = original_filename.rsplit('.', 1)
    base_name = name_parts[0]
    extension = f".{name_parts[1]}" if len(name_parts) > 1 else ""

    counter = 1
    new_filename = original_filename
    
    while new_filename in existing_filenames:
        new_filename = f"{base_name} copy({counter}){extension}"
        counter += 1
        
    return new_filename

# Sidebar navigation
with st.sidebar:
    if st.button("Add New Question"):
        st.session_state['option'] = "Add New Question"
    if st.button("View Questions"):
        st.session_state['option'] = "View Questions"
    if st.button("View and Upload Documents"):
        st.session_state['option'] = "View and Upload Documents"    
    if st.sidebar.button("Logout"):
        logout()
           
# Set default page           
option = st.session_state.get('option', "Add New Question")

# Get authentication tokens from session
TOKEN = st.session_state.get("token")
SITE_ID = st.session_state.get("site_id")

if not TOKEN or not SITE_ID:
    st.error("Authentication required. Please log in.")
else:
    # ADD NEW QUESTION PAGE
    if option == "Add New Question":
        st.header("Add a New Question")

        # Reset form after submission
        if st.session_state.get('form_submitted', False):
            st.session_state['question_input'] = ""
            st.session_state['ideal_answer_input'] = ""
            st.session_state['agent_name_input'] = ""
            st.session_state['reference_docs'] = ["Reference Document 1"]
            st.success("Question added successfully!")
            
            for key in list(st.session_state.keys()):
                if key.startswith(('doc_', 'pages_')):
                    st.session_state[key] = ""
            
            st.session_state['selected_tags'] = []
            st.session_state['new_tag_input'] = ""
            st.session_state['form_submitted'] = False

        # Input fields
        question = st.text_area("Question", help="Enter the question text", key="question_input")
        ideal_answer = st.text_area("Ideal Answer", help="Enter the expected answer", key="ideal_answer_input")
        agent_name = st.text_input("Agent Name", help="Enter the agent name", key="agent_name_input")

        # Document selection section
        libraries = get_document_libraries(TOKEN, SITE_ID)
        drive_id = None
        for lib in libraries:
            if "document" in lib["name"].lower():
                drive_id = lib["id"]
                st.session_state["document_drive_id"] = drive_id
                break
                
        # Get files
        if 'all_files' not in st.session_state or st.session_state.get('refresh_files', False):
            all_files = get_files_from_storage()
            st.session_state['all_files'] = all_files
            st.session_state['refresh_files'] = False
        
        all_files = st.session_state['all_files']
        # Ensure unique filenames in dropdown regardless of storage source
        available_files = list(set(file["name"] for file in all_files))

        if not available_files:
            st.info("No files found. Upload files in the 'View and Upload Documents' section.")
        
        # Reference documents section
        if 'reference_docs' not in st.session_state:
            st.session_state['reference_docs'] = ["Reference Document 1"]
        
        # Document container
        docs_container = st.container()
        with docs_container:
            for index, doc in enumerate(st.session_state['reference_docs']):
                cols = st.columns([4, 1])
                
                with cols[0]:
                    doc_key = f'doc_{index}'
                    if doc_key not in st.session_state:
                        st.session_state[doc_key] = ""
                        
                    st.selectbox(
                        f"{doc}",
                        options=[""] + available_files,
                        key=doc_key,
                        help="If you do not see your document, please upload one"
                    )
                    
                    pages_key = f'pages_{index}'
                    if pages_key not in st.session_state:
                        st.session_state[pages_key] = ""
                        
                    st.text_input(f"Page Numbers for {doc}", 
                                key=pages_key,
                                help="Comma-separated (e.g. 1,2,3)"
                                )
                
                with cols[1]:
                    if st.button("-", key=f'remove_{index}', help="Remove this document", on_click=remove_document, args=(index,)):
                        pass
        
        # Add document button
        st.button("+ ADD DOCUMENT", key="add_doc_btn", on_click=add_document)

        # Tags section
        existing_tags = get_all_tags_from_list(QUESTIONS)

        if 'selected_tags' not in st.session_state:
            st.session_state['selected_tags'] = []

        all_tags = list(existing_tags)
        for tag in st.session_state['selected_tags']:
            if tag not in all_tags:
                all_tags.append(tag)

        selected_tags = st.multiselect(
            "Select Tags", 
            options=all_tags, 
            default=st.session_state['selected_tags'],
            key="tag_multiselect"
        )
        st.session_state['selected_tags'] = selected_tags

        st.text_input(
            "Add New Tag (Optional)", 
            value="",
            help="Enter a new tag name and press Enter",
            key="new_tag_input",
            on_change=handle_new_tag
        )

        # Submit button
        if st.button("SUBMIT", key="submit_btn"):
            if not question.strip():
                st.error("Question is required.")
            elif not ideal_answer.strip():
                st.error("Ideal Answer is required.")
            elif not agent_name.strip():
                st.error("Agent Name is required.")
            else:
                reference_documents = []
                for idx, _ in enumerate(st.session_state['reference_docs']):
                    file_name = st.session_state.get(f'doc_{idx}')
                    pages = st.session_state.get(f'pages_{idx}', "")
                    if file_name:
                        # Find all sources where this file exists
                        file_sources = []
                        for file in st.session_state['all_files']:
                            if file["name"] == file_name:
                                file_sources.append(file["source"])
                                
                        file_source = ", ".join(sorted(set(file_sources))) if file_sources else "Unknown"
                                
                        reference_documents.append({
                            "name": file_name,
                            "pages": pages,
                            "source": file_source
                        })

                question_tags = st.session_state['selected_tags'].copy()
                submitted_by = st.session_state.get("username", "Unknown")
                
                # Create new question entry
                new_entry = {
                    "Question": question,
                    "Ideal Answer": ideal_answer,
                    "Reference Documents": reference_documents,
                    "Agent Name": agent_name,
                    "Tags": question_tags,
                    "Created On": pd.Timestamp.now().strftime("%Y-%m-%d"),
                    "Submitted By": submitted_by 
                }

                # Add to database
                QUESTIONS.append(new_entry)
                write_json_to_s3("submitted_questions.json", QUESTIONS)
                
                st.session_state['form_submitted'] = True
                st.rerun()

    # VIEW QUESTIONS PAGE
    elif option == "View Questions":
        st.header("Ground Truth Library")

        questions = QUESTIONS
        
        if questions:
            data = {
                "Question": [q.get("Question", "") for q in questions],
                "Ideal Answer": [q.get("Ideal Answer", "") for q in questions],
                "Reference Documents": [
                    "\n".join([
                        f"- {doc.get('name', '')} (Pages {doc.get('pages', '')}) [{doc.get('source', 'Unknown')}]" 
                        for doc in q.get("Reference Documents", [])
                    ]) for q in questions
                ],
                "Agent Name": [q.get("Agent Name", "") for q in questions],
                "Tags": [", ".join(q.get("Tags", [])) for q in questions],
                "Created On": [q.get("Created On", "") for q in questions],
                "Submitted By": [q.get("Submitted By", "Unknown") for q in questions]
            }
            df = pd.DataFrame(data)
            st.dataframe(df, width=3000, height=500)
        else:
            st.info("No questions found. Add new questions in the 'Add New Question' section.")
            
    # DOCUMENT MANAGEMENT PAGE
    elif option == "View and Upload Documents":
        st.header("Document Management")

        selected_page = option_menu(
            menu_title="",
            options=["File List", "Upload New File"],
            default_index=0,
            orientation="horizontal"
        )

        # FILE LIST PAGE
        if selected_page == "File List":
            all_files = get_files_from_storage()

            if all_files:
                unique_files = {}

                for file in all_files:
                    filename = file["name"]
                    modified_date = file.get("lastModified", "").split('T')[0] if "T" in file.get("lastModified", "") else file.get("lastModified", "")
                    created_by = file.get("createdBy", "Unknown")
                    source = file.get("source", "Unknown")

                    # If file already exists, merge storage sources and prioritize SharePoint metadata
                    if filename in unique_files:
                        if file["source"] == "SharePoint":
                            unique_files[filename].update({
                                "Last Modified": modified_date,
                                "Created By": created_by
                            })
                        # Add storage source to the list of sources
                        if source not in unique_files[filename]["Storage"]:
                            unique_files[filename]["Storage"] += f", {source}"
                    else:
                        unique_files[filename] = {
                            "File Name": filename,
                            "Last Modified": modified_date,
                            "Created By": created_by,
                            "Storage": source
                        }

                file_data = list(unique_files.values())
                if file_data:
                    df = pd.DataFrame(file_data)
                    st.table(df)
                else:
                    st.info("No files found. Use the 'Upload New File' tab to add files.")
            else:
                st.info("No files found. Use the 'Upload New File' tab to add files.")

       # UPLOAD FILE PAGE
        elif selected_page == "Upload New File":
            uploaded_files = st.file_uploader("Choose files to upload", type=None, accept_multiple_files=True)

            if uploaded_files:
                files_to_upload = []
                
                # Preview files and show renamed info
                st.subheader("Files Ready to Upload:")
                for uploaded_file in uploaded_files:
                    file_bytes = uploaded_file.getvalue()
                    original_filename = uploaded_file.name
                    upload_filename = get_unique_filename(original_filename)
                    
                    file_info = f"**{upload_filename}**"
                    if upload_filename != original_filename:
                        file_info += f" (renamed from {original_filename})"
                    
                    st.write(file_info)
                    files_to_upload.append((upload_filename, file_bytes))

                if st.button("Upload All Files"):
                    with st.spinner(f"Uploading {len(files_to_upload)} files..."):
                        successful_files = []
                        failed_files = []
                        
                        for filename, file_bytes in files_to_upload:
                            upload_results = upload_to_storage(filename, file_bytes)
                            successful_uploads = [storage for storage, result in upload_results if result]
                            failed_uploads = [storage for storage, result in upload_results if not result]
                            
                            if successful_uploads:
                                successful_files.append((filename, successful_uploads))
                            if failed_uploads:
                                failed_files.append((filename, failed_uploads))
                    
                    # Display upload summary
                    if len(successful_files) == len(files_to_upload):
                        st.success(f"All {len(successful_files)} files uploaded successfully.")
                    elif successful_files:
                        st.warning(f"{len(successful_files)} of {len(files_to_upload)} files uploaded successfully.")
                        
                        # Show successful uploads
                        with st.expander("Successful uploads"):
                            for filename, storages in successful_files:
                                st.write(f"{filename} - Uploaded to: {', '.join(storages)}")
                        
                        # Show failed uploads
                        if failed_files:
                            with st.expander("Failed uploads"):
                                for filename, storages in failed_files:
                                    st.write(f"{filename} - Failed to upload to: {', '.join(storages)}")
                    else:
                        st.error("All uploads failed. Please check your connection and try again.")
                    
                    st.session_state['refresh_files'] = True
