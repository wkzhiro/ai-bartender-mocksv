# マイグレーション実行履歴

このファイルは、データベースマイグレーションの実行履歴を記録しています。
新しいSupabaseプロジェクトでは、以下の順序でマイグレーションファイルを実行してください。

## 実行順序

### 2025-01-30 - 新Supabaseプロジェクト用データベース構築

以下のマイグレーションファイルを**順番通り**にSupabaseのSQLエディタで実行してください：

1. **20250130_01_create_base_tables.sql**
   - 基本テーブル（events, cocktails, poured_cocktails）を作成
   - デフォルトイベントを作成

2. **20250130_02_create_prompt_tables.sql** 
   - プロンプト関連テーブル（prompts, cocktail_prompts）を作成
   - デフォルトプロンプトを挿入

3. **20250130_03_create_violation_tables.sql**
   - 違反報告テーブル（violation_reports）を作成

4. **20250130_04_create_survey_tables.sql**
   - アンケート関連テーブル（surveys, survey_questions, survey_question_options, survey_responses, survey_answers）を作成

5. **20250130_05_create_indexes.sql**
   - 全テーブルのパフォーマンス最適化用インデックスを作成

6. **20250130_06_create_triggers.sql**
   - updated_atの自動更新トリガーを作成

## 実行方法

1. Supabaseダッシュボードにアクセス
2. 左メニューから「SQL Editor」を選択
3. 上記の順序で各SQLファイルの内容をコピー&ペースト
4. 「RUN」ボタンで実行
5. 各ファイル実行後、成功ログ（例：`Base tables created successfully`）が表示されることを確認

## 機能概要

### 基本機能
- イベント管理
- カクテル生成・管理
- プロンプト管理
- 違反報告システム

### 新機能（アンケート）
- イベントごとのアンケート作成
- フリーテキスト、単一選択、複数選択の質問タイプ
- アンケート回答の収集
- 回答の集計・統計

## API エンドポイント

### アンケート関連
- `POST /events/{event_id}/surveys/` - アンケート作成
- `GET /events/{event_id}/surveys/` - アンケート一覧
- `GET /surveys/{survey_id}` - アンケート詳細
- `PUT /surveys/{survey_id}` - アンケート更新
- `DELETE /surveys/{survey_id}` - アンケート削除
- `GET /surveys/{survey_id}/form` - 回答フォーム取得
- `POST /surveys/{survey_id}/responses/` - 回答送信
- `GET /surveys/{survey_id}/responses/` - 回答一覧
- `GET /surveys/{survey_id}/statistics` - 集計結果

## 注意事項

- マイグレーションファイルは必ず順番通りに実行してください
- 実行前に既存データのバックアップを取ることを推奨します
- エラーが発生した場合は、該当するファイルの依存関係を確認してください

## 次回マイグレーション追加時

新しいマイグレーションファイルを追加する場合は、以下のルールに従ってください：

1. ファイル名: `YYYYMMDD_NN_description.sql`
2. このファイルに実行記録を追加
3. 依存関係がある場合は明記
4. 実行後の確認方法を記載