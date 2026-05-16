from .llm_client import call_groq
from tools.web_search import search_exploits
from tools.crawler import crawl_target
import json
import asyncio
import omium

@omium.trace(name="Alpha Recon")
async def run_alpha(target_url, vuln_type, journal, broadcast_fn, trace_context=None) -> dict:
    from tracing import trace_step
    
    await broadcast_fn(f"Initiating reconnaissance on {target_url}...", "Alpha", "thinking")
    
    # ── PHASE 8: INTELLIGENT DISCOVERY (Crawler) ──
    endpoints = await crawl_target(target_url, trace_context)
    if endpoints:
        endpoints_str = json.dumps(endpoints, indent=2)
        await broadcast_fn(f"Discovery complete. Found {len(endpoints)} attack vectors: {', '.join([e['path'] for e in endpoints])}", "Alpha", "info")
    else:
        endpoints_str = "Fallback defaults: /login (POST), /ping (POST)"
        await broadcast_fn("Discovery failed or blocked. Using fallback heuristics.", "Alpha", "warning")
        
    prompt = f"""You are Alpha, an elite reconnaissance agent. 
Target: {target_url}
Vulnerability Class: {vuln_type}

DISCOVERED ATTACK SURFACE:
{endpoints_str}

Generate 3 specific, targeted web search queries to find real PoC payloads and bypass techniques for this exact environment and attack surface. 
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
    for i, query in enumerate(queries):
        if trace_context:
            span_id = trace_step(trace_context["workflow_id"], f"WEB_SEARCH_{i+1}", trace_context["parent_id"], {"query": query}, "running")
            results = await search_exploits(query, broadcast_fn, {"workflow_id": trace_context["workflow_id"], "parent_id": span_id})
            trace_step(trace_context["workflow_id"], f"WEB_SEARCH_{i+1}", trace_context["parent_id"], {"results_count": len(results)}, "success")
        else:
            results = await search_exploits(query, broadcast_fn)
            
        all_results.extend(results)
        await asyncio.sleep(2) # delay between tavily searches
        
    await broadcast_fn(f"Recon complete. Found {len(all_results)} intelligence sources.", "Alpha", "info")
    return {"queries": queries, "results": all_results, "endpoints": endpoints}
