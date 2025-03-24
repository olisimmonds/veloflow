from bs4 import BeautifulSoup
import json
from datetime import date
from openai import OpenAI
import params

OPENAI_KEY = params.OPENAI_KEY
client = OpenAI(api_key=OPENAI_KEY)

def extract_doc_structure_html(html):
    """
    Extracts a structured representation of the HTML document.
    Returns a list of document elements with their type, index information, and text.
    """
    soup = BeautifulSoup(html, "html.parser")
    elements = []
    # Extract paragraphs with index
    paragraphs = soup.find_all('p')
    for i, p in enumerate(paragraphs):
        elements.append({
            "type": "paragraph",
            "index": i,
            "text": p.get_text()
        })
    # Extract table cells with table, row, and column indices
    tables = soup.find_all('table')
    for ti, table in enumerate(tables):
        rows = table.find_all('tr')
        for ri, row in enumerate(rows):
            # Include both <td> and <th> cells
            cells = row.find_all(['td', 'th'])
            for ci, cell in enumerate(cells):
                elements.append({
                    "type": "table",
                    "table_index": ti,
                    "row_index": ri,
                    "col_index": ci,
                    "text": cell.get_text()
                })
    return elements

def replace_text_in_html(html, replacements):
    """
    Iterates over replacement suggestions and applies them based on precise location.
    Each replacement object should include a 'location' key that details the HTML element location,
    along with 'original' and 'replacement' keys.
    """
    soup = BeautifulSoup(html, "html.parser")
    # Replace in paragraphs
    paragraphs = soup.find_all('p')
    for rep in replacements:
        loc = rep.get("location", {})
        original = rep.get("original", "")
        new_text = rep.get("replacement", "")
        if loc.get("type") == "paragraph":
            idx = loc.get("index")
            if idx is not None and idx < len(paragraphs):
                p = paragraphs[idx]
                if original in p.get_text():
                    replaced_text = p.get_text().replace(original, new_text, 1)
                    p.string = replaced_text
        elif loc.get("type") == "table":
            ti = loc.get("table_index")
            ri = loc.get("row_index")
            ci = loc.get("col_index")
            try:
                tables = soup.find_all('table')
                table = tables[ti]
                rows = table.find_all('tr')
                row = rows[ri]
                cells = row.find_all(['td', 'th'])
                cell = cells[ci]
                if original in cell.get_text():
                    replaced_text = cell.get_text().replace(original, new_text, 1)
                    cell.string = replaced_text
            except IndexError:
                print(f"Invalid table location: {loc}")
    return str(soup)

def get_replacements_from_gpt_html(doc_structure, email, company_context, user_context, user_email):
    """
    Uses GPT-4 (via the OpenAI API) to analyze the document structure and determine which fields need updating.
    The prompt includes additional context and instructs the model to return a JSON list of objects.
    Each object includes:
      - 'location': an object with keys specifying the type and index info (for paragraphs: 'index'; for tables: 'table_index', 'row_index', 'col_index')
      - 'original': the exact text snippet that should be updated.
      - 'replacement': the new text to insert.
    """
    # Convert document structure to JSON string
    doc_structure_json = json.dumps(doc_structure, ensure_ascii=False, indent=2)
    
    prompt = f"""
        You are given a quote document represented as a list of document elements. Each element has a type 
        ('paragraph' or 'table') and corresponding index information, along with its text content. 
        Additionally, consider the following context:

        An email from a potential client:
        {email}

        Company context:
        {company_context}

        User provided context:
        {user_context}

        Todays date:
        {date.today()}

        User's email:
        {user_email}

        Any of the above provided context may be missing or not relevant. It is part of your job to determine what is relevant for completing a client's quote.
        The document may be a template or a previously filled-out template. Your task is to analyze the document elements 
        and complete a quote given the provided context. For each field, provide an object with:
        - 'location': an object indicating where the change should be applied. For a paragraph, include {{'type': 'paragraph', 'index': <paragraph_index>}}. 
          For a table cell, include {{'type': 'table', 'table_index': <table_index>, 'row_index': <row_index>, 'col_index': <col_index>}}.
        - 'original': the exact text snippet to be updated in that element.
        - 'replacement': the new text that should replace the original text.

        Maintain the quote's formatting and structure, only making edits where required to complete the quote. 
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
    # Extract the JSON portion (assuming it's in a code block with ```json markers)
    reply = reply.split("```json")[-1].split("```")[0]
    try:
        replacements = json.loads(reply)
    except Exception as e:
        print("Error parsing GPT-4 response:", e)
        replacements = []
    return replacements