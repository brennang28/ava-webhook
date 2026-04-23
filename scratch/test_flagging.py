import sys
import os
import io
import time

# Add src to path
sys.path.append(os.path.abspath("src"))

from ava_webhook.generator import AvaGenerator

def test_flagging():
    gen = AvaGenerator()
    
    # Mock content with <verify> tags
    letter_text = (
        "Dear Hiring Manager,\n\n"
        "I am writing to express my interest in the position.\n"
        "I have extensive experience in <verify>advanced quantum computing algorithms</verify> which I developed during my studies.\n"
        "I am confident that my skills in <verify>managing multi-million dollar budgets</verify> will be an asset.\n"
        "Sincerely,\nAva Aschettino"
    )
    
    job = {
        "company": "Test Company",
        "role": "Test Role"
    }
    
    print("--- Testing Uncertainty Flagging ---")
    
    # Generate the docx buffer
    try:
        buffer = gen._write_to_template(gen.template_path, letter_text, True, job)
        
        # Save it locally for manual inspection if needed
        test_output = "drafts/test_flagging_output.docx"
        with open(test_output, "wb") as f:
            f.write(buffer.getvalue())
        
        print(f"SUCCESS: Test document generated at {test_output}")
        print("Please verify that the phrases 'advanced quantum computing algorithms' and 'managing multi-million dollar budgets' are in RED.")
        
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    # Create drafts dir if not exists
    os.makedirs("drafts", exist_ok=True)
    test_flagging()
