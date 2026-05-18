"""日本語PDFの生成（ReportLab使用）

シンプル設計:
  - ページ単位の翻訳を順番に並べて出力
  - マークダウン見出し（# / ## / ###）を解釈して太字＋大きく表示
  - 各ページ末尾に「原書 p.X」の対応情報
  - 自前のページ番号をフッターに付与
  - スキップされたページ（著作権・目次・索引等）はまとめて省略表示
  - 日本語フォントは ReportLab 内蔵 Heisei系 CIDフォント
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

from .translator import TranslatedPage


FONT_REGULAR = "HeiseiMin-W3"        # 明朝（本文用）
FONT_BOLD = "HeiseiKakuGo-W5"        # ゴシック（見出し用）


def _register_fonts():
    registered = set(pdfmetrics.getRegisteredFontNames())
    if FONT_REGULAR not in registered:
        pdfmetrics.registerFont(UnicodeCIDFont(FONT_REGULAR))
    if FONT_BOLD not in registered:
        pdfmetrics.registerFont(UnicodeCIDFont(FONT_BOLD))


def _make_footer_callback(book_title: str):
    def _on_page(canvas, doc):
        canvas.saveState()
        canvas.setFont(FONT_REGULAR, 8)
        canvas.drawString(20 * mm, 10 * mm, book_title)
        canvas.drawRightString(190 * mm, 10 * mm, f"日本語版 p.{doc.page}")
        canvas.restoreState()
    return _on_page


def generate_pdf(
    output_path: str | Path,
    book_title: str,
    translated_pages: Iterable[TranslatedPage],
    metadata: dict | None = None,
):
    """日本語訳PDFを生成して書き出す。"""
    _register_fonts()
    pages = list(translated_pages)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=18 * mm,
        title=metadata.get("title", book_title) if metadata else book_title,
        author=metadata.get("author", "") if metadata else "",
    )

    # === スタイル定義 ===
    title_style = ParagraphStyle(
        name="Title", fontName=FONT_BOLD, fontSize=24, leading=32,
        alignment=1, spaceAfter=24,
    )
    meta_style = ParagraphStyle(
        name="Meta", fontName=FONT_REGULAR, fontSize=11, leading=18,
        alignment=1, spaceAfter=6,
    )
    h1_style = ParagraphStyle(
        name="H1", fontName=FONT_BOLD, fontSize=20, leading=30,
        spaceBefore=16, spaceAfter=14, textColor="#000000",
    )
    h2_style = ParagraphStyle(
        name="H2", fontName=FONT_BOLD, fontSize=15, leading=24,
        spaceBefore=12, spaceAfter=10, textColor="#222222",
    )
    h3_style = ParagraphStyle(
        name="H3", fontName=FONT_BOLD, fontSize=12, leading=20,
        spaceBefore=8, spaceAfter=6, textColor="#333333",
    )
    body_style = ParagraphStyle(
        name="Body", fontName=FONT_REGULAR, fontSize=10.5, leading=18,
        spaceAfter=6,
    )
    source_pg_style = ParagraphStyle(
        name="SourcePage", fontName=FONT_REGULAR, fontSize=8, leading=12,
        alignment=2, textColor="#888888", spaceBefore=8, spaceAfter=4,
    )
    skip_style = ParagraphStyle(
        name="Skip", fontName=FONT_REGULAR, fontSize=8, leading=12,
        alignment=2, textColor="#aaaaaa", spaceBefore=4, spaceAfter=4,
    )

    flow = []

    # === 表紙 ===
    flow.append(Spacer(1, 50 * mm))
    flow.append(Paragraph(_escape(book_title), title_style))
    flow.append(Spacer(1, 30 * mm))
    flow.append(Paragraph("日本語訳", meta_style))
    if metadata:
        if metadata.get("source_filename"):
            flow.append(Paragraph(f"原書: {_escape(metadata['source_filename'])}", meta_style))
        if metadata.get("date"):
            flow.append(Paragraph(f"翻訳日: {_escape(metadata['date'])}", meta_style))
        if metadata.get("source_page_count"):
            flow.append(Paragraph(f"原書ページ数: {metadata['source_page_count']}ページ", meta_style))
    flow.append(PageBreak())

    # === 本文 ===
    # 連続するスキップ/空ページはまとめて1行で表示
    skip_buffer: list[tuple[int, str]] = []

    def flush_skip():
        if not skip_buffer:
            return
        nums = [n for n, _ in skip_buffer]
        reasons = sorted(set(r for _, r in skip_buffer if r))
        range_str = (
            f"p.{nums[0]}" if len(nums) == 1
            else f"p.{nums[0]}-{nums[-1]}"
        )
        reason_str = ("・".join(reasons)) if reasons else "本文外"
        flow.append(Paragraph(
            f"（原書 {range_str} は{_escape(reason_str)}のため省略）",
            skip_style,
        ))
        skip_buffer.clear()

    for tp in pages:
        if tp.skipped or not tp.translated_text.strip():
            skip_buffer.append((tp.source_page_number, tp.skip_reason or ""))
            continue

        flush_skip()

        # 元PDFのページ番号を表示
        flow.append(Paragraph(f"原書 p.{tp.source_page_number}", source_pg_style))

        # マークダウン見出しを解釈して描画
        for line in tp.translated_text.split("\n"):
            line = line.rstrip()
            if not line:
                continue

            style, content = _parse_markdown_line(line, h1_style, h2_style, h3_style, body_style)
            flow.append(Paragraph(_escape(content), style))

    flush_skip()

    on_page = _make_footer_callback(book_title)
    doc.build(flow, onFirstPage=on_page, onLaterPages=on_page)


def _parse_markdown_line(line, h1_style, h2_style, h3_style, body_style):
    """マークダウン見出し（# / ## / ###）を解釈してスタイルとテキストを返す"""
    s = line.lstrip()
    if s.startswith("### "):
        return h3_style, s[4:]
    if s.startswith("## "):
        return h2_style, s[3:]
    if s.startswith("# "):
        return h1_style, s[2:]
    return body_style, line.strip()


def _escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
