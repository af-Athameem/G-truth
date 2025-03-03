import boto3
import os
import logging
from botocore.exceptions import ClientError
import streamlit as st

# Load AWS credentials from Streamlit secrets
AWS_ACCESS_KEY = st.secrets["aws"]["AWS_ACCESS_KEY_ID"]
AWS_SECRET_KEY = st.secrets["aws"]["AWS_SECRET_ACCESS_KEY"]
AWS_REGION = st.secrets["aws"]["AWS_REGION"]

bucket_name = "af-ground-truth-benchmark"

session = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION
)

s3_client = session.client("s3")

def upload_file(file_path, target_filename=None, bucket=bucket_name):
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

def list_files(prefix="", bucket=bucket_name):
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

def file_exists(file_name, bucket=bucket_name):
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
