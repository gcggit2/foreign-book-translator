# 洋書翻訳システム

英語書籍PDFを章ごとにサマリ付きで日本語訳PDFに変換するWebアプリ。

## ステータス

**✅ Phase 1 (MVP) 完成済み** - ローカルで動作確認可能。

## 起動方法（Makiさん用）

ターミナルで以下を実行：

```bash
cd /Users/ym/CC/gcg/洋書翻訳システム
source .venv/bin/activate
streamlit run app.py
```

ブラウザが自動で開きます（http://localhost:8501）。

## 使い方

1. **設定ページ**でGemini APIキーを入力
   - キーは [aistudio.google.com/apikey](https://aistudio.google.com/apikey) で取得
2. **メインページ**でPDFをドラッグ＆ドロップ
3. 「翻訳開始」ボタンクリック
4. 完了後、翻訳済みPDFをダウンロード

## ファイル構成

```
洋書翻訳システム/
├── app.py                  Streamlitエントリーポイント
├── requirements.txt        Python依存パッケージ
├── .venv/                  仮想環境
├── core/                   コアロジック
│   ├── llm_clients.py      Geminiクライアント（Phase2でOpenAI/Claude追加予定）
│   ├── pdf_extractor.py    PyMuPDFでテキスト抽出
│   ├── chapter_detector.py LLM経由で章検出
│   ├── translator.py       翻訳本体（5並列）
│   └── pdf_generator.py    日本語PDFを生成（ReportLab + 内蔵CJKフォント）
├── storage/
│   └── jobs.py             SQLiteジョブ管理
├── pages/                  Streamlitサブページ
│   ├── 1_⚙️_設定.py
│   └── 2_📊_履歴.py
├── data/                   実行時生成データ（.gitignore対象）
│   ├── jobs.db
│   ├── uploads/
│   └── outputs/
└── docs/
    ├── 要件定義.md
    └── claude_code_prompt.md  Phase 2/3の指示書
```

## 動作確認済み

- ✅ 全モジュール インポート成功
- ✅ Streamlit 起動成功
- ✅ ReportLab 日本語PDF生成成功

## 設計の特徴

- **章検出はLLM任せ**（正規表現は使わない）→ 書籍のフォーマット差に強い
- **3段階フォールバック** で「常に何かしらの結果」を保証
- **5並列翻訳** で高速化
- **CIDフォント** 使用でフォントファイル不要

## Phase 2/3（今後）

- Phase 2: 認証＋マルチユーザー＋OpenAI/Claude対応
- Phase 3: 商品化・Streamlit Cloudデプロイ

詳細は [docs/claude_code_prompt.md](docs/claude_code_prompt.md)
