# LangChain & Twilio ConversationRelay - Agentic Voice AI Demo

A Python project demonstrating agentic AI with LangChain 1.x and Twilio ConversationRelay for voice interactions.

## Setup

1. **Python Version**: Python 3.14+ (using `uv` for dependency management)

2. **Install Dependencies**:
   ```bash
   uv sync
   ```

3. **Configure Environment Variables**:
   - Copy the example environment file:
     ```bash
     cp .env.example .env
     ```
   - Update `.env` with your actual API keys:
     - **Required**: `OPENAI_API_KEY` - Get from [platform.openai.com](https://platform.openai.com/api-keys)
     - **Optional**: `LANGSMITH_API_KEY` - Get from [smith.langchain.com](https://smith.langchain.com)

4. **Enable LangSmith Tracing (Optional)**:
   - Sign up at [smith.langchain.com](https://smith.langchain.com)
   - Get your API key from Settings
   - Update `LANGSMITH_API_KEY` in `.env`
   - View traces at [smith.langchain.com](https://smith.langchain.com) to see:
     - Complete conversation flows
     - Token usage and costs
     - Latency for each step
     - Tool invocations (calculator calls)
     - LLM prompts and responses

## Current Features

### 1. Interactive Calculator Agent with Persistent Memory (text_agent.py)

An interactive LangChain agent with a calculator tool that demonstrates:
- Agent creation with LangChain 1.x
- Custom tool definition using the `@tool` decorator
- Tool binding and automatic invocation
- **Conversation memory** - remembers context across multiple exchanges
- **Persistent storage** - saves conversations to SQLite and restores them by session ID
- **LangSmith tracing** - full observability of agent behavior (optional)

**Run the demo**:
```bash
# Start with a session ID
uv run text_agent.py user123

# Or run without arguments and enter a session ID when prompted
uv run text_agent.py
```

**Example interaction**:
```
Session 1:
You: what is 5+3
Agent: 8
You: exit

Session 2 (later, same ID):
You: what was my last result?
Agent: Your last result was 8.
You: multiply that by 2
Agent: 16
```

The agent:
- Maintains conversation state automatically within a session
- Saves all conversations to `conversations.db` SQLite database
- Restores previous conversations when you use the same session ID
- Allows multiple users/sessions with different IDs

### 2. Voice Agent with Twilio ConversationRelay (voice_agent.py)

A production-ready voice agent server that handles phone calls using Twilio ConversationRelay:
- **WebSocket server** for real-time bidirectional communication with Twilio
- **Speech-to-text** and **text-to-speech** handled automatically by ConversationRelay
- **Streaming responses** - tokens sent as generated for reduced latency
- **Cross-call memory** - remembers conversations across calls from the same phone number
- **Twilio helper library** - uses Python SDK for TwiML generation
- **LangChain agent integration** - same calculator tool, voice-optimized responses
- **LangSmith tracing** - full observability of voice interactions (optional)

**Run the server**:
```bash
uv run voice_agent.py
```

**Endpoints**:
- Health check: `http://localhost:8000/`
- TwiML: `http://localhost:8000/twiml`
- WebSocket: `ws://localhost:8000/ws`

**Setup for Twilio**:

1. **Expose your local server publicly** (required for Twilio to reach it):
   ```bash
   # Using ngrok (install from ngrok.com)
   ngrok http 8000
   ```
   Copy the ngrok HTTPS URL (e.g., `https://abc123.ngrok.io`)

2. **Configure Twilio Phone Number**:
   - Go to [Twilio Console](https://console.twilio.com/)
   - Select your phone number
   - Under "Voice Configuration":
     - Set "A CALL COMES IN" to "Webhook"
     - Enter: `https://your-ngrok-url.ngrok.io/twiml`
     - Method: `HTTP POST`
   - Save

3. **Test the voice agent**:
   - **First call**: "My name is Daniel. What is 10 plus 5?"
   - Agent responds: "15"
   - Hang up
   - **Second call** (from same number): "What's my name?"
   - Agent responds: "Your name is Daniel!"
   - Memory persists across calls from the same phone number!

**How it works**:
- Twilio receives the call → sends POST to `/twiml` with `From` parameter (caller's phone number)
- TwiML endpoint adds phone number as custom parameter to ConversationRelay
- WebSocket receives setup message with custom parameters
- Uses phone number as `thread_id` for persistent memory (not Call SID)
- Conversation history is saved and restored based on caller's phone number
- Each caller has their own persistent conversation thread

## Project Structure

```
.
├── agent.py             # Shared "brain" - agent config, tools, prompts
├── text_agent.py        # Interactive text-based interface (CLI)
├── voice_agent.py       # Voice interface (ConversationRelay WebSocket)
├── pyproject.toml       # Project dependencies (uv)
├── .env.example         # Environment variables template (committed)
├── .env                 # Your actual API keys (not in git)
├── conversations.db     # SQLite database (auto-generated, not in git)
└── README.md           # This file
```

### Key Files

**agent.py** - The shared "brain"
- Contains all tool definitions (currently: calculator)
- Agent configuration (model, system prompt, etc.)
- `create_shared_agent()` - Creates configured agent (sync, for text interface)
- `create_shared_agent_async()` - Creates configured agent (async, for voice interface with streaming)
- `get_agent_info()` - Returns agent metadata

**text_agent.py** - Text interface
- Imports `create_shared_agent()` from agent.py
- Provides CLI for text-based interaction
- Session management via command-line arguments

**voice_agent.py** - Voice interface
- Imports `create_shared_agent_async()` from agent.py
- FastAPI server with WebSocket endpoint
- Integrates with Twilio ConversationRelay
- Uses async streaming for low-latency responses
- Phone number-based session management for cross-call memory

## Dependencies

- `langchain` (1.x) - LangChain framework
- `langchain-openai` - OpenAI integration
- `langchain-anthropic` - Anthropic Claude integration
- `langgraph-checkpoint-sqlite` - SQLite-based conversation persistence
- `aiosqlite` - Async SQLite database operations for streaming
- `fastapi` - Web framework for HTTP and WebSocket server
- `uvicorn` - ASGI server for running FastAPI
- `websockets` - WebSocket protocol implementation
- `python-multipart` - Form data parsing for FastAPI
- `twilio` - Twilio SDK for ConversationRelay
- `python-dotenv` - Environment variable management

## Architecture

### Shared Brain Architecture
```
                    agent.py (Shared Brain)
                    ├── Tools (calculator, etc.)
                    ├── System Prompt
                    ├── Model Config
                    └── create_shared_agent()
                            ↓
        ┌───────────────────┴───────────────────┐
        ↓                                       ↓
   text_agent.py (Text)                  voice_agent.py (Voice)
    CLI Interface                         WebSocket Server
        ↓                                       ↓
    User Types                            User Speaks
        ↓                                       ↓
    Agent Responds                        Agent Responds
        ↓                                       ↓
        └───────────────────┬───────────────────┘
                            ↓
                SQLite Persistence
            (conversations.db)
```

### Text Agent Flow (text_agent.py)
```
User Input → create_shared_agent() → Tool (Calculator) → Response → User
                                          ↓
                              SQLite Persistence (by session_id)
```

### Voice Agent Flow (voice_agent.py)
```
Phone Call → Twilio → TwiML Endpoint (extracts From: phone number)
                         ↓
         WebSocket Connection + custom parameter (caller_phone)
                         ↓
    ConversationRelay ← → FastAPI Server
    (STT/TTS)              ↓
                    create_shared_agent() → Tools
                         ↓
                SQLite Persistence (by phone number - persists across calls)
```

## Adding New Tools

To add a new tool that works in both text and voice interfaces:

1. **Edit `agent.py`** - Add your tool definition:
   ```python
   @tool
   def get_weather(city: str) -> str:
       """Get weather information for a city."""
       # Your implementation here
       return f"Weather in {city}: Sunny, 72°F"
   ```

2. **Add to TOOLS list** in `agent.py`:
   ```python
   TOOLS = [
       calculator,
       get_weather,  # Add your new tool here
   ]
   ```

3. **That's it!** Both `text_agent.py` and `voice_agent.py` will automatically have access to the new tool.

No need to modify `text_agent.py` or `voice_agent.py` - they both use `create_shared_agent()` which includes all tools defined in `agent.py`.

## Next Steps

- [x] Add conversation memory and context tracking
- [x] Add persistent memory with SQLite checkpointing
- [x] Integrate Twilio ConversationRelay WebSocket server
- [x] Refactor to shared "brain" architecture
- [x] Implement streaming responses for lower latency
- [x] Cross-call memory using phone number identification
- [ ] Add more sophisticated tools for the agent
- [ ] Add support for multiple LLM providers (Claude, etc.)
