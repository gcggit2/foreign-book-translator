"""洋書翻訳システム - Streamlitエントリーポイント"""

from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path

import streamlit as st

from core.llm_clients import GeminiClient
from core.pdf_extractor import extract_pdf
from core.pdf_generator import generate_pdf
from core.translator import translate_pages
from pages.shared_state import init_state
from storage import jobs
from ui.auth import require_auth
from ui.theme import apply_theme, render_flow, render_top_nav, section_label


# ===== ページ設定 =====
st.set_page_config(
    page_title="洋書翻訳システム",
    page_icon="📚",
    layout="centered",
    initial_sidebar_state="collapsed",
)
apply_theme()
require_auth()
init_state()
render_top_nav(active="translate")


DATA_DIR = Path(__file__).resolve().parent / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
OUTPUTS_DIR = DATA_DIR / "outputs"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)


# ===== ヒーロー =====
st.markdown("# 翻訳")
st.markdown(
    "<p style='color:#64748B;font-size:14px;margin-top:6px;'>"
    "英語書籍PDFをアップロードすると、章タイトル・本文を日本語訳したPDFを生成します。"
    "</p>",
    unsafe_allow_html=True,
)


# ===== APIキー未設定なら警告 =====
if not st.session_state.gemini_api_key:
    st.error(
        "Gemini APIキーが未設定です。管理者に連絡してください。"
        "（管理者は Streamlit Cloud の Secrets で GEMINI_API_KEY を設定する必要があります）"
    )
    st.stop()


# ===== 大まかな流れ =====
render_flow(
    active_step=1,
    steps=["アップロード", "翻訳実行", "PDF取得"],
)


# ===== アップロードフォーム =====
section_label("Step 1 │ ファイル選択")

uploaded = st.file_uploader(
    label="英語書籍PDF",
    type=["pdf"],
    accept_multiple_files=False,
    label_visibility="collapsed",
)


# ===== 詳細設定 =====
section_label("Step 2 │ オプション（任意）")

with st.expander("詳細設定", expanded=False):
    style_override = st.selectbox(
        "翻訳スタイル",
        ["ですます調", "である調"],
        index=0 if st.session_state.translation_style == "ですます調" else 1,
    )
if "style_override" not in dir():
    style_override = st.session_state.translation_style


# ===== 実行ボタン =====
section_label("Step 3 │ 実行")

start = st.button(
    "翻訳を開始",
    type="primary",
    disabled=uploaded is None,
    use_container_width=True,
)


# ===== 翻訳実行 =====
if start and uploaded:
    book_title = uploaded.name.removesuffix(".pdf").replace("_", " ").strip()

    source_path = UPLOADS_DIR / f"{int(time.time())}_{uploaded.name}"
    with open(source_path, "wb") as f:
        f.write(uploaded.getbuffer())

    job_id = jobs.create_job(uploaded.name, book_title, str(source_path))

    st.divider()

    progress = st.progress(0, text="開始しています…")
    status_box = st.empty()

    try:
        client = GeminiClient(st.session_state.gemini_api_key)

        # 1. PDF抽出
        status_box.info("PDFからテキストを抽出中…")
        jobs.update_job(job_id, status=jobs.STATUS_EXTRACTING)
        progress.progress(5, text="PDFテキスト抽出中…")
        extracted = extract_pdf(source_path)
        if not extracted.has_text:
            raise RuntimeError(
                "このPDFはOCR済みではない可能性があります（テキストが少なすぎる）。"
                "OCR化したPDFをアップロードしてください。"
            )

        total_pages = extracted.page_count
        non_empty_pages = sum(1 for t in extracted.page_texts if t.strip())

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("総ページ数", f"{total_pages}")
        with col2:
            st.metric("翻訳対象", f"{non_empty_pages}")
        with col3:
            st.metric("総文字数", f"{len(extracted.full_text):,}")

        # 2. 翻訳
        parallel = st.session_state.get("parallel_count", 5)
        status_box.info(f"{non_empty_pages}ページを翻訳中（並列{parallel}）…")
        jobs.update_job(
            job_id,
            status=jobs.STATUS_TRANSLATING,
            chapter_count=total_pages,
        )

        def on_progress(done, total, msg):
            ratio = 10 + int((done / max(total, 1)) * 80)
            progress.progress(ratio, text=f"翻訳中 {done}/{total}ページ")
            jobs.update_job(job_id, progress_done=done)

        translated_pages = translate_pages(
            page_texts=extracted.page_texts,
            client=client,
            book_title=book_title,
            style=style_override,
            parallel=parallel,
            progress_cb=on_progress,
        )

        # 3. PDF生成
        status_box.info("翻訳済みPDFを生成中…")
        jobs.update_job(job_id, status=jobs.STATUS_GENERATING)
        progress.progress(95, text="PDF生成中…")
        output_filename = f"{book_title}_日本語訳.pdf"
        output_path = OUTPUTS_DIR / f"{job_id}_{output_filename}"
        generate_pdf(
            output_path=output_path,
            book_title=book_title,
            translated_pages=translated_pages,
            metadata={
                "source_filename": uploaded.name,
                "date": datetime.now().strftime("%Y年%m月%d日"),
                "source_page_count": total_pages,
            },
        )

        # 4. 完了
        jobs.update_job(job_id, status=jobs.STATUS_DONE, output_path=str(output_path))
        progress.progress(100, text="完了")
        status_box.empty()

        st.divider()

        st.markdown(
            "<div style='background:#ECFDF5;border:1px solid #A7F3D0;"
            "border-left:3px solid #047857;border-radius:2px;"
            "padding:18px 20px;margin:16px 0;'>"
            "<div style='font-weight:700;color:#065F46;font-size:15px;'>翻訳完了</div>"
            "<div style='margin-top:6px;color:#047857;font-size:13px;'>"
            "下のボタンから日本語訳PDFをダウンロードしてください。"
            "</div></div>",
            unsafe_allow_html=True,
        )

        with open(output_path, "rb") as f:
            st.download_button(
                label="翻訳済みPDFをダウンロード",
                data=f.read(),
                file_name=output_filename,
                mime="application/pdf",
                use_container_width=True,
            )

    except Exception as e:
        jobs.update_job(job_id, status=jobs.STATUS_ERROR, error=str(e))
        status_box.empty()
        st.error(f"翻訳中にエラーが発生しました: {e}")
        with st.expander("詳細（開発者向け）"):
            st.exception(e)
