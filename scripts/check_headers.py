from docx import Document

def show_headers(path):
    print(f"--- Headers for {path} ---")
    doc = Document(path)
    for i, section in enumerate(doc.sections):
        print(f"Section {i} Header text:")
        for header in [section.header, section.first_page_header, section.even_page_header]:
            if header:
                for p in header.paragraphs:
                    print(f"  [Header] {p.text}")

show_headers("Aschettino, Ava - Cover Letter Template.docx")
show_headers("Aschettino, Ava- Resume.docx")
