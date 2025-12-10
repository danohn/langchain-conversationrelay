"""Twilio ConversationRelay server with LangChain agent integration."""
import os
import json
from typing import Dict
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import Response
from agent import create_shared_agent, get_agent_info

load_dotenv()

app = FastAPI(title="ConversationRelay Voice Agent")
active_sessions: Dict[str, dict] = {}


@app.get("/")
async def root():
    """Health check endpoint."""
    info = get_agent_info()
    return {
        "status": "ok",
        "service": "ConversationRelay Voice Agent",
        "agent_info": info
    }


@app.post("/twiml")
async def twiml_endpoint(request: Request):
    """Returns TwiML with ConversationRelay configuration."""
    base_url = str(request.base_url).rstrip('/')
    ws_url = base_url.replace("http://", "wss://").replace("https://", "wss://")
    ws_url = f"{ws_url}/ws"

    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <ConversationRelay
            url="{ws_url}"
            welcomeGreeting="Hello! I'm your AI assistant. How can I help you today?"
            language="en-US"
            voice="Polly.Joanna-Neural"
            dtmfDetection="true" />
    </Connect>
</Response>"""

    return Response(content=twiml, media_type="application/xml")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for ConversationRelay."""
    await websocket.accept()

    session_data = {
        "call_sid": None,
        "session_id": None,
        "agent": None,
        "config": None
    }

    try:
        async for message in websocket.iter_text():
            data = json.loads(message)
            msg_type = data.get("type")

            print(f"Received message type: {msg_type}")

            if msg_type == "setup":
                session_data["call_sid"] = data.get("callSid")
                session_data["session_id"] = data.get("sessionId")

                thread_id = session_data["call_sid"]
                session_data["config"] = {"configurable": {"thread_id": thread_id}}
                session_data["agent"] = create_shared_agent()

                print(f"Setup complete - CallSid: {session_data['call_sid']}, SessionId: {session_data['session_id']}")
                active_sessions[session_data["session_id"]] = session_data

            elif msg_type == "prompt":
                voice_prompt = data.get("voicePrompt", "")
                print(f"User said: {voice_prompt}")

                if not voice_prompt.strip():
                    continue

                agent = session_data["agent"]
                config = session_data["config"]

                if agent and config:
                    result = agent.invoke(
                        {"messages": [{"role": "user", "content": voice_prompt}]},
                        config=config
                    )

                    agent_response = result['messages'][-1].content
                    print(f"Agent response: {agent_response}")

                    response_message = {
                        "type": "text",
                        "token": agent_response,
                        "last": True
                    }

                    await websocket.send_text(json.dumps(response_message))

            elif msg_type == "interrupt":
                print(f"User interrupted with: {data.get('utteranceUntilInterrupt', '')}")

            elif msg_type == "dtmf":
                digit = data.get("digit", "")
                print(f"User pressed: {digit}")

            elif msg_type == "error":
                error_desc = data.get("description", "Unknown error")
                print(f"ConversationRelay error: {error_desc}")

    except WebSocketDisconnect:
        print(f"WebSocket disconnected for session: {session_data.get('session_id', 'unknown')}")

        if session_data.get("session_id") in active_sessions:
            del active_sessions[session_data["session_id"]]

    except Exception as e:
        print(f"Error in WebSocket handler: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import uvicorn

    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not found in .env file")
        exit(1)

    info = get_agent_info()
    print("Starting ConversationRelay Voice Agent Server...")
    print(f"Agent Model: {info['model']}")
    print(f"Available Tools: {', '.join(info['tools'])}")
    print("\nEndpoints:")
    print("  - Health check: http://localhost:8000/")
    print("  - TwiML: http://localhost:8000/twiml")
    print("  - WebSocket: ws://localhost:8000/ws")
    print("\nNote: For production, expose this server with a public URL (ngrok, etc.)")

    uvicorn.run(app, host="0.0.0.0", port=8000)
