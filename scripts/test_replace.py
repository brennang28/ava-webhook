from docx import Document
import os

def test_replacement(template_path, output_path):
    doc = Document(template_path)
    
    # Simple replacement in paragraphs
    for p in doc.paragraphs:
        if "[Company Name]" in p.text:
            p.text = p.text.replace("[Company Name]", "UTA Speakers")
        if "I am writing to express my strong interest" in p.text:
            # Replace the whole paragraph or just the text
            p.text = "TAILORED PARAGRAPH 1"
            
    doc.save(output_path)
    print(f"Saved to {output_path}")

test_replacement("Aschettino, Ava - Cover Letter Template.docx", "scratch/test_output.docx")
