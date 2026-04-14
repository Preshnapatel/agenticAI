from pathlib import Path
from dotenv import load_dotenv

from langchain_community.utilities import SQLDatabase
from langchain_community.tools.sql_database.tool import (
    InfoSQLDatabaseTool,
    ListSQLDatabaseTool,
    QuerySQLDataBaseTool,
)
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage

load_dotenv()

DB_PATH = Path(__file__).parent.parent / "data" / "customers.db"

_agent = None  # module-level cache so Streamlit doesn't re-init on every rerun


def get_agent():
    global _agent
    if _agent is not None:
        return _agent

    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found at {DB_PATH}.\n"
            "Run:  python data/seed_db.py"
        )

    db  = SQLDatabase.from_uri(f"sqlite:///{DB_PATH}")
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

    # Manually select tools — avoids the broken QuerySQLCheckerTool
    tools = [
        ListSQLDatabaseTool(db=db),
        InfoSQLDatabaseTool(db=db),
        QuerySQLDataBaseTool(db=db),
    ]

    system_prompt = """You are a helpful customer support assistant with access to a SQL database.
The database has two tables:
  - customers       : id, name, email, phone, company, plan, country, created_at
  - support_tickets : id, customer_id, title, description, category, status,
                      priority, created_at, resolved_at

When asked about a customer, always:
1. Look up their profile from the customers table.
2. Retrieve all their support tickets by joining on customer_id.
3. Present a clear, concise summary.

Always use SQL to get accurate data. Never guess or make up information."""

    _agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=system_prompt,
    )
    return _agent


def query(user_input: str) -> str:
    """Run the SQL agent and return the final text response."""
    agent    = get_agent()
    result   = agent.invoke({"messages": [HumanMessage(content=user_input)]})
    messages = result.get("messages", [])
    return messages[-1].content if messages else "No response generated."


# ── quick CLI test ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    questions = [
        "How many customers do we have?",
        "Give me a quick overview of customer Ema's profile and past support ticket details.",
        "List all open high-priority tickets.",
    ]
    for q in questions:
        print(f"\n{'='*60}")
        print(f"Q: {q}")
        print(f"A: {query(q)}")