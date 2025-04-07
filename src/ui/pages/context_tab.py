import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import date

from src.ui.app_config_functions import (
    get_company_documents, 
    upload_file_to_supabase, 
    delete_company_doc, 
    extract_filenames,
    diveder,
    store_document_embedding,
    remove_document_embedding,
    check_filename_in_table,
    get_items_from_embedding_table
)

def context_tab(company_name: str):
    st.write("")
    st.subheader("Additional context for email/quote")

    st.session_state.context_from_user = st.text_area(
        "Context",
        label_visibility="collapsed",
        placeholder=(
            "Would you like to offer a discount? "
            "What tone should the email have? "
            "Suggest edits to the generated quote or email..."
        ),
        value=st.session_state.context_from_user,  # Preserve input
        height=150,  # Adjust height as needed
    )



    diveder(1)

    st.subheader("Knowledge Base")

    tab1, tab2, tab3, tab4 = st.tabs([
        "Documents",
        "Quote template",
        "Websites",
        "Free text"
    ])

    with tab1:
        docs_tab(company_name)
    with tab2:
        quote_tab(company_name)
    with tab3:
        url_tab(company_name)
    with tab4:
        free_text_tab(company_name)

@st.fragment
def docs_tab(company_name):
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
                upload_file_to_supabase(company_name, "company_docs", file)
            st.rerun(scope="fragment")

    # List uploaded documents with options to delete
    company_doc_links = get_company_documents(company_name, "company_docs", True)

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
                        st.rerun(scope="fragment")

                # Check if confirm_del is True
                if st.session_state.confirm_del:
                    
                    if st.button("Confirm delete"):
                        print(f"{company_name}/company_docs/{selected_doc}")
                        delete_company_doc(f"{company_name}/company_docs/{selected_doc}")
                        st.session_state.confirm_del = False  # Reset the confirmation state
                        st.info(f"Document '{selected_doc}' deleted successfully!")
                        st.rerun(scope="fragment")
                
                    if st.button("Cancel"):
                        st.session_state.confirm_del = False  # Reset the confirmation state
                        st.info(f"Document deletion of '{selected_doc}' cancelled.")
                        st.rerun(scope="fragment")

@st.fragment
def quote_tab(company_name):
    # Quote Template Upload (Limited to One)
    st.subheader("Upload Quote Template / Previous Quote")
    existing_template = get_company_documents(company_name, "quote_template", True)

    if len(existing_template)>0:
        st.info("A quote template already exists. Delete it before uploading a new one.")
        if st.session_state.confirm_del_of_quote == False:
            if st.button("Delete Existing Quote Template"):
                st.session_state.confirm_del_of_quote = True
                st.rerun(scope="fragment")

        # Check if confirm_del is True
        if st.session_state.confirm_del_of_quote:
            cols3 = st.columns(4)
            with cols3[0]:
                if st.button("Confirm delete "):
                    delete_company_doc(f"{existing_template[0]}")
                    st.session_state.confirm_del_of_quote = False  # Reset the confirmation state
                    st.info(f"Quote template deleted successfully!")
                    st.rerun(scope="fragment")
            with cols3[1]:
                if st.button("Cancel "):
                    st.session_state.confirm_del_of_quote = False  # Reset the confirmation state
                    st.info(f"Deletion of quote template cancelled.")
                    st.rerun(scope="fragment")

    else:
        uploaded_template = st.file_uploader(
            "Upload a Quote Template - Note: Our softwear works best when the quote template is in an editable format, i.e. docx, html, md, txt, csv, xlsx", 
            label_visibility="collapsed", 
            type=["pdf" "docx", "txt", "csv", "html", "md", "xlsx"], 
            accept_multiple_files=False
        )
        if uploaded_template and st.button("Upload Quote Template"):
            upload_file_to_supabase(company_name, "quote_template", uploaded_template)
            st.rerun(scope="fragment")

