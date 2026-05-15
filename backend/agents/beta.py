from .llm_client import call_groq
from tools.http_exploit import fire_payload

async def run_beta(target_url, vuln_type, alpha_results, journal, broadcast_fn) -> dict:
    context = journal.get_context_string()
    recon_data = "\n".join(alpha_results)
    
    prompt = f"""You are Beta, the Striker agent.
ATTACK JOURNAL (everything tried so far — do NOT repeat any of these):
{context}

RECON INTELLIGENCE:
{recon_data[:4000]}

Your task: Based on the recon intelligence and the attack journal showing what has ALREADY FAILED, generate exactly ONE new payload to try for {vuln_type}.
The payload must be meaningfully different from all failed attempts. 
Output ONLY the raw payload string, nothing else — no explanation, no quotes, just the payload."""

    messages = [
        {"role": "system", "content": prompt}
    ]
    
    await broadcast_fn("Analyzing intelligence and designing payload...", "Beta", "thinking")
    payload = await call_groq(messages)
    payload = payload.strip().strip('"').strip("'")
    
    await broadcast_fn(f"Firing payload → {payload}", "Beta", "info")
    response = await fire_payload(target_url, vuln_type, payload)
    
    await broadcast_fn(f"Response received — Status {response['status_code']}", "Beta", "info")
    return {"payload": payload, "response": response}
