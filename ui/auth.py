"""ベーシック認証（共有パスワード方式）＋Cookieによる永続化

Streamlit Secrets の APP_PASSWORD と一致したら通過。
1回ログインしたらブラウザCookieに認証トークンを保存し、再アクセス時はパスワード入力不要。
"""

from __future__ import annotations

import hashlib

import streamlit as st
import extra_streamlit_components as stx


SESSION_KEY = "auth_passed"
COOKIE_NAME = "fbt_auth"
COOKIE_TTL_DAYS = 30


def _get_expected_password() -> str | None:
    """Streamlit Secrets からパスワードを取得。未設定なら None"""
    try:
        return st.secrets.get("APP_PASSWORD", None)
    except Exception:
        return None


def _make_token(password: str) -> str:
    """パスワードからCookie保存用のハッシュトークンを生成"""
    return hashlib.sha256(f"fbt-auth-v1-{password}".encode()).hexdigest()


@st.cache_resource
def _get_cookie_manager() -> stx.CookieManager:
    """CookieManager（プロセス共通インスタンス）"""
    return stx.CookieManager(key="fbt_auth_cookie_mgr")


def require_auth():
    """各ページの先頭で呼ぶ。
    認証通過していなければパスワード入力画面を表示してst.stop()する。
    Cookieに有効なトークンがあれば自動的に通過する。
    """
    expected = _get_expected_password()
    if not expected:
        # パスワード未設定 → 認証スキップ（ローカル開発用）
        return

    # セッション内に認証済みフラグがあれば通過
    if st.session_state.get(SESSION_KEY):
        return

    # Cookieに有効なトークンがあれば自動ログイン
    cookie_mgr = _get_cookie_manager()
    expected_token = _make_token(expected)
    stored_token = cookie_mgr.get(COOKIE_NAME)
    if stored_token == expected_token:
        st.session_state[SESSION_KEY] = True
        return

    _render_password_form(expected, cookie_mgr, expected_token)
    st.stop()


def _render_password_form(expected: str, cookie_mgr: stx.CookieManager, expected_token: str):
    """パスワード入力画面"""
    st.markdown(
        """
        <style>
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
        .auth-card-body [data-testid="stTextInput"] {
            margin-bottom: 12px;
        }
        .auth-card-body [data-testid="stTextInput"] input {
            border-radius: 2px !important;
        }
        hr.nav-divider, .top-nav-logo { display: none !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="auth-card-top">'
        '<p class="auth-card-title">洋書翻訳システム</p>'
        '<p class="auth-card-sub">利用にはパスワードが必要です</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="auth-card-body">', unsafe_allow_html=True)

    password = st.text_input(
        "パスワード",
        type="password",
        label_visibility="collapsed",
        placeholder="パスワードを入力",
        key="auth_input",
    )
    submitted = st.button("ログイン", type="primary", use_container_width=True, key="auth_btn")

    st.caption(f"ログイン状態はこの端末に最大 {COOKIE_TTL_DAYS} 日間保存されます")
    st.markdown('</div>', unsafe_allow_html=True)

    if submitted:
        if password == expected:
            st.session_state[SESSION_KEY] = True
            # Cookieに認証トークンを保存（30日有効）
            cookie_mgr.set(
                COOKIE_NAME,
                expected_token,
                max_age=COOKIE_TTL_DAYS * 24 * 60 * 60,
                key="auth_cookie_set",
            )
            st.rerun()
        else:
            st.error("パスワードが正しくありません")


def logout():
    """ログアウト処理（Cookieとセッションをクリア）。
    今は呼び出し箇所なし。将来「ログアウト」ボタンを付ける時に利用。
    """
    cookie_mgr = _get_cookie_manager()
    try:
        cookie_mgr.delete(COOKIE_NAME, key="auth_cookie_del")
    except Exception:
        pass
    st.session_state.pop(SESSION_KEY, None)
