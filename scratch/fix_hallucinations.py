import sys
import os
import json
import re

# Add src to path
sys.path.append(os.path.abspath("src"))

from langchain_ollama import ChatOllama
from ava_webhook.generator import AvaGenerator

def fix_drafts():
    generator = AvaGenerator()
    drafts_dir = "drafts"
    files = [f for f in os.listdir(drafts_dir) if f.endswith("_CoverLetter.txt")]
    
    # Ground truth
    current_role = "Marketing & Partnerships Assistant"
    current_company = "The Paley Center for Media"
    
    problem_files = []
    
    # 1. Identify problem files
    for filename in files:
        filepath = os.path.join(drafts_dir, filename)
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Get target company from filename (e.g. UTA_Speakers_CoverLetter.txt -> UTA Speakers)
        target_company = filename.replace("_CoverLetter.txt", "").replace("_", " ")
        
        # Look for "In my current role as ... at [Target Company]"
        pattern = rf"current role as .* at {re.escape(target_company)}"
        if re.search(pattern, content, re.IGNORECASE):
            print(f"Found hallucination in {filename}")
            problem_files.append((filename, target_company, content))

    if not problem_files:
        print("No hallucinations found.")
        return

    print(f"\nFixing {len(problem_files)} files...")

    for filename, target_company, content in problem_files:
        print(f"--- Fixing {filename} ---")
        
        # Use LLM to fix the specific paragraph
        prompt = f"""
You are an expert editor. The following cover letter draft has a factual error. 
It claims the applicant (Ava Aschettino) currently works at "{target_company}".
This is FALSE. 

Ava's REAL current role is: "{current_role}" at "{current_company}".

Please rewrite the following cover letter content to fix this error. 
Keep the rest of the text as similar as possible, but ensure her current experience is grounded in her role at The Paley Center.
Ensure she sounds like an EXTERNAL applicant interested in joining {target_company}.

TEXT:
{content}

REWRITTEN TEXT:
"""
        response = generator.reasoning_llm.invoke(prompt)
        new_content = response.content.strip()
        
        # Save fixed version
        new_filename = filename # Overwrite or create .fixed? User said "fix the drafts", so let's overwrite or save with .fixed
        filepath = os.path.join(drafts_dir, new_filename)
        
        # Backup original just in case
        with open(filepath + ".bak", 'w') as f:
            f.write(content)
            
        with open(filepath, 'w') as f:
            f.write(new_content)
        
        print(f"Successfully fixed {filename}")

if __name__ == "__main__":
    fix_drafts()
