import asyncio
import uuid
import os
from agents.alpha import run_alpha
from agents.beta import run_beta
from agents.gamma import run_gamma
from tools.file_ops import write_log
from tracing import trace

@trace(name="Zero-Day Pipeline Orchestrator")
async def run_scan(target_url, vuln_type, broadcast_fn, journal):
    scan_id = str(uuid.uuid4())
    MAX_RETRIES = 4
    
    from tracing import start_workflow, trace_step, end_workflow
    
    workflow_id = start_workflow("SCAN_STARTED")
    journal.reset()
    logs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "logs"))
    os.makedirs(logs_dir, exist_ok=True)
    
    await broadcast_fn(f"Starting actual scan against {target_url} for {vuln_type}", "System", "info")
    
    try:
        # Step 1: Alpha Recon
        alpha_span = trace_step(workflow_id, "ALPHA_RECON", None, {"target": target_url}, "running")
        alpha_data = await run_alpha(target_url, vuln_type, journal, broadcast_fn, {"workflow_id": workflow_id, "parent_id": alpha_span})
        trace_step(workflow_id, "ALPHA_RECON", None, {"results": len(alpha_data['results'])}, "success")
        
        breached = False
        
        # Step 2: Striker Loop
        for attempt in range(1, MAX_RETRIES + 1):
            await asyncio.sleep(2) # delay between agent rounds
            beta_span = trace_step(workflow_id, f"BETA_STRIKE_ATTEMPT_{attempt}", None, {}, "running")
            beta_data = await run_beta(target_url, vuln_type, alpha_data['results'], journal, broadcast_fn, {"workflow_id": workflow_id, "parent_id": beta_span})
            payload = beta_data["payload"]
            response = beta_data["response"]
            
            trace_step(workflow_id, f"BETA_STRIKE_ATTEMPT_{attempt}", None, {"payload": payload, "response_code": response["status_code"]}, "success")
            
            if response["is_breach"]:
                journal.add_entry(attempt, vuln_type, payload, str(response["status_code"]), "N/A", "breached")
                trace_step(workflow_id, "BREACH_CONFIRMED", None, {"payload": payload}, "success")
                await broadcast_fn(f"UNAUTHORIZED ACCESS ACHIEVED with payload: {payload}", "System", "breach")
                breached = True
                break
            else:
                gamma_span = trace_step(workflow_id, f"GAMMA_CRITIQUE_{attempt}", None, {}, "running")
                critique = await run_gamma(payload, response, vuln_type, journal, broadcast_fn, {"workflow_id": workflow_id, "parent_id": gamma_span})
                trace_step(workflow_id, f"GAMMA_CRITIQUE_{attempt}", None, {"critique": critique}, "success")
                journal.add_entry(attempt, vuln_type, payload, f"Status {response['status_code']}", critique, "failed")
                
        if not breached:
            await broadcast_fn("Red Swarm exhausted all attempts. Target hardened or scope exceeded.", "System", "error")
            
    except Exception as e:
        await broadcast_fn(f"Scan failed with error: {str(e)}", "System", "error")
        print(f"Orchestrator error: {str(e)}")
        
    # Write journal log
    log_content = journal.get_context_string()
    write_log(scan_id, log_content)
    trace_step(workflow_id, "FILE_WRITTEN", None, {"file": f"{scan_id}.txt"}, "success")
    
    # Save JSON journal
    journal.to_file(os.path.join(logs_dir, f"journal_{scan_id}.json"))
    trace_step(workflow_id, "SCAN_COMPLETE", None, {"breached": breached}, "success")
    end_workflow(workflow_id, "breached" if breached else "failed")
