# # Approach: 
#     # Accept pdf, docx, md, html, tex, xlsx, csv. (Can do)
#     # Save to local memory. (Can do)
#     # Convert pdf to original format. (Probs can do)
#     # Make intelignet edits for each file type. (Hard)
#         # For docx
#             # Itterate through each elemet, pass through gpt with context of whole document and suggest leave, edit or delete.
#             # Then pass through again with custormer stuff and for each field deside what the edit should be
#             # Then rebuild making the deletes and edits.
#         # Or
#             # Pass the AI all the content and get it to rewrite at once
#     # Return pdf and editable format. (Probs can do)


# from fpdf import FPDF
# import streamlit as st
# import io
# from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint, HuggingFacePipeline
# from langchain_core.messages import HumanMessage, SystemMessage
# import params
# from openai import OpenAI
# import fitz  # PyMuPDF for PDFs
# import docx 
# from openpyxl import load_workbook
# from bs4 import BeautifulSoup
# from pdf2docx import Converter
# import pandas as pd
# import requests

# HUGGING_FACE_API = params.HUGGING_FACE_API
# OPENAI_KEY = params.OPENAI_KEY


# #OpenAI

# client = OpenAI(
#     api_key=OPENAI_KEY,
# )

# # OpenAI
# def get_quote_content(template_text, client_email, company_context, user_context, user_email):

#     # Define the system message for the agent (context)
#     prompt = f"""
#         You are an assistant for a technical sales team. Your task is to generate a quote based on the provided template by filling in the necessary details using information from the customer's email, company context and user provided context.
#         The quote provided may be template for which you should fill in the blanks, or it may be a previous quote, in which case you should determin what information needs to be updated. 
        
#         Instructions:
#         - Use the email provided below to understand the customer's needs, including any specific product requests or pricing inquiries.
#         - Use the company context provided to identify relevant products or services that match the customer's needs.
#         - Consider the context providede by the user, it may be relevant.
#         - The quote should follow the provided template exactly, filling in the blanks, or replacing the feilds which need updating with appropriate details:
#         - Do not add any extra content beyond what is specified in the template.

#         Here is the company context:
#         {company_context}

#         Here is the customer's email:
#         {client_email}

#         Here is some contex the user has given you:
#         {user_context}

#         Generate the quote based on this information, following the template text provided in the user content, only filling in the blanks as directed.

#         Quote template extracted text: 
#         {template_text}

#         The user your working for has the email {user_email}.
#     """

#     response = client.chat.completions.create(
#         model="gpt-4o-mini",
#         messages=[{"role": "system", "content": prompt}]
#     )

#     # Extract the assistant's response from the API response
#     return response.choices[0].message.content
#     # return "hello"
# def generate_pdf(updated_text, original_pdf_path):
#     """Replaces text in a PDF while keeping formatting intact."""
#     response = requests.get(original_pdf_path)

#     response.raise_for_status()

#     pdf_bytes = io.BytesIO(response.content)
#     doc = fitz.open(stream=pdf_bytes, filetype="pdf") 
#     for page in doc:
#         page.insert_text((50, 50), updated_text)
#     output_pdf = io.BytesIO()
#     doc.save(output_pdf)
#     return output_pdf

# def generate_docx(updated_text, original_docx_url):
#     """Creates a new DOCX file with updated text while maintaining original formatting."""
#     response = requests.get(original_docx_url)
#     if response.status_code != 200:
#         raise Exception(f"Failed to download DOCX file: {response.status_code}")

#     # Open the DOCX file from bytes
#     doc_file = io.BytesIO(response.content)
#     doc = docx.Document(doc_file)
#     for para in doc.paragraphs:
#         para.text = updated_text
#     output_docx = io.BytesIO()
#     doc.save(output_docx)
#     return output_docx

# # def generate_txt(updated_text, original_txt_path):
# #     """Replaces content in a TXT file while keeping structure."""
# #     output_txt = io.BytesIO(updated_text.encode("utf-8"))
# #     return output_txt

# # def generate_csv(updated_text, original_csv_path):
# #     """Replaces content in a CSV file while keeping structure."""
# #     output_csv = io.BytesIO(updated_text.encode("utf-8"))
# #     return output_csv

# # def generate_html(updated_text, original_html_path):
# #     """Replaces body content in an HTML file while maintaining structure."""
# #     with open(original_html_path, "r", encoding="utf-8") as f:
# #         soup = BeautifulSoup(f, "html.parser")
# #     body_tag = soup.body
# #     if body_tag:
# #         body_tag.clear()
# #         body_tag.append(updated_text)
# #     output_html = io.BytesIO(str(soup).encode("utf-8"))
# #     return output_html

# # def generate_md(updated_text, original_md_path):
# #     """Replaces content in a Markdown file while keeping structure."""
# #     output_md = io.BytesIO(updated_text.encode("utf-8"))
# #     return output_md

# # def generate_xlsx(updated_text, original_xlsx_path):
# #     """Updates an Excel file with new quote data."""
# #     wb = load_workbook(original_xlsx_path)
# #     ws = wb.active
# #     ws.cell(row=2, column=2, value=updated_text)  # Example: Update first data cell
# #     output_xlsx = io.BytesIO()
# #     wb.save(output_xlsx)
# #     return output_xlsx

# # def convert_to_pdf(original_path, file_type):
# #     """Converts a given file type (docx, txt, csv, html, md, xlsx) into an identical PDF copy."""
# #     pdf = FPDF()
# #     pdf.add_page()
# #     pdf.set_auto_page_break(auto=True, margin=15)
# #     pdf.set_font("Arial", size=12)
    
