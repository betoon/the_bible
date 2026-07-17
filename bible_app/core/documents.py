"""Document conversion and document-library helpers."""

import re
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path

from bible_app.config.paths import DOCUMENT_IMAGE_DIR, DOCUMENT_LIBRARY_PATH
from bible_app.storage.data_manager import read_json, write_json
from bible_app.utils.logger import get_logger


logger = get_logger(__name__)


class PlainTextHTMLParser(HTMLParser):
    """Small HTML parser that keeps visible text and drops markup."""

    def __init__(self):
        super().__init__()
        self.parts = []
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag.lower() in {"script", "style", "noscript"}:
            self._skip_depth += 1

    def handle_endtag(self, tag):
        if tag.lower() in {"script", "style", "noscript"} and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data):
        if self._skip_depth:
            return
        data = data.strip()
        if data:
            self.parts.append(data)

    def text(self):
        return " ".join(self.parts)


def normalize_document_library(data):
    """Normalize raw document-library JSON into a safe list of dictionaries."""
    if not isinstance(data, list):
        return []
    documents = []
    for item in data:
        if not isinstance(item, dict):
            continue
        doc_id = str(item.get("id", "")).strip()
        title = str(item.get("title", "")).strip()
        if not doc_id or not title:
            continue
        documents.append({
            "id": doc_id,
            "title": title,
            "source_path": str(item.get("source_path", "")),
            "created": str(item.get("created", "")),
            "type": str(item.get("type", "")),
            "text": str(item.get("text", "")),
            "images": [str(path) for path in item.get("images", []) if str(path).strip()],
        })
    return documents


def read_document_library():
    """Load converted document metadata from the user document library."""
    return normalize_document_library(read_json(DOCUMENT_LIBRARY_PATH, []))


def write_document_library(documents):
    """Save converted document metadata after normalizing it."""
    logger.info("Writing document library with %s documents", len(documents))
    write_json(DOCUMENT_LIBRARY_PATH, normalize_document_library(documents))


def safe_document_id(title):
    """Build a filesystem-friendly document id from a title and timestamp."""
    base = re.sub(r"[^A-Za-z0-9_-]+", "-", title).strip("-") or "document"
    return f"{base}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"


def extract_docx_text_and_images(path, image_dir):
    """Extract plain text and embedded images from a DOCX file."""
    text_parts = []
    images = []
    try:
        import zipfile
        from xml.etree import ElementTree

        with zipfile.ZipFile(path) as archive:
            if "word/document.xml" in archive.namelist():
                tree = ElementTree.fromstring(archive.read("word/document.xml"))
                namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
                text_parts = [node.text or "" for node in tree.findall(".//w:t", namespace)]
            for name in archive.namelist():
                if name.startswith("word/media/"):
                    target = image_dir / Path(name).name
                    target.write_bytes(archive.read(name))
                    images.append(str(target))
    except Exception as exc:
        raise RuntimeError(f"Could not read DOCX file: {exc}") from exc
    return "\n".join(part for part in text_parts if part).strip(), images


def extract_pdf_text_and_images(path, image_dir):
    """Extract text and best-effort embedded images from a PDF file."""
    text = ""
    images = []
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        text = "\n\n".join(page.extract_text() or "" for page in reader.pages).strip()
    except Exception as exc:
        logger.info("pypdf could not extract text from %s; trying PyPDF2. Error: %s", path, exc)
        try:
            from PyPDF2 import PdfReader

            reader = PdfReader(str(path))
            text = "\n\n".join(page.extract_text() or "" for page in reader.pages).strip()
        except Exception as exc:
            raise RuntimeError(f"Could not extract PDF text. Install pypdf for PDF conversion. Details: {exc}") from exc

    try:
        import fitz

        doc = fitz.open(str(path))
        for page_index in range(len(doc)):
            for image_index, image in enumerate(doc[page_index].get_images(full=True), 1):
                xref = image[0]
                payload = doc.extract_image(xref)
                ext = payload.get("ext", "png")
                target = image_dir / f"page-{page_index + 1}-image-{image_index}.{ext}"
                target.write_bytes(payload["image"])
                images.append(str(target))
    except Exception as exc:
        logger.warning("Could not extract embedded PDF images from %s: %s", path, exc)
    return text, images


def convert_document_to_library_item(path, title=None, progress=None):
    """Convert a supported local document into a searchable library item.

    Args:
        path: Source file path. Supported types are PDF, DOCX, TXT, MD, HTML.
        title: Optional display title. Defaults to the file stem.
        progress: Optional callback receiving ``(percent, message)``.

    Returns:
        The saved document dictionary.

    Raises:
        FileNotFoundError: If the source file does not exist.
        RuntimeError: If the document type is unsupported or cannot be read.
    """
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(source)
    title = (title or source.stem).strip() or source.stem
    doc_id = safe_document_id(title)
    image_dir = DOCUMENT_IMAGE_DIR / doc_id
    image_dir.mkdir(parents=True, exist_ok=True)

    def report(value, message):
        if progress:
            progress(value, message)

    logger.info("Converting document to library item: %s", source)
    report(10, "Reading document...")
    ext = source.suffix.lower()
    images = []
    if ext == ".pdf":
        text, images = extract_pdf_text_and_images(source, image_dir)
    elif ext == ".docx":
        text, images = extract_docx_text_and_images(source, image_dir)
    elif ext in {".txt", ".md"}:
        text = source.read_text(encoding="utf-8", errors="ignore")
    elif ext in {".html", ".htm"}:
        raw = source.read_text(encoding="utf-8", errors="ignore")
        parser = PlainTextHTMLParser()
        parser.feed(raw)
        text = parser.text()
    else:
        raise RuntimeError("Supported document types: PDF, DOCX, TXT, MD, HTML.")

    report(70, "Saving converted JSON...")
    item = {
        "id": doc_id,
        "title": title,
        "source_path": str(source),
        "created": datetime.now().isoformat(timespec="seconds"),
        "type": ext.lstrip("."),
        "text": text.strip(),
        "images": images,
    }
    documents = read_document_library()
    documents.append(item)
    write_document_library(documents)
    logger.info("Converted document saved: %s", item["id"])
    report(100, "Conversion complete.")
    return item


def matching_document_for_source(documents, source_path):
    """Return the library item already created from ``source_path``, if any."""
    source = str(Path(source_path).resolve()).lower()
    for item in documents:
        item_source = str(item.get("source_path", "")).strip()
        if item_source and str(Path(item_source).resolve()).lower() == source:
            return item
    return None
