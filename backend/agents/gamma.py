from .llm_client import call_groq
from tracing import trace

@trace(name="Gamma Critique")
async def run_gamma(payload, response, vuln_type, journal, broadcast_fn, trace_context=None) -> str:
    context = journal.get_context_string()
    
    prompt = f"""You are Gamma, a deep security reasoning agent.
TARGET CONTEXT:
- SQLi: Post request to login. Payload injected into 'username'.
- CMDi: Post request to ping. Payload injected into 'host'.

Failed Payload: {payload}
Response Code: {response['status_code']}
Response Body Snippet: {response['body'][:500]}

Analyze why this payload failed to breach the {vuln_type} vulnerability. 
CRITICAL RULE: If the Response Body contains an SQL "syntax error" or "unrecognized token", it means the payload failed to "break out" of the application's string literal. You MUST explicitly tell Beta: "You are trapped inside a string. Start your next payload with a leading quote (e.g., ' ) to break out of the query structure."
Output only the technical critique, 2 sentences max."""

    messages = [
        {"role": "system", "content": prompt}
    ]
    
    await broadcast_fn("Analyzing failure...", "Gamma", "thinking")
    critique = await call_groq(messages)
    
    await broadcast_fn(f"{critique}", "Gamma", "info")
    return critique
