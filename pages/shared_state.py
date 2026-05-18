"""ページ間で共有するセッションステート初期化と参照ヘルパー

APIキーの読み取り優先順位:
  1. Streamlit Secrets (st.secrets["GEMINI_API_KEY"])  ← クラウド本番
  2. 環境変数 GEMINI_API_KEY                            ← ローカル開発
  3. .env ファイル                                       ← ローカル開発
"""

from __future__ import annotations

import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv


ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


def _read_api_key_from_secrets() -> str:
    """Streamlit Secrets から取得（ローカルでsecretsがなければ空文字）"""
    try:
        return st.secrets.get("GEMINI_API_KEY", "") or ""
    except Exception:
        return ""


def init_state():
    """セッションステートを初期化（複数ページで重複セーフ）"""
    load_dotenv(ENV_FILE)

    if "gemini_api_key" not in st.session_state:
        # 優先順位: Secrets → 環境変数 → .env
        key = _read_api_key_from_secrets() or os.environ.get("GEMINI_API_KEY", "")
        st.session_state.gemini_api_key = key

    if "translation_style" not in st.session_state:
        st.session_state.translation_style = "ですます調"
    if "parallel_count" not in st.session_state:
        st.session_state.parallel_count = 5


def get_api_key_status() -> str:
    """APIキー状態を文字列で返す: 'set' / 'unset'"""
    init_state()
    return "set" if st.session_state.gemini_api_key else "unset"


def is_api_key_from_secrets() -> bool:
    """APIキーがStreamlit Secretsから来ているか（読み取り専用かの判定）"""
    return bool(_read_api_key_from_secrets())
