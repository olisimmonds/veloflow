import streamlit as st
import time
import io

# from src.ai.master_agent import determine_action, get_action_from_response
from src.ai.draft_email_agent import generate_response
from src.ai.make_quote.master_quote_functions import generate_quote
from src.ai.extract_text import extract_text
from src.ui.app_config_functions import (
    get_company_documents, 
    retrieve_relevant_context,
    diveder
)

def docx_to_bytes(doc):
    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

def generation_tab(company_of_user: str):
    email_warining_message = st.empty()
    quote_warining_message = st.empty()
    
    st.title("Veloflow - AI Sales Assistant")
    st.subheader("Generate AI-Powered Responses & Quotes")

    email_text = st.text_area(
        "Paste the customer's email below:",
        height=150
        )

    cols_for_gen = st.columns([2, 5])
    with cols_for_gen[0]:
        if st.button("Generate Email"):
            with st.spinner("Generating Email Response"):
                if not st.session_state["generating_email"]:
                    email_warining_message.empty()
                    st.session_state["generating_email"] = True
                    
                    product_catalog_text = retrieve_relevant_context(company_of_user, "company_docs", email_text, word_limit=2000)
                    st.session_state.response_text = generate_response(email_text, product_catalog_text, st.session_state.context_from_user, st.session_state["user"])
                    st.session_state.email_in_mem = True

                    st.session_state["generating_email"] = False
                else: 
                    email_warining_message.markdown("<h3 style='color:red;'>Please only press 'Generate Response' once. \nWait a few seconds and then the button will become available again.</h3>", unsafe_allow_html=True)
                    time.sleep(2)
                    email_warining_message.empty()
                    st.session_state["generating_email"] = False
                    email_warining_message.markdown("<h3 style='color:red;'>Try again now</h3>", unsafe_allow_html=True)

    with cols_for_gen[1]:
        if st.button("Generate Quote"):
            with st.spinner("Generating Quote..."):
                if not st.session_state["generating_quote"]:
                    quote_warining_message.empty()
                    st.session_state["generating_quote"] = True
                    if email_text:
                        product_catalog_text = retrieve_relevant_context(company_of_user, "company_docs", email_text, word_limit=2000)
                        quote_template = get_company_documents(company_of_user, "quote_template")
                        if len(quote_template)==0:
                            quote_template = get_company_documents("default", "quote_template")
                        quote_template[0].rstrip('?')
                        print(f"{quote_template=}")
                        st.session_state.og_file_type, st.session_state.pdf_file_type_quote, st.session_state.ai_comment_on_quote = generate_quote(quote_template[0], email_text, product_catalog_text, st.session_state.context_from_user, st.session_state["user"])
                        st.session_state.og_file_type = docx_to_bytes(st.session_state.og_file_type)
                        st.session_state.quote_in_mem = True
                    
                    else:
                        st.error("Please paste an email to generate a response.")
                    st.session_state["generating_quote"] = False
                else: 
                    quote_warining_message.markdown("<h3 style='color:red;'>Please only press 'Generate Quote' once. \nWait a few seconds and then the button will become available again.</h3>", unsafe_allow_html=True)
                    time.sleep(2)
                    quote_warining_message.empty()
                    st.session_state["generating_quote"] = False
                    quote_warining_message.markdown("<h3 style='color:red;'>Try again now</h3>", unsafe_allow_html=True)


    if st.session_state.quote_in_mem:
        with cols_for_gen[0]:
            st.download_button(label="Download Quote as PDF", data=open(st.session_state.pdf_file_type_quote, "rb"), file_name="quote.pdf", mime="application/pdf")
        with cols_for_gen[1]:
            try:
                file_type = quote_template[0].split('.')[-1]
            except Exception as e:
                print(e)
                file_type = "docx"
            st.download_button(
                label=f"Download Quote as {file_type.upper()}",
                data=st.session_state.og_file_type.getvalue() if isinstance(st.session_state.og_file_type, io.BytesIO) else open(st.session_state.og_file_type, "rb"),
                file_name=f"quote.{file_type}",
                mime=f"application/{file_type if file_type != 'txt' else 'plain'}"
            )
        diveder(1)
        ai_suggestion_comment = "For improved quote generation, Veloflow AI recomends adding the following to the context box..."
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
                {ai_suggestion_comment}
            </div>
            """, 
            unsafe_allow_html=True
        )
        st.write("")
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
                {st.session_state.ai_comment_on_quote}
            </div>
            """, 
            unsafe_allow_html=True
        )

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