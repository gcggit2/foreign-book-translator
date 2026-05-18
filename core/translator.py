"""翻訳ロジック

シンプル設計（章検出なし）:
  - PDFのページ単位で翻訳
  - 並列実行で高速化
  - 元PDFのページ番号を保持
  - 著作権・目次・索引ページはLLMが判定してスキップ
  - 見出しは # / ## / ### マーカーで返してPDF生成側で太字化
"""

from __future__ import annotations

from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Optional

from .llm_clients import GeminiClient


@dataclass
class TranslatedPage:
    """1ページ分の翻訳結果"""
    source_page_number: int   # 元PDFの何ページ目か（1始まり）
    translated_text: str      # 日本語訳（マークダウン見出し # / ## / ### を含む）
    skipped: bool = False     # 翻訳対象外と判定されたか
    skip_reason: str = ""     # スキップ理由（著作権ページ等）


MAX_CHARS_PER_CHUNK = 6000   # 1リクエストで翻訳する原文の最大文字数
DEFAULT_PARALLEL = 5         # ページ並列度


TRANSLATION_PROMPT = """あなたはプロの翻訳者です。以下は英語書籍の1ページ（または1ページの一部）です。
翻訳すべきか判断し、必要に応じて自然な日本語に翻訳してください。

【ページの判定ルール】
以下のページは "skip": true で空文字を返してください（翻訳不要）:
- 著作権ページ（Copyright、ISBN、出版社情報、装丁クレジット等のみ）
- 目次（Table of Contents - 章タイトルやページ番号が列挙されているだけ）
- 索引（Index）
- 参考文献リスト（Bibliography, References）
- 図表のキャプションすらない白紙・装飾のみのページ
- 出版社の宣伝・近刊リストなど本文と無関係なページ

以下は翻訳してください（"skip": false）:
- 献辞（Dedication - 「To my wife..」のような短文）
- 序文・プロローグ・はじめに
- 本文すべて
- 章タイトル・見出し
- 謝辞（Acknowledgments）
- 著者紹介（About the Author）
- 本文に関連する注釈・脚注

【翻訳ルール】
- {style}で統一
- 原文の意味を正確に、日本語として自然に
- 直訳より意訳寄り、ただし原意は保持
- 専門用語は適切に訳出（必要なら原語併記）
- **見出しのマークアップ**:
  - 章タイトル（"Chapter N: Title"、"Part N: Title" 等）→ 行頭に **# **
  - セクション見出し（章の中の節）→ 行頭に **## **
  - サブ見出し → 行頭に **### **
  - 通常の段落は何も付けない
- 章タイトルは「第N章: タイトル」「第N部: タイトル」のように訳す
- ヘッダー・フッター・ページ番号のみの行は省く

【出力形式】
以下のJSON形式のみを出力（マークダウンコードブロック・前置きは付けない）:
{{
  "skip": false,
  "skip_reason": "",
  "translation": "翻訳本文（マークダウン見出し含む）"
}}

skipの場合:
{{
  "skip": true,
  "skip_reason": "著作権ページ",
  "translation": ""
}}

【書名】{book_title}
【元PDFのページ番号】{page_number}{chunk_info}

【原文】
{text}
"""


def translate_pages(
    page_texts: list[str],
    client: GeminiClient,
    book_title: str = "",
    style: str = "ですます調",
    parallel: int = DEFAULT_PARALLEL,
    progress_cb: Optional[Callable[[int, int, str], None]] = None,
) -> list[TranslatedPage]:
    """全ページを翻訳する（並列実行）。"""
    work_items = []
    for i, text in enumerate(page_texts):
        page_num = i + 1
        if not text or len(text.strip()) < 30:
            work_items.append((page_num, ""))
        else:
            work_items.append((page_num, text))

    total = sum(1 for _, t in work_items if t)
    results: dict[int, TranslatedPage] = {}
    completed = 0

    def _job(page_num: int, text: str) -> TranslatedPage:
        if not text:
            return TranslatedPage(
                source_page_number=page_num,
                translated_text="",
                skipped=True,
                skip_reason="空ページ",
            )
        return _translate_one_page(
            text=text,
            client=client,
            book_title=book_title,
            style=style,
            page_number=page_num,
        )

    with ThreadPoolExecutor(max_workers=parallel) as executor:
        futures = {executor.submit(_job, p, t): p for p, t in work_items}
        for fut in as_completed(futures):
            page = futures[fut]
            tp = fut.result()
            results[page] = tp
            if not tp.skipped:
                completed += 1
                if progress_cb:
                    progress_cb(completed, total, f"p.{page} 完了")
            elif progress_cb:
                progress_cb(completed, total, f"p.{page} スキップ({tp.skip_reason})")

    return [results[p] for p, _ in work_items]


def _translate_one_page(
    text: str,
    client: GeminiClient,
    book_title: str,
    style: str,
    page_number: int,
) -> TranslatedPage:
    """1ページ分を翻訳。長ければチャンク分割。"""
    chunks = _split_into_chunks(text, MAX_CHARS_PER_CHUNK)
    translations = []
    skip_results = []
    for ci, chunk in enumerate(chunks):
        chunk_info = (
            f"\n（このページは{len(chunks)}個に分割されており、{ci + 1}番目の部分です）"
            if len(chunks) > 1 else ""
        )
        prompt = TRANSLATION_PROMPT.format(
            style=style,
            book_title=book_title or "（不明）",
            page_number=page_number,
            chunk_info=chunk_info,
            text=chunk,
        )
        result = client.generate_json(
            prompt=prompt,
            model=client.TRANSLATION_MODEL,
            max_tokens=32768,
            temperature=0.3,
        )
        translations.append(result.get("translation", ""))
        skip_results.append((bool(result.get("skip")), result.get("skip_reason", "")))

    # スキップ判定: すべてのチャンクがskipなら、ページ全体をskip扱い
    all_skipped = all(s[0] for s in skip_results)
    if all_skipped:
        reasons = [s[1] for s in skip_results if s[1]]
        return TranslatedPage(
            source_page_number=page_number,
            translated_text="",
            skipped=True,
            skip_reason=reasons[0] if reasons else "本文外（著作権・目次等）",
        )

    return TranslatedPage(
        source_page_number=page_number,
        translated_text="\n\n".join(t for t in translations if t),
        skipped=False,
    )


def _split_into_chunks(text: str, max_chars: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    chunks = []
    paragraphs = text.split("\n\n")
    current = ""
    for para in paragraphs:
        if len(current) + len(para) + 2 > max_chars and current:
            chunks.append(current)
            current = para
        else:
            current = current + "\n\n" + para if current else para
    if current:
        chunks.append(current)
    return chunks
