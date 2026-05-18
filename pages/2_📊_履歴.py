"""履歴ページ"""

from pathlib import Path

import streamlit as st

from pages.shared_state import init_state
from storage import jobs
from ui.auth import require_auth
from ui.theme import apply_theme, badge, render_top_nav, section_label


st.set_page_config(
    page_title="履歴 - 洋書翻訳",
    page_icon="📊",
    initial_sidebar_state="collapsed",
)
apply_theme()
require_auth()
init_state()
render_top_nav(active="history")


st.markdown("# 履歴")
st.markdown(
    "<p style='color:#64748B;font-size:14px;margin-top:6px;'>"
    "過去の翻訳ジョブの一覧と再ダウンロード"
    "</p>",
    unsafe_allow_html=True,
)


def _delete_job_with_files(job):
    """ジョブと関連ファイルを削除"""
    jobs.delete_job(job.id)
    for p_str in [job.source_path, job.output_path]:
        if p_str and Path(p_str).exists():
            try:
                Path(p_str).unlink()
            except Exception:
                pass


all_jobs = jobs.list_jobs(limit=200)


# === 空状態 ===
if not all_jobs:
    st.markdown(
        """
        <div style="border:1px dashed #D1D5DB;border-radius:4px;
        padding:60px 24px;text-align:center;margin:24px 0;background:#F9FAFB;">
            <div style="color:#475569;font-weight:600;font-size:15px;">
                まだ翻訳ジョブはありません
            </div>
            <div style="color:#94A3B8;font-size:13px;margin-top:6px;">
                上部メニュー「翻訳」から開始してください
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.page_link("app.py", label="翻訳ページを開く")
    st.stop()


# === サマリ ===
done_count = sum(1 for j in all_jobs if j.status == jobs.STATUS_DONE)
error_count = sum(1 for j in all_jobs if j.status == jobs.STATUS_ERROR)
in_progress = len(all_jobs) - done_count - error_count
total_pages = sum(j.chapter_count or 0 for j in all_jobs if j.status == jobs.STATUS_DONE)

section_label("サマリ")
col1, col2, col3, col4 = st.columns(4)
col1.metric("総ジョブ", len(all_jobs))
col2.metric("完了", done_count)
col3.metric("翻訳ページ累計", f"{total_pages:,}")
col4.metric("エラー", error_count)

if in_progress > 0:
    st.info(f"現在 {in_progress} 件のジョブが処理中です")


# === 一括操作 ===
st.divider()
section_label("一括操作")

# 削除確認状態
if "confirm_delete_all" not in st.session_state:
    st.session_state.confirm_delete_all = False
if "confirm_delete_done" not in st.session_state:
    st.session_state.confirm_delete_done = False

col1, col2, col3 = st.columns([1, 1, 2])

with col1:
    if st.button("完了ジョブを削除", use_container_width=True, disabled=done_count == 0):
        st.session_state.confirm_delete_done = True

with col2:
    if st.button("全ジョブを削除", use_container_width=True, disabled=len(all_jobs) == 0):
        st.session_state.confirm_delete_all = True

# 確認モーダル風
if st.session_state.confirm_delete_done:
    st.warning(f"完了済みの {done_count} 件を削除します。関連PDFファイルも削除されます。")
    c1, c2, _ = st.columns([1, 1, 3])
    with c1:
        if st.button("削除実行", type="primary", key="exec_del_done"):
            for j in all_jobs:
                if j.status == jobs.STATUS_DONE:
                    _delete_job_with_files(j)
            st.session_state.confirm_delete_done = False
            st.success("削除しました")
            st.rerun()
    with c2:
        if st.button("キャンセル", key="cancel_del_done"):
            st.session_state.confirm_delete_done = False
            st.rerun()

if st.session_state.confirm_delete_all:
    st.warning(f"すべての {len(all_jobs)} 件を削除します。関連PDFファイルも削除されます。")
    c1, c2, _ = st.columns([1, 1, 3])
    with c1:
        if st.button("削除実行", type="primary", key="exec_del_all"):
            for j in all_jobs:
                _delete_job_with_files(j)
            st.session_state.confirm_delete_all = False
            st.success("削除しました")
            st.rerun()
    with c2:
        if st.button("キャンセル", key="cancel_del_all"):
            st.session_state.confirm_delete_all = False
            st.rerun()


# === 一覧 ===
st.divider()
section_label("ジョブ一覧")

for job in all_jobs:
    status_info = {
        jobs.STATUS_DONE: ("success", "完了"),
        jobs.STATUS_ERROR: ("danger", "エラー"),
    }.get(job.status, ("warning", job.status))

    badge_kind, badge_text = status_info

    with st.expander(f"#{job.id}  {job.book_title}"):
        st.markdown(
            f'<div style="margin:-8px 0 12px;">{badge(badge_text, badge_kind)}</div>',
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**ファイル名**　`{job.filename}`")
            st.markdown(f"**受付日時**　{job.created_at}")
        with col2:
            st.markdown(f"**ページ数**　{job.chapter_count}")
            if job.progress_done and job.chapter_count:
                st.markdown(f"**進捗**　{job.progress_done} / {job.chapter_count}")

        if job.error:
            st.error(f"エラー: {job.error}")

        if job.output_path and Path(job.output_path).exists():
            with open(job.output_path, "rb") as f:
                st.download_button(
                    label="翻訳済みPDFをダウンロード",
                    data=f.read(),
                    file_name=Path(job.output_path).name,
                    mime="application/pdf",
                    key=f"dl_{job.id}",
                    use_container_width=True,
                )

        if st.button("このジョブを削除", key=f"del_{job.id}"):
            _delete_job_with_files(job)
            st.rerun()
