import streamlit as st
from src.master_agent import determine_action, get_action_from_response
from src.draft_email_agent import generate_response
from src.make_quote import generate_quote
from src.draft_email_agent import extract_pdf_text

st.title("Veloflow")
st.subheader("AI-Powered Sales Email Assistant")

# Text area for users to paste emails
email_text = st.text_area("Paste the customer's email below:")

# File uploader for PDFs
uploaded_files = st.file_uploader("Drop PDFs here", type=["pdf"], accept_multiple_files=True)

if st.button("Generate Response"):
    if email_text:
        action = get_action_from_response(determine_action(email_text))
        print(action)
        product_catalog_pdf = 'company_docs\Product Catalog for Tech Solutions Ltd.pdf'
        product_catalog_text = extract_pdf_text(product_catalog_pdf)
        
        if action == 'b2' and uploaded_files:
            st.success("Generating a quote...")
            st.write(generate_response(email_text, product_catalog_text))
            pdf_file = generate_quote(uploaded_files, email_text, product_catalog_text)
            with open(pdf_file, "rb") as file:
                st.download_button(label="Download Quote as PDF", data=file, file_name="quote.pdf", mime="application/pdf")
        elif action == 'a1':
            st.write(generate_response(email_text, product_catalog_text))
        else:
            st.error("Unexpected response from AI. Please try again.")
    else:
        st.error("Please paste an email to generate a response.")
