import streamlit as st

def add_document():
    """Add a new document reference to the session state"""
    if 'reference_docs' not in st.session_state:
        st.session_state['reference_docs'] = ["Reference Document 1"]
    else:
        st.session_state['reference_docs'].append(f"Reference Document {len(st.session_state['reference_docs']) + 1}")

def remove_document(index):
    """Remove a document reference at the specified index"""
    if 'reference_docs' in st.session_state and index < len(st.session_state['reference_docs']):
        st.session_state['reference_docs'].pop(index)
        
        # Clean up session state
        keys_to_remove = []
        for key in st.session_state.keys():
            if key.startswith(f'doc_{index}') or key.startswith(f'pages_{index}'):
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            if key in st.session_state:
                del st.session_state[key]
                
        # Reindex remaining documents
        new_docs = {}
        new_pages = {}
        
        for i, doc_idx in enumerate(range(len(st.session_state['reference_docs']))):
            old_doc_key = f'doc_{doc_idx if doc_idx < index else doc_idx + 1}'
            old_pages_key = f'pages_{doc_idx if doc_idx < index else doc_idx + 1}'
            
            if old_doc_key in st.session_state:
                new_docs[f'doc_{i}'] = st.session_state[old_doc_key]
            if old_pages_key in st.session_state:
                new_pages[f'pages_{i}'] = st.session_state[old_pages_key]
        
        # Update session state with reindexed values
        for key, value in new_docs.items():
            st.session_state[key] = value
        for key, value in new_pages.items():
            st.session_state[key] = value

def handle_new_tag():
    """Add a new tag from the input field to the selected tags"""
    if 'new_tag_input' in st.session_state and st.session_state['new_tag_input'].strip() and 'selected_tags' in st.session_state:
        new_tag = st.session_state['new_tag_input'].strip()
        if new_tag not in st.session_state['selected_tags']:
            st.session_state['selected_tags'].append(new_tag)
        st.session_state['new_tag_input'] = ""
