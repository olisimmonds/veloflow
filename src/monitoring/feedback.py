import streamlit as st
import params
from supabase import create_client, Client

users = params.users
# HUGGING_FACE_API = params.HUGGING_FACE_API
SUPABASE_URL = params.SUPABASE_URL
SUPABASE_KEY = params.SUPABASE_KEY
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
BUCKET_NAME = "veloflow-company-docs"

def log_generated_email(client_email: str, generated_email: str, company_name: str, user_name: str):
    
    supabase.table("generated_responses_log").insert({
        "company": company_name,
        "user": user_name,
        "pasted_email": client_email,
        "generated_email": generated_email
    }).execute()


def log_generated_quote(client_email: str, generated_quote: str, company_name: str, user_name: str, upload_file_type: str):

    supabase.table("generated_quotes_log").insert({
        "company": company_name,
        "user": user_name,
        "pasted_email": client_email,
        "generated_quote": generated_quote,
        "file_type": upload_file_type
    }).execute()


def log_feedback_email(score: int, client_email: str, generated_email: str, company_name: str, user_name: str):
    
    with st.spinner("Sending Feedback..."):
        supabase.table("feedback_table_email").insert({
            "score": score,
            "pasted_email": client_email,
            "generated_email": generated_email,
            "company": company_name,
            "user_name": user_name
        }).execute()


def log_feedback_quote(score: int, client_email: str, generated_quote: str, company_name: str, user_name: str, upload_file_type: str):

    with st.spinner("Sending Feedback..."):
        supabase.table("feedback_table_quote").insert({
            "score": score,
            "pasted_email": client_email,
            "generated_quote": generated_quote,
            "file_type": upload_file_type,
            "company": company_name,
            "user_name": user_name
        }).execute()

