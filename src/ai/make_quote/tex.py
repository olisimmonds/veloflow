import re
import json
from datetime import date
from openai import OpenAI
import params

OPENAI_KEY = params.OPENAI_KEY
client = OpenAI(api_key=OPENAI_KEY)

def extract_doc_structure_tex(tex_text):
    """
    Extracts a structured representation of a TeX document.
    Splits the document into paragraphs (blocks separated by two or more newlines) and extracts table content 
    from tabular environments. Returns a list of elements with type and index information.
    """
    elements = []
    paragraphs = re.split(r'\n\s*\n', tex_text)
    para_index = 0
    for para in paragraphs:
        if r'\begin{tabular}' in para:
            # Extract each tabular environment
            table_matches = re.findall(r'\\begin\{tabular\}(.*?)\\end\{tabular\}', para, re.DOTALL)
            for table in table_matches:
                rows = [row.strip() for row in table.splitlines() if row.strip()]
                for ri, row in enumerate(rows):
                    cells = [cell.strip() for cell in row.split('&')]
                    for ci, cell in enumerate(cells):
                        elements.append({
                            "type": "table",
                            "table_index": para_index,  # using paragraph index as table identifier
                            "row_index": ri,
                            "col_index": ci,
                            "text": cell
                        })
            para_index += 1
        else:
            elements.append({
                "type": "paragraph",
                "index": para_index,
                "text": para.strip()
            })
            para_index += 1
    return elements

def replace_text_in_tex(tex_text, replacements):
    """
    Replaces text in a TeX document based on precise location.
    For paragraphs, uses paragraph index.
    For table cells in tabular environments, uses table_index, row_index, and col_index.
    """
    # Split text into paragraphs while keeping separators
    paragraphs = re.split(r'(\n\s*\n)', tex_text)
    new_paragraphs = []
    para_counter = 0
    for para in paragraphs:
        if para.strip():
            if r'\begin{tabular}' in para:
                def replace_in_tabular(match):
                    table_content = match.group(1)
                    rows = table_content.splitlines()
                    new_rows = []
                    for ri, row in enumerate(rows):
                        cells = row.split('&')
                        new_cells = []
                        for ci, cell in enumerate(cells):
                            cell_text = cell.strip()
                            for rep in replacements:
                                loc = rep.get("location", {})
                                if (loc.get("type") == "table" and 
                                    loc.get("table_index") == para_counter and 
                                    loc.get("row_index") == ri and 
                                    loc.get("col_index") == ci):
                                    if rep.get("original", "") in cell_text:
                                        cell_text = cell_text.replace(rep.get("original", ""), rep.get("replacement", ""), 1)
                            new_cells.append(cell_text)
                        new_rows.append(" & ".join(new_cells))
                    return r'\begin{tabular}' + "\n" + "\n".join(new_rows) + "\n" + r'\end{tabular}'
                para = re.sub(r'\\begin\{tabular\}(.*?)\\end\{tabular\}', replace_in_tabular, para, flags=re.DOTALL)
            else:
                for rep in replacements:
                    loc = rep.get("location", {})
                    if loc.get("type") == "paragraph" and loc.get("index") == para_counter:
                        if rep.get("original", "") in para:
                            para = para.replace(rep.get("original", ""), rep.get("replacement", ""), 1)
            new_paragraphs.append(para)
            para_counter += 1
        else:
            new_paragraphs.append(para)
    return "".join(new_paragraphs)

def get_replacements_from_gpt_tex(doc_structure, email, company_context, user_context, user_email):
    """
    Uses GPT-4 to analyze the TeX document structure and determine which fields need updating.
    Returns a JSON list where each object includes:
      - 'location': for paragraphs: {'type': 'paragraph', 'index': <paragraph_index>}; 
                    for table cells: {'type': 'table', 'table_index': <table_index>, 'row_index': <row_index>, 'col_index': <col_index>}
      - 'original': the exact text snippet to be replaced.
      - 'replacement': the new text.
    """
    doc_structure_json = json.dumps(doc_structure, ensure_ascii=False, indent=2)
    prompt = f"""
        You are given a quote document represented as a list of document elements from a TeX file. Each element has a type 
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
    print("GPT-4 response:", reply)
    reply = reply.split("```json")[-1].split("```")[0]
    try:
        replacements = json.loads(reply)
    except Exception as e:
        print("Error parsing GPT-4 response:", e)
        replacements = []
    return replacements