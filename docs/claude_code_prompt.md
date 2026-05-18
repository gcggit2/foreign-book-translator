# Claude Code 実行プロンプト集

このファイルの中身を **Claude Code のチャットにコピペ** すれば、洋書翻訳システムが順次構築されます。

Phase 1 → Phase 2 → Phase 3 の順で実行してください。各Phaseが完了してから次へ。

---

## 🚀 Phase 1：MVP構築（Maki社内利用版）

```
洋書翻訳システム（Python + Streamlit）を以下の仕様で作成してください。

## プロジェクト概要
英語書籍PDFをアップロードすると、章ごとにサマリ付きで日本語訳PDFを生成するWebアプリのMVP。

## 技術スタック
- Python 3.11+
- Streamlit（Web UI）
- PyMuPDF（PDF読み込み）
- ReportLab + Noto Sans JP（PDF生成）
- google-genai SDK（Gemini API）
- SQLite（ジョブ履歴）

## 機能（Phase 1のみ）
1. シンプルなWebUI（ログイン不要）
2. 設定ページ：Gemini APIキー入力、翻訳スタイル選択（ですます調 / である調）
3. メインページ：PDFアップロード → 翻訳実行 → 進捗表示 → 完成PDFダウンロード
4. 履歴ページ：過去のジョブ一覧

## 章検出ロジック（重要）
**正規表現で章を検出する旧式アプローチは禁止**。代わりに以下：

1. PDF最初の10ページのテキストを抽出
2. Gemini 2.5 Pro に「目次（Table of Contents）から章タイトル一覧を抽出してJSON配列で返して」と依頼
3. 返ってきた章タイトルを全文中で文字列検索→位置を特定
4. 各章のテキスト範囲を確定

フォールバック：
- 目次が解析できない → LLMに「本文を読んで論理的セクションに分けて」と依頼
- それでも失敗 → 文字数で10章に均等分割

## 翻訳処理
- 各章ごとに Gemini 2.5 Flash で翻訳＋サマリ生成
- 長い章は6,000文字ずつチャンク分割→結合
- 5並列で高速化
- 失敗時は3回リトライ

## 出力PDF仕様
- 表紙（書名・翻訳日・章数）
- 各章冒頭にサマリ（200〜300文字）
- 本文（指定スタイル）
- 章ごとに改ページ
- 日本語フォント（Noto Sans JP）埋め込み

## ファイル構成
```
洋書翻訳システム/
├── app.py                  # Streamlitエントリーポイント
├── requirements.txt
├── README.md
├── .gitignore
├── .streamlit/config.toml
├── core/
│   ├── __init__.py
│   ├── pdf_extractor.py
│   ├── chapter_detector.py
│   ├── translator.py
│   ├── pdf_generator.py
│   └── llm_clients.py      # 後でマルチLLM対応する想定で抽象化
├── storage/
│   ├── __init__.py
│   └── jobs.py             # SQLiteジョブ管理
├── pages/                  # Streamlitマルチページ
│   ├── 1_⚙️_設定.py
│   └── 2_📊_履歴.py
├── data/                   # 実行時生成（.gitignore対象）
│   ├── jobs.db
│   ├── uploads/
│   └── outputs/
└── assets/
    └── fonts/              # Noto Sans JP配置
```

## 完了条件
1. ローカルで `streamlit run app.py` が動く
2. テストPDF（後でユーザーが用意）で1冊翻訳完了
3. README に起動手順を記載
4. .gitignore で APIキー・DB・PDFを除外

## 作業手順
1. プロジェクト構造を作成
2. requirements.txt 作成
3. 各モジュール実装
4. Streamlit UI実装
5. 動作確認方法を README に明記
6. 完了後、起動コマンドを表示

質問があればその都度確認してください。よろしくお願いします。
```

---

## 🔐 Phase 2：マルチユーザー化（Phase 1 動作確認後）

