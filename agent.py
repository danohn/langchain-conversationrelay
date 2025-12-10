"""Shared LangChain agent brain used by both text and voice interfaces."""
import os
import sqlite3
import aiosqlite
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_ollama import ChatOllama
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

MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "openai")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
DB_PATH = "conversations.db"


def get_model():
    """Get configured model instance based on environment variables.

    Returns:
        Configured LLM instance (ChatOpenAI, ChatAnthropic, or ChatOllama)

    Raises:
        ValueError: If MODEL_PROVIDER is not supported
    """
    if MODEL_PROVIDER == "openai":
        return ChatOpenAI(model=MODEL_NAME)
    elif MODEL_PROVIDER == "anthropic":
        return ChatAnthropic(model=MODEL_NAME)
    elif MODEL_PROVIDER == "ollama":
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        return ChatOllama(model=MODEL_NAME, base_url=base_url)
    else:
        raise ValueError(
            f"Unknown MODEL_PROVIDER: {MODEL_PROVIDER}. "
            f"Supported providers: openai, anthropic, ollama"
        )


def create_shared_agent(db_path: str = DB_PATH):
    """Create and return a LangChain agent with persistent memory (sync)."""
    conn = sqlite3.connect(db_path, check_same_thread=False)
    checkpointer = SqliteSaver(conn)

    agent = create_agent(
        model=get_model(),
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
        model=get_model(),
        tools=TOOLS,
        system_prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer
    )

    return agent, conn


def get_agent_info():
    """Return information about the current agent configuration."""
    return {
        "provider": MODEL_PROVIDER,
        "model": MODEL_NAME,
        "tools": [tool.name for tool in TOOLS],
        "db_path": DB_PATH,
        "num_tools": len(TOOLS)
    }
