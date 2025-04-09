import os
import tempfile
import requests
import docx 
from pdf2docx import Converter
import pdfkit
import markdown
import pandas as pd
from io import StringIO
from docx import Document
import pypandoc
from supabase import create_client, Client
import random
from openai import OpenAI
import params
from io import BytesIO
# from weasyprint import HTML
import streamlit as st
from src.monitoring.feedback import log_generated_quote

# Initialize Supabase client
SUPABASE_URL = params.SUPABASE_URL
SUPABASE_KEY = params.SUPABASE_KEY
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
BUCKET_NAME = "veloflow-company-docs"

OPENAI_KEY = params.OPENAI_KEY
client = OpenAI(api_key=OPENAI_KEY)

from src.ai.make_quote.csv_xlsx import *
from src.ai.make_quote.docx import *
from src.ai.make_quote.html import *
from src.ai.make_quote.md import *
from src.ai.make_quote.tex import *
from src.ai.make_quote.pdf import *
from src.ai.extract_text import extract_text

def convert_pdf_to_docx(pdf_path: str, docx_path: str):
    """
    Converts a PDF file to DOCX format using pdf2docx.
    """
    cv = Converter(pdf_path)
    cv.convert(docx_path, start=0, end=None)
    cv.close()

def process_document(file_url, email_text, compan_conx, user_context, user_email):
    """
    Downloads a file from a given URL, determines its file type,
    extracts its structure, gets GPT-4 replacements, applies the changes,
    and returns the updated document object or text.
    
    Parameters:
        file_url (str): URL to the file in cloud storage.
        email_text (str): Email context.
        compan_conx (str): Company context.
        user_context (str): User-provided context.
        
    Returns:
        updated_doc: The updated document (object for DOCX, string for others).
    """
    # Download file to a temporary location
    response = requests.get(file_url)
    if response.status_code != 200:
        raise Exception(f"Failed to download file. Status code: {response.status_code}")

    # Get the file extension
    _, ext = os.path.splitext(file_url)
    ext = ext.lower()
    print(f"{ext=}")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp.write(response.content)
        tmp_path = tmp.name

    # Process based on file type
    updated_doc = None
    
    if ext == ".docx":
        # Process DOCX file
        doc = docx.Document(tmp_path)
        doc_structure = extract_doc_structure_docx(doc)
        print(f"{doc_structure=}")
        replacements = get_replacements_from_gpt_docx(doc_structure, email_text, compan_conx, user_context, user_email)
        print("Detected replacements:", replacements)
        updated_doc = replace_text_in_docx(doc, replacements)
        # Optionally, you can save to a new file if needed:
        # updated_doc.save("final_quote.docx")
    
    elif ext == ".html":
        # Process HTML file
        with open(tmp_path, "r", encoding="utf-8") as f:
            html_text = f.read()
        doc_structure = extract_doc_structure_html(html_text)
        replacements = get_replacements_from_gpt_html(doc_structure, email_text, compan_conx, user_context, user_email)
        print("Detected replacements:", replacements)
        updated_doc = replace_text_in_html(html_text, replacements)
        # Optionally, save updated HTML to a file:
        # with open("final_quote.html", "w", encoding="utf-8") as f: f.write(updated_doc)
    
    elif ext == ".md":
        # Process Markdown file
        with open(tmp_path, "r", encoding="utf-8") as f:
            md_text = f.read()
        doc_structure = extract_doc_structure_md(md_text)
        replacements = get_replacements_from_gpt_md(doc_structure, email_text, compan_conx, user_context, user_email)
        print("Detected replacements:", replacements)
        updated_doc = replace_text_in_md(md_text, replacements)
        # Optionally, save updated Markdown to a file:
        # with open("final_quote.md", "w", encoding="utf-8") as f: f.write(updated_doc)
    
    elif ext == ".tex":
        # Process TeX file
        with open(tmp_path, "r", encoding="utf-8") as f:
            tex_text = f.read()
        doc_structure = extract_doc_structure_tex(tex_text)
        replacements = get_replacements_from_gpt_tex(doc_structure, email_text, compan_conx, user_context, user_email)
        print("Detected replacements:", replacements)
        updated_doc = replace_text_in_tex(tex_text, replacements)
        # Optionally, save updated TeX to a file:
        # with open("final_quote.tex", "w", encoding="utf-8") as f: f.write(updated_doc)
    
    elif ext == ".csv":
        # Process CSV file
        doc_structure = extract_doc_structure_csv(tmp_path)
        replacements = get_replacements_from_gpt_csv_xlsx(doc_structure, email_text, compan_conx, user_context, user_email)
        print("Detected replacements:", replacements)
        output_csv = os.path.join(os.path.dirname(tmp_path), "final_quote.csv")
        replace_text_in_csv(tmp_path, replacements, output_csv)
        # with open(output_csv, "r", encoding="utf-8") as f:
        #     updated_doc = f.read()

    elif ext == ".xlsx":
        # Process CSV file
        doc_structure = extract_doc_structure_xlsx(tmp_path)
        replacements = get_replacements_from_gpt_csv_xlsx(doc_structure, email_text, compan_conx, user_context, user_email)
        print("Detected replacements:", replacements)
        output_csv = os.path.join(os.path.dirname(tmp_path), "final_quote.csv")
        replace_text_in_xlsx(tmp_path, replacements, output_csv)
        # with open(output_csv, "r", encoding="utf-8") as f:
        #     updated_doc = f.read()
    
    elif ext == ".pdf":

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            temp_output_path = tmp.name
        pdf_structure = extract_pdf_structure(tmp_path)
        replacements = get_replacements_from_gpt_pdf(pdf_structure, email_text, compan_conx, user_context, user_email)
        print("Detected replacements:", replacements)
        updated_pdf = replace_text_in_pdf(tmp_path, replacements, temp_output_path)
    
        # Process PDF file using conversion approach:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_docx:
            tmp_docx_path = tmp_docx.name
        convert_pdf_to_docx(tmp_path, tmp_docx_path)
        doc = docx.Document(tmp_docx_path)
        doc_structure = extract_doc_structure_docx(doc)
        replacements = get_replacements_from_gpt_docx(doc_structure, email_text, compan_conx, user_context, user_email)
        print("Detected replacements:", replacements)
        updated_doc = replace_text_in_docx(doc, replacements)
        # Optionally, convert updated_doc (a DOCX object) back to PDF using a conversion tool if needed.
        os.remove(tmp_docx_path)
        return (updated_doc, updated_pdf), ext, (doc_structure, replacements)

    else:
        raise Exception(f"Unsupported file type: {ext}")
    
    # Clean up temporary file(s)
    os.remove(tmp_path)
    file_type = ext
    return updated_doc, file_type, (doc_structure, replacements)


