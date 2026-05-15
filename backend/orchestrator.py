import asyncio
import uuid
import os
from agents.alpha import run_alpha
from agents.beta import run_beta
from agents.gamma import run_gamma
from tools.file_ops import write_log

async def run_scan(target_url, vuln_type, broadcast_fn, journal):
    scan_id = str(uuid.uuid4())
    MAX_RETRIES = 4
    
    journal.reset()
    logs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "logs"))
    os.makedirs(logs_dir, exist_ok=True)
    
    await broadcast_fn(f"Starting actual scan against {target_url} for {vuln_type}", "System", "info")
    
    try:
        # Step 1: Alpha Recon
        alpha_data = await run_alpha(target_url, vuln_type, journal, broadcast_fn)
        
        breached = False
        
        # Step 2: Striker Loop
        for attempt in range(1, MAX_RETRIES + 1):
            await asyncio.sleep(2) # delay between agent rounds
            beta_data = await run_beta(target_url, vuln_type, alpha_data['results'], journal, broadcast_fn)
            payload = beta_data["payload"]
            response = beta_data["response"]
            
            if response["is_breach"]:
                journal.add_entry(attempt, vuln_type, payload, str(response["status_code"]), "N/A", "breached")
                await broadcast_fn(f"UNAUTHORIZED ACCESS ACHIEVED with payload: {payload}", "System", "breach")
                breached = True
                break
            else:
                critique = await run_gamma(payload, response, vuln_type, journal, broadcast_fn)
                journal.add_entry(attempt, vuln_type, payload, f"Status {response['status_code']}", critique, "failed")
                
        if not breached:
            await broadcast_fn("Red Swarm exhausted all attempts. Target hardened or scope exceeded.", "System", "error")
            
    except Exception as e:
        await broadcast_fn(f"Scan failed with error: {str(e)}", "System", "error")
        print(f"Orchestrator error: {str(e)}")
        
    # Write journal log
    log_content = journal.get_context_string()
    write_log(scan_id, log_content)
    
    # Save JSON journal
    journal.to_file(os.path.join(logs_dir, f"journal_{scan_id}.json"))
