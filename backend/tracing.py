import os
import uuid
import omium
from dotenv import load_dotenv

load_dotenv()
print("[DEBUG] Tracing module loading...", flush=True)

# Initialize Omium SDK natively
try:
    api_key = os.getenv("OMIUM_API_KEY")
    print(f"[DEBUG] OMIUM_API_KEY found: {bool(api_key)}", flush=True)
    if api_key:
        print(f"[DEBUG] Initializing Omium with key: {api_key[:10]}...", flush=True)
        omium.init(api_key=api_key, project="project-zero-day", auto_trace=True)
        print("[OMIUM] SDK Initialized successfully.", flush=True)
    else:
        print("[DEBUG] OMIUM_API_KEY is missing from environment!", flush=True)
except Exception as e:
    print(f"[OMIUM] Failed to initialize SDK: {e}", flush=True)

# Keep the mock functions to prevent breaking orchestrator logic,
# but we will rely on native @omium.trace decorators for actual dashboard visibility.
def start_workflow(name):
    workflow_id = str(uuid.uuid4())
    print(f"[OMIUM MOCK] Started workflow {name}: {workflow_id}")
    return workflow_id

def trace_step(workflow_id, step_name, parent_id, data, status):
    span_id = str(uuid.uuid4())
    print(f"[OMIUM MOCK] Span: {step_name} (Status: {status})")
    return span_id

def end_workflow(workflow_id, outcome):
    print(f"[OMIUM MOCK] Ended workflow {workflow_id} with outcome: {outcome}")

# Export the native decorator for easy use
trace = omium.trace

