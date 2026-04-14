import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="Customer Support AI",
    page_icon="🤖",
    layout="centered",
)

from agents.rag_agent import save_and_ingest_pdf, delete_pdf, list_pdfs
from agents.router    import route

# ── sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Status")
    st.markdown("---")

    # SQL DB status
    db_ok = Path("data/customers.db").exists()
    col1, col2 = st.columns([1, 3])
    col1.markdown("🗄️")
    if db_ok:
        col2.success("Database ready")
    else:
        col2.error("DB missing — run seed_db.py")

    # PDF uploader
    st.markdown("---")
    st.markdown("**📄 Upload Policy PDFs**")
    uploaded_files = st.file_uploader(
        "Upload PDFs",
        type=["pdf"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    if uploaded_files:
        for uf in uploaded_files:
            if uf.name not in list_pdfs():
                with st.spinner(f"Ingesting {uf.name}..."):
                    msg = save_and_ingest_pdf(uf)
                st.success(msg)
            else:
                st.info(f"'{uf.name}' already loaded.")

    # List loaded PDFs
    pdfs = list_pdfs()
    if pdfs:
        st.markdown(f"**📂 {len(pdfs)} document(s) loaded**")
        for pdf_name in pdfs:
            c1, c2 = st.columns([5, 1])
            c1.markdown(f"📄 `{pdf_name}`")
            if c2.button("🗑️", key=f"del_{pdf_name}"):
                with st.spinner("Removing..."):
                    delete_pdf(pdf_name)
                st.rerun()
    else:
        st.caption("No PDFs uploaded yet.")

    st.markdown("---")
    st.markdown("### 💡 Try asking")
    examples = [
        "Give me Ema's profile and tickets",
        "List all high-priority open tickets",
        "What is the refund policy?",
        "How long does shipping take?",
        "Which customers are on the Pro plan?",
        "Can I return a digital download?",
    ]
    for eq in examples:
        if st.button(eq, use_container_width=True, key=f"ex_{eq}"):
            st.session_state["prefill"] = eq

    st.markdown("---")
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state["messages"] = []
        st.rerun()

# ── main chat ──────────────────────────────────────────────────────────────
st.title("🤖 Customer Support AI")
st.caption("Ask anything — I'll search the right source automatically.")
st.markdown("---")

if not db_ok:
    st.error("⚠️ Database not found. Run `python data/seed_db.py` first.")
    st.stop()

if "messages" not in st.session_state:
    st.session_state["messages"] = []

# render history
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant" and "source" in msg:
            st.caption(f"Answered from: {msg['source']}")
        st.markdown(msg["content"])

# input
prefill    = st.session_state.pop("prefill", None)
user_input = st.chat_input("Ask about a customer, ticket, or company policy...") or prefill

if user_input:
    # show user message
    st.session_state["messages"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # route & respond
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                result   = route(user_input)
                response = result["response"]
                source   = result["source"]
            except Exception as e:
                response = f"⚠️ Error: {e}"
                source   = "Error"
        st.caption(f"Answered from: {source}")
        st.markdown(response)

    st.session_state["messages"].append({
        "role"    : "assistant",
        "content" : response,
        "source"  : source,
    })