from tavily import TavilyClient
import os
import asyncio
from tracing import trace

@trace(name="Web Search Tool")
async def search_exploits(query: str, broadcast_fn, trace_context=None) -> list[str]:
    await broadcast_fn(f"Searching for — {query}", "Alpha", "info")
    try:
        client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, lambda: client.search(query=query, search_depth="advanced"))
        
        snippets = []
        for res in response.get('results', [])[:5]:
            snippets.append(res['content'])
        return snippets
    except Exception as e:
        await broadcast_fn(f"Search failed — {str(e)}", "Alpha", "error")
        return []
