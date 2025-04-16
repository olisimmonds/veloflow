import os
import re
from docx import Document
from openai import OpenAI
import params
import shutil

OPENAI_KEY = params.OPENAI_KEY
client = OpenAI(api_key=OPENAI_KEY)

def call_openai(prompt: str, model: str = "gpt-4", temperature: float = 0.2, max_tokens: int = 1500) -> str:
    """
    Calls the OpenAI API with the provided prompt and returns the resulting text.
    This function is used for both removing irrelevant content and inserting placeholders.
    """
    result_text = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an expert business quote editor that preserves all document formatting."},
                {"role": "user", "content": prompt}
        ]
    )

    return result_text.choices[0].message.content
    
def ensure_str(text):
    """
    Utility function that ensures the input is a string.
    If the input is not a string, it converts it to one.
    """
    if not isinstance(text, str):
        return str(text)
    return text

def remove_irrelevant_info(tmp_path: str, context: dict) -> None:
    """
    Opens the DOCX document from tmp_path and processes every paragraph and table cell.
    For each text snippet that might contain product details, call a cloud-based LLM
    instructing it to remove irrelevant product details based on the provided context.
    The document is edited in place so that any original line that isn't removed remains unchanged.
    """
    doc = Document(tmp_path)
    
    # Process paragraphs.
    for para in doc.paragraphs:
        text = para.text
        if text.strip():
            prompt = (
                "You are given a snippet from a business quote document. Remove content related to products that are not needed "
                "for this quote based on the context provided. Do not remove universally relevant information such as company details, "
                "terms and conditions, or any textual formatting markers. Return the edited text exactly.\n\n"
                f"Text: {text}\n\n"
                f"Context: {context}"
            )
            new_text = call_openai(prompt)
            new_text = ensure_str(new_text)
            # Only update if the response is non-empty.
            if new_text:
                para.text = new_text

    # Process each cell in all tables.
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                cell_text = cell.text
                if cell_text.strip():
                    prompt = (
                        "You are given a snippet from a business quote document table cell. Remove content related to products that are irrelevant "
                        "for this quote, while preserving essential company information and formatting. Return the edited text exactly.\n\n"
                        f"Text: {cell_text}\n\n"
                        f"Context: {context}"
                    )
                    new_cell_text = call_openai(prompt)
                    new_cell_text = ensure_str(new_cell_text)
                    if new_cell_text:
                        cell.text = new_cell_text

    doc.save(tmp_path)

def insert_placeholders(tmp_path: str, context: dict) -> None:
    """
    Opens the DOCX file from tmp_path and processes every paragraph and table cell.
    In each text section, call the LLM to insert standardized placeholders where dynamic content should be updated.
    The placeholders are of the format: {{PLACEHOLDER: description}}.
    The document is modified in place without altering any formatting.
    """
    doc = Document(tmp_path)
    
    # Process paragraphs.
    for para in doc.paragraphs:
        text = para.text
        if text.strip():
            prompt = (
                "You are given a snippet from a business quote document. Insert standardized placeholders in the text where dynamic content "
                "(such as client email, product descriptions, etc.) should be updated, based on the context provided. The placeholders must be "
                "in the exact format {{PLACEHOLDER: description}}. Preserve the formatting, punctuation, and overall structure exactly.\n\n"
                f"Text: {text}\n\n"
                f"Context: {context}"
            )
            new_text = call_openai(prompt)
            new_text = ensure_str(new_text)
            if new_text:
                para.text = new_text

    # Process each cell in all tables.
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                cell_text = cell.text
                if cell_text.strip():
                    prompt = (
                        "You are given a snippet from a business quote document table cell. Insert standardized placeholders where dynamic content "
                        "(such as client email, product description, etc.) should be updated. The placeholders must be in the exact format "
                        "{{PLACEHOLDER: description}}, and the cell formatting must remain unchanged.\n\n"
                        f"Text: {cell_text}\n\n"
                        f"Context: {context}"
                    )
                    new_cell_text = call_openai(prompt)
                    new_cell_text = ensure_str(new_cell_text)
                    if new_cell_text:
                        cell.text = new_cell_text

    doc.save(tmp_path)

