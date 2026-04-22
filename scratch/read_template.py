
from docx import Document
import os

path = "assets/Aschettino, Ava - Cover Letter Template.docx"
if os.path.exists(path):
    doc = Document(path)
    text = "\n".join([p.text for p in doc.paragraphs])
    print("--- Template Text ---")
    print(text)
else:
    print("Template not found")
