from io import BytesIO


def read_uploaded_resume(uploaded_file) -> str:
    """Read text from txt/pdf/docx uploaded through Streamlit."""
    if uploaded_file is None:
        return ""

    filename = uploaded_file.name.lower()
    file_bytes = uploaded_file.getvalue()

    if filename.endswith(".txt"):
        return file_bytes.decode("utf-8", errors="ignore")

    if filename.endswith(".pdf"):
        try:
            import pdfplumber
        except ImportError as exc:
            raise ImportError("Please install pdfplumber to read PDF files.") from exc

        text_parts = []
        with pdfplumber.open(BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text_parts.append(page_text)
        return "\n".join(text_parts).strip()

    if filename.endswith(".docx"):
        try:
            import docx
        except ImportError as exc:
            raise ImportError("Please install python-docx to read DOCX files.") from exc

        doc = docx.Document(BytesIO(file_bytes))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n".join(paragraphs).strip()

    raise ValueError("Unsupported file type. Please upload a .txt, .pdf, or .docx resume.")
