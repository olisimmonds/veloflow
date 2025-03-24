import os
import tempfile
import requests
import json
from datetime import date
import docx 

from src.ai.make_quote.csv_xlsx import *
from src.ai.make_quote.docx import *
from src.ai.make_quote.html import *
from src.ai.make_quote.md import *
from src.ai.make_quote.tex import *

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
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp.write(response.content)
        tmp_path = tmp.name

    # Process based on file type
    updated_doc = None
    
    if ext == ".docx":
        # Process DOCX file
        doc = docx.Document(tmp_path)
        doc_structure = extract_doc_structure_docx(doc)
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
    
    else:
        raise Exception(f"Unsupported file type: {ext}")
    
    # Clean up temporary file(s)
    os.remove(tmp_path)
    # Optionally, remove output file for CSV if not needed further.
    
    return updated_doc

# Example usage:
# updated = process_document("https://example.com/path/to/quote_template.docx",
#                            "Email context here",
#                            "Company context here",
#                            "User context here")
# Depending on file type, 'updated' will be a docx.Document object or a string.
