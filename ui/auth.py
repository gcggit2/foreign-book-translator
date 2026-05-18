"""ベーシック認証（共有パスワード方式）

Streamlit Secrets の APP_PASSWORD と一致したら通過。
未設定なら認証スキップ（ローカル開発時の挙動）。
"""

from __future__ import annotations

import streamlit as st


SESSION_KEY = "auth_passed"


def _get_expected_password() -> str | None:
    """Streamlit Secrets からパスワードを取得。未設定なら None"""
    try:
        # st.secrets はローカルで .streamlit/secrets.toml がなければ例外を投げる
        return st.secrets.get("APP_PASSWORD", None)
    except Exception:
        return None


def require_auth():
    """各ページの先頭で呼ぶ。
    認証通過していなければパスワード入力画面を表示してst.stop()する。
    """
    expected = _get_expected_password()
    if not expected:
        # パスワード未設定 → 認証スキップ（ローカル開発用）
        return

    if st.session_state.get(SESSION_KEY):
        return

    # === パスワード入力画面 ===
    _render_password_form(expected)
    st.stop()


def _render_password_form(expected: str):
    # 中央寄せの簡素なパスワード入力画面
    st.markdown(
        """
        <style>
        /* 認証画面では nav 非表示にしてシンプルに */
        .auth-wrapper {
            max-width: 360px;
            margin: 120px auto 0;
            padding: 32px 28px;
            border: 1px solid #D1D5DB;
            border-radius: 4px;
            background: white;
        }
        .auth-title {
            font-size: 18px;
            font-weight: 700;
            color: #0B1F3A;
            margin-bottom: 6px;
        }
        .auth-sub {
            font-size: 13px;
            color: #64748B;
            margin-bottom: 20px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="auth-wrapper">'
        '<div class="auth-title">洋書翻訳システム</div>'
        '<div class="auth-sub">利用にはパスワードが必要です</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # 入力欄
    cols = st.columns([1, 6, 1])
    with cols[1]:
        password = st.text_input(
            "パスワード",
            type="password",
            label_visibility="collapsed",
            placeholder="パスワード",
            key="auth_input",
        )
        if st.button("ログイン", type="primary", use_container_width=True, key="auth_btn"):
            if password == expected:
                st.session_state[SESSION_KEY] = True
                st.rerun()
            else:
                st.error("パスワードが正しくありません")
