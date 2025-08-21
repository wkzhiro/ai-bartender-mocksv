-- カクテルテーブルのIDをUUIDに変更するマイグレーション
-- 実行日: 2025-08-21
-- 説明: cocktailsテーブルのidカラムをSERIAL PRIMARY KEYからUUID PRIMARY KEYに変更
--       order_idカラムは外部API互換性のために維持

-- 1. 一時的にUUIDカラムを追加
ALTER TABLE cocktails ADD COLUMN uuid_id UUID DEFAULT gen_random_uuid();

-- 2. UUIDカラムにユニーク制約とNOT NULL制約を追加
ALTER TABLE cocktails ALTER COLUMN uuid_id SET NOT NULL;
ALTER TABLE cocktails ADD CONSTRAINT cocktails_uuid_id_unique UNIQUE (uuid_id);

-- 3. 関連テーブルの外部キー制約を一時的に削除
-- cocktail_promptsテーブルの外部キー制約を削除（存在する場合）
ALTER TABLE cocktail_prompts DROP CONSTRAINT IF EXISTS cocktail_prompts_cocktail_id_fkey;

-- violation_reportsテーブルの外部キー制約を削除（存在する場合）
ALTER TABLE violation_reports DROP CONSTRAINT IF EXISTS violation_reports_cocktail_id_fkey;

-- 4. 関連テーブルに新しいUUID外部キーカラムを追加
ALTER TABLE cocktail_prompts ADD COLUMN cocktail_uuid_id UUID;
ALTER TABLE violation_reports ADD COLUMN cocktail_uuid_id UUID;

-- 5. 既存データのUUIDマッピングを作成
UPDATE cocktail_prompts 
SET cocktail_uuid_id = c.uuid_id 
FROM cocktails c 
WHERE cocktail_prompts.cocktail_id = c.id;

UPDATE violation_reports 
SET cocktail_uuid_id = c.uuid_id 
FROM cocktails c 
WHERE violation_reports.cocktail_id = c.id;

-- 6. 古いSERIAL idカラムを削除
ALTER TABLE cocktails DROP COLUMN id;

-- 7. UUIDカラムをidにリネーム
ALTER TABLE cocktails RENAME COLUMN uuid_id TO id;

-- 8. 新しいUUID idカラムをプライマリキーに設定
ALTER TABLE cocktails ADD PRIMARY KEY (id);

-- 9. 関連テーブルの古い外部キーカラムを削除し、新しいUUIDカラムをリネーム
ALTER TABLE cocktail_prompts DROP COLUMN cocktail_id;
ALTER TABLE cocktail_prompts RENAME COLUMN cocktail_uuid_id TO cocktail_id;

ALTER TABLE violation_reports DROP COLUMN cocktail_id;
ALTER TABLE violation_reports RENAME COLUMN cocktail_uuid_id TO cocktail_id;

-- 10. 関連テーブルのNOT NULL制約を設定
ALTER TABLE cocktail_prompts ALTER COLUMN cocktail_id SET NOT NULL;
ALTER TABLE violation_reports ALTER COLUMN cocktail_id SET NOT NULL;

-- 11. 新しい外部キー制約を作成
ALTER TABLE cocktail_prompts 
ADD CONSTRAINT cocktail_prompts_cocktail_id_fkey 
FOREIGN KEY (cocktail_id) REFERENCES cocktails(id) ON DELETE CASCADE;

ALTER TABLE violation_reports 
ADD CONSTRAINT violation_reports_cocktail_id_fkey 
FOREIGN KEY (cocktail_id) REFERENCES cocktails(id) ON DELETE CASCADE;

-- 12. order_id → UUID のマッピング用ビューを作成（パフォーマンス向上のため）
CREATE INDEX IF NOT EXISTS idx_cocktails_order_id ON cocktails(order_id);

-- 実行完了ログ
SELECT 'Cocktail ID converted to UUID successfully' as status;