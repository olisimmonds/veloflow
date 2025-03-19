import streamlit as st
from PyPDF2 import PdfReader
import requests
from io import BytesIO
import os
from dotenv import load_dotenv
import json
from supabase import create_client, Client
import tempfile

# load_dotenv()
# users = json.loads(os.getenv("users"))
users = json.loads(st.secrets["users"])

# Initialize Supabase
# SUPABASE_URL = os.getenv("supabase_url")
# SUPABASE_KEY = os.getenv("supabase_api_key")
SUPABASE_URL = st.secrets["supabase_url"]
SUPABASE_KEY = st.secrets["supabase_api_key"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

BUCKET_NAME = "veloflow-company-docs"

def authenticate_user(email):
    if email in users:
        return email, users[email]
    else: return False, False

def extract_pdf_text(file_source):
    if isinstance(file_source, str):  # Check if it's a URL
        response = requests.get(file_source)
        if response.status_code == 200:
            file_source = BytesIO(response.content)  # Convert to a file-like object
        else:
            raise ValueError(f"Failed to fetch PDF from {file_source}, Status Code: {response.status_code}")

    pdf_reader = PdfReader(file_source)
    return "\n".join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])


# Function to upload files to Supabase Storage
def upload_file_to_supabase(company, type, uploaded_file):
    file_extension = os.path.splitext(uploaded_file.name)[1]
    file_path = f"{company}/{type}/{uploaded_file.name}"
    # Save file to a temporary location
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
        temp_file.write(uploaded_file.getbuffer())
        temp_filename = temp_file.name

    with open(temp_filename, "rb") as f:
        res = supabase.storage.from_(BUCKET_NAME).upload(file_path, f, {"content-type": "application/pdf"})

    os.remove(temp_filename)

    if res:
        st.success(f"File '{uploaded_file.name}' uploaded successfully!")
    else:
        st.error("Failed to upload file.")

# Function to fetch files for a company
def get_company_documents(company, type, for_display = False):
    res = supabase.storage.from_(BUCKET_NAME).list(f"{company}/{type}")

    if res:
        if for_display:
            file_links = [f"{company}/{type}/{file['name']}" for file in res]
            return file_links
        else: 
            file_links = [supabase.storage.from_(BUCKET_NAME).get_public_url(f"{company}/{type}/{file['name']}") for file in res]
            return file_links
    return []

# Function to delete a file
def delete_company_doc(file_path):
    res = supabase.storage.from_(BUCKET_NAME).remove([file_path])
    if res:
        st.success(f"Document '{file_path}' deleted successfully!")
    else:
        st.error("Failed to delete document.")

