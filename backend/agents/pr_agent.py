import httpx
import base64
import os
import datetime
from tracing import trace

GITHUB_API = "https://api.github.com"

@trace(name="PR Agent - GitHub Push")
async def run_pr_agent(vuln_type: str, payload: str, patched_code: str, target_folder: str, broadcast_fn, trace_context=None) -> str:
    """
    Creates a GitHub Pull Request with the security patch.
    Returns the PR URL or an error message.
    """
    token = os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPO")

    if not token or not repo:
        await broadcast_fn("GitHub credentials not found in .env. Skipping PR creation.", "PR Agent", "warning")
        return None

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json"
    }

    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    branch_name = f"security/fix-{vuln_type}-{timestamp}"
    file_path = f"{target_folder}/app.py"
    commit_message = f"[Security Patch] Fix {vuln_type.upper()} vulnerability in {target_folder}/app.py"

    await broadcast_fn(f"Creating security branch: {branch_name}", "PR Agent", "thinking")

    async with httpx.AsyncClient(timeout=20.0) as client:

        # Step 1: Get the SHA of the default branch (main)
        r = await client.get(f"{GITHUB_API}/repos/{repo}/git/ref/heads/main", headers=headers)
        if r.status_code != 200:
            # Try master
            r = await client.get(f"{GITHUB_API}/repos/{repo}/git/ref/heads/master", headers=headers)

        if r.status_code != 200:
            await broadcast_fn(f"Could not find default branch in repo. Status: {r.status_code}. Initializing repo first...", "PR Agent", "warning")
            # Initialize repo with a README
            init_content = base64.b64encode(b"# Project Zero-Day Security Demo\n\nThis repository is managed by the autonomous security pipeline.").decode()
            await client.put(
                f"{GITHUB_API}/repos/{repo}/contents/README.md",
                headers=headers,
                json={"message": "Initial commit", "content": init_content}
            )
            # Re-fetch
            r = await client.get(f"{GITHUB_API}/repos/{repo}/git/ref/heads/main", headers=headers)
            if r.status_code != 200:
                await broadcast_fn(f"GitHub API error: {r.text[:200]}", "PR Agent", "error")
                return None

        main_sha = r.json()["object"]["sha"]
        base_branch = r.json()["ref"].replace("refs/heads/", "")

        # Step 2: Create new security branch
        r = await client.post(
            f"{GITHUB_API}/repos/{repo}/git/refs",
            headers=headers,
            json={"ref": f"refs/heads/{branch_name}", "sha": main_sha}
        )
        if r.status_code not in [200, 201]:
            await broadcast_fn(f"Failed to create branch: {r.text[:200]}", "PR Agent", "error")
            return None

        # Step 3: Check if file exists on main to get its SHA
        file_sha = None
        r_file = await client.get(f"{GITHUB_API}/repos/{repo}/contents/{file_path}?ref={base_branch}", headers=headers)
        if r_file.status_code == 200:
            file_sha = r_file.json().get("sha")

        # Step 4: Commit the patched file to the new branch
        encoded_content = base64.b64encode(patched_code.encode()).decode()
        commit_body = {
            "message": commit_message,
            "content": encoded_content,
            "branch": branch_name
        }
        if file_sha:
            commit_body["sha"] = file_sha

        r = await client.put(
            f"{GITHUB_API}/repos/{repo}/contents/{file_path}",
            headers=headers,
            json=commit_body
        )
        if r.status_code not in [200, 201]:
            await broadcast_fn(f"Failed to commit patch: {r.text[:200]}", "PR Agent", "error")
            return None

        await broadcast_fn(f"Patch committed to branch: {branch_name}", "PR Agent", "info")

        # Step 5: Create the Pull Request
        vuln_names = {"sqli": "SQL Injection (SQLi)", "cmdi": "OS Command Injection (CMDi)"}
        vuln_full = vuln_names.get(vuln_type, vuln_type.upper())

        pr_body = f"""## 🛡️ Autonomous Security Patch — Project Zero-Day

**Vulnerability Detected:** `{vuln_full}`
**Affected File:** `{file_path}`
**Breach Payload:** `{payload}`
**Detection Time:** `{timestamp}`

---

### What Was Found
The autonomous Red Swarm agent detected and confirmed a **{vuln_full}** vulnerability by successfully breaching the application.

### What Was Fixed
The Architect agent rewrote the affected code to eliminate the vulnerability using secure coding best practices:
- **SQLi:** Replaced string concatenation with parameterized queries (`?` placeholders)
- **CMDi:** Replaced `os.popen()` with `subprocess` using list arguments and input validation

### Verification
The Blue Swarm Verifier confirmed the fix by:
1. Restarting the patched application
2. Re-firing the original exploit payload
3. Confirming the payload was **BLOCKED** ✅

---
*This PR was generated automatically by the Project Zero-Day autonomous DevSecOps pipeline.*"""

        r = await client.post(
            f"{GITHUB_API}/repos/{repo}/pulls",
            headers=headers,
            json={
                "title": f"🔒 [Security] Fix {vuln_full} in {target_folder}/app.py",
                "body": pr_body,
                "head": branch_name,
                "base": base_branch
            }
        )
        if r.status_code not in [200, 201]:
            await broadcast_fn(f"Failed to create PR: {r.text[:200]}", "PR Agent", "error")
            return None

        pr_url = r.json().get("html_url")
        await broadcast_fn(f"✅ Pull Request Created: {pr_url}", "PR Agent", "info")
        return pr_url
