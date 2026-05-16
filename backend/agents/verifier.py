import asyncio
import os
import subprocess
import time
import httpx
from tracing import trace

TARGET_APP_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "target", "app.py")
)

from .llm_client import call_groq

async def ai_security_audit(code: str, vuln_type: str, payload: str) -> tuple[bool, str]:
    """
    Uses an LLM to perform a professional security audit on the patched code.
    Returns (is_secure, audit_report).
    """
    prompt = f"""You are a Senior Application Security Engineer.
Your task is to audit the following source code to determine if it is vulnerable to {vuln_type}.
The attacker previously breached the system using this payload: `{payload}`.

SOURCE CODE:
```python
{code}
```


EVALUATION CRITERIA:
- For SQLi: Look for string concatenation (e.g., `query = "..." + input`). This is VULNERABLE. If the code uses parameterized queries (e.g., `query = "...?"` and `execute(query, (input,))`), this is 100% SECURE. You MUST return true for is_secure if parameterized queries are used. Do NOT complain about missing input sanitization or validation if parameterized queries are present, as parameterization is a complete defense against SQLi.
- For CMDi: Look for direct execution of inputs without validation (e.g., `os.popen`). This is VULNERABLE. If the code uses strong input validation, sanitization, or safe subprocess lists (e.g., `subprocess.run(["ping", host])`), this is SECURE.

Analyze the code and determine if the vulnerability still exists or if it has been properly mitigated.
You must output ONLY a valid JSON object with two keys:
1. "is_secure": true or false
2. "report": A short, professional 2-sentence explanation of your finding. If it is secure, state exactly how the mitigation (like parameterization) works.

Example Output:
{{"is_secure": true, "report": "The source code now uses SQLite parameterized queries instead of string concatenation. This ensures the malicious input is treated as literal data, effectively mitigating the SQL injection vulnerability."}}"""

    try:
        import json
        messages = [{"role": "system", "content": prompt}]
        response = await call_groq(messages, json_mode=True)
        data = json.loads(response)
        return data.get("is_secure", False), data.get("report", "Audit failed to produce a conclusive report.")
    except Exception as e:
        return False, f"Audit execution error: {e}"

@trace(name="Verifier Validation")
async def run_verifier(target_url, vuln_type, payload, endpoint_path, target_field, broadcast_fn, trace_context=None) -> bool:
    await broadcast_fn("Reading patched source code for analysis...", "Verifier", "info")

    # Dynamic target selection
    folder = "target_complex" if "5001" in str(target_url) else "target"
    target_app_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", folder, "app.py"))

    try:
        with open(target_app_path, "r") as f:
            patched_code = f.read()
    except Exception as e:
        await broadcast_fn(f"Could not read patched source from {target_app_path}: {e}", "Verifier", "error")
        return False

    # ── STEP 1: LIVE VERIFICATION (DAST - The Source of Truth) ───────────────
    await broadcast_fn("Attempting live restart to confirm patch in production...", "Verifier", "thinking")

    # Dynamic Port Selection for Process Killing
    import re
    port_match = re.search(r':(\d+)', str(target_url))
    port = port_match.group(1) if port_match else "5000"
    
    await broadcast_fn(f"Clearing ghost processes on port {port}...", "Verifier", "thinking")

    # Kill ALL processes on the target port (Windows)
    try:
        out = subprocess.check_output(f"netstat -ano | findstr :{port}", shell=True).decode()
        pids = set()
        for line in out.split("\n"):
            if "LISTENING" in line:
                pid = line.strip().split()[-1]
                pids.add(pid)
        
        for pid in pids:
            subprocess.run(f"taskkill /PID {pid} /F", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        if pids:
            time.sleep(4)
    except Exception:
        pass

    # Start the patched server
    target_dir = os.path.dirname(target_app_path)
    subprocess.Popen(
        "python app.py",
        cwd=target_dir,
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Poll for the server to be ready
    server_up = False
    for _ in range(20):
        await asyncio.sleep(1)
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                r = await client.get(f"{target_url}/health")
                if r.status_code == 200:
                    server_up = True
                    break
        except Exception:
            pass

    live_secure = False
    if server_up:
        await broadcast_fn(f"Live server ready. Re-firing original payload: {payload}", "Verifier", "info")
        from tools.http_exploit import fire_payload
        response = await fire_payload(target_url, vuln_type, payload, endpoint_path, target_field, trace_context)
        await broadcast_fn(f"Live response → {response['body'][:120]}", "Verifier", "info")
        
        if response["is_breach"]:
            await broadcast_fn("LIVE TEST FAILED — exploit still works!", "Verifier", "warning")
            live_secure = False
        else:
            await broadcast_fn("EXPLOIT BLOCKED ✅ — Live test confirmed.", "Verifier", "info")
            live_secure = True
    else:
        await broadcast_fn("Live server did not respond. Falling back to static analysis.", "Verifier", "warning")
        # If server didn't start, we have to trust SAST later.

    # ── STEP 2: AI SECURITY AUDITOR (SAST - Commentary & Fallback) ─────────
    await broadcast_fn("Performing intelligent code analysis for final report...", "Verifier", "thinking")
    is_secure, report = await ai_security_audit(patched_code, vuln_type, payload)
    
    if server_up:
        # DAST is the source of truth. SAST is just commentary.
        if live_secure:
            await broadcast_fn(f"SYSTEM SECURE ✅ — Auditor Report: {report}", "Verifier", "info")
            return True
        else:
            await broadcast_fn(f"SYSTEM VULNERABLE ❌ — Auditor Report: {report}", "Verifier", "error")
            return False
    else:
        # Fallback to SAST
        if is_secure:
            await broadcast_fn(f"TRUSTING SOURCE CODE ✅ — Auditor Report: {report}", "Verifier", "info")
            return True
        else:
            await broadcast_fn(f"SAST FAILURE ❌ — Auditor Report: {report}", "Verifier", "error")
            return False
