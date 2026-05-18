"""設定ページ"""

import streamlit as st

from pages.shared_state import delete_from_env, init_state, save_to_env
from ui.theme import apply_theme, badge, render_top_nav, section_label


st.set_page_config(
    page_title="設定 - 洋書翻訳",
    page_icon="⚙️",
    initial_sidebar_state="collapsed",
)
apply_theme()
init_state()
render_top_nav(active="settings")


st.markdown("# 設定")
st.markdown(
    "<p style='color:#64748B;font-size:14px;margin-top:6px;'>"
    "APIキー、翻訳スタイル、性能の設定"
    "</p>",
    unsafe_allow_html=True,
)


# ====== Gemini APIキー ======
section_label("Gemini API キー")

if st.session_state.gemini_api_key:
    st.markdown(badge("設定済", "success"), unsafe_allow_html=True)
else:
    st.markdown(badge("未設定", "warning"), unsafe_allow_html=True)

st.write("")
st.caption(
    "Google AI Studio で取得したAPIキーを入力。"
    "「保存」を押すと `.env` ファイルに保存され、次回起動時も自動読込されます。"
)
st.markdown("[Google AI Studio でAPIキーを取得](https://aistudio.google.com/apikey)")

api_key = st.text_input(
    "APIキー",
    value=st.session_state.gemini_api_key,
    type="password",
    placeholder="AIza...",
    label_visibility="collapsed",
)

col_save, col_clear, _ = st.columns([1, 1, 2])
with col_save:
    if st.button("保存", type="primary", use_container_width=True):
        if api_key:
            st.session_state.gemini_api_key = api_key
            save_to_env("GEMINI_API_KEY", api_key)
            st.success("APIキーを `.env` に保存しました")
        else:
            st.error("APIキーが入力されていません")
with col_clear:
    if st.button("クリア", use_container_width=True):
        st.session_state.gemini_api_key = ""
        delete_from_env("GEMINI_API_KEY")
        st.success("クリアしました")
        st.rerun()

if api_key != st.session_state.gemini_api_key:
    st.session_state.gemini_api_key = api_key

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
    "無料枠は1分5リクエストの制限あり。月数百円で有料枠に切り替えると並列5で高速化されます。"
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

with st.expander("有料枠への切替方法"):
    st.markdown("""
1. [Google Cloud Console](https://console.cloud.google.com/billing) を開く
2. APIキーを発行したプロジェクトに **お支払い情報** を追加
3. 「**予算とアラート**」で月額上限（例: 3,000円）を設定
4. このページで「**有料枠**」を選択

→ 1分5リクエストの制限が消え、章ごとに5並列で高速化（200ページで5〜10分程度）
""")

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
