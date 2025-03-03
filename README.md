# Ground Truth Benchmark Application

## Overview
The Ground Truth Benchmark is a Streamlit web application designed to manage a collection of benchmark questions and reference documents. This tool allows users to create, view, and manage benchmark questions along with their reference documents for evaluation purposes.

## Technical Architecture
### Components

- Frontend: Built with Streamlit
- Authentication: Custom authentication using bcrypt for password hashing
- Storage: SharePoint integration via Microsoft Graph API + AWS S3 for file and metadata storage

### File Structure

main.py: Entry point with login functionality
app.py: Main application with question and document management
auth.py: Authentication-related functions
s3.py: AWS S3 interaction functionality
sharepoint.py: SharePoint integration through Microsoft Graph API
form.py: Form handling utilities

### Security Features

Password Security: bcrypt hashing for all user passwords
Rate Limiting: Protection against brute force attacks
Session Management: Automatic session timeout for inactive users
