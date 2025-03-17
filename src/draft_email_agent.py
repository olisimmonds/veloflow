import PyPDF2
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint, HuggingFacePipeline

from langchain_core.messages import HumanMessage, SystemMessage
from functools import cache

import os
from dotenv import load_dotenv
import re

load_dotenv()
HUGGING_FACE_API = os.getenv("HUGGING_FACE_API")

# Function to extract text from the PDF product catalog
# @cache # Commented out for now cus want to make sure we pull info from template and catalog
def extract_pdf_text(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
    return text

# Function to generate a response based on customer email and the product catalog
def generate_response(email, product_catalog_text):

    # Define the system message for the agent (context)
    messages = [
        SystemMessage(content=(
            """
            You are an assistant for a technical sales team. Your task is to read a customer's email and, using the provided product catalog, generate a detailed response.
            You must:
            - Extract relevant products or services from the catalog to recommend or quote to the customer based on their inquiry.
            - Respond by summarizing the product or service, its features, and any associated costs. 
            If the email contains a request for a quote, provide the quote details. Otherwise, respond with product recommendations or explanations.
            
            The product catalog is provided below.
            You are also given a customer email. Use both the catalog and the email content to craft a response.
            Make sure your response is professional and addresses the customer's needs.
            """
        )),
        HumanMessage(content=f"Product Catalog:\n{product_catalog_text}\n\nCustomer Email:\n{email}"),
    ]
    # Load the model and chat agent
    model = HuggingFaceEndpoint(repo_id="HuggingFaceH4/zephyr-7b-beta", task="text-generation", huggingfacehub_api_token=HUGGING_FACE_API)
    chat_model = ChatHuggingFace(llm=model)
    
    # Get the model's response
    ai_msg = chat_model.invoke(messages)
    print(ai_msg)
    return ai_msg.content
