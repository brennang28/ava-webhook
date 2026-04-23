import sys
import os
import json
import time

# Add src to path
sys.path.append(os.path.abspath("src"))

from ava_webhook.generator import AvaGenerator

def regenerate_wme():
    # Ensure env vars are loaded if needed (though antigravity should have them)
    gen = AvaGenerator()
    
    # Reconstruct the job info for WME
    # Based on the draft file: Job: Music Central Assistant - New York at WME | William Morris Endeavor
    job = {
        "company": "WME | William Morris Endeavor",
        "role": "Music Central Assistant - New York",
        "description": "Administrative support, calendar management, industry knowledge of music publishing and synchronization, high-level communication, ability to multitask in a fast-paced agency environment."
    }
    
    print(f"--- Re-generating application for {job['company']} ---")
    
    # We will manually run the steps that _process_jobs_sequentially does
    job_state = {
        "job": job,
        "resume_text": gen.resume_text,
        "template_text": gen.template_text,
        "revision_count": 0,
        "job_analysis": {},
        "mapped_experience": [],
        "final_cover_letter": "",
        "final_resume_draft": "",
        "critique": "",
        "folder_link": ""
    }
    
    # 1. Analyze Job
    print("Step 1: Analyzing job...")
    job_state.update(gen._analyze_job(job_state))
    
    # 2. Map Experience
    print("Step 2: Mapping experience...")
    job_state.update(gen._map_experience(job_state))
    
    # 3. Iterative Drafting (with accuracy verification)
    print("Step 3: Iterative drafting...")
    while job_state["revision_count"] < 2:
        job_state.update(gen._draft_sections(job_state))
        job_state.update(gen._verify_accuracy(job_state))
        job_state.update(gen._critique_review(job_state))
        print(f"Critique (Round {job_state['revision_count']}): {job_state.get('critique')}")
        if "EXCELLENT" in job_state.get("critique", "").upper():
            break
            
    # 4. Finalize and Upload
    print("Step 4: Finalizing and uploading to Drive...")
    final_result = gen._finalize_job(job_state)
    
    # Save the local txt file as well (to keep it in sync)
    local_txt_path = os.path.join("drafts", "WME_|_William_Morris_Endeavor_CoverLetter.txt")
    with open(local_txt_path, "w") as f:
        f.write(job_state["final_cover_letter"])
    
    print(f"\nSUCCESS! Fixed cover letter saved to {local_txt_path}")
    print(f"Google Drive Folder Link: {final_result['results'][0].get('folder_link')}")

if __name__ == "__main__":
    regenerate_wme()
