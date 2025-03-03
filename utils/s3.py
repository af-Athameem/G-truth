import boto3
import json
import os
from botocore.exceptions import ClientError
import streamlit as st

# Load AWS credentials 
AWS_ACCESS_KEY = st.secrets["aws"]["AWS_ACCESS_KEY_ID"]
AWS_SECRET_KEY = st.secrets["aws"]["AWS_SECRET_ACCESS_KEY"]
AWS_REGION = st.secrets["aws"]["AWS_REGION"]
BUCKET_NAME = st.secrets["aws"]["S3_BUCKET_NAME"]

S3_FOLDER = "json-db/"

# Initialize S3 client
try:
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=AWS_REGION
    )
except Exception:
    st.error("Error connecting to S3. Please check your credentials.")

def read_json_from_s3(file_name):
    """Read and parse a JSON file from S3."""
    s3_key = f"{S3_FOLDER}{file_name}"
    try:
        response = s3_client.get_object(Bucket=BUCKET_NAME, Key=s3_key)
        data = json.loads(response["Body"].read().decode("utf-8"))
        return data
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            # File doesn't exist yet, return empty data
            if file_name.endswith("questions.json") or "questions" in file_name:
                return []
            return {}
        else:
            if file_name.endswith("questions.json") or "questions" in file_name:
                return []
            return {}
    except Exception:
        if file_name.endswith("questions.json") or "questions" in file_name:
            return []
        return {}

def write_json_to_s3(file_name, data):
    """Write JSON data to an S3 file."""
    s3_key = f"{S3_FOLDER}{file_name}"
    try:
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=s3_key,
            Body=json.dumps(data, indent=4)
        )
        st.success(f"Successfully updated {file_name}!")
        return True
    except Exception:
        st.error(f"Error writing {file_name} to S3")
        return False

def upload_file(file_path, target_filename=None, bucket=BUCKET_NAME):
    """Upload a file to an S3 bucket."""
    key = target_filename if target_filename else os.path.basename(file_path)
    
    try:
        with open(file_path, 'rb') as file_data:
            s3_client.upload_fileobj(file_data, bucket, key)
        return True
    except FileNotFoundError:
        return False
    except Exception:
        return False

def list_files(prefix="", bucket=BUCKET_NAME):
    """List all file names in an S3 bucket, excluding json-db/ folder files."""
    try:
        response = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
        
        if "Contents" in response:
            files = []
            for obj in response["Contents"]:
                key = obj["Key"]
                # Skip files in the json-db/ folder
                if not key.startswith(S3_FOLDER):
                    files.append(os.path.basename(key))
            return files
        return []
    except Exception:
        return []

def file_exists(file_name, bucket=BUCKET_NAME):
    """Check if a file exists in an S3 bucket."""
    try:
        s3_client.head_object(Bucket=bucket, Key=file_name)
        return True
    except ClientError:
        return False