# #     if file_type == "docx":
# #         doc = docx.Document(original_path)
# #         for para in doc.paragraphs:
# #             pdf.cell(200, 10, txt=para.text, ln=True)
# #     elif file_type == "txt" or file_type == "md":
# #         with open(original_path, "r", encoding="utf-8") as f:
# #             for line in f:
# #                 pdf.cell(200, 10, txt=line.strip(), ln=True)
# #     elif file_type == "csv":
# #         df = pd.read_csv(original_path)
# #         for index, row in df.iterrows():
# #             pdf.cell(200, 10, txt=str(row.values), ln=True)
# #     elif file_type == "html":
# #         with open(original_path, "r", encoding="utf-8") as f:
# #             soup = BeautifulSoup(f, "html.parser")
# #         text = soup.get_text()
# #         pdf.multi_cell(0, 10, txt=text)
# #     elif file_type == "xlsx":
# #         wb = load_workbook(original_path)
# #         sheet = wb.active
# #         for row in sheet.iter_rows(values_only=True):
# #             pdf.cell(200, 10, txt=str(row), ln=True)
    
# #     output_pdf = io.BytesIO()
# #     pdf.output(output_pdf)
# #     return output_pdf

# # def convert_pdf_to_docx(pdf_path, output_docx_path):
# #     """Converts a PDF file to a DOCX file while preserving formatting."""
# #     converter = Converter(pdf_path)
# #     converter.convert(output_docx_path, start=0, end=None)
# #     converter.close()
# #     return output_docx_path

# def generate_quote(quote_template, template_text, client_email, company_context, user_context, user_email):
    
#     quote_content = get_quote_content(template_text, client_email, company_context, user_context, user_email)

#     if quote_template.endswith('.pdf'):
#         pdf = generate_pdf(quote_content, quote_template)
#         # docx = convert_pdf_to_docx(pdf, "doxc_quote.docx")
#         return pdf#, docx
#     elif quote_template.endswith('.docx'):
#         docx = generate_docx(quote_content, quote_template)
#         # pdf = convert_to_pdf(docx, "docx")
#         return docx #pdf, docx
#     # elif quote_template.endswith('.txt'):
#     #     txt = generate_txt(quote_content, quote_template)
#     #     pdf = convert_to_pdf(txt, "txt")
#     #     return pdf, txt
#     # elif quote_template.endswith('.csv'):
#     #     csv =  generate_csv(quote_content, quote_template)
#     #     pdf = convert_to_pdf(csv, "csv")
#     #     return pdf, csv
#     # elif quote_template.endswith('.html'):
#     #     html = generate_html(quote_content, quote_template)
#     #     pdf = convert_to_pdf(html, "html")
#     #     return pdf, html
#     # elif quote_template.endswith('.md'):
#     #     md = generate_md(quote_content, quote_template)
#     #     pdf = convert_to_pdf(md, "md")
#     #     return pdf, md
#     # elif quote_template.endswith('.xlsx'):
#     #     xlsx = generate_xlsx(quote_content, quote_template)
#     #     pdf = convert_to_pdf(xlsx, "xlsx")
#     #     return pdf, xlsx
#     else:
#         raise ValueError("Unsupported file format")




# # def clean_text(text):
# #     return text.encode("latin-1", "ignore").decode("latin-1")  # Removes unsupported characters

# # def generate_pdf(text):
# #     pdf = FPDF()
# #     pdf.set_auto_page_break(auto=True, margin=15)
# #     pdf.add_page()
# #     pdf.set_font("Arial", size=12)
    
# #     cleaned_text = clean_text(text)
# #     pdf.multi_cell(0, 10, cleaned_text)
    
# #     pdf_output = "response.pdf"
# #     pdf.output(pdf_output)
# #     return pdf_output









# # Hugging face
# # def generate_quote(template_quote, client_email, product_catalog_text, user_context, user_email):

# #     # Define the system message for the agent (context)
# #     messages = [
# #         SystemMessage(content=(
# #             f"""
# #             You are an assistant for a technical sales team. Your task is to generate a quote based on the provided template by filling in the necessary details using information from the customer's email and the product catalog.
# #             The quote provided may be template for which you should fill in the blanks, or it may be a previous quote, in which case you should determin want information needs to be updates. 
            
# #             Instructions:
# #             - Use the email provided below to understand the customer's needs, including any specific product requests or pricing inquiries.
# #             - Use the company context provided to identify relevant products or services that match the customer's needs.
# #             - If context has been provided by the user, include this as well.
# #             - The quote should follow the provided template exactly, filling in the blanks, or replacing the feilds which need updating with appropriate details:
# #             - Do not add any extra content beyond what is specified in the template.

# #             Here is the company context:
# #             {product_catalog_text}

# #             Here is the customer's email:
# #             {client_email}

# #             Here is some contex the user has given you:
# #             {user_context}

# #             Generate the quote based on this information, following the template and only filling in the blanks as directed.

# #             The user your working for has the email {user_email}.
# #             """
# #         )),
# #         HumanMessage(content=f"Here is the template: {template_text}"),
# #     ]
    
# #     # Load the model and chat agent
# #     model_repo = "HuggingFaceH4/zephyr-7b-beta"
# #     model = HuggingFaceEndpoint(repo_id=model_repo, task="text-generation", huggingfacehub_api_token=HUGGING_FACE_API)
# #     chat_model = ChatHuggingFace(llm=model)
    
# #     # Get the model's response
# #     ai_msg = chat_model.invoke(messages)
# #     print(ai_msg.content)
# #     return generate_pdf(ai_msg.content)