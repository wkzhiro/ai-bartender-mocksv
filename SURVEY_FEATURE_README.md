# アンケート機能実装ガイド

本ドキュメントでは、AI Bartender アプリケーションに実装されたアンケート機能について説明します。

## 目次

1. [概要](#概要)
2. [機能仕様](#機能仕様)
3. [データベース設計](#データベース設計)
4. [API設計](#api設計)
5. [フロントエンド実装](#フロントエンド実装)
6. [セットアップ手順](#セットアップ手順)
7. [使用方法](#使用方法)
8. [トラブルシューティング](#トラブルシューティング)

## 概要

### 実装された機能
- **イベント別アンケート作成・管理**
- **3種類の質問タイプサポート**
  - フリーテキスト入力
  - 単一選択（ラジオボタン）
  - 複数選択（チェックボックス）
- **回答収集とリアルタイム統計**
- **CSVエクスポート機能**
- **レスポンシブデザイン対応**

### 技術スタック
- **バックエンド**: FastAPI + Supabase (PostgreSQL)
- **フロントエンド**: React + TypeScript + shadcn/ui
- **データベース**: PostgreSQL (UUID主キー)
- **認証**: 管理者パスワード認証

## 機能仕様

### 1. アンケート作成機能
- イベントごとのアンケート作成
- 複数質問の追加・編集・削除
- 質問の表示順序設定
- 必須/任意の設定
- アクティブ/非アクティブの状態管理
- 開始日・終了日の設定

### 2. 質問タイプ
#### フリーテキスト
- 自由記述回答
- 最大文字数制限なし
- 必須回答設定可能

#### 単一選択
- ラジオボタン形式
- 最低2つ以上の選択肢必須
- 選択肢の追加・削除・並び替え

#### 複数選択
- チェックボックス形式
- 最低2つ以上の選択肢必須
- 複数項目同時選択可能

### 3. 回答収集機能
- 公開URLでのアンケート回答
- 期間外アクセス制御
- 非アクティブアンケートの非表示
- カクテルIDとの関連付け（任意）

### 4. 統計・分析機能
- リアルタイム回答数表示
- 選択式質問の円グラフ・棒グラフ表示
- フリーテキストの一覧表示
- CSVファイルエクスポート

## データベース設計

### テーブル構成

#### 1. surveys (アンケート)
```sql
CREATE TABLE surveys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID REFERENCES events(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    start_date TIMESTAMP WITH TIME ZONE,
    end_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### 2. survey_questions (質問)
```sql
CREATE TABLE survey_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    survey_id UUID REFERENCES surveys(id) ON DELETE CASCADE,
    question_type VARCHAR(20) NOT NULL CHECK (question_type IN ('text', 'single_choice', 'multiple_choice')),
    question_text TEXT NOT NULL,
    is_required BOOLEAN DEFAULT false,
    display_order INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### 3. survey_question_options (選択肢)
```sql
CREATE TABLE survey_question_options (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id UUID REFERENCES survey_questions(id) ON DELETE CASCADE,
    option_text TEXT NOT NULL,
    display_order INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### 4. survey_responses (回答セッション)
```sql
CREATE TABLE survey_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    survey_id UUID REFERENCES surveys(id) ON DELETE CASCADE,
    cocktail_id INTEGER REFERENCES cocktails(id),
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### 5. survey_answers (個別回答)
```sql
CREATE TABLE survey_answers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    response_id UUID REFERENCES survey_responses(id) ON DELETE CASCADE,
    question_id UUID REFERENCES survey_questions(id) ON DELETE CASCADE,
    answer_text TEXT,
    selected_option_ids UUID[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## API設計

### エンドポイント一覧

#### アンケート管理
- `POST /events/{event_id}/surveys/` - アンケート作成
- `GET /events/{event_id}/surveys/` - イベント別アンケート一覧
- `GET /surveys/{survey_id}` - アンケート詳細取得
- `PUT /surveys/{survey_id}` - アンケート更新
- `DELETE /surveys/{survey_id}` - アンケート削除

#### 回答機能
- `GET /surveys/{survey_id}/form` - 回答フォーム取得
- `POST /surveys/{survey_id}/responses/` - 回答送信

#### 統計機能
- `GET /surveys/{survey_id}/responses/` - 回答一覧取得
- `GET /surveys/{survey_id}/statistics` - 統計データ取得

### リクエスト/レスポンス例

#### アンケート作成
```json
POST /events/{event_id}/surveys/
{
  "title": "満足度調査",
  "description": "イベント参加者の満足度を調査します",
  "is_active": true,
  "questions": [
    {
      "question_type": "single_choice",
      "question_text": "総合的な満足度はいかがでしたか？",
      "is_required": true,
      "display_order": 1,
      "options": [
        {"option_text": "非常に満足", "display_order": 1},
        {"option_text": "満足", "display_order": 2},
        {"option_text": "普通", "display_order": 3},
        {"option_text": "不満", "display_order": 4}
      ]
    }
  ]
}
```

#### 回答送信
```json
POST /surveys/{survey_id}/responses/
{
  "cocktail_id": 123,
  "answers": [
    {
      "question_id": "uuid-here",
      "selected_option_ids": ["option-uuid-here"]
    }
  ]
}
```

## フロントエンド実装

### コンポーネント構成

#### 1. SurveyManager.tsx
- アンケート一覧表示
- 作成・編集・削除機能
- 質問・選択肢の動的追加
- バリデーション機能

#### 2. SurveyForm.tsx
- 公開回答フォーム
- 質問タイプ別UI
- 期間・状態チェック
- 回答送信機能

#### 3. SurveyStatistics.tsx
- 統計ダッシュボード
- グラフ表示（円・棒グラフ）
- CSVエクスポート
- 回答一覧表示

### ページ構成

#### 1. SurveyManagement.tsx (`/admin/events/{eventId}/surveys`)
- 管理者向けアンケート管理画面
- SurveyManagerコンポーネントを使用

#### 2. SurveyResponse.tsx (`/survey/{surveyId}`)
- 一般ユーザー向け回答ページ
- SurveyFormコンポーネントを使用

### ルーティング
```typescript
// App.tsx
<Route path="/admin/events/:eventId/surveys" element={<SurveyManagement />} />
<Route path="/admin/events/:eventId/surveys/:surveyId/statistics" element={<SurveyManagement />} />
<Route path="/survey/:surveyId" element={<SurveyResponse />} />
```

## セットアップ手順

### 1. データベースマイグレーション
```bash
# venv環境をアクティベート
source venv/bin/activate

# マイグレーション実行スクリプト
python test_migration.py
```

**または手動実行（推奨）：**
1. Supabaseダッシュボード → SQL Editor
2. 以下ファイルを順番に実行：
   - `migration/20250130_01_create_base_tables.sql`
   - `migration/20250130_02_create_prompt_tables.sql`
   - `migration/20250130_03_create_violation_tables.sql`
   - `migration/20250130_04_create_survey_tables.sql`
   - `migration/20250130_05_create_indexes.sql`
   - `migration/20250130_06_create_triggers.sql`

### 2. 環境変数設定
```bash
# .env ファイル
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

### 3. フロントエンド依存関係
```bash
cd react/ai-barten-react
npm install
```

### 4. バックエンド起動
```bash
# FastAPI サーバー
python main.py
```

### 5. フロントエンド起動
```bash
cd react/ai-barten-react
npm run dev
```

## 使用方法

### 管理者向け

#### 1. アンケート作成
1. 管理画面 `/admin/events` にアクセス
2. 対象イベントの「📋」ボタンをクリック
3. 「アンケート作成」ボタンから新規作成
4. タイトル・説明・期間を設定
5. 質問を追加（質問タイプ・内容・選択肢）
6. 「作成」ボタンで保存

#### 2. 統計確認
1. アンケート一覧から「📊」ボタンをクリック
2. 概要・質問別集計・回答一覧タブで確認
3. 「CSVエクスポート」でデータダウンロード

### 一般ユーザー向け

#### 1. アンケート回答
1. 提供されたURL `/survey/{survey_id}` にアクセス
2. 各質問に回答
3. 必須項目をすべて入力
4. 「回答を送信」ボタンで送信
5. 完了画面が表示

## URL構成

### 管理者画面
- `/admin/events` - イベント管理
- `/admin/events/{eventId}/surveys` - アンケート管理
- `/admin/events/{eventId}/surveys/{surveyId}/statistics` - 統計表示

### 一般ユーザー画面
- `/survey/{surveyId}` - アンケート回答

### API エンドポイント
- `GET /events/{eventId}/surveys/` - アンケート一覧
- `POST /events/{eventId}/surveys/` - アンケート作成
- `GET /surveys/{surveyId}` - アンケート詳細
- `GET /surveys/{surveyId}/form` - 回答フォーム
- `POST /surveys/{surveyId}/responses/` - 回答送信
- `GET /surveys/{surveyId}/statistics` - 統計データ

## トラブルシューティング

### よくある問題

#### 1. マイグレーション失敗
**症状**: テーブル作成エラー
**対処法**: 
- Supabaseダッシュボードで手動実行
- 既存テーブルの依存関係を確認
- service_role_keyの権限を確認

#### 2. API接続エラー
**症状**: フロントエンドからAPIにアクセスできない
**対処法**:
- `VITE_API_BASE_URL`環境変数を確認
- CORSの設定を確認
- FastAPIサーバーの起動を確認

#### 3. アンケートが表示されない
**症状**: 回答フォームでアンケートが見つからない
**対処法**:
- アンケートのis_activeがtrueか確認
- 開始日・終了日の設定を確認
- UUIDの形式が正しいか確認

#### 4. 統計が表示されない
**症状**: 統計画面でデータが表示されない
**対処法**:
- 回答データが存在するか確認
- JOINクエリの結果を確認
- ブラウザのJavaScriptエラーを確認

### デバッグ方法

#### バックエンド
```python
# ログレベルを DEBUG に設定
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### フロントエンド
```javascript
// ブラウザの開発者ツール Console タブでエラーを確認
// Network タブで API リクエストを確認
console.log('API Response:', response);
```

## 技術的な注意事項

### セキュリティ
- 管理者パスワードは環境変数化推奨
- SQL インジェクション対策済み
- XSS 対策済み（フロントエンド）

### パフォーマンス
- インデックス設定済み
- ページネーション対応
- 大量データ対応

### スケーラビリティ
- UUID主キー採用
- 正規化されたテーブル設計
- RESTful API設計

## ライセンス・クレジット

このアンケート機能は以下のライブラリを使用しています：
- React + TypeScript
- shadcn/ui (UIコンポーネント)
- Recharts (グラフ表示)
- FastAPI (バックエンドAPI)
- Supabase (データベース)

---

**実装日**: 2025年1月30日  
**バージョン**: 1.0.0  
**開発者**: Claude AI Assistant

## サポート

問題が発生した場合は、以下を確認してください：
1. このREADMEのトラブルシューティング
2. `migration/migration_history.md`
3. ブラウザの開発者ツール
4. FastAPIのログ出力

必要に応じて、データベースのリセットやマイグレーションの再実行を行ってください。