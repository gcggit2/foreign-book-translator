"""Streamlit Cloud エントリーポイント

Streamlit Cloud のデフォルトでは main.py を探すことがあるため、
app.py への薄いラッパーとして main.py を用意する。

実際の処理は app.py を参照。
"""

import runpy

runpy.run_path("app.py", run_name="__main__")
