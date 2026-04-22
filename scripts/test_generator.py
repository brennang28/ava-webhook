import os
import sys
import json
import logging
from dotenv import load_dotenv

# Ensure the root directory is in the path so we can import generator
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from generator import AvaGenerator

logging.basicConfig(level=logging.INFO)
load_dotenv()

def test_specific_job():
    # Setup test job
    job = {
        "company": "UTA Speakers",
        "role": "Assistant",
        "link": "https://uta.greenhouse.io/test",
        "description": "Assistant role in the UTA Speakers department. Supporting high-profile talent, managing schedules, and coordinating event logistics in the entertainment space. Requires strong communication skills and passion for talent management."
    }
    
    # Initialize generator
    gen = AvaGenerator()
    
    # Run targeted workflow
    print(f"\n--- Testing Generator with {job['role']} @ {job['company']} ---\n")
    state = {"jobs": [job], "results": []}
    result = gen.workflow.invoke(state)
    
    # Print results
    print("\n" + "="*50)
    print("--- TEST COMPLETED ---")
    print("="*50)
    if result.get("results"):
        final_job = result["results"][0]
        print(f"Folder Link: {final_job.get('folder_link')}")
        print("\n" + "="*20 + " COVER LETTER PREVIEW " + "="*20)
        print(final_job.get('cover_letter_text', 'No cover letter generated'))
        print("\n" + "="*20 + " RESUME DRAFT PREVIEW " + "="*20)
        print(final_job.get('resume_draft_text', 'No resume draft generated'))
    else:
        print("No results returned.")

if __name__ == '__main__':
    test_specific_job()
