from .llm_client import call_groq
import os
from tracing import trace

@trace(name="Architect Patch Generation")
async def run_architect(vuln_type, payload, broadcast_fn, trace_context=None) -> str:
    await broadcast_fn("Analyzing vulnerability to design patch...", "Architect", "info")
    
    # Read vulnerable code
    target_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "target", "app.py"))
    with open(target_path, "r") as f:
        code = f.read()
        
    prompt = f"""You are the Architect, an elite secure coding agent.
The Red Swarm just breached our app.py using this {vuln_type} payload:
{payload}

VULNERABLE SOURCE CODE:
```python
{code}
```

Your task: Rewrite the source code to perfectly patch this vulnerability.
- If it's SQLi, use parameterized queries (e.g., `execute("SELECT ... WHERE username=?", (username,))`).
- If it's CMDi, use proper input validation and the `subprocess` module with a list of arguments.
- IMPORTANT: Ensure ALL necessary imports (flask, sqlite3, os, subprocess, database) are at the VERY TOP of the file.
Output ONLY the raw Python code for the completely patched app.py. Do not include markdown formatting."""

    messages = [{"role": "system", "content": prompt}]
    
    await broadcast_fn("Writing secure patch...", "Architect", "thinking")
    patched_code = await call_groq(messages)
    
    # Clean up markdown if any
    patched_code = patched_code.replace("```python", "").replace("```", "").strip()
    
    # Write the patch
    with open(target_path, "w") as f:
        f.write(patched_code)
        
    await broadcast_fn("Patch applied to target/app.py", "Architect", "info")
    return patched_code
