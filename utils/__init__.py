# Authentication functions
from utils.auth import (
    authenticate_user,
    check_session_timeout,
    logout,
    check_login,
)

# SharePoint functions
from utils.sharepoint import (
    get_document_libraries,
    get_files_in_eval_benchmark,
    get_file_item,
    upload_to_eval_benchmark,
    get_access_token,
    get_site_id
)

# Database functions 
from utils.sharepoint import (
    load_json_db_file,
    save_json_db_file,
    get_all_tags,
    get_all_documents,
    add_question
)

# UI helper functions
from utils.form import (
    add_document,
    remove_document,
    handle_new_tag
)

from utils.s3 import (
    upload_file, 
    list_files, 
    file_exists
)
# Define which symbols should be exported with "from utils import *"
__all__ = [
    # Auth functions
    'authenticate_user', 
    'check_session_timeout',
    'logout', 
    'check_login',
    
    # SharePoint functions
    'get_document_libraries',
    'get_files_in_eval_benchmark',
    'get_file_item',
    'upload_to_eval_benchmark',
    'get_access_token',
    'get_site_id',
    
    # Database functions
    'load_json_db_file',
    'save_json_db_file',
    'get_all_tags',
    'get_all_documents',
    'add_question',
    
    # UI helper functions
    'add_document',
    'remove_document',
    'handle_new_tag'
    
    #s3
    'upload_file', 
    'list_files', 
    'file_exists'
]