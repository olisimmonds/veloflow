import json
from datetime import date
from openai import OpenAI
import params

OPENAI_KEY = params.OPENAI_KEY
client = OpenAI(api_key=OPENAI_KEY)

def extract_doc_structure_md(md_text):
    """
    Extracts a structured representation of a Markdown document.
    Splits content into blocks separated by two newlines. If a block looks like a table (contains '|' 
    and a line with dashes), it is processed as a table; otherwise as a paragraph.
    Returns a list of elements with type and index information.
    """
    elements = []
    blocks = md_text.split("\n\n")
    para_index = 0
    table_index = 0
    for block in blocks:
        lines = block.splitlines()
        # Heuristic: if any line contains '|' and at least one line is only dashes/pipes/spaces, treat as table.
        if any('|' in line for line in lines) and any(set(line.strip()) <= set("-| ") and '-' in line for line in lines):
            rows = [line.strip() for line in lines if line.strip() != ""]
            for ri, row in enumerate(rows):
                # Split row by '|' and trim spaces
                cells = [cell.strip() for cell in row.split('|') if cell.strip()]
                for ci, cell in enumerate(cells):
                    elements.append({
                        "type": "table",
                        "table_index": table_index,
                        "row_index": ri,
                        "col_index": ci,
                        "text": cell
                    })
            table_index += 1
        else:
            elements.append({
                "type": "paragraph",
                "index": para_index,
                "text": block.strip()
            })
            para_index += 1
    return elements

def replace_text_in_md(md_text, replacements):
    """
    Replaces text in a Markdown document based on precise location.
    For paragraphs, uses the paragraph index.
    For tables, uses table_index, row_index, and col_index.
    """
    blocks = md_text.split("\n\n")
    new_blocks = []
    para_index = 0
    table_index = 0
    for block in blocks:
        lines = block.splitlines()
        if any('|' in line for line in lines) and any(set(line.strip()) <= set("-| ") and '-' in line for line in lines):
            new_lines = []
            rows = [line for line in lines if line.strip() != ""]
            for ri, row in enumerate(rows):
                cells = row.split('|')
                new_cells = []
                for ci, cell in enumerate(cells):
                    cell_text = cell.strip()
                    for rep in replacements:
                        loc = rep.get("location", {})
                        if (loc.get("type") == "table" and 
                            loc.get("table_index") == table_index and 
                            loc.get("row_index") == ri and 
                            loc.get("col_index") == ci):
                            if rep.get("original", "") in cell_text:
                                cell_text = cell_text.replace(rep.get("original", ""), rep.get("replacement", ""), 1)
                    new_cells.append(cell_text)
                new_lines.append(" | ".join(new_cells))
            new_blocks.append("\n".join(new_lines))
            table_index += 1
        else:
            text = block.strip()
            for rep in replacements:
                loc = rep.get("location", {})
                if loc.get("type") == "paragraph" and loc.get("index") == para_index:
                    if rep.get("original", "") in text:
                        text = text.replace(rep.get("original", ""), rep.get("replacement", ""), 1)
            new_blocks.append(text)
            para_index += 1
    return "\n\n".join(new_blocks)

def get_replacements_from_gpt_md(doc_structure, email, company_context, user_context, user_email):
    """
    Uses GPT-4 to analyze the Markdown document structure and determine which fields need updating.
    Returns a JSON list where each object includes:
      - 'location': for paragraphs: {'type': 'paragraph', 'index': <paragraph_index>}; 
                    for tables: {'type': 'table', 'table_index': <table_index>, 'row_index': <row_index>, 'col_index': <col_index>}
      - 'original': the exact text snippet to be replaced.
      - 'replacement': the new text.
    """
    doc_structure_json = json.dumps(doc_structure, ensure_ascii=False, indent=2)
    prompt = f"""
        You are given a quote document represented as a list of document elements from a Markdown file. Each element has a type 
        ('paragraph' or 'table') and corresponding index information, along with its text content.
        Additionally, consider the following context:

        An email from a potential client:
        {email}

        Company context:
        {company_context}

        User provided context:
        {user_context}

        Today's date:
        {date.today()}

        User's email:
        {user_email}

        The document may be a template or a previously filled-out template. Your task is to analyze the document elements 
        and complete a quote given the provided context. For each field, provide an object with:
          - 'location': for a paragraph, include {{'type': 'paragraph', 'index': <paragraph_index>}}; 
                        for a table cell, include {{'type': 'table', 'table_index': <table_index>, 'row_index': <row_index>, 'col_index': <col_index>}}.
          - 'original': the exact text snippet to be updated.
          - 'replacement': the new text to use.
        Return your answer as a JSON list.
        Document structure:
        {doc_structure_json}
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a professional sales assistant helping generate and update quotes."},
            {"role": "user", "content": prompt}
        ]
    )
    reply = response.choices[0].message.content
    
    reply = reply.split("```json")[-1].split("```")[0]
    try:
        replacements = json.loads(reply)
    except Exception as e:
        print("Error parsing GPT-4 response:", e)
        replacements = []
    return replacements