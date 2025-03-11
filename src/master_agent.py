# Determin action
from langchain_core.prompts import PromptTemplate

prompt_template = PromptTemplate.from_template(
    """
    You are a master agent who's job is to determin which subtask should be started. 
    The aim of this task is to aid technical sales people respond to costurmer emails and generate quote. 
    You will read the email chain provided below and determin what action should be take.
    You have three options...
    a) Take no action - this email is not from a costormer or does not warent a response
    b) Make a quote - the custormer has asked for a quote to be generated, or it would be useful to provide one
    c) Draft email - this email needs a response but does not need a quote to be generated.

    The email is {email}.

    Determin the action and responde with a single letter to signal your response, 'a', 'b', or 'c'.  
    You must only responde with a signle letter, no exceptions!
    """
)
