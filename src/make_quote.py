from fpdf import FPDF
from src.draft_email_agent import extract_pdf_text
import io
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint, HuggingFacePipeline
from langchain_core.messages import HumanMessage, SystemMessage
import os
from dotenv import load_dotenv
import re

load_dotenv()
HUGGING_FACE_API = os.getenv("HUGGING_FACE_API")

def generate_pdf(text):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, text)
    pdf_output = "response.pdf"
    pdf.output(pdf_output)
    return pdf_output

def generate_quote(template_pdf, client_email, product_catalog_text):

    # Extract the text from the uploaded template PDF
    template_text = extract_pdf_text(template_pdf)

    # Define the system message for the agent (context)
    messages = [
        SystemMessage(content=(
            f"""
            You are an assistant for a technical sales team. Your task is to generate a quote based on the provided template by filling in the necessary details using information from the customer's email and the product catalog.

            Instructions:
            - Use the email provided below to understand the customer's needs, including any specific product requests or pricing inquiries.
            - Use the product catalog provided to identify relevant products or services that match the customer's needs.
            - The quote should follow the provided template exactly, filling in the blanks with appropriate details:
            - Do not add any extra content beyond what is specified in the template.

            Here is the product catalog:
            {product_catalog_text}

            Here is the customer's email:
            {client_email}

            Generate the quote based on this information, following the template and only filling in the blanks as directed.

            """
        )),
        HumanMessage(content=f"Here is the template: {template_text}"),
    ]
    
    # Load the model and chat agent
    model = HuggingFaceEndpoint(repo_id="HuggingFaceH4/zephyr-7b-beta", task="text-generation", huggingfacehub_api_token=HUGGING_FACE_API)
    chat_model = ChatHuggingFace(llm=model)
    
    # Get the model's response
    ai_msg = chat_model.invoke(messages)

    return generate_pdf(ai_msg.content)