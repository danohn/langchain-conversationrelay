"""Interactive text-based interface for the LangChain agent."""
import os
import sys
from dotenv import load_dotenv
from agent import create_shared_agent, get_agent_info, DB_PATH

load_dotenv()


def main():
    info = get_agent_info()
    provider = info['provider']

    required_keys = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
    }

    if provider in required_keys and not os.getenv(required_keys[provider]):
        print(f"Error: {required_keys[provider]} not found in .env file")
        print(f"Required for MODEL_PROVIDER={provider}")
        return

    if len(sys.argv) > 1:
        session_id = sys.argv[1]
    else:
        print("Enter a session ID (e.g., 'user123', 'session1', etc.)")
        print("This ID will be used to save and restore your conversation.")
        session_id = input("Session ID: ").strip()
        if not session_id:
            session_id = "default"
        print()

    print(f"Session ID: {session_id}")
    print(f"Conversations saved to: {DB_PATH}")
    print(f"Provider: {info['provider']}, Model: {info['model']}")
    print(f"Available tools: {', '.join(info['tools'])}")

    config = {"configurable": {"thread_id": session_id}}
    agent = create_shared_agent()

    try:
        existing_state = agent.get_state(config)
        if existing_state.values.get("messages"):
            print(f"Restored conversation with {len(existing_state.values['messages'])} previous messages")
        else:
            print("Starting new conversation")
    except:
        print("Starting new conversation")

    print()
    print("="*50)
    print("Interactive Agent - Type 'quit' or 'exit' to end")
    print("Conversations are automatically saved and will be")
    print("restored when you use the same session ID.")
    print("="*50 + "\n")

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() in ["quit", "exit", "q"]:
            print("\nConversation saved! Use the same session ID to continue later.")
            print("Goodbye!")
            break

        if not user_input:
            continue

        result = agent.invoke(
            {"messages": [{"role": "user", "content": user_input}]},
            config=config
        )

        agent_response = result['messages'][-1].content
        print(f"Agent: {agent_response}\n")


if __name__ == "__main__":
    main()