@st.fragment
def url_tab(company_name):
    st.subheader("Link relevant websites")
    web_url = st.text_input(label="Website URL")

    if st.button("Upload URL"):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
        }

        # Send a GET request with headers
        response = requests.get(web_url, headers=headers)

        # Check if the request was successful
        if response.status_code == 200:
            # Parse the HTML content using BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract the content you need
            # For example, extracting all paragraph text
            paragraphs = soup.find_all('p')
            web_content = ""
            for paragraph in paragraphs:
                web_content+=paragraph.get_text()
        else:
            st.warning(f"Failed to retrieve content. HTTP Status Code: {response.status_code}")

        todays_date = date.today().strftime('%d/%m/%Y').split('/')
        file_name = f"{todays_date[1]}{todays_date[2]}_{web_url}"

        if check_filename_in_table(company_name, file_name):
            st.warning("URL already in knowlage base")
        else:
            store_document_embedding(company_name, "url", file_name, web_content)


    urls_added_to_kb = set(get_items_from_embedding_table(company_name, "url"))

    # Check if the document exists
    if len(urls_added_to_kb)>0:
        cols_for_doc_selector = st.columns(2)
        with cols_for_doc_selector[0]:
            selected_url = st.selectbox("Select a URL to delete", label_visibility = "collapsed", options=urls_added_to_kb)
        with cols_for_doc_selector[1]:
            if selected_url:
                if st.session_state.confirm_del_of_url == False:
                    if st.button("Remove selceted URL"):
                        st.session_state.confirm_del_of_url = True
                        st.rerun(scope="fragment")

                # Check if confirm_del is True
                if st.session_state.confirm_del_of_url:
                    
                    if st.button("Confirm delete  "):
                        remove_document_embedding(company_name, "url", selected_url)
                        st.session_state.confirm_del_of_url = False  # Reset the confirmation state
                        st.info(f"URL '{selected_url}' removed successfully!")
                        st.rerun(scope="fragment")
                
                    if st.button("Cancel  "):
                        st.session_state.confirm_del_of_url = False  # Reset the confirmation state
                        st.info(f"URL deletion of '{selected_url}' cancelled.")
                        st.rerun(scope="fragment")

@st.fragment
def free_text_tab(company_name):
    st.subheader("Save Free text")

    content_to_save = st.text_area(
        "Save free text to knowledge base",
        label_visibility="collapsed",
        placeholder=(
            "What information isn't captured in your company websites and documents?"
            "What information do you offten have to add to the above secnario context box?"
        ),
        value=st.session_state.context_from_user,  # Preserve input
        height=150,  # Adjust height as needed
    )

    if st.button("Upload Text to Knowledge Base"):
        todays_date = date.today().strftime('%d/%m/%Y').split('/')
        file_name = f"{todays_date[1]}{todays_date[2]}_{content_to_save}"
        if check_filename_in_table(company_name, file_name):
            st.warning("This text has already been uploaded")
        else:
            store_document_embedding(company_name, "free_text", file_name, content_to_save)
            


    text_added_to_kb = get_items_from_embedding_table(company_name, "free_text")

    # Check if the document exists
    if len(text_added_to_kb)>0:
        cols_for_doc_selector = st.columns(2)
        with cols_for_doc_selector[0]:
            selected_text = st.selectbox("Select a Text to delete", label_visibility = "collapsed", options=text_added_to_kb)
        with cols_for_doc_selector[1]:
            if selected_text:
                if st.session_state.confirm_del_of_free_text == False:
                    if st.button("Remove selceted Text"):
                        st.session_state.confirm_del_of_free_text = True
                        st.rerun(scope="fragment")

                # Check if confirm_del is True
                if st.session_state.confirm_del_of_free_text:
                    
                    if st.button("Confirm delete   "):
                        remove_document_embedding(company_name, "free_text", selected_text)
                        st.session_state.confirm_del_of_free_text = False  # Reset the confirmation state
                        st.info(f"Text '{selected_text}' removed successfully!")
                        st.rerun(scope="fragment")
                
                    if st.button("Cancel   "):
                        st.session_state.confirm_del_of_free_text = False  # Reset the confirmation state
                        st.info(f"Text deletion of '{selected_text}' cancelled.")
                        st.rerun(scope="fragment")