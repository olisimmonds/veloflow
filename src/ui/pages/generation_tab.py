import streamlit as st
import streamlit.components.v1 as components
import io, os, tempfile, time, pypandoc, json
from docx import Document
from pdflatex import PDFLaTeX
# from src.ai.master_agent import determine_action, get_action_from_response
from src.ai.draft_email_agent import generate_response
from src.ai.make_quote.master_quote_functions import generate_quote
from src.ai.extract_text import extract_text
from src.ui.app_config_functions import (
    get_company_documents, 
    retrieve_relevant_context,
    diveder
)

def docx_to_bytes(doc):
    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

# def convert_latex_to_pdf(latex_path: str, pdf_path: str):
#     """
#     Converts a LaTeX file to PDF using pandoc.
#     """
#     # Convert the LaTeX source back to PDF
#     pypandoc.convert_file(latex_path, 'pdf', outputfile=pdf_path)

# def convert_docx_to_pdf(doc: Document) -> bytes:
#     """
#     Converts a python-docx Document into PDF by:
#     1. Saving the Document as a DOCX file.
#     2. Converting DOCX to LaTeX using Pandoc.
#     3. Converting LaTeX to PDF using Pandoc.
#     Returns the PDF as bytes.
#     """
#     # Step 1: Save the Document to a temporary DOCX file.
#     with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_docx:
#         doc.save(tmp_docx.name)
#         docx_path = tmp_docx.name

#     # Step 2: Convert the DOCX file to LaTeX.
#     with tempfile.NamedTemporaryFile(delete=False, suffix=".tex") as tmp_tex:
#         tex_path = tmp_tex.name
#     latex_content = pypandoc.convert_file(docx_path, 'latex', format='docx')
#     with open(tex_path, 'w', encoding='utf-8') as f:
#         f.write(latex_content)

#     # Step 3: Convert the LaTeX file to PDF.
#     with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
#         pdf_path = tmp_pdf.name
#     pypandoc.convert_file(tex_path, 'pdf', outputfile=pdf_path, extra_args=['--pdf-engine=xelatex'])

#     # Read the generated PDF as bytes.
#     with open(pdf_path, 'rb') as f:
#         pdf_bytes = f.read()

#     # Clean up temporary files.
#     os.remove(docx_path)
#     if os.path.exists(tex_path):
#         os.remove(tex_path)
#     if os.path.exists(pdf_path):
#         os.remove(pdf_path)

#     return pdf_bytes

# def convert_docx_to_pdf(doc: Document) -> bytes:
#     """
#     Converts a python-docx Document into a PDF.
#     Uses Pandoc to convert DOCX -> LaTeX, then pdflatex to compile LaTeX -> PDF.
#     Returns PDF as bytes.
#     """
#     with tempfile.TemporaryDirectory() as tmpdir:
#         docx_path = os.path.join(tmpdir, "input.docx")
#         tex_path = os.path.join(tmpdir, "file.tex")
#         pdf_path = os.path.join(tmpdir, "file.pdf")

#         # Save the DOCX file
#         doc.save(docx_path)

#         # Convert DOCX to LaTeX
#         latex_content = pypandoc.convert_file(docx_path, 'latex', format='docx')
#         with open(tex_path, 'w', encoding='utf-8') as f:
#             f.write(latex_content)

#         # Compile LaTeX to PDF
#         pdfl = PDFLaTeX.from_texfile(tex_path)
        
#         pdf_bytes, log, proc = pdfl.create_pdf(
#             keep_pdf_file=True,  # keep it so we can open it
#             keep_log_file=True
#         )
#         # Check that the PDF exists
#         if not os.path.exists(pdf_path):
#             raise FileNotFoundError(f"Expected PDF not found at {pdf_path}. "
#                                     f"LaTeX log:\n{log}")

#         # Read and return PDF
#         with open(pdf_path, 'rb') as f:
#             return f.read()

