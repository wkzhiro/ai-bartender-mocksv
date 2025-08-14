-- カクテルテーブルに表示/非表示と違反報告関連のカラムを安全に追加
-- 既存カラムがある場合はスキップする

-- カラムが存在しない場合のみ追加
DO $$ 
BEGIN
    -- is_visibleカラムを追加（存在しない場合のみ）
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='cocktails' AND column_name='is_visible') THEN
        ALTER TABLE cocktails ADD COLUMN is_visible BOOLEAN DEFAULT true;
    END IF;
    
    -- violation_reports_countカラムを追加（存在しない場合のみ）
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='cocktails' AND column_name='violation_reports_count') THEN
        ALTER TABLE cocktails ADD COLUMN violation_reports_count INTEGER DEFAULT 0;
    END IF;
    
    -- hidden_atカラムを追加（存在しない場合のみ）
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='cocktails' AND column_name='hidden_at') THEN
        ALTER TABLE cocktails ADD COLUMN hidden_at TIMESTAMP;
    END IF;
    
    -- hidden_reasonカラムを追加（存在しない場合のみ）
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='cocktails' AND column_name='hidden_reason') THEN
        ALTER TABLE cocktails ADD COLUMN hidden_reason TEXT;
    END IF;
END $$;

-- 既存データのis_visibleを確実にtrueに設定
UPDATE cocktails SET is_visible = true WHERE is_visible IS NULL;

-- violation_reportsテーブルを作成（存在しない場合のみ）
CREATE TABLE IF NOT EXISTS violation_reports (
    id BIGSERIAL PRIMARY KEY,
    cocktail_id BIGINT REFERENCES cocktails(id) ON DELETE CASCADE,
    reporter_id VARCHAR(255),  -- 報告者のIPアドレス（IPv6対応のため255文字）
    report_reason TEXT,
    report_category VARCHAR(50), -- 'inappropriate', 'offensive', 'spam', 'other'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- 同じ報告者から同じカクテルへの重複報告を防ぐ
    UNIQUE(cocktail_id, reporter_id)
);

-- インデックスを安全に作成（存在しない場合のみ）
CREATE INDEX IF NOT EXISTS idx_cocktails_is_visible ON cocktails(is_visible);
CREATE INDEX IF NOT EXISTS idx_cocktails_violation_reports_count ON cocktails(violation_reports_count);
CREATE INDEX IF NOT EXISTS idx_violation_reports_cocktail_id ON violation_reports(cocktail_id);
CREATE INDEX IF NOT EXISTS idx_violation_reports_created_at ON violation_reports(created_at);