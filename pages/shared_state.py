"""ページ間で共有するセッションステート初期化と参照ヘルパー"""

from __future__ import annotations

import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv


ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


def init_state():
    """セッションステートを初期化（複数ページで重複セーフ）"""
    load_dotenv(ENV_FILE)
    if "gemini_api_key" not in st.session_state:
        st.session_state.gemini_api_key = os.environ.get("GEMINI_API_KEY", "")
    if "translation_style" not in st.session_state:
        st.session_state.translation_style = "ですます調"
    if "parallel_count" not in st.session_state:
        st.session_state.parallel_count = 5


def get_api_key_status() -> str:
    """APIキー状態を文字列で返す: 'set' / 'unset'"""
    init_state()
    return "set" if st.session_state.gemini_api_key else "unset"


def save_to_env(key: str, value: str):
    """指定キー=値を .env に保存（既存行は上書き）"""
    lines = []
    if ENV_FILE.exists():
        with open(ENV_FILE, "r") as f:
            lines = f.readlines()
    lines = [ln for ln in lines if not ln.strip().startswith(f"{key}=")]
    lines.append(f"{key}={value}\n")
    with open(ENV_FILE, "w") as f:
        f.writelines(lines)


def delete_from_env(key: str):
    if not ENV_FILE.exists():
        return
    with open(ENV_FILE, "r") as f:
        lines = f.readlines()
    lines = [ln for ln in lines if not ln.strip().startswith(f"{key}=")]
    with open(ENV_FILE, "w") as f:
        f.writelines(lines)
