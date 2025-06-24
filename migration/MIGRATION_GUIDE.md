# MySQLからSupabaseへのデータ移行手順

## 概要
このガイドでは、MySQLWorkbenchを使用してMySQLからSupabaseへデータを移行する手順を説明します。

## 準備

### 1. 必要なファイルの確認
- `migration/supabase_create_tables.sql` - Supabaseテーブル作成用SQL
- `migration/migrate_data.py` - データ移行用Pythonスクリプト
- `.env.supabase` - Supabase接続情報

### 2. 依存関係のインストール
```bash
pip install supabase mysql-connector-python python-dotenv
```

## 移行手順

### ステップ1: Supabaseでテーブル作成

1. **Supabaseダッシュボードにアクセス**
   - https://supabase.com にログイン
   - プロジェクトを選択

2. **SQL Editorを開く**
   - 左サイドバーから "SQL Editor" を選択

3. **テーブル作成SQLを実行**
   - `migration/supabase_create_tables.sql` の内容をコピー
   - SQL Editorに貼り付けて実行
   - テーブルが正常に作成されたことを確認

### ステップ2: 環境変数の設定確認

`.env.supabase` ファイルに以下が正しく設定されていることを確認：
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

### ステップ3: データ移行の実行

#### 方法A: 自動移行スクリプト（推奨）

```bash
python migration/migrate_data.py
```

このスクリプトは以下を自動実行します：
- MySQLからのデータ取得
- Supabaseへのデータ挿入
- 移行結果の検証

#### 方法B: 手動移行（MySQLWorkbench使用）

1. **MySQLWorkbenchでデータエクスポート**
   ```sql
   -- cocktailsテーブル
   SELECT * FROM cocktails ORDER BY id;
   ```
   - 結果を右クリック → "Export Recordset to an External File"
   - CSV形式で保存（cocktails.csv）

   ```sql
   -- poured_cocktailsテーブル
   SELECT * FROM poured_cocktails ORDER BY id;
   ```
   - CSV形式で保存（poured_cocktails.csv）

2. **Supabaseダッシュボードでインポート**
   - Table Editor → 対象テーブル → "Insert" → "Import data from CSV"
   - ヘッダー行をスキップしてインポート

### ステップ4: 移行結果の確認

1. **Supabaseダッシュボードで確認**
   - Table Editor で各テーブルのデータを確認
   - 件数が一致しているか確認

2. **アプリケーションでのテスト**
   ```bash
   # Supabase版アプリケーションを起動
   python -m uvicorn main_supabase:app --reload
   ```
   - エンドポイントが正常に動作するか確認

## トラブルシューティング

### エラー: "Connection refused"
- MySQL接続情報を確認
- VPNやファイアウォール設定を確認

### エラー: "Permission denied"
- SUPABASE_SERVICE_ROLE_KEYを使用していることを確認
- SupabaseのRLS設定を確認

### エラー: "Duplicate key"
- 重複するorder_idがある場合、手動で重複データを確認
- 必要に応じてデータクリーニングを実行

### 大量データの移行時
- `migrate_data.py`のbatch_sizeを調整
- 途中で失敗した場合は、失敗したバッチから再開

## 移行後の作業

### 1. 環境変数の更新
```bash
# .envファイルでSupabase設定を有効化
cp .env.supabase .env
```

### 2. アプリケーションの切り替え
```bash
# main.pyをバックアップ
mv main.py main_mysql.py

# Supabase版を本番に
cp main_supabase.py main.py
```

### 3. 依存関係の更新
```bash
# MySQL関連パッケージを削除
pip uninstall sqlalchemy mysql-connector-python

# Supabaseパッケージを追加
pip install supabase
```

### 4. 旧MySQLデータベースの処理
- 移行が完全に完了し、動作確認が済んだらMySQLサーバーを停止
- 必要に応じてMySQLデータをバックアップとして保持

## 移行完了チェックリスト

- [ ] Supabaseテーブルが作成されている
- [ ] 全データが正常に移行されている
- [ ] アプリケーションが正常に動作している
- [ ] 新しいデータの作成・更新が可能
- [ ] 画像データが正常に表示される
- [ ] APIエンドポイントが全て動作している
- [ ] 依存関係が更新されている
- [ ] 本番環境での動作確認が完了している

## 参考情報

- [Supabase公式ドキュメント](https://supabase.com/docs)
- [Supabase Python Client](https://github.com/supabase/supabase-py)
- [PostgreSQL データ型](https://www.postgresql.org/docs/current/datatype.html)