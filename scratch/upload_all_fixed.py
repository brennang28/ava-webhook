import sys
import os
import io
import re

# Add src to path
sys.path.append(os.path.abspath("src"))

from ava_webhook.generator import AvaGenerator

def upload_all_fixed():
    gen = AvaGenerator()
    
    # Files we know we fixed or might have fixed
    # We'll just look for all fixed .txt files in drafts/
    drafts_dir = "drafts"
    files = [f for f in os.listdir(drafts_dir) if f.endswith("CoverLetter.txt")]
    
    # We'll only upload if a .bak exists (meaning we fixed it) OR if it's WME
    to_upload = []
    for f in files:
        if os.path.exists(os.path.join(drafts_dir, f + ".bak")) or "WME" in f:
            to_upload.append(f)
            
    print(f"--- Syncing {len(to_upload)} fixed drafts to Drive ---")
    
    for filename in to_upload:
        company_clean = filename.replace("_CoverLetter.txt", "").replace("_", " ")
        
        # Try to find the matching ResumeDraft for the STAR mapping
        resume_filename = filename.replace("CoverLetter.txt", "ResumeDraft.txt")
        resume_path = os.path.join(drafts_dir, resume_filename)
        
        if not os.path.exists(resume_path):
            print(f"Skipping {filename} - no resume draft found for mapping.")
            continue
            
        with open(os.path.join(drafts_dir, filename), "r") as f:
            letter_text = f.read()
        with open(resume_path, "r") as f:
            resume_text = f.read()
            
        # We need the role. We can extract it from the resume draft.
        # Format: Job: Role at Company
        role = "Assistant" # Default
        match = re.search(r"Job:\s*(.*)\s*at", resume_text)
        if match:
            role = match.group(1).strip()
            
        job = {
            "company": company_clean,
            "role": role
        }
        
        print(f"Uploading {company_clean} - {role}...")
        try:
            cover_letter_buffer = gen._write_to_template(gen.template_path, letter_text, True, job)
            resume_draft_buffer = gen._write_to_template(gen.resume_path, resume_text, False, job)

            folder_link = gen._upload_to_drive(
                company_clean, 
                role, 
                cover_letter_buffer,
                resume_draft_buffer
            )
            print(f"  [+] Success: {folder_link}")
        except Exception as e:
            print(f"  [-] Failed: {e}")

if __name__ == "__main__":
    upload_all_fixed()