```
Phase 1で作成した洋書翻訳システムに、以下の機能を追加してください。

## 追加機能
1. ユーザー認証（メール+パスワード）
   - 管理者・一般ユーザーの2階層
   - bcryptでパスワードハッシュ化
   - セッション管理

2. ユーザーごとの設定保存
   - LLMプロバイダー選択（Gemini / OpenAI / Claude の3つから選択可能に）
   - APIキー（AES-256で暗号化してDB保存、復号は使用時のみ）
   - 翻訳スタイル

3. core/llm_clients.py を拡張
   - 共通インターフェース: GeminiClient, OpenAIClient, ClaudeClient
   - 各社SDKをラップ
   - chat_completion(messages, model) で統一呼び出し

4. core/translator.py を修正
   - ユーザー設定からプロバイダーを取得して切り替え
   - 章検出は Gemini 2.5 Pro / GPT-4o / Claude Sonnet 4.6（顧客選択モデルの高品質版）
   - 翻訳本文は Gemini Flash / GPT-4o-mini / Claude Haiku（コスト最適）

5. 管理者画面（pages/3_👤_管理.py）
   - ユーザー追加・削除
   - ジョブ統計
   - パスワードリセット

## 環境変数
- APP_SECRET_KEY: AES暗号化用のマスターキー（.envに保存）
- ADMIN_EMAIL / ADMIN_PASSWORD: 初期管理者アカウント（.envから初回起動時に読み込み）

## 完了条件
1. 複数ユーザーがそれぞれ自分のAPIキーで動かせる
2. APIキーがDBに平文で保存されていないことを確認
3. 管理者は他ユーザーの履歴を見られる、一般ユーザーは自分のだけ

質問があればその都度確認してください。よろしくお願いします。
```

---

## 🚢 Phase 3：商品化＆デプロイ（Phase 2 動作確認後）

```
Phase 2で作成した洋書翻訳システムを、Streamlit Community Cloudにデプロイできるようにしてください。

## 追加作業
1. GitHubリポジトリ準備
   - .gitignoreの整備（.env, *.db, data/ を除外）
   - README.md にデプロイ手順を追記
   - LICENSE ファイル（プロプライエタリ）

2. Streamlit Cloud対応
   - secrets.toml.example を作成
   - Streamlit Secretsの仕組みでAPP_SECRET_KEY等を管理
   - .streamlit/config.toml でテーマカスタマイズ

3. 顧客向けマニュアル（docs/顧客向けマニュアル.md）
   - 初期ログイン手順
   - APIキー取得方法（Gemini/OpenAI/Claude各社）
   - 翻訳実行手順
   - トラブルシューティング

4. 法的書類テンプレート（docs/legal/）
   - 利用規約.md
   - プライバシーポリシー.md
   - 重要事項説明書.md（API代は顧客負担、AI翻訳の精度保証なし等）

5. オペレーション用スクリプト
   - scripts/add_customer.py（新規顧客アカウント発行）
   - scripts/backup_db.py（DBバックアップ）
   - scripts/cleanup_old_files.py（30日経過ファイル削除）

## 完了条件
1. GitHubにpushすればStreamlit Cloudに即デプロイできる状態
2. 新規顧客追加が `python scripts/add_customer.py` 1コマンドで完結
3. 顧客向けマニュアルが画像入りで完成

質問があればその都度確認してください。よろしくお願いします。
```

---

## 💡 Tips

### Claude Codeへの追加の指示例

- 「Phase 1を実装する前に、まず実装計画を箇条書きで見せて」
- 「テストPDFは Project Gutenberg からダウンロードしたい。短編で良いのでおすすめを教えて」
- 「動かしてみたらエラーが出ました。`<エラーメッセージ>`」

### よくある対応

| 状況 | Claude Code への指示 |
|------|--------------------|
| 依存ライブラリのインストールエラー | 「`pip install` でエラー出た：`<エラー>`」 |
| Streamlit が起動しない | 「`streamlit run app.py` でエラー：`<エラー>`」 |
| 翻訳結果がおかしい | 「翻訳結果が `<状況>` なので調整して」 |
| 顧客から機能追加要望 | 「以下の機能を追加して：`<要望>`」 |
