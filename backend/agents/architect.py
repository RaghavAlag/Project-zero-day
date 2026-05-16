from .llm_client import call_groq
import os
from tracing import trace

@trace(name="Architect Patch Generation")
async def run_architect(target_url, vuln_type, payload, broadcast_fn, trace_context=None) -> str:
    await broadcast_fn("Analyzing vulnerability to design patch...", "Architect", "info")
    
    # Dynamic target selection
    folder = "target_complex" if "5001" in str(target_url) else "target"
    target_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", folder, "app.py"))
    
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

CRITICAL RULE: Output ONLY the raw Python code. NO conversational text. NO explanations. NO markdown formatting. Your entire output must be valid, runnable Python code. If you add English text like "Here is the code", the system will crash."""

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
