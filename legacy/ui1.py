import os
os.environ["KMP_DUPLICATE_LIB_OK"]="TRUE"

import base64
import streamlit as st

st.set_page_config(
    layout="wide",
    page_icon="static/background.jpg"  # Path to your icon image
)

# @st.experimental_memo
def get_img_as_base64(file):
    with open(file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

img1 = get_img_as_base64("static/background.jpg")
img2 = get_img_as_base64("static/background5.jpg")

page_bg_img = f"""
<style>
[data-testid="stAppViewContainer"] {{
    background-image: url("data:image/png;base64,{img2}");
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    background-attachment: fixed;
}}

[data-testid="stHeader"], [data-testid="stToolbar"] {{
    background: rgba(0,0,0,0);
}}

[data-testid="stSidebar"] {{
background-image: url("data:image/png;base64,{img1}");
background-size: cover;
background-position: left; 
background-repeat: no-repeat;
background-attachment: fixed;
}}
</style>
"""


st.markdown(page_bg_img, unsafe_allow_html=True)

from src.master_agent import determine_action, get_action_from_response
from src.draft_email_agent import generate_response
from src.make_quote import generate_quote
from PyPDF2 import PdfReader
import time
from src.app_config_functions import get_company_documents, upload_file_to_supabase, delete_company_doc, authenticate_user, extract_pdf_text
from PIL import Image
from pathlib import Path

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if "generating_email" not in st.session_state:
    st.session_state["generating_email"] = False

if 'confirm_del' not in st.session_state:
    st.session_state.confirm_del = False

message = st.empty()

# Your existing Streamlit code for login logic
if not st.session_state.get("logged_in", False):
       
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
    # Sidebar navigation
    page = st.sidebar.radio(" ", ["Generate Response", "Upload Documents"])
    company = st.session_state["company"]
    if page == "Generate Response":
        
        st.title("Veloflow - AI Sales Assistant")
        st.subheader("Generate AI-Powered Responses & Quotes")

        email_text = st.text_area("Paste the customer's email below:")

        if st.button("Generate Response"):
            if not st.session_state["generating_email"]:
                message.empty()
                st.session_state["generating_email"] = True
                if email_text:
                    action = get_action_from_response(determine_action(email_text))
                    product_catalog_text = [extract_pdf_text(link) for link in get_company_documents(company, "company_docs")]
                    quote_template = get_company_documents(company, "quote_template")

                    if action == 'b2' and len(quote_template)>0:
                        template_text = extract_pdf_text(quote_template[0])
                        st.info("Generating a quote...")
                        response_text = generate_response(email_text, product_catalog_text)
                        st.text(response_text)
                        pdf_file = generate_quote(template_text, email_text, product_catalog_text)
                        st.download_button(label="Download Quote as PDF", data=open(pdf_file, "rb"), file_name="quote.pdf", mime="application/pdf")
                        
                    else:
                        response_text = generate_response(email_text, product_catalog_text)
                        st.text(response_text)
                else:
                    st.error("Please paste an email to generate a response.")
                st.session_state["generating_email"] = False
            else: 
                message.markdown("<h3 style='color:red;'>Please only press 'Generate Response' once. \nWait a few seconds and then the button will become available again.</h3>", unsafe_allow_html=True)
                time.sleep(2)
                message.empty()
                st.session_state["generating_email"] = False
                message.markdown("<h3 style='color:red;'>Try again now</h3>", unsafe_allow_html=True)

    elif page == "Upload Documents":
        
        cols = st.columns(2)
        with cols[0]:
            # Company Documents Upload
            st.title("Upload Company Documents")
            uploaded_files = st.file_uploader("Upload PDFs", label_visibility="collapsed", type=["pdf"], accept_multiple_files=True)

            if st.button("Upload Company Documents") and uploaded_files:
                for file in uploaded_files:
                    upload_file_to_supabase(company, "company_docs", file)
                st.rerun()

            # List uploaded documents with options to delete
            company_doc_links = get_company_documents(company, "company_docs", True)

            # Check if the document exists
            if len(company_doc_links)>0:
                st.subheader("Uploaded Company Documents")
                selected_doc = st.selectbox("Select a document to delete", label_visibility = "collapsed", options=company_doc_links)

                if selected_doc:
                    if st.button("Remove Document"):
                        st.session_state.confirm_del = True

                    # Check if confirm_del is True
                    if st.session_state.confirm_del:
                        cols3 = st.columns(4)
                        with cols3[0]:
                            if st.button("Confirm delete"):
                                delete_company_doc(f"{selected_doc}")
                                st.session_state.confirm_del = False  # Reset the confirmation state
                                st.info(f"Document '{selected_doc}' deleted successfully!")
                                st.rerun()
                        with cols3[1]:
                            if st.button("Cancel"):
                                st.session_state.confirm_del = False  # Reset the confirmation state
                                st.info(f"Document deletion of '{selected_doc}' cancelled.")
                                st.rerun()
        with cols[1]:
            # Quote Template Upload (Limited to One)
            st.title("Upload Quote Template")
            existing_template = get_company_documents(company, "quote_template", True)

            if len(existing_template)>0:
                st.info("A quote template already exists. Delete it before uploading a new one.")
                if st.button("Delete Existing Quote Template"):
                    delete_company_doc(f"{existing_template[0]}")
                    st.rerun()
            else:
                uploaded_template = st.file_uploader("Upload a Quote Template (PDF)", label_visibility = "collapsed", type=["pdf"], accept_multiple_files=False)
                if uploaded_template and st.button("Upload Quote Template"):
                    upload_file_to_supabase(company, "quote_template", uploaded_template)
                    st.rerun()
