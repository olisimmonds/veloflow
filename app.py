import os 
os.environ["KMP_DUPLICATE_LIB_OK"]="TRUE"
import streamlit as st

st.set_page_config(
    layout="wide",
    page_title="Veloflow",
    page_icon="static/background.jpg"  # Path to your icon image
)

from PyPDF2 import PdfReader
import time
import io
import base64

from src.ai.master_agent import determine_action, get_action_from_response
from src.ai.draft_email_agent import generate_response
from src.ai.make_quote import generate_quote
from src.ai.extract_text import extract_text
from src.ui.app_config_functions import (
    get_company_documents, 
    upload_file_to_supabase, 
    delete_company_doc, 
    authenticate_user, 
    extract_filenames, 
    retrieve_relevant_context,
    get_img_as_base64,
    diveder
)
from src.ui.pages.login_page import login_page
from src.ui.pages.generation_tab import generation_tab

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if "generating_email" not in st.session_state:
    st.session_state["generating_email"] = False

if "generating_quote" not in st.session_state:
    st.session_state["generating_quote"] = False

if 'confirm_del' not in st.session_state:
    st.session_state.confirm_del = False

if 'confirm_del_of_quote' not in st.session_state:
    st.session_state.confirm_del_of_quote = False

if "force_quote_gen" not in st.session_state:
    st.session_state.force_quote_gen = False

if "email_in_mem" not in st.session_state:
    st.session_state.email_in_mem = False

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
        st.write("")
        st.subheader("Optional: Additional context for email")
        st.session_state.context_from_user = st.text_area(
            "Context",
            label_visibility="collapsed",
            placeholder=(
                "Would you like to offer a discount? "
                "What tone should the email have? "
                "Are there any key details that must be included?"
            ),
            value=st.session_state.context_from_user,  # Preserve input
            height=150,  # Adjust height as needed
        )

        diveder(1)
        st.subheader("Company Documents and Product Catalogues")

        cols_right_side = st.columns([3,2])
        with cols_right_side[0]:
            uploaded_files = st.file_uploader(
                "Upload Files", 
                label_visibility="collapsed", 
                type=["pdf", "docx", "txt", "csv", "jpg", "png", "html", "md", "xls", "xlsx"], 
                accept_multiple_files=True
            )

        with cols_right_side[1]:
            st.write("")
            if st.button("Upload Company Documents") and uploaded_files:
                for file in uploaded_files:
                    upload_file_to_supabase(company, "company_docs", file)
                st.rerun()

        # List uploaded documents with options to delete
        company_doc_links = get_company_documents(company, "company_docs", True)

        # Check if the document exists
        if len(company_doc_links)>0:
            file_names_to_display = extract_filenames(company_doc_links)
            cols_for_doc_selector = st.columns(2)
            with cols_for_doc_selector[0]:
                selected_doc = st.selectbox("Select a document to delete", label_visibility = "collapsed", options=file_names_to_display)
            with cols_for_doc_selector[1]:
                if selected_doc:
                    if st.session_state.confirm_del == False:
                        if st.button("Delete selceted company document"):
                            st.session_state.confirm_del = True
                            st.rerun()

                    # Check if confirm_del is True
                    if st.session_state.confirm_del:
                        
                        if st.button("Confirm delete"):
                            print(f"{company}/company_docs/{selected_doc}")
                            delete_company_doc(f"{company}/company_docs/{selected_doc}")
                            st.session_state.confirm_del = False  # Reset the confirmation state
                            st.info(f"Document '{selected_doc}' deleted successfully!")
                            st.rerun()
                    
                        if st.button("Cancel"):
                            st.session_state.confirm_del = False  # Reset the confirmation state
                            st.info(f"Document deletion of '{selected_doc}' cancelled.")
                            st.rerun()
        
        diveder(1)

        # Quote Template Upload (Limited to One)
        # st.subheader("Upload Quote Template / Previous Quote")
        # existing_template = get_company_documents(company, "quote_template", True)

        # if len(existing_template)>0:
        #     st.info("A quote template already exists. Delete it before uploading a new one.")
        #     if st.session_state.confirm_del_of_quote == False:
        #         if st.button("Delete Existing Quote Template"):
        #             st.session_state.confirm_del_of_quote = True
        #             st.rerun()

        #     # Check if confirm_del is True
        #     if st.session_state.confirm_del_of_quote:
        #         cols3 = st.columns(4)
        #         with cols3[0]:
        #             if st.button("Confirm delete"):
        #                 delete_company_doc(f"{existing_template[0]}")
        #                 st.session_state.confirm_del_of_quote = False  # Reset the confirmation state
        #                 st.info(f"Quote template deleted successfully!")
        #                 st.rerun()
        #         with cols3[1]:
        #             if st.button("Cancel"):
        #                 st.session_state.confirm_del_of_quote = False  # Reset the confirmation state
        #                 st.info(f"Deletion of quote template cancelled.")
        #                 st.rerun()

        # else:
        #     uploaded_template = uploaded_files = st.file_uploader(
        #         "Upload a Quote Template", 
        #         label_visibility="collapsed", 
        #         type=["pdf", "docx", "txt", "csv", "html", "md", "xlsx"], 
        #         accept_multiple_files=False
        #     )
        #     if uploaded_template and st.button("Upload Quote Template"):
        #         upload_file_to_supabase(company, "quote_template", uploaded_template)
        #         st.rerun()
