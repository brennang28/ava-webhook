import os
import re
import json
import sys
from typing import List

# Add src to path
sys.path.append(os.path.abspath("src"))

from langchain_ollama import OllamaLLM
from langchain_core.messages import SystemMessage, HumanMessage

# Constants for Ground Truth
REAL_TITLE = "Marketing & Partnerships Assistant"
REAL_COMPANY = "The Paley Center for Media"

def get_draft_files(directory: str) -> List[str]:
    return [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith("CoverLetter.txt")]

def audit_draft(file_path: str, model: OllamaLLM):
    with open(file_path, 'r') as f:
        content = f.read()

    # Extract the company name from the filename or content
    # Filename format: Company_Name_CoverLetter.txt
    filename = os.path.basename(file_path)
    target_company = filename.replace("_CoverLetter.txt", "").replace("_", " ")
    
    print(f"--- Auditing {filename} ---")
    
    # Heuristic check for quick flagging
    # 1. Check if she claims to work at target_company
    # 2. Check if her title at Paley Center is wrong
    
    # We'll use the LLM for a more robust check since titles can vary slightly in phrasing
    audit_prompt = (
        f"Audit this cover letter for factual hallucinations.\n"
        f"GROUND TRUTH:\n"
        f"- Candidate Name: Ava Aschettino\n"
        f"- Current Role: {REAL_TITLE} at {REAL_COMPANY}\n"
        f"- Target Company: {target_company}\n\n"
        f"COVER LETTER CONTENT:\n{content}\n\n"
        f"RULES:\n"
        f"1. If she claims to currently work at {target_company}, it is a HALLUCINATION.\n"
        f"2. If her title at {REAL_COMPANY} is anything other than '{REAL_TITLE}', it is a HALLUCINATION.\n"
        f"3. Ignore minor differences in 'a' or 'the'.\n\n"
        f"Return JSON: {{\"hallucinated\": true/false, \"reason\": \"...\"}}"
    )
    
    try:
        res = model.invoke(audit_prompt)
        # Simple JSON extraction
        match = re.search(r'\{.*\}', res, re.DOTALL)
        if match:
            report = json.loads(match.group(0))
            if report.get("hallucinated"):
                print(f"  [!] Hallucination found: {report.get('reason')}")
                return True
    except Exception as e:
        print(f"  [?] Audit error: {e}")
    
    return False

def fix_draft(file_path: str, model: OllamaLLM):
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Backup
    if not os.path.exists(file_path + ".bak"):
        with open(file_path + ".bak", 'w') as f:
            f.write(content)
    
    filename = os.path.basename(file_path)
    target_company = filename.replace("_CoverLetter.txt", "").replace("_", " ")

    fix_prompt = (
        f"Rewrite this cover letter to remove factual hallucinations. Keep the tone and specific tailoring, but fix the errors.\n\n"
        f"ERRORS TO FIX:\n"
        f"- She does NOT work at {target_company}.\n"
        f"- Her ACTUAL current role is {REAL_TITLE} at {REAL_COMPANY}.\n\n"
        f"ORIGINAL LETTER:\n{content}\n\n"
        f"Return ONLY the corrected letter text."
    )
    
    try:
        fixed_content = model.invoke(fix_prompt)
        # Clean up any markdown blocks
        fixed_content = re.sub(r'```[a-z]*\s*|\s*```', '', fixed_content).strip()
        
        with open(file_path, 'w') as f:
            f.write(fixed_content)
        print(f"  [+] Fixed {filename}")
    except Exception as e:
        print(f"  [-] Failed to fix {filename}: {e}")

def main():
    # Use a reasoning model for auditing/fixing
    model = OllamaLLM(model="gemma4:31b:cloud") # Assuming this is available via the environment
    
    drafts_dir = "drafts"
    files = get_draft_files(drafts_dir)
    
    print(f"Starting audit of {len(files)} drafts...")
    
    for f in files:
        if audit_draft(f, model):
            fix_draft(f, model)

if __name__ == "__main__":
    main()
