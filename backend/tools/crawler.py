import httpx
from bs4 import BeautifulSoup
from tracing import trace

@trace(name="Web Crawler")
async def crawl_target(target_url: str, trace_context=None) -> list[dict]:
    """
    Crawls the base URL to dynamically discover forms and attack surfaces.
    Returns a list of dictionaries describing the discovered endpoints.
    """
    discovered_endpoints = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ProjectZeroDay/1.0"}
    try:
        async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
            response = await client.get(target_url)
            
            if response.status_code != 200:
                return []
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all forms on the page
            forms = soup.find_all('form')
            for form in forms:
                action = form.get('action', '/')
                method = form.get('method', 'GET').upper()
                
                # Extract input fields to understand what the form expects
                inputs = []
                for input_tag in form.find_all('input'):
                    input_name = input_tag.get('name')
                    if input_name:
                        inputs.append(input_name)
                
                endpoint_info = {
                    "path": action,
                    "method": method,
                    "inputs": inputs,
                    "type": "form_submission"
                }
                discovered_endpoints.append(endpoint_info)
                
            return discovered_endpoints
            
    except Exception as e:
        print(f"Crawler error: {e}")
        return []
