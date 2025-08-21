-- 著作権確認用のカラムをcocktailsテーブルに追加
-- 実行日: 2025-08-21
-- 説明: カクテル生成後の著作権確認機能で使用するカラムを追加

-- 1. cocktailsテーブルに著作権確認用のカラムを追加
DO $$
BEGIN
    -- copyright_confirmedカラムを追加（存在しない場合のみ）
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='cocktails' AND column_name='copyright_confirmed') THEN
        ALTER TABLE cocktails ADD COLUMN copyright_confirmed BOOLEAN DEFAULT false;
    END IF;
    
    -- copyright_confirmed_atカラムを追加（存在しない場合のみ）
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='cocktails' AND column_name='copyright_confirmed_at') THEN
        ALTER TABLE cocktails ADD COLUMN copyright_confirmed_at TIMESTAMP WITH TIME ZONE;
    END IF;
END $$;

-- 2. 既存データのcopyright_confirmedをfalseに設定（NULLの場合のみ）
UPDATE cocktails 
SET copyright_confirmed = false 
WHERE copyright_confirmed IS NULL;

-- 3. パフォーマンス向上のためのインデックスを作成
CREATE INDEX IF NOT EXISTS idx_cocktails_copyright_confirmed 
ON cocktails(copyright_confirmed);

-- 4. 確認用のクエリ（実行後の確認用）
-- SELECT column_name, data_type, is_nullable, column_default 
-- FROM information_schema.columns 
-- WHERE table_name = 'cocktails' 
-- AND column_name IN ('copyright_confirmed', 'copyright_confirmed_at')
-- ORDER BY column_name;

-- 実行完了ログ
SELECT 'Copyright confirmation columns added to cocktails table successfully' as status;