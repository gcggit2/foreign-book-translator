"""キーボードショートカット制御

Streamlit のデフォルトショートカット（C: キャッシュクリア、R: 再実行）を無効化する。
"""

from __future__ import annotations

import streamlit.components.v1 as components


_BLOCKER_JS = """
<script>
(function() {
    var doc = window.parent.document;
    if (doc.dataset.shortcutBlocked === 'true') return;
    doc.dataset.shortcutBlocked = 'true';

    doc.addEventListener('keydown', function(e) {
        // 対象キー以外はスルー
        if (e.key !== 'c' && e.key !== 'C' && e.key !== 'r' && e.key !== 'R') return;
        // 入力欄ではブロックしない（通常のコピー/編集を許可）
        var active = doc.activeElement;
        if (active) {
            var tag = (active.tagName || '').toLowerCase();
            if (tag === 'input' || tag === 'textarea' || active.isContentEditable) return;
        }
        // Streamlitのキーバインドだけ無効化（preventDefault は呼ばないので
        // ブラウザネイティブのコピー/リロード等のデフォルト動作は維持される）
        e.stopImmediatePropagation();
    }, true);
})();
</script>
"""


def disable_streamlit_shortcuts():
    """各ページの先頭で呼ぶ。Streamlitのキーボードショートカットを無効化。"""
    components.html(_BLOCKER_JS, height=0)
