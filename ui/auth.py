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

    _render_password_form(expected)
    st.stop()


def _render_password_form(expected: str):
    # 認証画面専用CSS（メインコンテナを狭く中央寄せに）
    st.markdown(
        """
        <style>
        /* 認証画面ではメインコンテナを狭くしてカード風に */
        .main .block-container {
            max-width: 420px !important;
            padding-top: 14vh !important;
        }
        .auth-card-top {
            border: 1px solid #D1D5DB;
            border-bottom: none;
            border-radius: 4px 4px 0 0;
            background: white;
            padding: 28px 28px 18px;
        }
        .auth-card-title {
            font-size: 19px;
            font-weight: 700;
            color: #0B1F3A;
            margin: 0 0 4px 0;
        }
        .auth-card-sub {
            font-size: 13px;
            color: #64748B;
            margin: 0;
        }
        .auth-card-body {
            border: 1px solid #D1D5DB;
            border-top: none;
            border-radius: 0 0 4px 4px;
            background: white;
            padding: 6px 28px 24px;
            margin-bottom: 0;
        }
        /* 入力欄の余白調整 */
        .auth-card-body [data-testid="stTextInput"] {
            margin-bottom: 12px;
        }
        .auth-card-body [data-testid="stTextInput"] input {
            border-radius: 2px !important;
        }
        /* このページではトップナビとフッターも非表示にしてシンプルに */
        hr.nav-divider, .top-nav-logo { display: none !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # カード上部（タイトル）
    st.markdown(
        '<div class="auth-card-top">'
        '<p class="auth-card-title">洋書翻訳システム</p>'
        '<p class="auth-card-sub">利用にはパスワードが必要です</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # カード下部（入力欄＋ボタン）
    st.markdown('<div class="auth-card-body">', unsafe_allow_html=True)

    password = st.text_input(
        "パスワード",
        type="password",
        label_visibility="collapsed",
        placeholder="パスワードを入力",
        key="auth_input",
    )
    submitted = st.button("ログイン", type="primary", use_container_width=True, key="auth_btn")

    st.markdown('</div>', unsafe_allow_html=True)

    if submitted:
        if password == expected:
            st.session_state[SESSION_KEY] = True
            st.rerun()
        else:
            st.error("パスワードが正しくありません")