def suggested_context_for_quote(text: str):
    prompt = f"""
        Hey, I've got AI to make me a quote but pottentially it could have done with some extra information.
        Could you take a quick look at this quote and let me know what additional context I should think about providing so that it's ready to send to a client?
        What feilds are missing? 

        Here's the content of the quote: 

        \"\"\"{text}\"\"\" 

        If the quote is ready to show to a client then say so, you don't have to suggest improvments.
        Keep it brief and to the point. 
        I want a short response.
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

def generate_quote(file_url, email_text, company_contex, user_contex, user_email):
    """
    Downloads and processes a quote document from a URL and converts it to a PDF.
    
    Parameters:
        file_url (str): URL to the file in cloud storage.
        email_text (str): Email context.
        company_contex (str): Company context.
        user_contex (str): User provided context.
        user_email (str): The user's email.
        
    Returns:
        updated_doc: The updated document object or text.
        pdf_file (str): The file path of the generated PDF.
    """
    # Run the document processing function (assumed to return updated_doc and file_type)
    try:
        updated_docs, file_type, struct_and_replcments = process_document(file_url, email_text, company_contex, user_contex, user_email)
    except:
        updated_docs, file_type, struct_and_replcments = process_document(file_url[:-1], email_text, company_contex, user_contex, user_email)
    
    if type(updated_docs) == tuple:
        updated_doc = updated_docs[0]
        file_type_text_extraction = ".docx"
    else: 
        updated_doc = updated_docs
        file_type_text_extraction = file_type

    # Generate random 6 digit number for temp file
    temp_id = random.randint(100000, 999999)
    file_path = f"temp/temp_quote_gen/temp{temp_id}{file_type_text_extraction}"
    
    buffer = BytesIO()
    updated_doc.save(buffer)
    buffer.seek(0) 
    response = supabase.storage.from_(BUCKET_NAME).upload(file_path, buffer.getvalue(), {"upsert": "true", "content-type": f"application/{file_type_text_extraction.rstrip('.')}"})
    if response.status_code == 200:
        
        public_url = supabase.storage.from_(BUCKET_NAME).get_public_url(file_path)
        print(f"{public_url=}")
        # public_url = public_url.rstrip('?')
        print(f"{public_url=}")
        extracted_text = extract_text(public_url)
    response = supabase.storage.from_(BUCKET_NAME).remove([file_path])

    requested_additional_context = suggested_context_for_quote(extracted_text)
    
    log_generated_quote(client_email = email_text, generated_quote = extracted_text, company_name = st.session_state["company"], user_name = user_email, upload_file_type = file_type)

    if type(updated_docs) == tuple:
        return (updated_doc, updated_docs[1]), file_type, requested_additional_context, extracted_text
    
    return updated_doc, file_type, requested_additional_context, extracted_text, struct_and_replcments