def generation_tab(company_of_user: str):
    email_warining_message = st.empty()
    quote_warining_message = st.empty()
    
    st.title("Veloflow - AI Sales Assistant")
    st.subheader("Generate AI-Powered Responses & Quotes")

    email_text = st.text_area(
        "Paste the customer's email below:",
        height=150
        )

    cols_for_gen = st.columns([2, 5])
    with cols_for_gen[0]:
        if st.button("Generate Email"):
            with st.spinner("Generating Email Response"):
                if not st.session_state["generating_email"]:
                    email_warining_message.empty()
                    st.session_state["generating_email"] = True
                    
                    company_context = retrieve_relevant_context(company_of_user, email_text, word_limit=2000)
                    st.session_state.response_text = generate_response(email_text, company_context, st.session_state.context_from_user, st.session_state["user"])
                    st.session_state.email_in_mem = True

                    st.session_state["generating_email"] = False
                else: 
                    email_warining_message.markdown("<h3 style='color:red;'>Please only press 'Generate Response' once. \nWait a few seconds and then the button will become available again.</h3>", unsafe_allow_html=True)
                    time.sleep(2)
                    email_warining_message.empty()
                    st.session_state["generating_email"] = False
                    email_warining_message.markdown("<h3 style='color:red;'>Try again now</h3>", unsafe_allow_html=True)

    with cols_for_gen[1]:
        with st.popover("Generate Quote"):
            st.markdown("**Instructions:** Select from existing quote templates or let us make one for you. You can also upload more templates to the knowledge base.")
            quote_templates = get_company_documents(company_of_user, "quote_template", True)
            template_options = ["Veloflow's Quote Template"] + quote_templates
        
            # Let user select a template
            selected_template = st.selectbox(
                "Select a quote template:",
                template_options,
                index=0
            )
            
            generate = st.button("Generate Quote")

            if generate:
                if not st.session_state["generating_quote"]:
                    quote_warining_message.empty()
                    st.session_state["generating_quote"] = True

                    if selected_template=="Veloflow's Quote Template":
                        st.session_state.quote_template = get_company_documents("default", "quote_template")[0]
                    else:
                        selected_template = selected_template.split("/")[-1]
                        print(f"selected_template: {selected_template}")
                        st.session_state.quote_template = get_company_documents(company_of_user, "quote_template", file_name=selected_template)
            
                    print(f"quote_template: {st.session_state.quote_template}")

                else: 
                    quote_warining_message.markdown("<h3 style='color:red;'>Please only press 'Generate Quote' once. \nWait a few seconds and then the button will become available again.</h3>", unsafe_allow_html=True)
                    time.sleep(2)
                    quote_warining_message.empty()
                    st.session_state["generating_quote"] = False
                    quote_warining_message.markdown("<h3 style='color:red;'>Try again now</h3>", unsafe_allow_html=True)

            
        if st.session_state["generating_quote"]:    
            with st.spinner("Generating Quote..."):
                company_context = retrieve_relevant_context(company_of_user, email_text, word_limit=2000)
                
                quotes, st.session_state.file_type_of_quote, st.session_state.ai_comment_on_quote = generate_quote(st.session_state.quote_template, email_text, company_context, st.session_state.context_from_user, st.session_state["user"])
                
                if type(quotes) == tuple:
                    st.session_state.edited_quote_template = quotes[0]
                    st.session_state.quote_as_pdf = quotes[1]
                else: 
                    st.session_state.edited_quote_template = quotes
                
                st.session_state.edited_quote_template_bytes = docx_to_bytes(st.session_state.edited_quote_template)
                st.session_state.quote_in_mem = True
                
                st.session_state["generating_quote"] = False
            

    if st.session_state.quote_in_mem:
        with cols_for_gen[0]:
            file_type = st.session_state.file_type_of_quote
            if file_type == ".pdf":
                file_type = "docx" 
            st.download_button(
                label=f"Download Quote as {file_type.upper()}",
                data=st.session_state.edited_quote_template_bytes.getvalue() if isinstance(st.session_state.edited_quote_template_bytes, io.BytesIO) else open(st.session_state.edited_quote_template_bytes, "rb"),
                file_name=f"quote.{file_type}",
                mime=f"application/{file_type if file_type != 'txt' else 'plain'}"
            )
        if st.session_state.file_type_of_quote == ".pdf":
            
            with cols_for_gen[1]:
                with open(st.session_state.quote_as_pdf, "rb") as f:
                    pdf_bytes = f.read()
                st.download_button(label="Download Quote as PDF", data=pdf_bytes, file_name="quote.pdf", mime="application/pdf")
        
            
        diveder(1)
        ai_suggestion_comment = "For improved quote generation, Veloflow AI recomends adding the following to the context box..."
        st.markdown(
            f"""
            <div id="response-box" style="
                background-color: white; 
                padding: 10px; 
                border-radius: 5px; 
                box-shadow: 2px 2px 10px rgba(0,0,0,0.1); 
                border: 1px solid #ddd;
                width: 100%;
                word-wrap: break-word;">
                {ai_suggestion_comment}
            </div>
            """, 
            unsafe_allow_html=True
        )
        st.write("")
        st.markdown(
            f"""
            <div id="response-box" style="
                background-color: white; 
                padding: 10px; 
                border-radius: 5px; 
                box-shadow: 2px 2px 10px rgba(0,0,0,0.1); 
                border: 1px solid #ddd;
                width: 100%;
                word-wrap: break-word;">
                {st.session_state.ai_comment_on_quote}
            </div>
            """, 
            unsafe_allow_html=True
        )

    diveder(1)

    if st.session_state.email_in_mem:
        safe_email = json.dumps(st.session_state.response_text)

        html_code = f"""
        <html>
        <body style="margin: 0; padding: 0;">
            <button id="copy-button" style="padding: 0.5em 1em; font-size: 1em; border-radius: 8px; border: none; float: right;">
            📋 Copy
            </button>
            <script>
            document.getElementById("copy-button").addEventListener("click", function() {{
                const emailText = {safe_email};
                if (navigator.clipboard && window.isSecureContext) {{
                navigator.clipboard.writeText(emailText).then(function() {{
                    alert("Email copied to clipboard!");
                }}, function(err) {{
                    alert("Copy failed: " + err);
                }});
                }} else {{
                var tempTextArea = document.createElement("textarea");
                tempTextArea.value = emailText;
                document.body.appendChild(tempTextArea);
                tempTextArea.select();
                try {{
                    var successful = document.execCommand('copy');
                    if(successful) {{
                    alert("Email copied to clipboard!");
                    }} else {{
                    alert("Copy command was unsuccessful.");
                    }}
                }} catch (err) {{
                    alert("Copy failed: " + err);
                }}
                document.body.removeChild(tempTextArea);
                }}
            }});
            </script>
        </body>
        </html>
        """
        
        col1, col2 = st.columns([4,1])
        with col1:
            st.subheader("Veloflow's AI generated email:")
        with col2:
            components.html(html_code, height=60)

        st.markdown(
            f"""
            <div id="response-box" style="
                background-color: white; 
                padding: 10px; 
                border-radius: 5px; 
                box-shadow: 2px 2px 10px rgba(0,0,0,0.1); 
                border: 1px solid #ddd;
                width: 100%;
                word-wrap: break-word;">
                {st.session_state.response_text}
            </div>
            """, 
            unsafe_allow_html=True
        )
