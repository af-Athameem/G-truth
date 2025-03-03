# Ground Truth Benchmark Application

## Overview
The Ground Truth Benchmark is a Streamlit web application designed to manage a collection of benchmark questions and reference documents. This tool allows users to create, view, and manage benchmark questions along with their reference documents for evaluation purposes.

## Technical Architecture
### Components

- Frontend: Built with Streamlit
- Authentication: Custom authentication using bcrypt for password hashing
- Storage: SharePoint integration via Microsoft Graph API + AWS S3 for file and metadata storage

### File Structure
```
GroundTruthBenchmark/
│── main.py                    # Entry point with login functionality
│── pages/                     # Streamlit pages directory
│   │── app.py                 # Main application with question & document management
│   │── login.py               # Microsoft Graph Authentication
│   │── dashboard.py           # Dashboard for benchmark questions & docs
│   │── settings.py            # User settings & profile management
│
│── utils/                     # Utility functions & reusable components
│   │── auth.py                # Authentication-related functions
│   │── s3.py                  # AWS S3 interaction functionality
│   │── sharepoint.py          # SharePoint integration via Microsoft Graph API
│   │── form.py                # Form handling utilities
│   │── session.py             # Session management & timeout handling
│   │── rate_limiter.py        # Rate limiting logic for security
│
│── requirements.txt           # Python dependencies
│
│── README.md
```


