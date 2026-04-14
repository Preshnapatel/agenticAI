# 🤖 Customer Support AI — Multi-Agent System

A Generative AI–powered Multi-Agent System that enables natural language interaction
with both structured customer data and unstructured policy documents.

Built with **LangGraph · LangChain · Groq · ChromaDB · Streamlit**

***

## 🏗️ Architecture

```
User Query
    │
    ▼
┌─────────────────────────────────┐
│         Streamlit UI            │
│         (Single Chat)           │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│         Router Agent            │  ← classifies query as sql / rag / both
└──────┬──────────────────┬───────┘
       │                  │
       ▼                  ▼
┌─────────────┐    ┌─────────────┐
│  SQL Agent  │    │  RAG Agent  │
│  LangGraph  │    │  ChromaDB   │
│  SQLite DB  │    │  PDF Docs   │
└─────────────┘    └─────────────┘
       │                  │
       └────────┬─────────┘
                ▼
       ┌─────────────────┐
       │ Synthesizer LLM │  ← merges both answers (when "both")
       └─────────────────┘
```

***

## ✨ Features

- 🔀 **Intelligent Routing** — automatically decides whether to query the database,
  search policy documents, or both
- 🗄️ **SQL Agent** — answers natural language questions about customers and tickets
- 📄 **RAG Agent** — searches uploaded PDF policy documents using semantic similarity
- 🔗 **Multi-Agent Synthesis** — combines answers from both agents into one response
- 📤 **PDF Upload** — upload any policy PDF directly from the UI sidebar
- 🗑️ **PDF Management** — delete documents and auto-rebuild the vector store

***

## 🛠️ Technology Stack

| Layer       | Technology                        |
|-------------|-----------------------------------|
| LLM         | Groq (`llama-3.3-70b-versatile`)  |
| Agents      | LangGraph + LangChain             |
| Vector DB   | ChromaDB                          |
| Embeddings  | HuggingFace `all-MiniLM-L6-v2`   |
| SQL DB      | SQLite + SQLAlchemy               |
| UI          | Streamlit                         |

***

## 📁 Project Structure

```
customer-support-agent/
├── agents/
│   ├── __init__.py
│   ├── sql_agent.py        # LangGraph SQL agent
│   ├── rag_agent.py        # RAG agent with ChromaDB
│   └── router.py           # Query classifier & multi-agent router
├── data/
│   ├── seed_db.py          # Generates synthetic customer + ticket data
│   ├── customers.db        # SQLite database (auto-created, not in repo)
│   └── policies/           # Upload PDFs here (or via UI sidebar)
├── vectorstore/            # ChromaDB store (auto-created, not in repo)
├── app.py                  # Streamlit single-chat UI
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

***

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/Preshnapatel/customer-support-agent.git
cd customer-support-agent
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```
> ⚠️ First run downloads the `all-MiniLM-L6-v2` embedding model (~90MB). One-time only.

### 4. Configure API Key
```bash
cp .env.example .env
```
Open `.env` and add your free Groq API key:
```
GROQ_API_KEY=your-key-here
```
Get a free key at → https://console.groq.com

### 5. Seed the Database
```bash
python data/seed_db.py
```
Creates 51 synthetic customers and ~160 support tickets including a demo customer **"Ema Johnson"**.

### 6. Run the App
```bash
streamlit run app.py
```

### 7. Upload Policy PDFs
- Open the app in your browser
- Use the **sidebar** to upload any PDF policy document
- The RAG agent will automatically ingest and index it

***

## 💬 Example Queries

### Customer Data (SQL Agent)
- *"Give me an overview of customer Ema's profile and past tickets"*
- *"List all open high-priority tickets"*
- *"Which customers are on the Pro plan?"*
- *"Show all billing-related tickets"*

### Policy Documents (RAG Agent)
- *"What is the refund policy?"*
- *"How long does shipping take?"*
- *"Can I return a digital download?"*
- *"What personal data do you collect?"*

### Both Agents Combined
- *"Has Ema had any refund issues and what is our refund policy?"*
- *"Show John's tickets and explain our shipping policy"*

***

## 🔄 How the Router Works

```
Query → Router LLM → "sql" | "rag" | "both"

"both" → SQL Agent ──┐
                     ├──► Synthesizer LLM ──► Unified Answer
         RAG Agent ──┘
```

The router runs both agents **in parallel** using `ThreadPoolExecutor` for speed,
then merges the results with a third LLM synthesis call.

***

## ⚙️ Environment Variables

| Variable       | Description                  | Required |
|----------------|------------------------------|----------|
| `GROQ_API_KEY` | Free API key from Groq       | ✅ Yes   |

***

## 📦 Dependencies

```
langchain · langgraph · langchain-community
langchain-groq · sentence-transformers
chromadb · sqlalchemy · pypdf
streamlit · faker · python-dotenv
```

***

## 📌 Notes

- The `.env` file is excluded from the repo — never commit API keys
- `customers.db` and `vectorstore/` are excluded — generated locally on first run
- PDFs placed in `data/policies/` are auto-ingested on startup
