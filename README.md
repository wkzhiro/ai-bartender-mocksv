# AIカクテル生成システム

AIを活用してパーソナライズされたカクテルレシピと画像を生成するFastAPIベースのWebアプリケーションです。ユーザーの個人情報や体験に基づいて、オリジナルのカクテルを自動生成します。

## 🍹 機能概要

- **AIカクテル生成**: ユーザーの最近の出来事、キャリア、趣味などの情報をもとにしたパーソナライズされたカクテルレシピの生成
- **画像生成**: 生成されたカクテルに対応した透過背景のカクテル画像をAIで自動生成
- **名前フィルタリング**: FUSIONフィルタによるブランド名・企業名の自動検証と再生成
- **データベース管理**: Supabaseを使用したカクテルデータの永続化
- **注文管理**: 注文番号によるカクテル情報の取得・管理
- **匿名利用**: ユーザー情報を保存せずにカクテル生成が可能

## 🚀 セットアップ

### 必要な環境

- Python 3.8+
- Supabase アカウント
- Azure OpenAI または OpenAI API キー

### インストール

1. リポジトリをクローン
```bash
git clone <repository-url>
cd <project-directory>
```

2. 依存関係をインストール
```bash
pip install -r requirements.txt
```

3. 環境変数を設定
```bash
# .env ファイルを作成し、以下の値を設定
AZURE_OPENAI_API_KEY_LLM=your_azure_openai_key
AZURE_OPENAI_ENDPOINT_LLM=your_azure_endpoint
AZURE_OPENAI_ENDPOINT_LLM_MINI=your_mini_llm_endpoint  # 名前再生成用
GPT_API_KEY=your_openai_key_for_image_generation
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

4. データベースセットアップ
```bash
# Supabaseでテーブルを作成
python -c "from db.database import create_tables; create_tables()"
```

5. アプリケーション起動

**本番環境（高負荷対応）**
```bash
# Gunicornを使用（推奨）- 複数ワーカーで並行処理
gunicorn -c gunicorn.conf.py main:app

# またはDockerを使用
docker build -t ai-bartender-mocksv .
docker run -p 8000:8000 --env-file .env ai-bartender-mocksv
```

**開発環境**
```bash
# Uvicornを使用（単一プロセス、リロード機能付き）
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 📝 カクテル生成方法の詳細

### 1. カクテル生成プロセス

カクテル生成は `/cocktail/` エンドポイント（main.py:334-337行）で実行され、以下のステップで行われます：

#### ステップ1: ユーザー情報の収集
システムは以下の情報を受け取ります：
- `recent_event`: 最近の出来事
- `event_name`: イベント名
- `name`: 名前（オプション）
- `career`: キャリア情報
- `hobby`: 趣味
- `prompt`: 画像生成用の追加プロンプト（オプション）
- `save_user_info`: ユーザー情報保存フラグ

#### ステップ2: レシピ生成（main.py:355-398行）

**シロップ情報の読み込み（main.py:235-258行）**
```
4種類のシロップの特性情報を storage/syrup.txt から読み込み：
- ベリー: ベリーレッド色、軽い甘さと穏やかな酸味、ラズベリーの香り
- 青りんご: ライトブルー色、軽い甘さと穏やかな酸味、アップルの香り
- シトラス: イエロー色、中程度の甘さと強い酸味、グレープフルーツの香り
- ホワイト: ホワイト色、穏やかな甘さと酸味、紅茶の深い味わい
```

**AIプロンプト生成（main.py:497-536行）**
システムプロンプトには以下が含まれます：
- プロのバーテンダーとしての役割設定
- 4種類のシロップ情報と色の説明
- 合計25%以内でのレシピ制約
- ホワイトシロップは0-10%の制約
- 日本語20文字以内のカクテル名制約
- **既存のブランド名・企業名を使用しない制約**
- JSON形式での出力指定

**レスポンス例:**
```json
{
  "cocktail_name": "桜舞う春風",
  "concept": "新しい季節の始まりを祝う、優雅で爽やかなカクテル",
  "color": "淡いピンク色に白い泡が舞う",
  "recipe": [
    {"syrup": "ベリー", "ratio": "12%"},
    {"syrup": "青りんご", "ratio": "8%"},
    {"syrup": "シトラス", "ratio": "0%"},
    {"syrup": "ホワイト", "ratio": "5%"}
  ]
}
```

#### ステップ3: カクテル名検証とフィルタリング（main.py:639-662行）

**FUSIONフィルタによる名前検証:**
- `storage/FUSIONフィルタ_v1.0.csv` から1416件のフィルタ対象語句を読み込み
- カクテル名との部分一致、完全一致、編集距離1（1文字の削除・追加・置換）をチェック
- フィルタに引っかかった場合、ミニLLMエンドポイントで最大3回まで再生成
- 再生成に失敗した場合は「特製カクテル{時刻}」という汎用名を使用

