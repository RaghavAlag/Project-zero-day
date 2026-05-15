from .llm_client import call_groq

async def run_gamma(payload, response, vuln_type, journal, broadcast_fn) -> str:
    context = journal.get_context_string()
    
    prompt = f"""You are Gamma, a deep security reasoning agent.
ATTACK JOURNAL (everything tried so far):
{context}

Failed Payload: {payload}
Response Code: {response['status_code']}
Response Body Snippet: {response['body'][:500]}

Analyze this failed exploit attempt and generate a specific technical critique explaining exactly WHY it failed and what specific technique Beta should try next for {vuln_type}.
Be concrete: name the exact bypass technique. Output only the critique, 2-3 sentences max."""

    messages = [
        {"role": "system", "content": prompt}
    ]
    
    await broadcast_fn("Analyzing failure...", "Gamma", "thinking")
    critique = await call_groq(messages)
    
    await broadcast_fn(f"{critique}", "Gamma", "info")
    return critique
