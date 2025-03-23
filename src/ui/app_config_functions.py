import streamlit as st
from PyPDF2 import PdfReader
import requests
from io import BytesIO
import os
import json
import numpy as np
from supabase import create_client, Client
import tempfile
import params
from typing import List
import torch.nn.functional as F
from transformers import AutoModel, AutoTokenizer
import torch
from sklearn.metrics.pairwise import cosine_similarity
from src.ai.extract_text import extract_text
from storage3.utils import StorageException
import base64

users = params.users
HUGGING_FACE_API = params.HUGGING_FACE_API
SUPABASE_URL = params.SUPABASE_URL
SUPABASE_KEY = params.SUPABASE_KEY
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
BUCKET_NAME = "veloflow-company-docs"

model_id = "sentence-transformers/all-MiniLM-L6-v2"
# api_url = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{model_id}"
# headers = {"Authorization": f"Bearer {HUGGING_FACE_API}"}

from huggingface_hub import InferenceClient

# Initialize the Hugging Face Inference Client
client = InferenceClient(
    model=model_id,  # Replace with your actual model ID
    token=HUGGING_FACE_API  # Replace with your actual Hugging Face token
)

def embed(texts):
    return client.feature_extraction(texts)


# def embed(texts):
#     response = requests.post(api_url, headers=headers, json={"inputs": texts, "options":{"wait_for_model":True}})
#     print(f"emedded email = {response}")
#     return response.json()

def diveder(pix):
    with st.container():
        st.markdown(
            """
            <hr style="border: {pix}px solid #000; width: 100%; margin: 10px 0;">
            """,
            unsafe_allow_html=True,
        )   

def get_img_as_base64(file):
    with open(file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

def authenticate_user(email):
    email = email.lower()
    if email in users:
        return email, users[email]
    else: return False, False

def extract_filenames(directories: List[str]) -> List[str]:
    return [path.split('/')[-1] for path in directories]

# def extract_pdf_text(file_source):
#     if isinstance(file_source, str):  # Check if it's a URL
#         response = requests.get(file_source)
#         if response.status_code == 200:
#             file_source = BytesIO(response.content)  # Convert to a file-like object
#         else:
#             raise ValueError(f"Failed to fetch PDF from {file_source}, Status Code: {response.status_code}")

#     pdf_reader = PdfReader(file_source)
#     return "\n".join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])


# Function to upload files to Supabase Storage and embedings to Supabase Tables
def upload_file_to_supabase(company, type, uploaded_file):
    file_extension = os.path.splitext(uploaded_file.name)[1]
    file_path = f"{company}/{type}/{uploaded_file.name}"

    # Save file to a temporary location
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
        temp_file.write(uploaded_file.getbuffer())
        temp_filename = temp_file.name

    with open(temp_filename, "rb") as f:
        try:
            res = supabase.storage.from_(BUCKET_NAME).upload(file_path, f, {"content-type": "application/pdf"})
        except StorageException as e:
            st.info("Resource already exists in storage")
            return None
        
    os.remove(temp_filename)

    if res:
        st.success(f"File '{uploaded_file.name}' uploaded successfully!")
        if type == "company_docs":
            file_link = supabase.storage.from_(BUCKET_NAME).get_public_url(file_path)
            text = extract_text(file_link)
            store_document_embedding(company, type, uploaded_file.name, text)
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
        company, type, filename = file_path.split('/')
        remove_document_embedding(company, type, filename)
        st.success(f"Document '{file_path}' deleted successfully!")
    else:
        st.error("Failed to delete document.")

# Store document embeddings in Supabase Postgres
def store_document_embedding(company, type, filename, text):
    with st.spinner("Embedding document..."):
        chunks = text.split(". ")  # Simple sentence-based chunking

        embeddings = embed(chunks)
            
        # Store embeddings in the Supabase database
        for chunk, embedding in zip(chunks, embeddings):
            supabase.table("document_embeddings").insert({
                "company": company,
                "type": type,
                "filename": filename,
                "text": chunk,
                "embedding": embedding.tolist()
            }).execute()

# Remove embeddings when deleting a document
def remove_document_embedding(company, type, filename):
    supabase.table("document_embeddings").delete().match({
        "company": company,
        "type": type,
        "filename": filename
    }).execute()

# Retrieve relevant document passages for an email
def retrieve_relevant_context(company, type, email_text, word_limit=2000):
    
    email_embedding = embed(email_text)
    
    # Fetch all document embeddings from Supabase for the given company and type
    response = supabase.table("document_embeddings").select("id, company, type, filename, text, embedding").eq("company", company).eq("type", type).execute()

    if response.data:
        # Calculate cosine similarity between the email embedding and document embeddings
        embeddings = np.array([np.array(eval(doc["embedding"])) for doc in response.data])
        email_embedding = np.array(email_embedding).reshape(1, -1)
        similarities = cosine_similarity(email_embedding, embeddings)
        
        # Get indices of the top N most similar documents (e.g., top 3)
        top_n = 15  # You can adjust this based on your needs
        top_indices = np.argsort(similarities[0])[-top_n:][::-1]
             
        word_limit = 2000
        words = []
        current_word_count = 0

        for idx in top_indices:
            doc = response.data[idx]  # Document data from your response
            doc_text = doc["text"]
            
            # Split the text into words and add to the words list until the word limit is reached
            doc_words = doc_text.split()
            remaining_space = word_limit - current_word_count
            if remaining_space > 0:
                words_to_add = doc_words[:remaining_space]
                words.extend(words_to_add)
                current_word_count += len(words_to_add)
            else:
                break

        # Return the words as a sequence of strings
        return ' '.join(words)
    return None