**名前再生成プロセス（main.py:393-448行）:**
```python
# ミニLLMを使用した名前再生成
- エンドポイント: AZURE_OPENAI_ENDPOINT_LLM_MINI
- システムプロンプトで明示的にブランド名・企業名の使用を禁止
- 元のコンセプトと色を保持しながら新しい名前を生成
```

#### ステップ4: 画像生成（main.py:675-718行）

**画像生成プロンプト構築:**
```
"{color}のカクテル。{concept}。{user_prompt}。背景は完全な透明（透過PNG）、カクテル以外は描かず、カクテルそのものだけをリアルな質感の写真風イラストとして生成してください。"
```

**画像処理（main.py:720-749行）:**
- OpenAI DALL-E APIで1024x1536サイズの画像生成
- 自動的に720x1080サイズにクロップ・リサイズ
- 中央クロップにより最適なアスペクト比を維持
- Base64エンコード形式で返却

#### ステップ5: 注文番号生成（main.py:664-673行）
- 6桁のランダムな数字を生成
- データベースでの重複チェック
- 最大10回まで重複回避を試行

#### ステップ6: データベース保存（main.py:759-824行）
生成されたデータは以下の形式でSupabaseに保存されます：

**cocktailsテーブル構造:**
```sql
- order_id: 注文番号（6桁、ユニーク）
- status: ステータス（デフォルト200）
- name: カクテル名
- image: base64エンコードされた画像データ
- flavor_ratio1-4: 各シロップの配合比率
- comment: カクテルのコンセプト
- recent_event, event_name, user_name, career, hobby: ユーザー情報
- created_at: 作成日時
```

### 2. 匿名モード

`/cocktail/anonymous/` エンドポイント（main.py:545-562行）では：
- ユーザー情報は空文字として保存
- 画像はSupabase Storageに保存（URLとして管理）
- レシピ生成は全ての入力情報を使用
- 名前フィルタリングは通常モードと同様に適用

### 3. カクテル取得

**個別取得 (`/order/` GET):**
- 注文番号でカクテル情報を取得
- main.py:129-163行で実装

**全件取得 (`/order/?order_id=all`):**
- 全てのカクテルデータを配列で返却
- レシピ情報を構造化して返却

## 🔧 API エンドポイント

### カクテル生成
- `POST /cocktail/` - 通常のカクテル生成（ユーザー情報保存）
- `POST /cocktail/anonymous/` - 匿名カクテル生成

### カクテル取得
- `GET /order/?order_id={注文番号}` - 特定カクテル取得
- `GET /order/?order_id=all` - 全カクテル取得
- `POST /order/` - 注文情報取得（POSTリクエスト）

### その他
- `POST /delivery/` - カクテル配送情報登録
- `GET /` - ヘルスチェック
- `GET /status_check` - ステータス確認

## 📁 プロジェクト構造

```
├── main.py                 # メインアプリケーション
├── db/                     # データベース関連
│   ├── database.py         # データベース操作
│   ├── supabase_client.py  # Supabaseクライアント
│   └── *.py               # その他DB操作
├── storage/
│   ├── syrup.txt          # シロップ情報定義
│   └── FUSIONフィルタ_v1.0.csv  # ブランド名フィルタ
├── migration/             # データベース移行
├── images/                # 画像ファイル
└── requirements.txt       # 依存関係
```

## 🛠️ 技術スタック

- **バックエンド**: FastAPI, Python
- **Webサーバー**: Gunicorn（本番環境）, Uvicorn（開発環境）
- **データベース**: Supabase (PostgreSQL)
- **AI/ML**: Azure OpenAI (GPT-4, Mini LLM), OpenAI DALL-E
- **画像処理**: Pillow (PIL)
- **テキスト処理**: difflib（文字列類似度計算）
- **その他**: Requests, python-dotenv

## 🔒 セキュリティ機能

### FUSIONフィルタによる名前検証

システムには以下のセキュリティ機能が実装されています：

1. **ブランド名・企業名フィルタ**: `storage/FUSIONフィルタ_v1.0.csv` に含まれる1416件のフィルタ対象語句との照合
2. **部分一致検証**: カクテル名にフィルタ語句が含まれる場合もブロック
3. **編集距離検証**: 1文字の削除・追加・置換で一致する類似名もブロック
4. **自動名前再生成**: フィルタに引っかかった場合の自動的な代替名生成
5. **フォールバック機能**: 再生成に失敗した場合の安全な汎用名の使用

### 処理フロー

```
カクテル名生成 → FUSIONフィルタ検証 → フィルタ該当?
                                      ↓ Yes
              汎用名使用 ← 再生成失敗? ← ミニLLM再生成（最大3回）
                                      ↓ No
                        画像生成・DB保存 ← 検証通過
```

## 📜 ライセンス

このプロジェクトは適切なライセンスの下で公開されています。

## 🤝 コントリビューション

プロジェクトへの貢献を歓迎します。プルリクエストやイシューの報告をお待ちしています。