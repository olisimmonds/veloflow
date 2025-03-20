from dotenv import load_dotenv
import json
import os
import streamlit as st
load_dotenv()

def running_on_cloud():
    try:
        SUPABASE_URL = st.secrets["supabase_url"]
        return True
    except Exception:
        return False
    
if running_on_cloud():
    # Cloud
    users = json.loads(st.secrets["users"])
    SUPABASE_URL = st.secrets["supabase_url"]
    SUPABASE_KEY = st.secrets["supabase_api_key"]
    HUGGING_FACE_API = st.secrets["HUGGING_FACE_API"]
    OPENAI_KEY = st.secrets["OPENAI_KEY"]
    
else:
    # Local
    users = json.loads(os.getenv("users"))
    SUPABASE_URL = os.getenv("supabase_url")
    SUPABASE_KEY = os.getenv("supabase_api_key")
    HUGGING_FACE_API = os.getenv("HUGGING_FACE_API")
    OPENAI_KEY = os.getenv("OPENAI_KEY")

