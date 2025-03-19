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

users = params.users
HUGGING_FACE_API = params.HUGGING_FACE_API
SUPABASE_URL = params.SUPABASE_URL
SUPABASE_KEY = params.SUPABASE_KEY
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
BUCKET_NAME = "veloflow-company-docs"

local_model_path = './models/local_model'  # This is the directory where you saved the model
tokenizer = AutoTokenizer.from_pretrained(local_model_path)
model = AutoModel.from_pretrained(local_model_path, trust_remote_code=True)


def authenticate_user(email):
    if email in users:
        return email, users[email]
    else: return False, False

def extract_filenames(directories: List[str]) -> List[str]:
    return [path.split('/')[-1] for path in directories]

def extract_pdf_text(file_source):
    if isinstance(file_source, str):  # Check if it's a URL
        response = requests.get(file_source)
        if response.status_code == 200:
            file_source = BytesIO(response.content)  # Convert to a file-like object
        else:
            raise ValueError(f"Failed to fetch PDF from {file_source}, Status Code: {response.status_code}")

    pdf_reader = PdfReader(file_source)
    return "\n".join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])


# Function to upload files to Supabase Storage and embedings to Supabase Tables
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
        if type == "company_docs":
            file_link = supabase.storage.from_(BUCKET_NAME).get_public_url(file_path)
            text = extract_pdf_text(file_link)
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

        embeddings = []
        with torch.no_grad():  # Disable gradients for inference
            # Process all chunks at once by tokenizing in batch
            inputs = tokenizer(chunks, padding=True, truncation=True, return_tensors='pt', max_length=8192)
            
            # Generate embeddings by passing inputs through the model
            outputs = model(**inputs)
            
            # Extract the first token embeddings (CLS token) and normalize them
            chunk_embeddings = outputs.last_hidden_state[:, 0]
            normalized_embeddings = F.normalize(chunk_embeddings, p=2, dim=1)
            
            # Convert embeddings to list for database storage
            embeddings = normalized_embeddings.tolist()

        # Store embeddings in the Supabase database
        for chunk, embedding in zip(chunks, embeddings):
            supabase.table("document_embeddings").insert({
                "company": company,
                "type": type,
                "filename": filename,
                "text": chunk,
                "embedding": embedding
            }).execute()

# Remove embeddings when deleting a document
def remove_document_embedding(company, type, filename):
    supabase.table("document_embeddings").delete().match({
        "company": company,
        "type": type,
        "filename": filename
    }).execute()

def generate_embedding(text):
    # Tokenize the input text
    inputs = tokenizer(text, return_tensors='pt', padding=True, truncation=True, max_length=8192)
    
    # Generate the embedding using the local model
    with torch.no_grad():
        outputs = model(**inputs)
        
    # Extract the embedding (first token's representation)
    embedding = outputs.last_hidden_state[:, 0]
    
    # Normalize the embedding
    normalized_embedding = F.normalize(embedding, p=2, dim=1)
    
    # Convert to list (for storing or further processing)
    return normalized_embedding.tolist()[0]

# Retrieve relevant document passages for an email
def retrieve_relevant_context(company, type, email_text, word_limit=2000):
    email_embedding = generate_embedding(email_text)
    
    response = supabase.rpc("pgvector_search", {
        "query_embedding": email_embedding,
        "company": company,
        "type": type,
        "limit": 10
    }).execute()
    
    if response.data:
        passages = sorted(response.data, key=lambda x: np.dot(email_embedding, x["embedding"]), reverse=True)
        selected_texts = []
        word_count = 0
        
        for passage in passages:
            words = passage["text"].split()
            if word_count + len(words) > word_limit:
                break
            selected_texts.append(passage["text"])
            word_count += len(words)
        
        print(f"word count = {word_count}")
        print(f"selected_texts = {selected_texts}")

        return "\n".join(selected_texts) if selected_texts else None
    return None
