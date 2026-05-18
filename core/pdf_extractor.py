"""PDFテキスト抽出（PyMuPDF使用）

OCR済みPDF（テキスト埋め込み済み）専用。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import fitz  # PyMuPDF


@dataclass
class ExtractedPdf:
    """PDFから抽出した情報"""
    full_text: str
    page_texts: list[str]
    page_count: int
    has_text: bool  # OCRされてテキストが入っているか


def extract_pdf(pdf_path: str | Path) -> ExtractedPdf:
    """PDFを開いてテキスト抽出。

    Returns:
        ExtractedPdf。has_text=Falseならスキャン画像PDFの可能性が高い。
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDFが見つかりません: {pdf_path}")

    doc = fitz.open(str(pdf_path))
    try:
        page_texts = []
        for page in doc:
            page_texts.append(page.get_text() or "")
        full_text = "\n\n".join(page_texts)
        # 文字数で判定。1ページあたり50文字未満なら画像PDFの可能性
        avg_chars = len(full_text) / max(len(page_texts), 1)
        has_text = avg_chars >= 50
        return ExtractedPdf(
            full_text=full_text,
            page_texts=page_texts,
            page_count=len(page_texts),
            has_text=has_text,
        )
    finally:
        doc.close()


def get_first_n_pages_text(extracted: ExtractedPdf, n: int = 10) -> str:
    """先頭Nページのテキストを返す（章検出用）"""
    return "\n\n".join(extracted.page_texts[:n])
