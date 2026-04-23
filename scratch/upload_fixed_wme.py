import sys
import os
import io

# Add src to path
sys.path.append(os.path.abspath("src"))

from ava_webhook.generator import AvaGenerator

def upload_fixed_wme():
    gen = AvaGenerator()
    
    # Read the manually fixed letter
    path = "drafts/WME_|_William_Morris_Endeavor_CoverLetter.txt"
    with open(path, "r") as f:
        letter_text = f.read()
    
    # Read the resume draft text (from the existing file)
    resume_path = "drafts/WME_|_William_Morris_Endeavor_ResumeDraft.txt"
    with open(resume_path, "r") as f:
        resume_text = f.read()
        
    job = {
        "company": "WME | William Morris Endeavor",
        "role": "Music Central Assistant - New York"
    }
    
    print(f"--- Uploading fixed application for {job['company']} to Drive ---")
    
    # Generate buffers
    cover_letter_buffer = gen._write_to_template(gen.template_path, letter_text, True, job)
    resume_draft_buffer = gen._write_to_template(gen.resume_path, resume_text, False, job)

    # Upload
    folder_link = gen._upload_to_drive(
        job.get("company"), 
        job.get("role"), 
        cover_letter_buffer,
        resume_draft_buffer
    )
    
    print(f"SUCCESS! Google Drive Folder Link: {folder_link}")

if __name__ == "__main__":
    upload_fixed_wme()
