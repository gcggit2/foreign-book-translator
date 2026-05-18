"""章境界検出（LLM活用）

正規表現は使わず、LLM自身に「目次から章一覧を返して」と頼む方式。
複数のフォールバックで「常に何かしらの結果を返す」を保証。
"""

from __future__ import annotations

from dataclasses import dataclass

from .llm_clients import GeminiClient
from .pdf_extractor import ExtractedPdf, get_first_n_pages_text


@dataclass
class Chapter:
    """1章分の情報"""
    number: int
    title: str
    start_offset: int
    end_offset: int  # 次章の開始位置 or 文書末尾

    def text(self, full_text: str) -> str:
        return full_text[self.start_offset:self.end_offset]


@dataclass
class ChapterDetectionResult:
    chapters: list[Chapter]
    method: str  # 検出方法（デバッグ用）


# プロンプト：目次から章一覧を取得
TOC_PROMPT = """以下は英語書籍のPDFから抽出したテキストの先頭部分です。
このテキストには通常、目次（Table of Contents）が含まれています。

【タスク】
目次を読み取り、本書の章/セクション一覧を抽出してください。

【出力フォーマット】
以下のJSON形式で返してください（マークダウンや前置きは不要、JSONのみ）。

{{
  "found": true,
  "chapters": [
    {{"number": 1, "title": "Chapter 1 タイトル"}},
    {{"number": 2, "title": "Chapter 2 タイトル"}}
  ]
}}

【注意事項】
- "title"は本文中で実際にその章の見出しとして使われている文字列をそのまま記載してください（位置検索に使うため）
- 番号と区切り記号（: や - 等）は省かない（例: "Chapter 1: The Beginning"）
- 目次が見つからない、または不完全な場合は {{"found": false, "reason": "理由"}} を返してください
- 章は3個以上見つかった場合のみ found=true としてください

【テキスト】
{text}
"""


def detect_chapters(
    extracted: ExtractedPdf,
    client: GeminiClient,
) -> ChapterDetectionResult:
    """章境界を検出する。

    3段階フォールバック:
      1. LLMで目次から章一覧を取得 → 本文中で位置検索
      2. LLMに本文を読ませて論理セクションに分けてもらう
      3. 文字数で10章に均等分割
    """
    full_text = extracted.full_text

    # === 第1段: 目次解析 ===
    toc_text = get_first_n_pages_text(extracted, n=15)
    try:
        result = client.generate_json(
            prompt=TOC_PROMPT.format(text=toc_text[:30000]),
            model=client.DETECTION_MODEL,
            max_tokens=8192,
            temperature=0.0,
        )
        if result.get("found") and result.get("chapters"):
            chapters = _locate_chapters_in_text(result["chapters"], full_text)
            if len(chapters) >= 2:
                return ChapterDetectionResult(chapters=chapters, method="目次から検出")
    except Exception as e:
        print(f"[chapter_detector] 第1段失敗: {e}")

    # === 第2段: 均等分割（10章） ===
    chapters = _even_split(full_text, count=10)
    return ChapterDetectionResult(
        chapters=chapters,
        method="自動検出失敗→10章で均等分割",
    )


def _locate_chapters_in_text(
    chapter_list: list[dict],
    full_text: str,
) -> list[Chapter]:
    """LLMが返した章タイトル群を本文中で検索して位置を確定。

    位置検索は完全一致 → 前方部分一致の順で試す。
    見つからない章はスキップ。
    """
    located = []
    search_start = 0
    for item in chapter_list:
        title = item.get("title", "").strip()
        if not title:
            continue

        # まず完全一致
        pos = full_text.find(title, search_start)
        if pos == -1:
            # タイトルが長すぎて改行などで分断されている可能性
            # 先頭30文字で検索
            short_title = title[:30]
            pos = full_text.find(short_title, search_start)

        if pos != -1:
            located.append({
                "number": item.get("number", len(located) + 1),
                "title": title,
                "start_offset": pos,
            })
            search_start = pos + 1

    if len(located) < 2:
        return []

    # end_offset を埋める
    chapters = []
    for i, loc in enumerate(located):
        end = located[i + 1]["start_offset"] if i + 1 < len(located) else len(full_text)
        chapters.append(Chapter(
            number=loc["number"],
            title=loc["title"],
            start_offset=loc["start_offset"],
            end_offset=end,
        ))
    return chapters


def _even_split(full_text: str, count: int) -> list[Chapter]:
    """文字数で均等分割。段落境界に寄せる。"""
    chapters = []
    chunk_size = max(len(full_text) // count, 1)
    for i in range(count):
        start = i * chunk_size
        if i > 0:
            nearby = full_text.find("\n\n", max(0, start - 200))
            if 0 <= nearby < start + 500:
                start = nearby + 2
        end = (i + 1) * chunk_size if i < count - 1 else len(full_text)
        chapters.append(Chapter(
            number=i + 1,
            title=f"Section {i + 1}",
            start_offset=start,
            end_offset=end,
        ))
    return chapters
