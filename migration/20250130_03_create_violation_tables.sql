-- 違反報告テーブル作成マイグレーション
-- 実行日: 2025-01-30
-- 説明: 違反報告関連テーブルを作成

-- 1. violation_reportsテーブルの作成
CREATE TABLE IF NOT EXISTS violation_reports (
    id SERIAL PRIMARY KEY,
    cocktail_id BIGINT REFERENCES cocktails(id) ON DELETE CASCADE,
    reason TEXT,
    reported_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'pending',
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 実行完了ログ
SELECT 'Violation tables created successfully' as status;