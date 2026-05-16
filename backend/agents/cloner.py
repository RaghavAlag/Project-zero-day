import os
import subprocess
import shutil
import time
import re
from tracing import trace
from .llm_client import call_groq

@trace(name="Cloner Agent")
async def run_cloner(repo_url: str, broadcast_fn) -> dict:
    """
    Clones a repo, analyzes it, and starts the server.
    Returns { "port": 5005, "target_url": "http://localhost:5005", "folder": "..." }
    """
    # 1. Clean up old clones
    clones_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "clones"))
    if os.path.exists(clones_dir):
        # We use a unique folder name based on timestamp to avoid lock issues
        pass
    else:
        os.makedirs(clones_dir)

    repo_name = repo_url.split("/")[-1].replace(".git", "")
    timestamp = int(time.time())
    target_folder = os.path.join(clones_dir, f"{repo_name}_{timestamp}")

    await broadcast_fn(f"Cloning repository: {repo_url}...", "Cloner", "thinking")
    
    try:
        subprocess.run(["git", "clone", repo_url, target_folder], check=True, capture_output=True)
    except Exception as e:
        await broadcast_fn(f"Clone failed: {str(e)}", "Cloner", "error")
        return None

    # 2. Analyze the repo to find the start command and ACTUAL PORT
    files = []
    main_file = "app.py"
    for root, _, filenames in os.walk(target_folder):
        for f in filenames:
            if not f.startswith("."):
                files.append(os.path.relpath(os.path.join(root, f), target_folder))
    
    # Surgical port detection: Read app.py if it exists
    detected_port = 5000
    app_path = os.path.join(target_folder, "app.py")
    if os.path.exists(app_path):
        with open(app_path, "r") as f:
            content = f.read()
            # Look for port=5001 or similar
            port_match = re.search(r"port\s*=\s*(\d+)", content)
            if port_match:
                detected_port = int(port_match.group(1))

    await broadcast_fn(f"Analyzing repository structure. Detected entry: {main_file}, Port: {detected_port}", "Cloner", "thinking")
    
    start_cmd = f"python {main_file}"
    hint_port = detected_port

    # 3. Start the server in the background
    await broadcast_fn(f"Launching autonomous sandbox: `{start_cmd}`", "Cloner", "info")
    
    # Surgically kill only the target port, NOT all python processes
    try:
        kill_out = subprocess.check_output(f"netstat -ano | findstr :{hint_port}", shell=True).decode()
        for line in kill_out.split("\n"):
            if "LISTENING" in line:
                pid = line.strip().split()[-1]
                subprocess.run(f"taskkill /PID {pid} /F", shell=True, capture_output=True)
        time.sleep(2)
    except:
        pass

    # Start it
    process = subprocess.Popen(
        start_cmd,
        cwd=target_folder,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Wait for health
    await broadcast_fn(f"Waiting for sandbox at port {hint_port} to stabilize...", "Cloner", "thinking")
    time.sleep(5) 

    return {
        "target_url": f"http://localhost:{hint_port}",
        "folder": target_folder,
        "process_pid": process.pid
    }
