from io import BytesIO
from typing import List, Tuple


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


def load_resume_files(uploaded_files) -> Tuple[str, List[str], List[str]]:
    """Read multiple uploaded resume files and combine them with clear separators."""
    if not uploaded_files:
        return "", [], []

    text_parts = []
    file_names = []
    warnings = []

    for idx, uploaded_file in enumerate(uploaded_files, start=1):
        if uploaded_file is None:
            continue
        file_name = getattr(uploaded_file, "name", f"file_{idx}")
        file_names.append(file_name)
        try:
            text = read_uploaded_resume(uploaded_file)
            if text.strip():
                text_parts.append(f"===== 文件 {idx}: {file_name} =====\n{text.strip()}")
            else:
                warnings.append(f"{file_name}: 没有读取到有效文本")
        except Exception as exc:
            warnings.append(f"{file_name}: {exc}")

    return "\n\n".join(text_parts).strip(), file_names, warnings
