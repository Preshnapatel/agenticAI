from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()

_llm = None

def get_llm():
    global _llm
    if _llm is None:
        _llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
    return _llm


def classify_query(user_input: str) -> str:
    """
    Returns 'sql', 'rag', or 'both'.
    """
    response = get_llm().invoke([
        SystemMessage(content="""You are a query classifier for a customer support AI system.

Classify the user query into exactly ONE of these three categories:

- sql  → ONLY about customer profiles, support tickets, orders, plans, billing history,
          user accounts — anything stored in a structured database.

- rag  → ONLY about company policies, refund rules, shipping terms, privacy policy,
          return procedures — anything found in policy documents.

- both → The query asks about BOTH customer/ticket data AND company policies at the same time.
          Examples:
            "Has Ema had refund issues and what is the refund policy?"
            "Show me John's tickets and explain our shipping policy"
            "What issues does customer X have and how do we handle them per policy?"

Reply with ONLY one word: sql  OR  rag  OR  both
No explanation. No punctuation."""),
        HumanMessage(content=user_input),
    ])
    label = response.content.strip().lower()
    if "both" in label:
        return "both"
    if "rag" in label:
        return "rag"
    return "sql"


def synthesize(user_input: str, sql_result: str, rag_result: str) -> str:
    """Merge SQL + RAG answers into one unified response."""
    response = get_llm().invoke([
        SystemMessage(content="You are a helpful customer support assistant. "
                              "Combine two data sources into one clear, well-structured answer."),
        HumanMessage(content=f"""The user asked: "{user_input}"

CUSTOMER DATABASE ANSWER:
{sql_result}

POLICY DOCUMENTS ANSWER:
{rag_result}

Your task:
- Combine BOTH answers into a single, unified, well-formatted response.
- Use Markdown — headings, bullet points, tables where helpful.
- First address the customer-specific part, then the policy part.
- Use section headers:
    ## 👤 Customer Information
    ## 📄 Policy Details
- End with a brief ## 💡 Summary that connects both (e.g. whether the customer's issue
  is covered by the policy).
- Be concise and accurate. Do not repeat information."""),
    ])
    return response.content


def route(user_input: str) -> dict:
    """
    Route query to sql, rag, or both agents.
    Returns { 'agent': str, 'response': str, 'source': str }
    """
    from agents.sql_agent import query as sql_query
    from agents.rag_agent import query as rag_query, list_pdfs

    agent = classify_query(user_input)

    # If classified as rag/both but no PDFs uploaded
    if agent in ("rag", "both") and not list_pdfs():
        if agent == "rag":
            return {
                "agent": "rag",
                "response": "⚠️ No policy documents uploaded yet. "
                            "Please upload a PDF using the sidebar.",
                "source": "⚠️ No documents",
            }
        # "both" but no PDFs → fall back to sql only
        agent = "sql"

    if agent == "sql":
        return {
            "agent": "sql",
            "response": sql_query(user_input),
            "source": "🗄️ Customer Database",
        }

    if agent == "rag":
        return {
            "agent": "rag",
            "response": rag_query(user_input),
            "source": "📄 Policy Documents",
        }

    # agent == "both" — run both in parallel then synthesize
    with ThreadPoolExecutor(max_workers=2) as executor:
        sql_future = executor.submit(sql_query, user_input)
        rag_future = executor.submit(rag_query, user_input)
        sql_result = sql_future.result()
        rag_result = rag_future.result()

    combined = synthesize(user_input, sql_result, rag_result)

    return {
        "agent": "both",
        "response": combined,
        "source": "🗄️ Customer Database  +  📄 Policy Documents",
    }