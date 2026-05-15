from fastapi import FastAPI, WebSocket, BackgroundTasks, Request, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import os
import datetime
import uuid
import json
from dotenv import load_dotenv

from journal import AttackJournal
import orchestrator

load_dotenv()

app = FastAPI()

# Enable CORS for localhost:5173
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

journal = AttackJournal()
scan_status = "idle"

active_connections = []

async def send_update(message: str, agent: str, level: str):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    update = {
        "agent": agent,
        "message": message,
        "level": level,
        "timestamp": timestamp
    }
    
    global scan_status
    if level == "breach":
        scan_status = "breached"
    elif message == "Red Swarm exhausted all attempts. Target hardened or scope exceeded.":
        scan_status = "failed"

    dead_connections = []
    for connection in active_connections:
        try:
            await connection.send_text(json.dumps(update))
        except Exception:
            dead_connections.append(connection)
            
    for dc in dead_connections:
        active_connections.remove(dc)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in active_connections:
            active_connections.remove(websocket)

@app.post("/scan")
async def scan_endpoint(request: Request, background_tasks: BackgroundTasks):
    global scan_status
    data = await request.json()
    target_url = data.get("target_url")
    vuln_type = data.get("vuln_type")
    
    scan_id = str(uuid.uuid4())
    scan_status = "running"
    
    background_tasks.add_task(orchestrator.run_scan, target_url, vuln_type, send_update, journal)
    
    return {"status": "started", "scan_id": scan_id}

@app.post("/webhook/github")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    # Verify push event via headers (simplified for phase 2)
    event_type = request.headers.get("x-github-event")
    if event_type != "push":
        return {"status": "ignored", "reason": "not a push event"}
        
    target_url = os.getenv("TARGET_URL", "http://localhost:5000")
    vuln_type = "sqli"
    
    global scan_status
    scan_status = "running"
    
    background_tasks.add_task(orchestrator.run_scan, target_url, vuln_type, send_update, journal)
    return {"status": "started"}

@app.get("/journal")
async def get_journal():
    return journal.entries

@app.get("/status")
async def get_status():
    global scan_status
    return {"status": scan_status}
