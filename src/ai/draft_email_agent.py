import params
from openai import OpenAI
import streamlit as st
from src.monitoring.feedback import log_generated_email

OPENAI_KEY = params.OPENAI_KEY

client = OpenAI(
    api_key=OPENAI_KEY,
)

def generate_response(email, company_context, user_context, user_email):

    prompt = f"""
    You are an assistant for a sales team. Your task is to read a customer's email and, using the provided company context and user-provided context, generate a detailed response.
    If nothing is passed in the email feild then generate an introduction email based on the context.
    You must:
    - Extract relevant products or services from the company context to recommend or quote to the customer based on their inquiry.
    - Respond by summarizing the product or service, its features, and any associated costs.
    - Take into account any context provided by the user.
    - Match the tone of the clients email.
    
    The company context and user-provided context is given below:
    Company context:
    {company_context}

    User provided context:
    {user_context}

    The user your working for has the email {user_email}.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": prompt},  # System-level context
            {"role": "user", "content": email},    # Customer email
        ]
    )

    # Extract the assistant's response from the API response
    ai_msg = response.choices[0].message.content
    log_generated_email(email, ai_msg, st.session_state["company"], user_email)
    print(ai_msg)
    return ai_msg
