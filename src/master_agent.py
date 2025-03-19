# Determin action
import streamlit as st
from langchain.prompts import PromptTemplate
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint, HuggingFacePipeline
import re
from langchain_core.messages import HumanMessage, SystemMessage
# from langchain_openai import ChatOpenAI
import params

HUGGING_FACE_API = params.HUGGING_FACE_API

def determine_action(email):

    messages = [
        SystemMessage(content=
            """
            You are an AI assistant helping technical salespeople. 
            Your task is to determine if a quote should be generated based on the customer's email.

            Instructions:
            - Respond with only 'a1' (no quote needed) or 'b2' (quote should be generated).
            - No extra text, explanations, or punctuation.
            - If unsure, default to 'a1'.
            
            Example:
            Email: "Can you provide a quote for 10 units?"
            Response: b2
            
            Email: "Thanks for your help."
            Response: a1
            """
        ),
        HumanMessage(
            content=email
        ),
    ]

    # model_repo = "meta-llama/Llama-3.3-70B-Instruct"
    model_repo = "HuggingFaceH4/zephyr-7b-beta"
    model = HuggingFaceEndpoint(repo_id=model_repo, task="text-generation", huggingfacehub_api_token=HUGGING_FACE_API)
    chat_model = ChatHuggingFace(llm=model)
    ai_msg = chat_model.invoke(messages)

   
    return ai_msg.content

def get_action_from_response(model_output):
    # Regular expression to match the action labels
    match = re.search(r'\b(a1|b2)\b', model_output.lower())  #|c3
    
    if match:
        return match.group(0)
    else:
        print("No valid action found")
        # If no valid action is found, return a default action or raise an error
        return 'a1'
    

# You are a master agent whose job is to determine which subtask should be started. 
#             The aim of this task is to aid technical salespeople in responding to customer emails and generating quotes. 
#             You will read the email provided and determine what action should be taken.
#             You have three options:
#             a1) Take no action - this email is not from a customer or does not warrant a response.
#             b2) Make a quote - the customer has asked for a quote to be generated, or it would be useful to provide one.
#             c3) Draft email - this email needs a response but does not need a quote to be generated.

#             Determine the action and respond with a single word to signal your response: 'a1', 'b2', or 'c3'.  
#             You must only respond with a single word, 'a1', 'b2', or 'c3', no exceptions!

# Change bellow to stronger model
    # model = HuggingFaceHub(repo_id="mistralai/Mistral-7B-Instruct", huggingfacehub_api_token=HUGGING_FACE_API)
    # response = model(prompt_template.format(email=email))
    # llm = HuggingFacePipeline.from_model_id(
    #     model_id="HuggingFaceH4/zephyr-7b-beta",
    #     task="text-generation",
    #     pipeline_kwargs=dict(
    #         max_new_tokens=512,
    #         do_sample=False,
    #         repetition_penalty=1.03,
    #     ),
    # )
    # chat_model = ChatHuggingFace(llm=llm)
    # response = model(prompt_template.format(email=email))

    # model = ChatOpenAI(api_key=OPEN_AI_API)
    # response = model.predict(prompt_template.format(email=email))
    # return response.strip().lower()