import streamlit as st
from fpdf import FPDF
import io

def merge_replacements(doc_structure, replacements):
    """
    Merges the original document structure with any detected replacements.
    Updates blocks if a replacement was found, and for any extra replacement that
    isn’t already present in the structure, inserts it into the list in the right order.
    """
    # Make a copy of the list (to preserve the original order)
    merged = list(doc_structure)
    used_replacements = set()
    
    # Step 1: For every block already in the document, check for a replacement and update
    for i, block in enumerate(merged):
        for r_i, rep in enumerate(replacements):
            loc = rep['location']
            # Check for matching types
            if block['type'] == loc['type']:
                if block['type'] == 'paragraph':
                    if block.get('index') == loc.get('index'):
                        # Use the replacement if provided; fallback to original text.
                        merged[i]['text'] = rep.get('replacement', block.get('text', ''))
                        used_replacements.add(r_i)
                elif block['type'] == 'table':
                    if (block.get('table_index') == loc.get('table_index') and 
                        block.get('row_index') == loc.get('row_index') and 
                        block.get('col_index') == loc.get('col_index')):
                        if 'replacement' in rep:
                            merged[i]['text'] = rep['replacement']
                        used_replacements.add(r_i)
                        
    # Step 2: Insert any replacements that are not already in doc_structure.
    # For now, we assume extra replacements only apply to paragraphs.
    for r_i, rep in enumerate(replacements):
        if r_i not in used_replacements:
            if rep['location']['type'] == 'paragraph':
                rep_idx = rep['location']['index']
                # Find the first paragraph in merged whose index is greater than rep_idx.
                insert_position = None
                for i, block in enumerate(merged):
                    if block['type'] == 'paragraph' and block.get('index', -1) > rep_idx:
                        insert_position = i
                        break
                new_block = {'type': 'paragraph', 'index': rep_idx, 'text': rep.get('replacement','')}
                if insert_position is not None:
                    merged.insert(insert_position, new_block)
                else:
                    merged.append(new_block)
    return merged

def compile_document(merged):
    """
    Compiles the merged doc structure into one string.
    Paragraphs are added as-is (with newlines between them).
    For table blocks, consecutive table items from the same table are grouped and
    converted into a markdown formatted table.
    """
    compiled_parts = []
    i = 0
    n = len(merged)
    
    while i < n:
        block = merged[i]
        if block['type'] == 'paragraph':
            # Simply add the paragraph text.
            compiled_parts.append(block['text'])
            i += 1
        elif block['type'] == 'table':
            # Start grouping the table blocks for this table.
            table_blocks = []
            current_table_idx = block.get('table_index')
            while i < n and merged[i]['type'] == 'table' and merged[i].get('table_index') == current_table_idx:
                table_blocks.append(merged[i])
                i += 1
            # Build a dictionary with rows as keys
            table_dict = {}
            for cell in table_blocks:
                row = cell.get('row_index')
                col = cell.get('col_index')
                if row not in table_dict:
                    table_dict[row] = {}
                table_dict[row][col] = cell['text']
            # Construct rows sorted by row index.
            rows = []
            max_cols = 0
            for row_idx in sorted(table_dict.keys()):
                # For each row, extract values sorted by column
                cols = [table_dict[row_idx][col] for col in sorted(table_dict[row_idx].keys())]
                max_cols = max(max_cols, len(cols))
                rows.append(cols)
            # Ensure that all rows have the same number of columns
            for j in range(len(rows)):
                if len(rows[j]) < max_cols:
                    rows[j].extend([''] * (max_cols - len(rows[j])))
            # Create a Markdown table string.
            if rows:
                header = '| ' + ' | '.join(rows[0]) + ' |'
                separator = '| ' + ' | '.join(['---'] * max_cols) + ' |'
                table_str = header + "\n" + separator + "\n"
                for r in rows[1:]:
                    table_str += '| ' + ' | '.join(r) + ' |\n'
                compiled_parts.append(table_str)
        else:
            i += 1

    # Join all parts with two newlines for readability.
    return "\n\n".join(compiled_parts)

def strip_non_latin1(text):
    """Remove characters not supported by Latin-1 encoding."""
    return text.encode('latin-1', 'ignore').decode('latin-1')

def sanitize_text(text):
    """Replace problematic characters with supported alternatives."""
    replacements = {
        '•': '-',   # Bullet point to dash
        '–': '-',   # En dash
        '—': '-',   # Em dash
        '“': '"', '”': '"',
        '‘': "'", '’': "'",
        '…': '...',  # Ellipsis
        # Add more replacements if needed
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    return strip_non_latin1(text)

def convert_to_pdf(text):
    """Convert sanitized text to a PDF using only core fonts."""
    clean_text = sanitize_text(text)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)

    for line in clean_text.split('\n'):
        pdf.multi_cell(0, 10, line)

    # Output as bytes
    pdf_bytes = pdf.output(dest="S").encode("latin-1")
    return io.BytesIO(pdf_bytes)

def generate_editable_document(doc_structure, detected_replacements, file_type):
    """
    Generates an editable text area in Streamlit based on the original document structure,
    the detected replacements, and the original file type.
    
    - Merges any LLM generated changes with the original document.
    - Compiles paragraphs and tables appropriately so that structure is maintained.
    - Displays an editable text area that the user can update.
    - Offers download button(s); if file_type is PDF then only a PDF download is provided,
      otherwise both a PDF and an original format download are shown.
    """
    st.write("Make edits here in Veloflow")
    merged = merge_replacements(doc_structure, detected_replacements)
    compiled_text = compile_document(merged)
    
    # Create a text area pre-populated with the compiled document text.
    edited_text = st.text_area("Edit Document", compiled_text, height=600)
    
    # Offer download buttons based on the original file type.
    pdf_bytes = convert_to_pdf(edited_text)
    
    if file_type.lower() == "pdf":
        st.download_button("Download PDF", pdf_bytes, file_name="document.pdf", mime="application/pdf")
    else:
        st.download_button("Download PDF", pdf_bytes, file_name="document.pdf", mime="application/pdf")
        # In this example, we'll consider the original file as a plain text file.
        docx_buffer = create_docx_bytes(edited_text)

        # Streamlit download button with correct MIME type
        st.download_button(
            "Download Word Document",
            data=docx_buffer,
            file_name="document.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    return edited_text

from docx import Document
def create_docx_bytes(text):
    doc = Document()
    for line in text.split('\n'):
        doc.add_paragraph(line)
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer