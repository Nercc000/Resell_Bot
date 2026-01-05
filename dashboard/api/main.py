import asyncio
import os
import signal
from typing import List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://45.147.7.54.nip.io",
        "http://45.147.7.54.nip.io"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
bot_process: Optional[asyncio.subprocess.Process] = None
active_websockets: List[WebSocket] = []

class BotStatus(BaseModel):
    status: str  # idle, running
    pid: int | None = None

@app.get("/api/bot/status", response_model=BotStatus)
async def get_status():
    global bot_process
    if bot_process and bot_process.returncode is None:
        return BotStatus(status="running", pid=bot_process.pid)
    return BotStatus(status="idle")

class StartRequest(BaseModel):
    mode: str = "full"

@app.post("/api/bot/start")
async def start_bot(request: Optional[StartRequest] = None):
    print(f"👉 API: START REQUEST RECEIVED ({request.mode if request else 'full'})", flush=True)
    global bot_process
    
    # Aggressives Cleanup (Nur den Bot killen, nicht die API!)
    # Wir suchen spezifisch nach "python3 -u main.py" um nicht dashboard/api/main.py zu treffen
    os.system("pkill -f 'python3 -u main.py'")
    os.system("pkill -f 'sender.py'")
    os.system("pkill -f 'scraper.py'")
    
    if bot_process and bot_process.returncode is None:
        # Sollte durch pkill eigentlich eh weg sein
        bot_process = None
    
    mode = request.mode if request else "full"
    
    if mode == "debug":
        # Rufe das minimale Debug-Script direkt auf
        cmd = "python3 -u simple_debug.py"
    else:
        # Normaler Modus via main.py
        cmd = f"python3 -u main.py --mode {mode}"
    
    cwd = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    cwd = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    
    # Use start_new_session=True effectively does setsid()
    bot_process = await asyncio.create_subprocess_shell(
        cmd,
        cwd=cwd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        start_new_session=True
    )
    
    # Start background task to read logs
    asyncio.create_task(read_logs())
    
    return {"status": "started", "pid": bot_process.pid, "mode": mode}

@app.post("/api/bot/stop")
async def stop_bot():
    global bot_process
    if bot_process and bot_process.returncode is None:
        try:
            # Kill the entire process group
            os.killpg(os.getpgid(bot_process.pid), signal.SIGTERM)
            try:
                await asyncio.wait_for(bot_process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                 os.killpg(os.getpgid(bot_process.pid), signal.SIGKILL)
        except ProcessLookupError:
            pass # Already dead
        except Exception as e:
            await broadcast_log(f"Error stopping bot: {e}")
            
        await broadcast_log("🛑 Bot wurde vom Benutzer gestoppt.")
        return {"status": "stopped"}
    return {"status": "not_running"}

@app.websocket("/api/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_websockets.append(websocket)
    try:
        while True:
            await websocket.receive_text() # Keep connection alive
    except WebSocketDisconnect:
        active_websockets.remove(websocket)

async def read_logs():
    global bot_process
    if not bot_process or not bot_process.stdout:
        return
        
    # Read line by line asynchronously
    try:
        while True:
            line = await bot_process.stdout.readline()
            if not line:
                break
            
            text = line.decode().strip()
            # Filter unwanted logs
            if "Ignoring unsupported entryTypes" in text:
                continue

            await broadcast_log(text)
            # Yield control to event loop just in case
            await asyncio.sleep(0.01)
    except Exception as e:
        await broadcast_log(f"Error reading logs: {e}")
        
    try:
        return_code = await bot_process.wait()
        await broadcast_log(f"Process finished with exit code {return_code}")
    except Exception:
        pass

async def broadcast_log(message: str):
    if not message:
        return
    # Copy list to avoid concurrent modification issues
    for connection in list(active_websockets):
        try:
            await connection.send_json({"message": message})
        except:
            # If sending fails, we might want to remove the closed socket
            if connection in active_websockets:
                try:
                    active_websockets.remove(connection)
                except ValueError:
                    pass

@app.post("/api/config")
async def update_config(config: dict):
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.env"))
    
    # Read existing
    existing = {}
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                if "=" in line:
                    key, val = line.strip().split("=", 1)
                    existing[key] = val
    
    # Update
    existing.update(config)
    
    # Write back
    with open(env_path, "w") as f:
        for key, val in existing.items():
            f.write(f"{key}={val}\n")
            
    return {"status": "updated"}

@app.get("/api/config")
async def get_config():
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.env"))
    config = {}
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                if "=" in line:
                    key, val = line.strip().split("=", 1)
                    config[key] = val
    return config

import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except: pass

@app.get("/api/stats")
async def get_stats():
    stats = {
        "scraped": 0,
        "ai_filtered": 0,
        "sent": 0,
        "error": 0
    }
    
    if supabase:
        try:
            # Scraped / AI Filtered (In listings table)
            res = supabase.table("listings").select("id", count="exact").execute()
            stats["scraped"] = res.count
            stats["ai_filtered"] = res.count # Currently we save all AI validated listings
            
            # Sent / Error (In sent_messages table)
            res_sent = supabase.table("sent_messages").select("id", count="exact").eq("status", "sent").execute()
            stats["sent"] = res_sent.count
            
            res_error = supabase.table("sent_messages").select("id", count="exact").eq("status", "failed").execute()
            stats["error"] = res_error.count
            
            return stats
        except Exception as e:
            print(f"DB Stats Error: {e}")
            # Fallback to local files if DB fails
            pass

    # Fallback: Local JSON Files
    cwd = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    try:
        if os.path.exists(os.path.join(cwd, "ready_to_send.json")):
            with open(os.path.join(cwd, "ready_to_send.json"), "r") as f:
                data = json.load(f)
                stats["ai_filtered"] = len(data.get("listings", []))
    except: pass

    try:
        if os.path.exists(os.path.join(cwd, "sent_messages.json")):
            with open(os.path.join(cwd, "sent_messages.json"), "r") as f:
                data = json.load(f)
                listings = data.get("listings", [])
                stats["sent"] = sum(1 for l in listings if l.get("sent"))
                stats["error"] = sum(1 for l in listings if not l.get("sent"))
    except: pass
    
    return stats

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

