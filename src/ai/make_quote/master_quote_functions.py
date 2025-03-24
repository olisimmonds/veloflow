import os
import tempfile
import requests
import docx 
from pdf2docx import Converter
import pdfkit
import docx2pdf
import markdown
import pandas as pd
from io import StringIO
from docx import Document

from src.ai.make_quote.csv_xlsx import *
from src.ai.make_quote.docx import *
from src.ai.make_quote.html import *
from src.ai.make_quote.md import *
from src.ai.make_quote.tex import *

def convert_pdf_to_docx(pdf_path, docx_path):
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
    
    elif ext == ".pdf":
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

    else:
        raise Exception(f"Unsupported file type: {ext}")
    
    # Clean up temporary file(s)
    os.remove(tmp_path)
    file_type = ext
    return updated_doc, file_type

def convert_updated_doc_to_pdf(updated_doc, file_ext, output_pdf=None):
    """
    Converts the given updated document to a PDF.
    
    Parameters:
        updated_doc: The updated document object or text.
            - For DOCX: a docx.Document object.
            - For HTML, MD, TEX, CSV: a string.
            - For XLSX: a filename (string) pointing to the updated Excel file.
        file_ext (str): The original file extension (e.g. ".docx", ".html", ".md", ".tex", ".csv", ".xlsx")
        output_pdf (str): (Optional) The desired output PDF filename. If not provided, a temporary file will be used.
        
    Returns:
        pdf_file (str): The file path of the generated PDF.
    """
    
    tmp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf_file = tmp_pdf.name
    tmp_pdf.close()
    
    if file_ext == ".docx":
        # updated_doc is a docx.Document object; save to temporary DOCX file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
            tmp_docx_path = tmp.name
        updated_doc.save(tmp_docx_path)
        # Convert DOCX to PDF using docx2pdf
        docx2pdf.convert(tmp_docx_path, pdf_file)
        os.remove(tmp_docx_path)
    
    elif file_ext == ".html":
        # updated_doc is a HTML string
        pdfkit.from_string(updated_doc, pdf_file)
    
    elif file_ext == ".md":
        # updated_doc is a Markdown string; convert to HTML then to PDF
        html_content = markdown.markdown(updated_doc)
        pdfkit.from_string(html_content, pdf_file)
    
    elif file_ext == ".tex":
        # updated_doc is a TeX string; save to .tex file and run pdflatex
        with tempfile.NamedTemporaryFile(delete=False, suffix=".tex") as tmp:
            tex_path = tmp.name
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(updated_doc)
        # Run pdflatex
        os.system(f"pdflatex -interaction=nonstopmode -output-directory {os.path.dirname(tex_path)} {tex_path}")
        base = os.path.splitext(os.path.basename(tex_path))[0]
        generated_pdf = os.path.join(os.path.dirname(tex_path), base + ".pdf")
        os.rename(generated_pdf, pdf_file)
        # Cleanup auxiliary files
        for ext_aux in [".aux", ".log", ".tex"]:
            try:
                os.remove(os.path.join(os.path.dirname(tex_path), base + ext_aux))
            except Exception:
                pass
    
    elif file_ext == ".csv":
        # updated_doc is a CSV string; use pandas to create an HTML table then convert to PDF
        df = pd.read_csv(StringIO(updated_doc))
        html_content = df.to_html(index=False)
        pdfkit.from_string(html_content, pdf_file)
    
    elif file_ext == ".xlsx":
        # updated_doc is assumed to be a filename for the updated XLSX.
        df = pd.read_excel(updated_doc)
        html_content = df.to_html(index=False)
        pdfkit.from_string(html_content, pdf_file)
    
    else:
        raise Exception(f"Unsupported file type for PDF conversion: {file_ext}")
    
    print(f"PDF saved as: {pdf_file}")
    return pdf_file

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
    updated_doc, file_type = process_document(file_url, email_text, company_contex, user_contex, user_email)
    
    # Convert the updated document to PDF
    pdf_file = convert_updated_doc_to_pdf(updated_doc, file_type)
    
    return updated_doc, pdf_file

# Example usage:
# updated_doc, pdf_file = generate_quote(file_url, email_text, company_contex, user_contex, user_email)
# Then you can pass pdf_file to st.download_button:
# st.download_button(label="Download Quote as PDF", data=open(pdf_file, "rb"), file_name="quote.pdf", mime="application/pdf")

# Example usage:
# updated = process_document("https://example.com/path/to/quote_template.docx",
#                            "Email context here",
#                            "Company context here",
#                            "User context here")
# Depending on file type, 'updated' will be a docx.Document object or a string.
