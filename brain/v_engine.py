"""
V Engine — The central nervous system.
FastAPI server with WebSocket for the 3D orb UI + voice processing pipeline.
"""
import asyncio
import json
import os
import sys
import queue
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Add brain directory to path for local imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from system_tools import SystemTools
from ai_brain import AIBrain
from voice_io import VoiceIO

# --- Global State ---
transcript_queue = queue.Queue()  # Thread-safe: voice thread → async processing
ws_clients: set = set()
current_state = {"state": "idle", "text": "V is booting up..."}
processing_lock = asyncio.Lock() if hasattr(asyncio, 'Lock') else None

# --- Components (initialized in lifespan) ---
tools: SystemTools = None
brain: AIBrain = None
voice: VoiceIO = None


async def broadcast(state: str, text: str = ""):
    """Broadcast state update to all connected WebSocket clients."""
    current_state["state"] = state
    if text:
        current_state["text"] = text
    msg = json.dumps({"type": "state", **current_state})
    dead = set()
    for ws in ws_clients.copy():
        try:
            await ws.send_text(msg)
        except Exception:
            dead.add(ws)
    ws_clients.difference_update(dead)


async def process_transcript(text: str):
    """Full pipeline: think → execute tools → speak → idle."""
    global processing_lock
    if processing_lock is None:
        processing_lock = asyncio.Lock()
    
    async with processing_lock:  # Prevent concurrent processing
        try:
            # Phase 1: Thinking
            print(f"[V-Engine] Thinking about: {text}")
            await broadcast("thinking", f"Soch raha hoon: {text[:60]}...")
            
            # Phase 2: AI Processing (blocking call, run in executor)
            loop = asyncio.get_event_loop()
            response_text, tools_used = await loop.run_in_executor(None, brain.process, text)
            
            # Phase 3: Tool Execution feedback
            if tools_used:
                tool_names = ', '.join(tools_used)
                await broadcast("executing", f"Running: {tool_names}")
                await asyncio.sleep(0.5)
            
            # Phase 4: Speaking
            print(f"[V-Voice] Speaking: {response_text}")
            await broadcast("speaking", response_text[:100])
            await voice.speak(response_text)
            
            # Phase 5: Back to idle
            await broadcast("idle", "Ready for next command, Boss...")
            
        except Exception as e:
            print(f"[V-Engine] Processing error: {e}")
            await broadcast("idle", f"Error: {str(e)[:80]}")


async def transcript_poller():
    """Continuously polls the thread-safe queue for new voice transcripts."""
    while True:
        try:
            text = transcript_queue.get_nowait()
            await process_transcript(text)
        except queue.Empty:
            await asyncio.sleep(0.15)
        except Exception as e:
            print(f"[V-Engine] Poller error: {e}")
            await asyncio.sleep(1)


def on_voice_transcript(text: str):
    """Callback from voice listener — puts transcript in queue."""
    transcript_queue.put(text)


@asynccontextmanager
async def lifespan(app):
    """Initialize all V components on startup."""
    global tools, brain, voice, processing_lock
    
    print("="*50)
    print("    V — Autonomous AI Assistant")
    print("    Initializing all systems...")
    print("="*50)
    
    processing_lock = asyncio.Lock()
    
    # Initialize components
    tools = SystemTools()
    print("[V] ✅ System Tools ready.")
    
    brain = AIBrain(system_tools=tools)
    print("[V] ✅ AI Brain ready (Groq).")
    
    voice = VoiceIO(on_transcript=on_voice_transcript)
    voice.start_listening()
    print("[V] ✅ Voice I/O ready.")
    
    # Start transcript poller as async task
    poller_task = asyncio.create_task(transcript_poller())
    
    print("="*50)
    print("    V IS ONLINE. All systems nominal.")
    print("    Listening for voice commands...")
    print("="*50)
    
    yield
    
    # Cleanup
    poller_task.cancel()
    voice.stop()
    print("[V] Shutting down...")


# --- FastAPI App ---
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def serve_orb():
    """Serve the 3D orb HTML interface."""
    orb_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'orb', 'index.html')
    return FileResponse(os.path.abspath(orb_path))


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for the 3D orb frontend."""
    await websocket.accept()
    ws_clients.add(websocket)
    
    # Send current state immediately
    await websocket.send_text(json.dumps({"type": "state", **current_state}))
    
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                # Handle text input from frontend (fallback for when mic doesn't work)
                if msg.get("type") == "text_input" and msg.get("text"):
                    await process_transcript(msg["text"])
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        ws_clients.discard(websocket)
    except Exception:
        ws_clients.discard(websocket)


# Also keep the old REST endpoint for backward compatibility
@app.post("/v1/brain/process")
async def rest_process(request_data: dict):
    """REST endpoint for backward compatibility with WhatsApp/old dashboard."""
    message = request_data.get("message", "")
    source = request_data.get("source", "api")
    
    if not message:
        return {"status": "error", "response": "No message provided."}
    
    try:
        response_text, tools_used = brain.process(message)
        
        # If from voice source, also speak
        if source == "voice" and voice:
            await voice.speak(response_text)
        
        return {"status": "success", "response": response_text, "tools_used": tools_used}
    except Exception as e:
        return {"status": "error", "response": f"Error: {str(e)}"}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8888, log_level="info")
