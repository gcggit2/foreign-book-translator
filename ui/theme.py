"""共通UIコンポーネント＋CSSテーマ"""

from __future__ import annotations

import streamlit as st


# === カラーパレット（コンサル風） ===
COLORS = {
    "ink":          "#0B1F3A",   # ほぼ黒の濃紺（タイトル）
    "navy":         "#1A3A6C",   # 深いネイビー（プライマリ）
    "navy_dark":    "#0F2C4D",
    "navy_light":   "#E7EEF7",
    "text":         "#1F2937",   # 本文
    "text_muted":   "#64748B",   # 補助
    "border":       "#D1D5DB",
    "border_soft":  "#E5E7EB",
    "bg_soft":      "#F9FAFB",
    "accent":       "#B8860B",   # ゴールド系アクセント
    "success":      "#047857",
    "warning":      "#B45309",
    "danger":       "#B91C1C",
}


GLOBAL_CSS = """
<style>
/* ============================================================
   Streamlit デフォルトUIの非表示
   ============================================================ */
[data-testid="stSidebar"], section[data-testid="stSidebar"],
[data-testid="collapsedControl"],
[data-testid="stToolbar"],
.stDeployButton,
[data-testid="stStatusWidget"] {
    display: none !important;
}
#MainMenu { visibility: hidden !important; }
header[data-testid="stHeader"] {
    height: 0 !important;
    background: transparent !important;
}
footer { display: none !important; }

/* ============================================================
   タイポグラフィ
   ============================================================ */
html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, "Hiragino Sans",
                 "Yu Gothic UI", "Meiryo", sans-serif;
    color: #1F2937;
}
h1, h2, h3, h4, h5 {
    color: #0B1F3A !important;
    font-weight: 700 !important;
    letter-spacing: -0.01em;
}
h1 {
    font-size: 28px !important;
    border-bottom: 2px solid #0B1F3A;
    padding-bottom: 10px;
    margin-bottom: 6px !important;
}
h2 { font-size: 20px !important; }
h3 { font-size: 16px !important; }
.section-label {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #64748B;
    margin: 24px 0 8px 0;
}

/* ============================================================
   メインコンテナ
   ============================================================ */
.main .block-container {
    max-width: 980px;
    padding-top: 1rem;
    padding-bottom: 4rem;
}

/* ============================================================
   トップナビゲーション
   ============================================================ */
.top-nav-logo {
    font-size: 17px;
    font-weight: 700;
    color: #0B1F3A;
    letter-spacing: -0.01em;
    padding-top: 8px;
}
.top-nav-logo .sub {
    font-size: 11px;
    color: #64748B;
    font-weight: 500;
    letter-spacing: 0.08em;
    margin-left: 8px;
    text-transform: uppercase;
}
[data-testid="stPageLink"] {
    border-radius: 0 !important;
    border-bottom: 2px solid transparent !important;
}
[data-testid="stPageLink"]:hover {
    background: transparent !important;
    border-bottom-color: #1A3A6C !important;
}
[data-testid="stPageLink"] a {
    padding: 10px 16px !important;
    font-weight: 500 !important;
    color: #1F2937 !important;
    font-size: 14px !important;
}
[data-testid="stPageLink"][aria-current="page"] {
    border-bottom-color: #1A3A6C !important;
}
[data-testid="stPageLink"][aria-current="page"] a {
    color: #1A3A6C !important;
    font-weight: 700 !important;
}
hr.nav-divider {
    margin: 0 0 28px 0 !important;
    border: none !important;
    border-top: 1px solid #0B1F3A !important;
}

/* ============================================================
   「大まかな流れ」フロー枠
   ============================================================ */
.flow-wrapper {
    border: 1px solid #D1D5DB;
    border-radius: 4px;
    padding: 14px 18px 16px;
    margin: 16px 0 28px 0;
    background: #F9FAFB;
    position: relative;
}
.flow-label {
    position: absolute;
    top: -9px;
    left: 14px;
    background: white;
    padding: 0 8px;
    font-size: 10px;
    color: #64748B;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    font-weight: 700;
}
.flow-steps {
    display: flex;
    align-items: center;
    gap: 0;
    margin-top: 4px;
}
.flow-step {
    flex: 1;
    text-align: center;
    padding: 8px 6px;
    background: white;
    border: 1px solid #E5E7EB;
    font-size: 13px;
    color: #6B7280;
    user-select: none;
    cursor: default;
}
.flow-step.active {
    background: #0B1F3A;
    color: white;
    border-color: #0B1F3A;
    font-weight: 600;
}
.flow-step.done {
    background: #F3F4F6;
    color: #94A3B8;
    text-decoration: line-through;
    text-decoration-color: #CBD5E1;
}
.flow-arrow {
    color: #94A3B8;
    font-size: 14px;
    padding: 0 8px;
    user-select: none;
}

/* ============================================================
   バッジ
   ============================================================ */
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 2px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    border: 1px solid transparent;
}
.badge-success { background: #ECFDF5; color: #047857; border-color: #A7F3D0; }
.badge-warning { background: #FFFBEB; color: #B45309; border-color: #FCD34D; }
.badge-danger  { background: #FEF2F2; color: #B91C1C; border-color: #FCA5A5; }
.badge-info    { background: #EFF6FF; color: #1A3A6C; border-color: #BFDBFE; }
.badge-muted   { background: #F3F4F6; color: #4B5563; border-color: #D1D5DB; }

/* ============================================================
   ボタン
   ============================================================ */
.stButton > button {
    border-radius: 2px !important;
    font-weight: 600 !important;
    letter-spacing: 0.02em;
    transition: all 0.15s ease;
}
.stButton > button[kind="primary"] {
    background: #0B1F3A !important;
    color: white !important;
    border: 1px solid #0B1F3A !important;
    padding: 0.65rem 1.75rem !important;
    font-size: 14px !important;
}
.stButton > button[kind="primary"]:hover {
    background: #1A3A6C !important;
    border-color: #1A3A6C !important;
}
.stButton > button[kind="secondary"] {
    background: white !important;
    color: #1F2937 !important;
    border: 1px solid #D1D5DB !important;
}
.stButton > button[kind="secondary"]:hover {
    border-color: #0B1F3A !important;
    color: #0B1F3A !important;
}
.stDownloadButton > button {
    background: #0B1F3A !important;
    color: white !important;
    border: 1px solid #0B1F3A !important;
    border-radius: 2px !important;
    font-weight: 600 !important;
    padding: 0.65rem 1.75rem !important;
}

/* ============================================================
   ファイルアップローダー（日本語化）
   ============================================================ */
[data-testid="stFileUploader"] section {
    background: #F9FAFB !important;
    border: 2px dashed #D1D5DB !important;
    border-radius: 4px !important;
    transition: border-color 0.15s ease;
}
[data-testid="stFileUploader"] section:hover {
    border-color: #0B1F3A !important;
}
/* デフォルトの「Browse files」ボタンのテキストを差し替え */
[data-testid="stFileUploaderDropzone"] button {
    background: #0B1F3A !important;
    color: transparent !important;
    border: 1px solid #0B1F3A !important;
    border-radius: 2px !important;
    position: relative !important;
    min-width: 200px !important;
    height: 40px !important;
}
[data-testid="stFileUploaderDropzone"] button::after {
    content: "洋書PDFを選択";
    color: white;
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 600;
    font-size: 14px;
    letter-spacing: 0.02em;
}
/* 「Drag and drop file here」テキスト差し替え */
[data-testid="stFileUploaderDropzoneInstructions"] > div > span {
    display: none !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] > div::before {
    content: "ここに洋書PDFをドラッグ＆ドロップ";
    display: block;
    color: #1F2937;
    font-size: 15px;
    font-weight: 500;
    margin-bottom: 4px;
}
[data-testid="stFileUploaderDropzoneInstructions"] small {
    display: none !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] > div::after {
    content: "PDF形式・最大500MB";
    display: block;
    color: #64748B;
    font-size: 12px;
    margin-top: 4px;
}

/* ============================================================
   その他
   ============================================================ */
hr { margin: 1.5rem 0 !important; border-color: #E5E7EB !important; }
[data-testid="stCaptionContainer"] { color: #64748B !important; }

/* メトリック */
[data-testid="stMetric"] {
    background: white;
    border: 1px solid #D1D5DB;
    border-left: 3px solid #0B1F3A;
    border-radius: 2px;
    padding: 14px 18px;
}
[data-testid="stMetricLabel"] {
    font-size: 11px !important;
    color: #64748B !important;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    font-weight: 600 !important;
}
[data-testid="stMetricValue"] {
    font-size: 28px !important;
    font-weight: 700 !important;
    color: #0B1F3A !important;
}

/* 警告・情報ボックスを控えめに */
[data-testid="stAlertContentInfo"],
[data-testid="stAlertContentWarning"],
[data-testid="stAlertContentSuccess"],
[data-testid="stAlertContentError"] {
    border-radius: 2px !important;
}

/* expander の見た目 */
[data-testid="stExpander"] {
    border: 1px solid #E5E7EB !important;
    border-radius: 2px !important;
}
[data-testid="stExpander"] summary {
    font-weight: 600 !important;
    color: #0B1F3A !important;
}
</style>
"""


