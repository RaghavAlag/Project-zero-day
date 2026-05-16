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
    
    # PHASE 11: Cloud Flow (Clone -> Deploy -> Scan)
    cloned_folder = None
    if "github.com" in str(target_url):
        from agents.cloner import run_cloner
        await broadcast_fn("CLOUD MODE DETECTED: Initializing remote ingestion...", "System", "info")
        cloned_data = await run_cloner(target_url, broadcast_fn)
        if not cloned_data:
            await broadcast_fn("Cloud ingestion failed.", "System", "error")
            return
        target_url = cloned_data["target_url"]
        cloned_folder = cloned_data["folder"]
        await broadcast_fn(f"Repository ingested and deployed to sandbox: {target_url}", "System", "info")
    
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
            beta_data = await run_beta(target_url, vuln_type, alpha_data, journal, broadcast_fn, {"workflow_id": workflow_id, "parent_id": beta_span})
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
        else:
            # PHASE 7: Blue Swarm Auto-Remediation
            from agents.architect import run_architect
            from agents.verifier import run_verifier
            
            await broadcast_fn("Breach detected. Activating Blue Swarm for auto-remediation...", "System", "info")
            
            # Architect writes the patch
            await run_architect(target_url, vuln_type, payload, broadcast_fn, override_folder=cloned_folder)
            
            # Verifier applies the patch and tests it
            is_secure = await run_verifier(target_url, vuln_type, payload, beta_data["endpoint_path"], beta_data["input_field"], broadcast_fn, override_folder=cloned_folder)
            
            if is_secure:
                await broadcast_fn("SYSTEM SECURED. Zero-Day Pipeline Complete. 🛡️", "System", "info")
                
                # PHASE 10: GitHub PR Auto-Generation
                from agents.pr_agent import run_pr_agent
                
                # Identify folder for PR
                if cloned_folder:
                    folder_for_pr = "." # If cloned, we are in the root
                    patched_code = open(os.path.join(cloned_folder, "app.py")).read()
                else:
                    folder_for_pr = "target_complex" if "5001" in str(target_url) else "target"
                    patched_code = open(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", folder_for_pr, "app.py"))).read()
                
                await broadcast_fn("Initiating GitHub PR creation...", "System", "info")
                pr_url = await run_pr_agent(vuln_type, payload, patched_code, folder_for_pr, broadcast_fn)
                if pr_url:
                    await broadcast_fn(f"🐙 GitHub PR Ready for Review: {pr_url}", "System", "info")
                else:
                    await broadcast_fn("PR creation skipped or failed.", "System", "warning")
            else:
                await broadcast_fn("REMEDIATION FAILED. Manual intervention required.", "System", "error")
            
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
