-- UUIDプライマリキー変換マイグレーション
-- 実行日: 2025-08-21
-- 説明: cocktailsテーブルのidをUUIDに変換し、プライマリキーに設定

-- 1. uuid拡張を有効化（既に有効な場合はスキップ）
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. 外部キー制約を一時的に削除（関連テーブルがある場合）
-- survey_responsesテーブルのcocktail_idがcocktails.idを参照している場合
ALTER TABLE survey_responses DROP CONSTRAINT IF EXISTS survey_responses_cocktail_id_fkey;
-- cocktail_promptsテーブルがある場合
ALTER TABLE cocktail_prompts DROP CONSTRAINT IF EXISTS cocktail_prompts_cocktail_id_fkey;
-- violation_reportsテーブルがある場合
ALTER TABLE violation_reports DROP CONSTRAINT IF EXISTS violation_reports_cocktail_id_fkey;

-- 3. 既存のプライマリキー制約を削除
ALTER TABLE cocktails DROP CONSTRAINT IF EXISTS cocktails_pkey;

-- 4. 新しいuuidカラムを追加し、既存データにUUIDを生成
ALTER TABLE cocktails ADD COLUMN IF NOT EXISTS uuid UUID DEFAULT gen_random_uuid();

-- 5. 既存のレコードにUUIDを割り当て（NULLの場合のみ）
UPDATE cocktails 
SET uuid = gen_random_uuid() 
WHERE uuid IS NULL;

-- 6. uuidカラムをNOT NULLに設定し、プライマリキーにする
ALTER TABLE cocktails ALTER COLUMN uuid SET NOT NULL;
ALTER TABLE cocktails ADD CONSTRAINT cocktails_pkey PRIMARY KEY (uuid);

-- 7. 古いidカラムを削除
ALTER TABLE cocktails DROP COLUMN IF EXISTS id;

-- 8. 必要なインデックスを作成
CREATE INDEX IF NOT EXISTS idx_cocktails_order_id ON cocktails(order_id);
CREATE INDEX IF NOT EXISTS idx_cocktails_event_id ON cocktails(event_id);

-- 9. 関連テーブルの外部キー制約を再作成（UUIDベース）
-- survey_responsesテーブルのcocktail_idカラムをUUIDに変更
DO $$ 
BEGIN
    -- cocktail_idカラムが存在する場合のみ実行
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'survey_responses' AND column_name = 'cocktail_id') THEN
        -- 既存のデータをクリア（参照整合性のため）
        UPDATE survey_responses SET cocktail_id = NULL;
        -- 古いカラムを削除
        ALTER TABLE survey_responses DROP COLUMN cocktail_id;
        -- 新しいUUID型カラムを追加
        ALTER TABLE survey_responses ADD COLUMN cocktail_id UUID;
        -- 外部キー制約を再作成
        ALTER TABLE survey_responses ADD CONSTRAINT survey_responses_cocktail_id_fkey 
            FOREIGN KEY (cocktail_id) REFERENCES cocktails(uuid) ON DELETE SET NULL;
    END IF;
END $$;

-- 10. cocktail_promptsテーブルが存在する場合の処理
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'cocktail_prompts') THEN
        -- 既存のデータをクリア
        DELETE FROM cocktail_prompts;
        -- 古いカラムを削除
        ALTER TABLE cocktail_prompts DROP COLUMN IF EXISTS cocktail_id;
        -- 新しいUUID型カラムを追加
        ALTER TABLE cocktail_prompts ADD COLUMN cocktail_id UUID NOT NULL;
        -- 外部キー制約を再作成
        ALTER TABLE cocktail_prompts ADD CONSTRAINT cocktail_prompts_cocktail_id_fkey 
            FOREIGN KEY (cocktail_id) REFERENCES cocktails(uuid) ON DELETE CASCADE;
    END IF;
END $$;

-- 11. violation_reportsテーブルが存在する場合の処理
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'violation_reports') THEN
        -- 既存のデータをクリア（参照整合性のため）
        DELETE FROM violation_reports;
        -- 古いカラムを削除
        ALTER TABLE violation_reports DROP COLUMN IF EXISTS cocktail_id;
        -- 新しいUUID型カラムを追加
        ALTER TABLE violation_reports ADD COLUMN cocktail_id UUID NOT NULL;
        -- 外部キー制約を再作成
        ALTER TABLE violation_reports ADD CONSTRAINT violation_reports_cocktail_id_fkey 
            FOREIGN KEY (cocktail_id) REFERENCES cocktails(uuid) ON DELETE CASCADE;
    END IF;
END $$;

-- 実行完了ログ
SELECT 'Cocktails table converted to UUID primary key successfully' as status;