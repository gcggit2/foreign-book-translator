"""設定ページ"""

import streamlit as st

from pages.shared_state import init_state, is_api_key_from_secrets
from ui.auth import require_auth
from ui.theme import apply_theme, badge, render_top_nav, section_label


st.set_page_config(
    page_title="設定 - 洋書翻訳",
    page_icon="⚙️",
    initial_sidebar_state="collapsed",
)
apply_theme()
require_auth()
init_state()
render_top_nav(active="settings")


st.markdown("# 設定")
st.markdown(
    "<p style='color:#64748B;font-size:14px;margin-top:6px;'>"
    "翻訳スタイル・性能の設定"
    "</p>",
    unsafe_allow_html=True,
)


# ====== APIキー情報（読み取り専用） ======
section_label("Gemini API キー")

if st.session_state.gemini_api_key:
    if is_api_key_from_secrets():
        st.markdown(badge("Streamlit Secrets で設定済", "success"), unsafe_allow_html=True)
        st.caption(
            "APIキーは Streamlit Cloud の Secrets で管理されています。"
            "変更する場合は管理者が `share.streamlit.io` の Settings → Secrets で書き換えてください。"
        )
    else:
        st.markdown(badge("ローカル設定で設定済", "info"), unsafe_allow_html=True)
        st.caption("ローカル環境変数または .env ファイルから読み込まれています。")
else:
    st.markdown(badge("未設定", "danger"), unsafe_allow_html=True)
    st.caption(
        "APIキーが未設定です。管理者にお問い合わせください。"
    )

st.divider()


# ====== 翻訳設定 ======
section_label("翻訳スタイル")

style = st.radio(
    "翻訳スタイル",
    ["ですます調", "である調"],
    index=0 if st.session_state.translation_style == "ですます調" else 1,
    horizontal=True,
    label_visibility="collapsed",
)
st.session_state.translation_style = style

st.divider()


# ====== Gemini API階層 ======
section_label("Gemini API 階層")
st.caption(
    "無料枠は1分5リクエストの制限あり。有料枠なら並列5で高速化されます。"
)

current_label = (
    "有料枠（並列5・高速）" if st.session_state.parallel_count > 1
    else "無料枠（並列1・低速）"
)
st.markdown(
    f'<div style="margin:8px 0 14px;">{badge("現在", "muted")} '
    f'<span style="margin-left:8px;font-weight:600;">{current_label}</span></div>',
    unsafe_allow_html=True,
)

tier = st.radio(
    "階層",
    ["無料枠（並列1・低速・安全）", "有料枠（並列5・高速）"],
    index=0 if st.session_state.parallel_count <= 1 else 1,
    label_visibility="collapsed",
)
st.session_state.parallel_count = 1 if tier.startswith("無料") else 5

st.divider()


# ====== 動作確認 ======
section_label("動作確認")
st.caption("APIキーが正しく動作するかテスト")

if st.button("Gemini API疎通テスト", use_container_width=True):
    if not st.session_state.gemini_api_key:
        st.error("APIキーが未設定です")
    else:
        try:
            with st.spinner("Gemini API を呼び出し中…"):
                from core.llm_clients import GeminiClient
                client = GeminiClient(st.session_state.gemini_api_key)
                resp = client.generate(
                    prompt="日本語で「接続テスト成功」とだけ返答してください。",
                    max_tokens=2048,
                    temperature=0.0,
                )
            text = (resp.text or "").strip()
            if text:
                st.success(f"疎通成功 — Gemini応答: **{text}**")
                st.caption(f"使用トークン: 入力={resp.input_tokens}, 出力={resp.output_tokens}")
            else:
                st.warning("応答が空でした。APIキーは有効ですが、モデル側で内容が生成されませんでした。")
        except Exception as e:
            st.error(f"失敗: {e}")
            with st.expander("詳細"):
                st.exception(e)
