from fpdf import FPDF
import streamlit as st
import io
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint, HuggingFacePipeline
from langchain_core.messages import HumanMessage, SystemMessage
import params

HUGGING_FACE_API = params.HUGGING_FACE_API


def clean_text(text):
    return text.encode("latin-1", "ignore").decode("latin-1")  # Removes unsupported characters

def generate_pdf(text):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    cleaned_text = clean_text(text)
    pdf.multi_cell(0, 10, cleaned_text)
    
    pdf_output = "response.pdf"
    pdf.output(pdf_output)
    return pdf_output

def generate_quote(template_text, client_email, product_catalog_text, user_context, user_email):

    # Define the system message for the agent (context)
    messages = [
        SystemMessage(content=(
            f"""
            You are an assistant for a technical sales team. Your task is to generate a quote based on the provided template by filling in the necessary details using information from the customer's email and the product catalog.
            The quote provided may be template for which you should fill in the blanks, or it may be a previous quote, in which case you should determin want information needs to be updates. 
            
            Instructions:
            - Use the email provided below to understand the customer's needs, including any specific product requests or pricing inquiries.
            - Use the company context provided to identify relevant products or services that match the customer's needs.
            - If context has been provided by the user, include this as well.
            - The quote should follow the provided template exactly, filling in the blanks, or replacing the feilds which need updating with appropriate details:
            - Do not add any extra content beyond what is specified in the template.

            Here is the company context:
            {product_catalog_text}

            Here is the customer's email:
            {client_email}

            Here is some contex the user has given you:
            {user_context}

            Generate the quote based on this information, following the template and only filling in the blanks as directed.

            The user your working for has the email {user_email}.
            """
        )),
        HumanMessage(content=f"Here is the template: {template_text}"),
    ]
    
    # Load the model and chat agent
    model_repo = "HuggingFaceH4/zephyr-7b-beta"
    model = HuggingFaceEndpoint(repo_id=model_repo, task="text-generation", huggingfacehub_api_token=HUGGING_FACE_API)
    chat_model = ChatHuggingFace(llm=model)
    
    # Get the model's response
    ai_msg = chat_model.invoke(messages)
    print(ai_msg.content)
    return generate_pdf(ai_msg.content)