def apply_theme():
    """ページの先頭で呼ぶ。CSS適用"""
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


def render_top_nav(active: str = "translate"):
    """画面上部のナビゲーションバー（コンサル風）"""
    cols = st.columns([4, 1, 1, 1])
    with cols[0]:
        st.markdown(
            '<div class="top-nav-logo">'
            '洋書翻訳システム<span class="sub">Translation Workflow</span>'
            '</div>',
            unsafe_allow_html=True,
        )
    with cols[1]:
        st.page_link("app.py", label="翻訳")
    with cols[2]:
        st.page_link("pages/1_⚙️_設定.py", label="設定")
    with cols[3]:
        st.page_link("pages/2_📊_履歴.py", label="履歴")

    st.markdown('<hr class="nav-divider">', unsafe_allow_html=True)


def section_label(text: str):
    """セクション小見出し（小さい大文字風ラベル）"""
    st.markdown(f'<div class="section-label">{text}</div>', unsafe_allow_html=True)


def badge(text: str, kind: str = "info") -> str:
    """インラインバッジHTML"""
    return f'<span class="badge badge-{kind}">{text}</span>'


def render_flow(active_step: int, steps: list):
    """「大まかな流れ」のフロー図（人が押せない＝表示専用）

    Args:
        active_step: 1始まり。現在のステップ番号。
        steps: ステップ名のリスト
    """
    parts = []
    for i, name in enumerate(steps, start=1):
        cls = "flow-step"
        if i < active_step:
            cls += " done"
        elif i == active_step:
            cls += " active"
        parts.append(f'<div class="{cls}">{i}. {name}</div>')
        if i < len(steps):
            parts.append('<div class="flow-arrow">▶</div>')

    html = (
        '<div class="flow-wrapper">'
        '<div class="flow-label">大まかな流れ</div>'
        '<div class="flow-steps">' + "".join(parts) + '</div>'
        '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)
