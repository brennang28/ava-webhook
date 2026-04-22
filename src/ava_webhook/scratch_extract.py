import docx
import os

def extract_text(filename):
    doc = docx.Document(filename)
    fullText = []
    for para in doc.paragraphs:
        fullText.append(para.text)
    return '\n'.join(fullText)

# Project paths
project_dir = "/home/brenn/ava-webhook"
scratch_dir = os.path.join(project_dir, "scratch")
os.makedirs(scratch_dir, exist_ok=True)

resume_path = os.path.join(project_dir, "Aschettino, Ava- Resume.docx")
template_path = os.path.join(project_dir, "Aschettino, Ava - Cover Letter Template.docx")

resume_text = extract_text(resume_path)
template_text = extract_text(template_path)

# Save to project scratch
with open(os.path.join(scratch_dir, "resume.txt"), "w") as f:
    f.write(resume_text)

with open(os.path.join(scratch_dir, "template.txt"), "w") as f:
    f.write(template_text)

print("--- Extraction Preview ---")
print(f"\nResume Preview (first 200 chars):\n{resume_text[:200]}...")
print(f"\nTemplate Preview (first 200 chars):\n{template_text[:200]}...")
print("\nExtraction complete.")
