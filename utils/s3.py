import boto3
import json
import logging
import os
from botocore.exceptions import ClientError
import streamlit as st

# Configure logging
logger = logging.getLogger('s3_utils')

# Load AWS credentials from Streamlit secrets
AWS_ACCESS_KEY = st.secrets["aws"]["AWS_ACCESS_KEY_ID"]
AWS_SECRET_KEY = st.secrets["aws"]["AWS_SECRET_ACCESS_KEY"]
AWS_REGION = st.secrets["aws"]["AWS_REGION"]
BUCKET_NAME = st.secrets["aws"]["S3_BUCKET_NAME"]

# Define the folder in S3
S3_FOLDER = "json-db/"

# Initialize S3 client
try:
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=AWS_REGION
    )
except Exception as e:
    logger.error(f"Failed to initialize S3 client: {str(e)}")
    st.error("Error connecting to S3. Please check your credentials.")

# Function to read JSON from S3
def read_json_from_s3(file_name):
    """
    Read and parse a JSON file from S3.
    
    Args:
        file_name: Name of the JSON file to read from the S3_FOLDER.
        
    Returns:
        dict or list: The parsed JSON data, or empty dict/list if the file doesn't exist or has errors.
    """
    s3_key = f"{S3_FOLDER}{file_name}"  # Store JSON inside "json-db/" folder
    try:
        response = s3_client.get_object(Bucket=BUCKET_NAME, Key=s3_key)
        data = json.loads(response["Body"].read().decode("utf-8"))
        logger.info(f"Successfully read {s3_key} from S3")
        return data
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            # File doesn't exist yet, return empty data instead of error
            logger.warning(f"File {file_name} not found in S3")
            st.warning(f"File {file_name} not found in S3. Creating new file.")
            # Determine appropriate empty value based on filename
            if file_name.endswith("questions.json") or "questions" in file_name:
                return []  # Return empty list for question files
            return {}      # Return empty dict for other files
        else:
            # Log other errors
            logger.error(f"Error reading {s3_key} from S3: {str(e)}")
            st.error(f"Error reading {s3_key} from S3: {str(e)}")
            if file_name.endswith("questions.json") or "questions" in file_name:
                return []
            return {}
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {s3_key}: {str(e)}")
        st.error(f"File {file_name} contains invalid JSON: {str(e)}")
        if file_name.endswith("questions.json") or "questions" in file_name:
            return []
        return {}
    except Exception as e:
        logger.error(f"Error reading {s3_key} from S3: {str(e)}")
        st.error(f"Error reading {s3_key} from S3: {str(e)}")
        if file_name.endswith("questions.json") or "questions" in file_name:
            return []
        return {}

# Function to write JSON to S3
def write_json_to_s3(file_name, data):
    """
    Write JSON data to an S3 file.
    
    Args:
        file_name: Name of the file to write in the S3_FOLDER.
        data: The Python object (dict, list, etc.) to serialize to JSON and store.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    s3_key = f"{S3_FOLDER}{file_name}"  # Store JSON inside "json-db/" folder
    try:
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=s3_key,
            Body=json.dumps(data, indent=4)
        )
        logger.info(f"Successfully updated {s3_key} in S3")
        st.success(f"Successfully updated {file_name}!")
        return True
    except Exception as e:
        logger.error(f"Error writing {s3_key} to S3: {str(e)}")
        st.error(f"Error writing {file_name} to S3: {str(e)}")
        return False

def upload_file(file_path, target_filename=None, bucket=BUCKET_NAME):
    """
    Upload a file to an S3 bucket.
    
    Args:
        file_path: Local path of the file to upload.
        target_filename: Optional custom filename to use in S3.
        bucket: S3 bucket to upload to.
    
    Returns:
        bool: True if file was uploaded successfully, False otherwise.
    """
    key = target_filename if target_filename else os.path.basename(file_path)
    
    try:
        with open(file_path, 'rb') as file_data:
            s3_client.upload_fileobj(file_data, bucket, key)
        logger.info(f"Successfully uploaded {file_path} to {bucket}/{key}")
        return True
    except FileNotFoundError:
        st.error(f"File not found: {file_path}")
        logger.error(f"File not found: {file_path}")
        return False
    except ClientError as e:
        st.error(f"Error uploading to S3: {str(e)}")
        logger.error(f"Error uploading to S3: {str(e)}")
        return False
    except Exception as e:
        st.error(f"Unexpected error uploading file: {str(e)}")
        logger.error(f"Unexpected error uploading file: {str(e)}")
        return False

def list_files(prefix="", bucket=BUCKET_NAME):
    """
    List all file names in an S3 bucket, optionally filtered by a prefix.
    
    Args:
        prefix: Optional prefix to filter by.
        bucket: S3 bucket to list files from.
    
    Returns:
        list: List of file names, or an empty list if an error occurs.
    """
    try:
        response = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
        
        if "Contents" in response:
            files = [os.path.basename(obj["Key"]) for obj in response["Contents"]]
            logger.info(f"Found {len(files)} files with prefix '{prefix}'")
            return files
        
        logger.info(f"No files found with prefix '{prefix}'")
        return []
    except ClientError as e:
        st.error(f"Error listing S3 files: {str(e)}")
        logger.error(f"Error listing S3 files: {str(e)}")
        return []
    except Exception as e:
        st.error(f"Unexpected error listing files: {str(e)}")
        logger.error(f"Unexpected error listing files: {str(e)}")
        return []

def file_exists(file_name, bucket=BUCKET_NAME):
    """
    Check if a file exists in an S3 bucket.
    
    Args:
        file_name: Name of the file to check in S3.
        bucket: S3 bucket to check.
    
    Returns:
        bool: True if the file exists, False otherwise.
    """
    try:
        s3_client.head_object(Bucket=bucket, Key=file_name)
        return True
    except ClientError:
        return False
