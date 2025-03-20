import PyPDF2
import streamlit as st
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint, HuggingFacePipeline

from langchain_core.messages import HumanMessage, SystemMessage
from functools import cache
import params

HUGGING_FACE_API = params.HUGGING_FACE_API

# Function to generate a response based on customer email and the product catalog
def generate_response(email, product_catalog_text, user_context):

    # Define the system message for the agent (context)
    messages = [
        SystemMessage(content=(
            """
            You are an assistant for a technical sales team. Your task is to read a customer's email and, using the provided company context and user provided contex, generate a detailed response.
            You must:
            - Extract relevant products or services from the catalog to recommend or quote to the customer based on their inquiry.
            - Respond by summarizing the product or service, its features, and any associated costs. 
            - Take into account any context provided by the user.
            If the email contains a request for a quote, provide the quote details. Otherwise, respond with product recommendations or explanations.
            
            The company context and user provided context is given in the human message.
            You are also given a customer email. Use all provided information to produce a response.
            Make sure your response is professional and addresses the customer's needs.
            """
        )),
        HumanMessage(content=f"Company context:\n{product_catalog_text}\n\nUser provided contex:\n{user_context}\n\nCustomer Email:\n{email}"),
    ]
    # Load the model and chat agent
    # model_repo = "meta-llama/Llama-3.3-70B-Instruct"
    model_repo = "HuggingFaceH4/zephyr-7b-beta"
    model = HuggingFaceEndpoint(repo_id=model_repo, task="text-generation", huggingfacehub_api_token=HUGGING_FACE_API)
    chat_model = ChatHuggingFace(llm=model)
    
    # Get the model's response
    ai_msg = chat_model.invoke(messages)
    print(ai_msg)
    return ai_msg.content
