"""履歴ページ

Drive連携が有効なら Google Drive上のPDF一覧を主表示。
未設定なら従来通り SQLite（ローカル一時保存）の履歴を表示。
"""

import re
from datetime import datetime
from pathlib import Path

import streamlit as st

from core import drive_storage
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
    "過去の翻訳済PDFの一覧と再ダウンロード"
    "</p>",
    unsafe_allow_html=True,
)


# =====================================================================
#  メイン：Drive連携が有効ならDriveの一覧を表示
# =====================================================================
drive_enabled = drive_storage.is_available()

if drive_enabled:
    section_label("クラウド保存（Google Drive）")

    try:
        drive_files = drive_storage.list_files(limit=500)
    except Exception as e:
        st.error(f"Drive一覧の取得に失敗しました: {e}")
        drive_files = []

    if not drive_files:
        st.markdown(
            """
            <div style="border:1px dashed #D1D5DB;border-radius:4px;
            padding:60px 24px;text-align:center;margin:24px 0;background:#F9FAFB;">
                <div style="color:#475569;font-weight:600;font-size:15px;">
                    まだ翻訳済PDFはありません
                </div>
                <div style="color:#94A3B8;font-size:13px;margin-top:6px;">
                    上部メニュー「翻訳」から翻訳を開始してください
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        # サマリ
        total_size_mb = sum(f.size_bytes for f in drive_files) / (1024 * 1024)
        col1, col2 = st.columns(2)
        col1.metric("保存件数", len(drive_files))
        col2.metric("合計サイズ", f"{total_size_mb:.1f} MB")

        st.divider()
        section_label("ファイル一覧")

        # ファイル名から日時と書名を抽出
        # 命名規則: "YYYYMMDD_HHMMSS_書名_日本語訳.pdf"
        FILENAME_RE = re.compile(r"^(\d{8})_(\d{6})_(.+?)_日本語訳\.pdf$")

        for df in drive_files:
            m = FILENAME_RE.match(df.name)
            if m:
                date_str, time_str, book_title = m.groups()
                created_dt = (
                    f"{date_str[:4]}/{date_str[4:6]}/{date_str[6:8]} "
                    f"{time_str[:2]}:{time_str[2:4]}"
                )
                display_title = book_title
            else:
                display_title = df.name.replace(".pdf", "")
                created_dt = df.created_at[:16].replace("T", " ") if df.created_at else "-"

            with st.expander(f"{display_title} — {created_dt}"):
                col_l, col_r = st.columns([3, 1])
                with col_l:
                    st.markdown(f"**ファイル名**　`{df.name}`")
                    st.markdown(f"**サイズ**　{df.size_bytes / 1024:.0f} KB")
                    if df.web_view_link:
                        st.markdown(f"[Google Drive で開く]({df.web_view_link})")

                # ダウンロードボタン（Driveから取得）
                if st.button("ダウンロード準備", key=f"prep_{df.id}"):
                    try:
                        with st.spinner("Drive からダウンロード中…"):
                            data = drive_storage.download_file(df.id)
                        st.session_state[f"dl_data_{df.id}"] = data
                    except Exception as e:
                        st.error(f"ダウンロード失敗: {e}")

                if f"dl_data_{df.id}" in st.session_state:
                    st.download_button(
                        label="このボタンを押して保存",
                        data=st.session_state[f"dl_data_{df.id}"],
                        file_name=df.name,
                        mime="application/pdf",
                        key=f"dl_btn_{df.id}",
                        use_container_width=True,
                    )

                # 削除
                if st.button("このファイルを削除", key=f"del_{df.id}"):
                    try:
                        drive_storage.delete_file(df.id)
                        st.success("削除しました")
                        st.rerun()
                    except Exception as e:
                        st.error(f"削除失敗: {e}")

else:
    # =================================================================
    #  Drive 未設定時: 従来通りローカルSQLite履歴を表示
    # =================================================================
    st.info(
        "Google Drive 連携が未設定のため、履歴は一時的なローカル保存のみです。"
        "アプリ再起動で消えます。"
    )

    def _delete_job_with_files(job):
        jobs.delete_job(job.id)
        for p_str in [job.source_path, job.output_path]:
            if p_str and Path(p_str).exists():
                try:
                    Path(p_str).unlink()
                except Exception:
                    pass

    all_jobs = jobs.list_jobs(limit=200)

    if not all_jobs:
        st.markdown(
            """
            <div style="border:1px dashed #D1D5DB;border-radius:4px;
            padding:60px 24px;text-align:center;margin:24px 0;background:#F9FAFB;">
                <div style="color:#475569;font-weight:600;font-size:15px;">
                    まだ翻訳ジョブはありません
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.stop()

    section_label("ジョブ一覧（一時保存）")
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
            st.markdown(f"**ファイル名**　`{job.filename}`")
            st.markdown(f"**受付日時**　{job.created_at}")
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
