import os 
os.environ["KMP_DUPLICATE_LIB_OK"]="TRUE"
import streamlit as st

st.set_page_config(
    layout="wide",
    page_title="Veloflow",
    page_icon="static/background.jpg"  # Path to your icon image
)

from typing import List
import pythoncom

pythoncom.CoInitialize()

from src.ui.app_config_functions import get_img_as_base64
from src.ui.pages.login_page import login_page
from src.ui.pages.generation_tab import generation_tab
from src.ui.pages.context_tab import context_tab

def set_up_session_states_init_to_false(list_of_session_states: List[str]):
    for session_state_name in list_of_session_states:
        if session_state_name not in st.session_state:
            st.session_state[session_state_name] = False

set_up_session_states_init_to_false([
    "logged_in", 
    "generating_email", 
    "generating_quote", 
    "confirm_del",
    "confirm_del_of_quote",
    "force_quote_gen",
    "email_in_mem"
])

if "response_text" not in st.session_state:
    st.session_state.response_text = ""

if "context_from_user" not in st.session_state:
    st.session_state.context_from_user = ""

main_back = get_img_as_base64("static/bg8.jpg")

# Your existing Streamlit code for login logic
if not st.session_state.get("logged_in", False):
    login_page()
    
# If logged in, show the main app
else:
    # Main page config set up
    page_bg_img = f"""
    <style>
    [data-testid="stAppViewContainer"] {{
        background-image: url("data:image/png;base64,{main_back}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}

    [data-testid="stHeader"], [data-testid="stToolbar"] {{
        background: rgba(0,0,0,0);
    }}
    </style>
    """
    st.markdown(page_bg_img, unsafe_allow_html=True)

    company = st.session_state["company"]
    
    cols_main_page = st.columns([10, 1, 8])

    with cols_main_page[0]:
        generation_tab(company)

    with cols_main_page[2]:
        context_tab(company)
