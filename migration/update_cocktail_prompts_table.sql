-- cocktail_promptsテーブルの変更用migrationファイル
-- 既存のテーブルにprompt_typeカラムを追加し、制約を変更

-- 1. prompt_typeカラムを追加（既存レコードがある場合はデフォルト値を設定）
ALTER TABLE cocktail_prompts 
ADD COLUMN IF NOT EXISTS prompt_type VARCHAR(50) DEFAULT 'recipe';

-- 2. 既存のUNIQUE制約を削除
ALTER TABLE cocktail_prompts 
DROP CONSTRAINT IF EXISTS cocktail_prompts_cocktail_id_prompt_id_key;

-- 3. 新しいUNIQUE制約を追加（cocktail_id + prompt_typeの組み合わせでユニーク）
ALTER TABLE cocktail_prompts 
ADD CONSTRAINT cocktail_prompts_cocktail_id_prompt_type_key 
UNIQUE(cocktail_id, prompt_type);

-- 4. prompt_typeカラムをNOT NULLに変更
ALTER TABLE cocktail_prompts 
ALTER COLUMN prompt_type SET NOT NULL;

-- 5. prompt_typeカラムのデフォルト値を削除
ALTER TABLE cocktail_prompts 
ALTER COLUMN prompt_type DROP DEFAULT;

-- 6. インデックスを追加（パフォーマンス向上）
CREATE INDEX IF NOT EXISTS idx_cocktail_prompts_prompt_type ON cocktail_prompts(prompt_type);
CREATE INDEX IF NOT EXISTS idx_cocktail_prompts_cocktail_id_type ON cocktail_prompts(cocktail_id, prompt_type);