-- カクテルテーブルに表示/非表示と違反報告関連のカラムを追加

-- is_visible: 表示フラグ（デフォルト: true）
-- violation_reports_count: 違反報告数（デフォルト: 0）  
-- hidden_at: 非表示にされた日時
-- hidden_reason: 非表示にした理由

ALTER TABLE cocktails 
ADD COLUMN is_visible BOOLEAN DEFAULT true,
ADD COLUMN violation_reports_count INTEGER DEFAULT 0,
ADD COLUMN hidden_at TIMESTAMP,
ADD COLUMN hidden_reason TEXT;

-- 既存データには is_visible = true を設定
UPDATE cocktails SET is_visible = true WHERE is_visible IS NULL;

-- 違反報告テーブルを作成
CREATE TABLE violation_reports (
    id BIGSERIAL PRIMARY KEY,
    cocktail_id BIGINT REFERENCES cocktails(id) ON DELETE CASCADE,
    reporter_id VARCHAR(255),  -- 報告者のIPアドレス（IPv6対応のため255文字）
    report_reason TEXT,
    report_category VARCHAR(50), -- 'inappropriate', 'offensive', 'spam', 'other'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- 同じ報告者から同じカクテルへの重複報告を防ぐ
    UNIQUE(cocktail_id, reporter_id)
);

-- インデックスを追加
CREATE INDEX idx_cocktails_is_visible ON cocktails(is_visible);
CREATE INDEX idx_cocktails_violation_reports_count ON cocktails(violation_reports_count);
CREATE INDEX idx_violation_reports_cocktail_id ON violation_reports(cocktail_id);
CREATE INDEX idx_violation_reports_created_at ON violation_reports(created_at);