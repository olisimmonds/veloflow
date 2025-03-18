
import firebase_admin
from firebase_admin import auth, credentials, firestore

# Initialize Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate("secrets/veloflow-4b4bc-firebase-adminsdk-fbsvc-0a59ddf78d.json") 
    firebase_admin.initialize_app(cred)

db = firestore.client()

# Function to fetch company documents
def get_company_documents(company):
    docs_ref = db.collection("company_docs").document(company).get()
    if docs_ref.exists:
        return docs_ref.to_dict().get("product_catalog", "")
    return ""

def delete_company_doc(company, doc_name):
    db.collection("company_documents").document(company).get(doc_name).delete()
    st.success("Document deleted successfully!")

# Function to get the existing quote template
def get_existing_quote_template(company):
    template_ref = db.collection("quote_templates").document(company).get()
    if template_ref.exists:
        return template_ref.to_dict().get("template_text", "")
    return None

# Function to upload a quote template (Limited to one per company)
def upload_quote_template(company, uploaded_file):
    existing_template = get_existing_quote_template(company)

    if existing_template:
        st.success("A quote template already exists. Please remove it before uploading a new one.")
        return

    template_text = extract_pdf_text(uploaded_file)
    db.collection("quote_templates").document(company).set({"template_text": template_text})
    st.success("Quote template uploaded successfully!")

# Function to delete an existing quote template
def delete_quote_template(company):
    db.collection("quote_templates").document(company).delete()
    st.success("Quote template deleted successfully!")

# Function to upload company documents
def upload_company_documents(company, uploaded_files):
    combined_text = ""
    for file in uploaded_files:
        combined_text += extract_pdf_text(file) + "\n"

    db.collection("company_docs").document(company).set({"product_catalog": combined_text})
    st.success("Company documents uploaded successfully!")