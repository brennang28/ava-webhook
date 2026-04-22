
import sys
import os
import json
import logging

# Add src to path
sys.path.append(os.path.abspath("src"))

from ava_webhook.generator import AvaGenerator

# Mock State for testing
mock_job = {
    "company": "UTA Speakers",
    "role": "Assistant",
    "description": "Looking for a high-energy assistant to manage calendars and talent relations."
}

def test_accuracy_logic():
    print("--- Initializing AvaGenerator ---")
    gen = AvaGenerator()
    
    # We want to test if it correctly identifies a hallucination if we FORCE one
    # But first, let's see if the REFINED prompt fixes it naturally
    
    job_state = {
        "job": mock_job,
        "resume_text": gen.resume_text,
        "template_text": gen.template_text,
        "revision_count": 0,
        "job_analysis": {"requirements": ["Calendar management", "Talent relations"], "vibe": "Fast-paced", "problem": "Admin burden"},
        "mapped_experience": [
            {"requirement": "Calendar management", "evidence": "Managed complex calendars at NYU Special Collections."},
            {"requirement": "Talent relations", "evidence": "Managed high-profile partner relationships at The Paley Center."}
        ],
        "final_cover_letter": "",
        "accuracy_report": "",
        "critique": ""
    }
    
    print("--- 1. Drafting Sections ---")
    draft_update = gen._draft_sections(job_state)
    job_state.update(draft_update)
    print("DRAFT:")
    print(job_state["final_cover_letter"])
    
    print("\n--- 2. Verifying Accuracy ---")
    verify_update = gen._verify_accuracy(job_state)
    job_state.update(verify_update)
    print("ACCURACY REPORT:")
    print(job_state["accuracy_report"])
    
    print("\n--- 3. Critique Review ---")
    critique_update = gen._critique_review(job_state)
    job_state.update(critique_update)
    print("CRITIQUE:")
    print(job_state["critique"])
    
    # Check if the hallucination is present
    hallucination_detected = "UTA" in job_state["final_cover_letter"] and "current role" in job_state["final_cover_letter"].lower()
    if hallucination_detected:
        print("\n[FAIL] Hallucination still present in draft.")
    else:
        print("\n[PASS] No role-confusion hallucination detected in draft.")

    report = json.loads(job_state["accuracy_report"])
    if report.get("status") == "PASS":
        print("[PASS] Auditor passed the letter.")
    else:
        print(f"[AUDIT] Auditor found issues: {report.get('hallucinations')}")

if __name__ == "__main__":
    test_accuracy_logic()
