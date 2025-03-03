import boto3
import json
import logging
import os
from botocore.exceptions import ClientError  # Add this import
import streamlit as st

# Load AWS credentials from Streamlit secrets
AWS_ACCESS_KEY = st.secrets["aws"]["AWS_ACCESS_KEY_ID"]
AWS_SECRET_KEY = st.secrets["aws"]["AWS_SECRET_ACCESS_KEY"]
AWS_REGION = st.secrets["aws"]["AWS_REGION"]
BUCKET_NAME = st.secrets["aws"]["S3_BUCKET_NAME"]

# Define the folder in S3
S3_FOLDER = "json-db/"

# Initialize S3 client
s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION
)

# Function to read JSON from S3
def read_json_from_s3(file_name):
    s3_key = f"{S3_FOLDER}{file_name}"  # Store JSON inside "json-db/" folder
    try:
        response = s3_client.get_object(Bucket=BUCKET_NAME, Key=s3_key)
        return json.loads(response["Body"].read().decode("utf-8"))
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            # File doesn't exist yet, return empty data instead of error
            st.warning(f"File {file_name} not found in S3. Creating new file.")
            return {}
        else:
            # Log other errors
            st.error(f"Error reading {s3_key} from S3: {str(e)}")
            return {}
    except Exception as e:
        st.error(f"Error reading {s3_key} from S3: {str(e)}")
        return {}

# Function to write JSON to S3
def write_json_to_s3(file_name, data):
    s3_key = f"{S3_FOLDER}{file_name}"  # Store JSON inside "json-db/" folder
    try:
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=s3_key,
            Body=json.dumps(data, indent=4)
        )
        st.success(f"Successfully updated {s3_key} in S3!")
    except Exception as e:
        st.error(f"Error writing {s3_key} to S3: {str(e)}")

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
        s3_client.upload_file(file_path, bucket, key)
        return True
    except ClientError as e:
        st.error(f"Error uploading to S3: {str(e)}")
        logging.error(e)
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
            return [os.path.basename(obj["Key"]) for obj in response["Contents"]]
        return []
    except ClientError as e:
        st.error(f"Error listing S3 files: {str(e)}")
        logging.error(e)
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
