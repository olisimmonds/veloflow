import os
os.environ["KMP_DUPLICATE_LIB_OK"]="TRUE"

import base64
import streamlit as st

st.set_page_config(
    layout="wide",
    page_title="Veloflow",
    page_icon="static/background.jpg"  # Path to your icon image
)

# @st.experimental_memo
def get_img_as_base64(file):
    with open(file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

main_back = get_img_as_base64("static/bg8.jpg")
login_back = get_img_as_base64("static/background5.jpg")

from src.master_agent import determine_action, get_action_from_response
from src.draft_email_agent import generate_response
from src.make_quote import generate_quote
from PyPDF2 import PdfReader
import time
from src.app_config_functions import get_company_documents, upload_file_to_supabase, delete_company_doc, authenticate_user, extract_pdf_text, extract_filenames, retrieve_relevant_context
from PIL import Image
from pathlib import Path

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if "generating_email" not in st.session_state:
    st.session_state["generating_email"] = False

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

message = st.empty()

def diveder(pix):
    with st.container():
        st.markdown(
            """
            <hr style="border: {pix}px solid #000; width: 100%; margin: 10px 0;">
            """,
            unsafe_allow_html=True,
        )    

# Your existing Streamlit code for login logic
if not st.session_state.get("logged_in", False):

    page_bg_img = f"""
    <style>
    [data-testid="stAppViewContainer"] {{
        background-image: url("data:image/png;base64,{login_back}");
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
        
    cols = st.columns(3)
    with cols[1]:
        st.markdown(
            """
            <style>
            .title-box {
                background: rgba(255, 255, 255, 0.7); /* Translucent white */
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
                text-align: center;
            }
            </style>
            <div class="title-box">
                <h1>Veloflow</h1>
            </div>
            """,
            unsafe_allow_html=True,
        )

        cols2 = st.columns([4, 1])
        with cols2[0]:
            st.write("")
            email = st.text_input(label="email", label_visibility = "collapsed", placeholder="Enter your email")
        with cols2[1]:
            st.write("")
            login_button = st.button("Login")

        st.markdown(
            """
            <style>
            .note-box {
                background: rgba(255, 255, 255, 0.7); 
                padding: 5px;
                border-radius: 10px;
                box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
                text-align: center;
            }
            </style>
            <div class="note-box">
                <h3>MVP - Version 1.0</h3>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if login_button:
            user, company = authenticate_user(email)
            if user:
                st.session_state["user"] = user
                st.session_state["company"] = company
                st.session_state["logged_in"] = True  # Mark user as logged in
                st.info("Login successful!")
                st.rerun()
            else:
                st.error("Invalid email or password.")


# If logged in, show the main app
else:

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
        
        st.title("Veloflow - AI Sales Assistant")
        st.subheader("Generate AI-Powered Responses & Quotes")

        email_text = st.text_area(
            "Paste the customer's email below:",
            height=150
            )

        cols_for_gen = st.columns([1, 3])
        with cols_for_gen[0]:
            if st.button("Generate Response"):
                
                if not st.session_state["generating_email"]:
                    message.empty()
                    st.session_state["generating_email"] = True
                    if email_text:
                        action = get_action_from_response(determine_action(email_text))
                        product_catalog_text = retrieve_relevant_context(company, "company_docs", email_text, word_limit=2000)
                        quote_template = get_company_documents(company, "quote_template")

                        if action == 'b2' and len(quote_template)>0 or st.session_state.force_quote_gen:
                            template_text = extract_pdf_text(quote_template[0])
                            st.session_state.response_text = generate_response(email_text, product_catalog_text, st.session_state.context_from_user)
                            pdf_file = generate_quote(template_text, email_text, product_catalog_text, st.session_state.context_from_user)
                            st.download_button(label="Download Quote as PDF", data=open(pdf_file, "rb"), file_name="quote.pdf", mime="application/pdf")
                            st.session_state.email_in_mem = True
                        else:
                            st.session_state.response_text = generate_response(email_text, product_catalog_text, st.session_state.context_from_user)
                            st.session_state.email_in_mem = True
                    else:
                        st.error("Please paste an email to generate a response.")
                    st.session_state["generating_email"] = False
                else: 
                    message.markdown("<h3 style='color:red;'>Please only press 'Generate Response' once. \nWait a few seconds and then the button will become available again.</h3>", unsafe_allow_html=True)
                    time.sleep(2)
                    message.empty()
                    st.session_state["generating_email"] = False
                    message.markdown("<h3 style='color:red;'>Try again now</h3>", unsafe_allow_html=True)
        
        with cols_for_gen[1]:
            st.session_state.force_quote_gen = st.toggle("Force Quote Generation")
            existing_template = get_company_documents(company, "quote_template", True)
            if len(existing_template)==0 and st.session_state.force_quote_gen:
                st.info("For improved quote generation, upload a quote.")

        diveder(1)
        
        if st.session_state.email_in_mem:
            st.markdown(
                f"""
                <div id="response-box" style="
                    background-color: white; 
                    padding: 10px; 
                    border-radius: 5px; 
                    box-shadow: 2px 2px 10px rgba(0,0,0,0.1); 
                    border: 1px solid #ddd;
                    width: 100%;
                    word-wrap: break-word;">
                    {st.session_state.response_text}
                </div>
                """, 
                unsafe_allow_html=True
            )
        

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
            uploaded_files = st.file_uploader("Upload PDFs", label_visibility="collapsed", type=["pdf"], accept_multiple_files=True)
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
        st.subheader("Upload Quote Template / Previous Quote")
        existing_template = get_company_documents(company, "quote_template", True)

        if len(existing_template)>0:
            st.info("A quote template already exists. Delete it before uploading a new one.")
            if st.session_state.confirm_del_of_quote == False:
                if st.button("Delete Existing Quote Template"):
                    st.session_state.confirm_del_of_quote = True
                    st.rerun()

            # Check if confirm_del is True
            if st.session_state.confirm_del_of_quote:
                cols3 = st.columns(4)
                with cols3[0]:
                    if st.button("Confirm delete"):
                        delete_company_doc(f"{existing_template[0]}")
                        st.session_state.confirm_del_of_quote = False  # Reset the confirmation state
                        st.info(f"Quote template deleted successfully!")
                        st.rerun()
                with cols3[1]:
                    if st.button("Cancel"):
                        st.session_state.confirm_del_of_quote = False  # Reset the confirmation state
                        st.info(f"Deletion of quote template cancelled.")
                        st.rerun()

        else:
            uploaded_template = st.file_uploader("Upload a Quote Template (PDF)", label_visibility = "collapsed", type=["pdf"], accept_multiple_files=False)
            if uploaded_template and st.button("Upload Quote Template"):
                upload_file_to_supabase(company, "quote_template", uploaded_template)
                st.rerun()
