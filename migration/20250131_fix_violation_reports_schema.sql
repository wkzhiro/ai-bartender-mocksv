-- 違反報告テーブルのスキーマ修正マイグレーション
-- 実行日: 2025-01-31
-- 説明: violation_reportsテーブルのカラム不整合を修正

-- 1. 必要なカラムが存在しない場合は追加
DO $$
BEGIN
    -- reporter_idカラムを追加（存在しない場合のみ）
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'violation_reports' 
        AND column_name = 'reporter_id'
    ) THEN
        ALTER TABLE violation_reports 
        ADD COLUMN reporter_id VARCHAR(255);
        RAISE NOTICE 'Added reporter_id column';
    END IF;

    -- report_reasonカラムを追加（存在しない場合のみ）
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'violation_reports' 
        AND column_name = 'report_reason'
    ) THEN
        ALTER TABLE violation_reports 
        ADD COLUMN report_reason TEXT;
        RAISE NOTICE 'Added report_reason column';
    END IF;

    -- report_categoryカラムを追加（存在しない場合のみ）
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'violation_reports' 
        AND column_name = 'report_category'
    ) THEN
        ALTER TABLE violation_reports 
        ADD COLUMN report_category VARCHAR(50);
        RAISE NOTICE 'Added report_category column';
    END IF;

    -- created_atカラムがなくreported_atがある場合はリネーム
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'violation_reports' 
        AND column_name = 'created_at'
    ) AND EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'violation_reports' 
        AND column_name = 'reported_at'
    ) THEN
        ALTER TABLE violation_reports 
        RENAME COLUMN reported_at TO created_at;
        RAISE NOTICE 'Renamed reported_at to created_at';
    END IF;

    -- created_atカラムが全く存在しない場合は追加
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'violation_reports' 
        AND column_name = 'created_at'
    ) THEN
        ALTER TABLE violation_reports 
        ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
        RAISE NOTICE 'Added created_at column';
    END IF;

    -- reasonカラムが存在し、report_reasonが存在しない場合はデータを移行
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'violation_reports' 
        AND column_name = 'reason'
    ) AND EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'violation_reports' 
        AND column_name = 'report_reason'
    ) THEN
        -- reasonカラムのデータをreport_reasonにコピー
        UPDATE violation_reports 
        SET report_reason = reason 
        WHERE report_reason IS NULL AND reason IS NOT NULL;
        
        -- reasonカラムを削除
        ALTER TABLE violation_reports DROP COLUMN IF EXISTS reason;
        RAISE NOTICE 'Migrated data from reason to report_reason and dropped reason column';
    END IF;

    -- statusカラムが存在しない場合は追加
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'violation_reports' 
        AND column_name = 'status'
    ) THEN
        ALTER TABLE violation_reports 
        ADD COLUMN status VARCHAR(50) DEFAULT 'pending';
        RAISE NOTICE 'Added status column';
    END IF;

    -- updated_atカラムが存在しない場合は追加
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'violation_reports' 
        AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE violation_reports 
        ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
        RAISE NOTICE 'Added updated_at column';
    END IF;
END $$;

-- 2. 重複を防ぐためのユニーク制約を追加（存在しない場合のみ）
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'violation_reports_cocktail_id_reporter_id_key' 
        AND table_name = 'violation_reports'
    ) THEN
        ALTER TABLE violation_reports 
        ADD CONSTRAINT violation_reports_cocktail_id_reporter_id_key 
        UNIQUE(cocktail_id, reporter_id);
        RAISE NOTICE 'Added unique constraint for cocktail_id and reporter_id';
    END IF;
END $$;

-- 3. インデックスを追加（パフォーマンス向上のため）
CREATE INDEX IF NOT EXISTS idx_violation_reports_cocktail_id ON violation_reports(cocktail_id);
CREATE INDEX IF NOT EXISTS idx_violation_reports_status ON violation_reports(status);
CREATE INDEX IF NOT EXISTS idx_violation_reports_created_at ON violation_reports(created_at);

-- 4. 既存データの修正
-- report_categoryがNULLの場合はデフォルト値を設定
UPDATE violation_reports 
SET report_category = 'inappropriate' 
WHERE report_category IS NULL;

-- statusがNULLの場合はデフォルト値を設定
UPDATE violation_reports 
SET status = 'pending' 
WHERE status IS NULL;

-- updated_atがNULLの場合はcreated_atと同じ値を設定
UPDATE violation_reports 
SET updated_at = created_at 
WHERE updated_at IS NULL;

-- 実行完了ログ
SELECT 'Violation reports schema fixed successfully' as status;