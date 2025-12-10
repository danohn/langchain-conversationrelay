"""Shared LangChain agent brain used by both text and voice interfaces."""
import sqlite3
import aiosqlite
from langchain.agents import create_agent
from langchain.tools import tool
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver


@tool
def calculator(expression: str) -> str:
    """Performs arithmetic calculations. Use this for math operations like addition, subtraction, multiplication, and division."""
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return str(result)
    except Exception as e:
        return f"Error calculating: {str(e)}"


TOOLS = [calculator]

SYSTEM_PROMPT = """You are a helpful AI assistant.

When asked to perform calculations, use the calculator tool.

For voice interactions, keep your responses concise and conversational.
For text interactions, you can be more detailed if needed.

Remember conversation context and refer back to previous exchanges when relevant."""

MODEL = "gpt-4o-mini"
DB_PATH = "conversations.db"


def create_shared_agent(db_path: str = DB_PATH):
    """Create and return a LangChain agent with persistent memory (sync)."""
    conn = sqlite3.connect(db_path, check_same_thread=False)
    checkpointer = SqliteSaver(conn)

    agent = create_agent(
        model=MODEL,
        tools=TOOLS,
        system_prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer
    )

    return agent


async def create_shared_agent_async(db_path: str = DB_PATH):
    """Create and return a LangChain agent with persistent memory (async).

    Returns tuple of (agent, connection) so connection can be closed later.
    """
    conn = await aiosqlite.connect(db_path)
    checkpointer = AsyncSqliteSaver(conn)

    agent = create_agent(
        model=MODEL,
        tools=TOOLS,
        system_prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer
    )

    return agent, conn


def get_agent_info():
    """Return information about the current agent configuration."""
    return {
        "model": MODEL,
        "tools": [tool.name for tool in TOOLS],
        "db_path": DB_PATH,
        "num_tools": len(TOOLS)
    }
