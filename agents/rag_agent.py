from pathlib import Path
from dotenv import load_dotenv
import shutil

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()

POLICIES_DIR    = Path(__file__).parent.parent / "data" / "policies"
VECTORSTORE_DIR = Path(__file__).parent.parent / "vectorstore"

POLICIES_DIR.mkdir(parents=True, exist_ok=True)
VECTORSTORE_DIR.mkdir(parents=True, exist_ok=True)

_vectorstore = None
_llm         = None


def get_llm():
    global _llm
    if _llm is None:
        _llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
    return _llm


def get_embeddings():
    return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")


def get_vectorstore():
    global _vectorstore
    if _vectorstore is not None:
        return _vectorstore

    chroma_db = VECTORSTORE_DIR / "chroma.sqlite3"
    if chroma_db.exists():
        _vectorstore = Chroma(
            persist_directory=str(VECTORSTORE_DIR),
            embedding_function=get_embeddings(),
        )
        return _vectorstore

    # No vectorstore yet — check if any PDFs exist to build from
    pdf_files = list(POLICIES_DIR.glob("*.pdf"))
    if pdf_files:
        return ingest_all_pdfs()

    return None  # No PDFs uploaded yet


def ingest_all_pdfs():
    """Re-ingest all PDFs in policies folder from scratch."""
    global _vectorstore

    pdf_files = list(POLICIES_DIR.glob("*.pdf"))
    if not pdf_files:
        return None

    # Wipe old vectorstore and rebuild
    if VECTORSTORE_DIR.exists():
        shutil.rmtree(VECTORSTORE_DIR)
    VECTORSTORE_DIR.mkdir(exist_ok=True)

    all_docs = []
    for pdf_path in pdf_files:
        loader = PyPDFLoader(str(pdf_path))
        docs   = loader.load()
        for doc in docs:
            doc.metadata["source"] = pdf_path.name
        all_docs.extend(docs)
        print(f"  Loaded: {pdf_path.name} ({len(docs)} page(s))")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ".", " "],
    )
    chunks = splitter.split_documents(all_docs)
    print(f"  Total chunks: {len(chunks)}")

    _vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=get_embeddings(),
        persist_directory=str(VECTORSTORE_DIR),
    )
    print(f"Vectorstore saved → {VECTORSTORE_DIR}")
    return _vectorstore


def save_and_ingest_pdf(uploaded_file) -> str:
    """
    Save a Streamlit UploadedFile to policies folder and ingest into vectorstore.
    Returns a status message.
    """
    global _vectorstore

    # Save file to disk
    save_path = POLICIES_DIR / uploaded_file.name
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    print(f"Saved: {save_path}")

    # Load and chunk just this new PDF
    loader = PyPDFLoader(str(save_path))
    docs   = loader.load()
    for doc in docs:
        doc.metadata["source"] = uploaded_file.name

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ".", " "],
    )
    chunks = splitter.split_documents(docs)

    embeddings = get_embeddings()

    # Add to existing vectorstore or create a new one
    if _vectorstore is not None:
        _vectorstore.add_documents(chunks)
    else:
        _vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=str(VECTORSTORE_DIR),
        )

    return f"✅ '{uploaded_file.name}' ingested — {len(docs)} page(s), {len(chunks)} chunks"


def delete_pdf(filename: str) -> str:
    """Remove a PDF and rebuild the vectorstore from remaining files."""
    global _vectorstore

    pdf_path = POLICIES_DIR / filename
    if pdf_path.exists():
        pdf_path.unlink()

    _vectorstore = None
    remaining = list(POLICIES_DIR.glob("*.pdf"))
    if remaining:
        ingest_all_pdfs()
        return f"🗑️ '{filename}' deleted. Vectorstore rebuilt with {len(remaining)} file(s)."
    else:
        if VECTORSTORE_DIR.exists():
            shutil.rmtree(VECTORSTORE_DIR)
        return f"🗑️ '{filename}' deleted. No PDFs remaining."


def list_pdfs() -> list:
    return [f.name for f in sorted(POLICIES_DIR.glob("*.pdf"))]


def has_vectorstore() -> bool:
    return (VECTORSTORE_DIR / "chroma.sqlite3").exists()


def query(user_input: str, k: int = 4) -> str:
    vectorstore = get_vectorstore()

    if vectorstore is None:
        return "⚠️ No policy documents uploaded yet. Please upload a PDF using the sidebar."

    docs = vectorstore.similarity_search(user_input, k=k)
    if not docs:
        return "I couldn't find relevant information in the uploaded policy documents."

    context = "\n\n---\n\n".join([
        f"[Source: {doc.metadata.get('source', 'Unknown')}, "
        f"Page {doc.metadata.get('page', '?')}]\n{doc.page_content}"
        for doc in docs
    ])

    prompt = f"""You are a helpful customer support assistant.
Answer the user's question based ONLY on the policy documents provided below.

POLICY CONTEXT:
{context}

USER QUESTION: {user_input}

INSTRUCTIONS:
- Answer specifically and clearly using ONLY the information above.
- Use bullet points for lists or steps.
- Quote exact policy details (timelines, amounts, conditions) when available.
- If the answer is not in the context say:
  "This information is not covered in the uploaded policy documents."
- End with: 📄 Source: [filename]
"""

    response = get_llm().invoke([
        SystemMessage(content="You are a precise policy document assistant."),
        HumanMessage(content=prompt),
    ])
    return response.content


if __name__ == "__main__":
    pdfs = list_pdfs()
    if not pdfs:
        print("No PDFs found. Upload PDFs via the Streamlit UI first.")
    else:
        tests = [
            "What is the refund policy?",
            "How long does shipping take?",
            "What personal data do you collect?",
        ]
        for q in tests:
            print(f"\n{'='*60}\nQ: {q}\nA: {query(q)}")