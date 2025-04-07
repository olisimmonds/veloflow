import docx
import json
from openai import OpenAI
from datetime import date
import params
import fitz

OPENAI_KEY = params.OPENAI_KEY
client = OpenAI(api_key=OPENAI_KEY)

def extract_pdf_structure(pdf_path):
    """
    Extract a structured representation of the PDF.
    Returns a list of document elements where each element is a text block (treated as a paragraph)
    with its page number, an index for the block on that page, its bounding box, and its text.
    """
    doc = fitz.open(pdf_path)
    elements = []
    for page_number in range(len(doc)):
        page = doc.load_page(page_number)
        # Get text blocks: each block is a tuple (x0, y0, x1, y1, text, block_no, block_type)
        blocks = page.get_text("blocks")
        for block_index, block in enumerate(blocks):
            x0, y0, x1, y1, text, block_no, block_type = block
            # Skip empty blocks
            if text.strip():
                elements.append({
                    "type": "paragraph",
                    "page": page_number,
                    "index": block_index, 
                    "bbox": (x0, y0, x1, y1),
                    "text": text.strip()
                })
    doc.close()
    return elements

def replace_text_in_pdf(pdf_path, replacements, output_path):
    """
    Opens a PDF, applies text replacements, and saves the updated PDF.
    The replacements argument should be a list of objects with:
      - 'location': an object with 'type' ('paragraph'), 'page', and 'index' keys.
      - 'original': the exact text snippet to be replaced.
      - 'replacement': the new text.
    
    It works by searching for the text in the designated text block, redacting it,
    and then overlaying the new text on the redacted area.
    """
    doc = fitz.open(pdf_path)
    
    for rep in replacements:
        loc = rep.get("location", {})
        original = rep.get("original", "")
        new_text = rep.get("replacement", "")
        
        if loc.get("type") == "paragraph":
            page_num = loc.get("page")
            block_index = loc.get("index")
            
            # Ensure valid page and block index
            if page_num is None or block_index is None or page_num >= len(doc):
                print(f"Invalid location: {loc}")
                continue
            
            page = doc.load_page(page_num)
            blocks = page.get_text("blocks")
            
            if block_index >= len(blocks):
                print(f"Invalid block index on page {page_num}: {block_index}")
                continue
            
            # Get the block info
            x0, y0, x1, y1, block_text, _, _ = blocks[block_index]
            if original not in block_text:
                print(f"Original text not found in block on page {page_num} index {block_index}")
                continue
            
            # Find the exact position of the original text within the block
            # (this searches the whole page but we assume a match in the correct block)
            rects = page.search_for(original)
            rects = rects[:1]
            if not rects:
                print(f"Could not locate text '{original}' on page {page_num}")
                continue
            
            rect = rects[0]
            # Redact (i.e. cover) the area where the original text is located
            page.add_redact_annot(rect, fill=(1, 1, 1))
            page.apply_redactions()
            
            # Overlay the new text. Here we try to maintain font size and location.
            # In practice, you might want to adjust font, size, alignment, etc., based on your needs.
            page.insert_text(rect.tl, new_text, fontsize=12, color=(0, 0, 0))
    
    doc.save(output_path)
    doc.close()
    return output_path

def get_replacements_from_gpt_pdf(pdf_structure, email, company_context, user_context, user_email):
    """
    Uses GPT-4 (via the OpenAI API) to analyze the PDF structure and determine which fields need updating.
    The prompt includes additional context and instructs the model to return a JSON list of objects.
    Each object includes:
      - 'location': an object with keys specifying the type and location (for a paragraph: 'page' and 'index').
      - 'original': the exact text snippet that should be updated.
      - 'replacement': the new text.
    
    (Note: The client.chat.completions.create call below assumes that your client is already set up.)
    """
    doc_structure_json = json.dumps(pdf_structure, ensure_ascii=False, indent=2)
    prompt = f"""
        You are given a quote document represented as a list of document elements. Each element has a type 
        ('paragraph') along with page number, block index, bounding box coordinates, and its text content.
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

        Your job is to determine which fields in the document require updating in order to complete the quote.
        For each field, provide an object with:
        - 'location': an object indicating where the change should be applied. For a paragraph, include {{"type": "paragraph", "page": <page_number>, "index": <block_index>}}.
        - 'original': the exact text snippet to be updated.
        - 'replacement': the new text that should replace the original text.

        Maintain the document's formatting and structure, only making edits where required.
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
    # Expecting the JSON to be in a code block demarcated with ```json
    reply = reply.split("```json")[-1].split("```")[0]
    try:
        replacements = json.loads(reply)
    except Exception as e:
        print("Error parsing GPT-4 response:", e)
        replacements = []
    return replacements


    
