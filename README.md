# 洋書翻訳システム

英語書籍PDFをページ単位で日本語訳PDFに変換するStreamlit製Webアプリ。

## 概要

| 項目 | 内容 |
|------|------|
| 用途 | 英語書籍PDF → 日本語訳PDF |
| 翻訳エンジン | Gemini 2.5 Flash（有料枠想定） |
| インフラ | Python + Streamlit / Streamlit Community Cloud |
| 認証 | ベーシック認証（共有パスワード） |
| 課金モデル | BYOK（APIキーは利用者負担） |

## 機能

- **ページ単位で並列翻訳**（並列5）
- 章タイトル・見出しの自動強調表示（マークダウン解析）
- 著作権ページ・索引・出版社情報の自動スキップ
- 元PDFのページ番号を日本語訳PDFに併記
- 翻訳履歴の管理（SQLite）と一括削除
- パスワード保護されたWeb UI

## 公開URL

`https://foreign-book-translator.streamlit.app`

（パスワード認証あり）

## 起動方法

### ローカル開発

```bash
cd /path/to/洋書翻訳システム
source .venv/bin/activate
streamlit run app.py
```

ブラウザで `http://localhost:8501` が自動で開く。

### Streamlit Cloud 環境

GitHub `main` ブランチに push → 自動で再デプロイ。
APIキー・パスワードは Streamlit Cloud の Secrets で管理。

## 使い方

1. URLにアクセス → パスワード入力
2. メインページでPDFをドラッグ＆ドロップ
3. 「翻訳開始」ボタンクリック
4. 完了後、翻訳済みPDFをダウンロード

## ファイル構成

```
洋書翻訳システム/
├── app.py                       Streamlitエントリーポイント（翻訳ページ）
├── main.py                      app.py への薄いラッパー
├── requirements.txt             Python依存パッケージ
├── .streamlit/
│   ├── config.toml              テーマ・アップロード上限
│   └── secrets.toml.example     Secrets設定の見本
├── core/                        コアロジック
│   ├── llm_clients.py           Geminiクライアント（リトライ・スロットリング）
│   ├── pdf_extractor.py         PyMuPDFでテキスト抽出
│   ├── translator.py            ページ単位翻訳（並列・チャンク分割）
│   └── pdf_generator.py         日本語PDFを生成（ReportLab + 内蔵CJKフォント）
├── storage/
│   └── jobs.py                  SQLiteジョブ管理
├── pages/                       Streamlitサブページ
│   ├── shared_state.py          ページ間共通ステート
│   ├── 1_⚙️_設定.py             翻訳設定・APIテスト
│   └── 2_📊_履歴.py             翻訳ジョブ履歴
├── ui/
│   ├── theme.py                 共通CSSテーマ・ナビゲーション
│   ├── auth.py                  ベーシック認証
│   └── keyboard.py              Streamlit標準ショートカット無効化
├── data/                        実行時生成データ（.gitignore対象）
└── docs/
    ├── 要件定義.md
    └── claude_code_prompt.md
```

## 設計の特徴

- **ページ単位の翻訳**：章検出に頼らず、PDFのページごとに翻訳して構造を維持
- **3段階のエラー対応**：APIエラー時の自動リトライ＋待機（429・502・503等）
- **本文外ページの自動スキップ**：著作権・索引・装飾ページをLLMが判定して除外
- **CIDフォント使用**：日本語フォントファイルの同梱不要
- **BYOK（Bring Your Own Key）**：管理者がStreamlit SecretsにAPIキー設定。利用者は意識しない

## 今後の拡張

- マルチユーザー認証（ID/パスワード方式）
- OpenAI / Claude 等の他LLMプロバイダー対応
- カスタムドメイン・ブランディング機能
- 顧客向けセットアップツール・SaaS化

詳細は [docs/要件定義.md](docs/要件定義.md) を参照。