def fill_placeholders(tmp_path: str, context: dict) -> None:
    """
    Opens the DOCX file from tmp_path and searches for standardized placeholders of the form:
       {{PLACEHOLDER: description}}
    Replaces each placeholder with its corresponding value from the context.
    Uses regex to perform a safe replacement so that formatting remains intact.
    The keys in the context are expected to match the placeholder description, normalized to lowercase with underscores.
    """
    doc = Document(tmp_path)
    placeholder_pattern = re.compile(r"\{\{PLACEHOLDER:\s*(.*?)\s*\}\}")

    # Process paragraphs.
    for para in doc.paragraphs:
        text = para.text
        placeholders_found = placeholder_pattern.findall(text)
        new_text = text
        for placeholder in placeholders_found:
            # Ensure the placeholder is treated as a string.
            placeholder = ensure_str(placeholder)
            key = placeholder.lower().replace(" ", "_")
            if key in context:
                replacement = ensure_str(context[key])
                new_text = re.sub(r"\{\{PLACEHOLDER:\s*" + re.escape(placeholder) + r"\s*\}\}", replacement, new_text)
        if new_text != text:
            para.text = new_text

    # Process each cell in tables.
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                cell_text = cell.text
                placeholders_found = placeholder_pattern.findall(cell_text)
                new_cell_text = cell_text
                for placeholder in placeholders_found:
                    placeholder = ensure_str(placeholder)
                    key = placeholder.lower().replace(" ", "_")
                    if key in context:
                        replacement = ensure_str(context[key])
                        new_cell_text = re.sub(r"\{\{PLACEHOLDER:\s*" + re.escape(placeholder) + r"\s*\}\}", replacement, new_cell_text)
                if new_cell_text != cell_text:
                    cell.text = new_cell_text

    doc.save(tmp_path)

def save_intermediate(tmp_path: str, step: str) -> None:
    """
    Copies the current document at tmp_path to a new file that includes the step name.
    This lets you inspect the file after each step.
    """
    base, ext = os.path.splitext(tmp_path)
    new_path = f"{base}_{step}{ext}"
    shutil.copy(tmp_path, new_path)
    print(f"Saved intermediate document: {new_path}")

# ------------------------------------------------------------------------------
# LandGraph Agent Class using the updated workflow
# ------------------------------------------------------------------------------
class LandGraphAgent:
    """
    An agent that processes a .docx file (provided as tmp_path) in three steps:
      1. remove_irrelevant_info: Removes product details not needed for the given quote context.
      2. insert_placeholders: Inserts standardized placeholders (e.g. {{PLACEHOLDER: client_email}})
         in the document wherever dynamic content is required.
      3. fill_placeholders: Replaces these placeholders with the actual content from the context.
    The document is edited directly while preserving its original formatting.
    Intermediate document files are saved after each step.
    """
    def __init__(self):
        self.context = {}

    def update_context(self, context: dict):
        # The context should include both control flags and actual replacement values.
        self.context = context

    def run(self, tmp_path: str) -> str:
        print("Step 1: Removing irrelevant information from document.")
        remove_irrelevant_info(tmp_path, self.context)
        save_intermediate(tmp_path, "step1_removed")
        
        # print("Step 2: Inserting placeholders in document.")
        # insert_placeholders(tmp_path, self.context)
        # save_intermediate(tmp_path, "step2_placeholders")
        
        # print("Step 3: Filling placeholders with provided dynamic content.")
        # fill_placeholders(tmp_path, self.context)
        # save_intermediate(tmp_path, "step3_filled")
        
        # print("Document processing complete. Updated document saved at:", tmp_path)
        return tmp_path

# ------------------------------------------------------------------------------
# Example Workflow Execution
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    # Example temporary DOCX file path (ensure this file exists and is accessible)
    tmp_docx_path = "Tech Solutions Quote Template Ltd.docx"  # Replace with your input document path
    
    # Define the context for both placeholder insertion and replacement.
    # Note: Keys for replacement (for example "client_email") must match the placeholder descriptions
    # normalized to lowercase with underscores.
    context = {
        "client_requirements": {
            "requires_product_a": False,
            "requires_product_b": True
        },
        "client_email": "client@example.com",
        "product_description": "Advanced widget with extended warranty.",
        "company_name": "Company XYZ",
        "terms": "Standard terms and conditions apply."
    }
    
    # Instantiate and run the LandGraph Agent.
    agent = LandGraphAgent()
    agent.update_context(context)
    
    final_doc_path = agent.run(tmp_docx_path)
    print("Final document ready for client at:", final_doc_path)