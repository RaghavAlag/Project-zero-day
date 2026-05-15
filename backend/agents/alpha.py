from .llm_client import call_groq
from tools.web_search import search_exploits
import json
import asyncio

async def run_alpha(target_url, vuln_type, journal, broadcast_fn) -> dict:
    await broadcast_fn(f"Initiating recon for {vuln_type} on {target_url}", "Alpha", "info")
    
    prompt = f"""You are Alpha, an elite reconnaissance agent. 
Target: {target_url}
Vulnerability: {vuln_type}

Generate 3 specific, targeted web search queries to find real PoC payloads and bypass techniques for this exact environment. 
Output ONLY a JSON object with a single key 'queries' containing an array of 3 search query strings."""
    messages = [
        {"role": "system", "content": prompt}
    ]
    
    try:
        response = await call_groq(messages, json_mode=True)
        data = json.loads(response)
        queries = data.get("queries", [])
    except Exception as e:
        queries = [f"{vuln_type} bypass payload"]
        
    all_results = []
    for query in queries:
        results = await search_exploits(query, broadcast_fn)
        all_results.extend(results)
        await asyncio.sleep(2) # delay between tavily searches
        
    await broadcast_fn(f"Recon complete. Found {len(all_results)} intelligence sources.", "Alpha", "info")
    return {"queries": queries, "results": all_results}
