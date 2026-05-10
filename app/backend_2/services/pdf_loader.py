import pdfplumber

def extract_text_from_pdf(file_path: str) -> str:
    text = []
    
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            # .extract_text(layout=True) attempts to preserve the visual layout,
            # which is critical for multi-column CVs.
            page_text = page.extract_text(layout=True)
            if page_text:
                text.append(page_text)
                
    return "\n".join(text)