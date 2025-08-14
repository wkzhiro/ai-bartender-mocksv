-- violation_reportsテーブルにstatusとupdated_atカラムを追加

-- statusカラムを追加（デフォルトは'pending'）
ALTER TABLE violation_reports 
ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'pending';

-- updated_atカラムを追加（デフォルトは作成時刻）
ALTER TABLE violation_reports 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- 既存のレコードのupdated_atをcreated_atと同じにする
UPDATE violation_reports 
SET updated_at = created_at 
WHERE updated_at IS NULL;

-- statusカラムにCHECK制約を追加（制約が存在しない場合のみ）
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'check_violation_status' 
        AND table_name = 'violation_reports'
    ) THEN
        ALTER TABLE violation_reports 
        ADD CONSTRAINT check_violation_status 
        CHECK (status IN ('pending', 'reviewing', 'resolved', 'rejected'));
    END IF;
END $$;

-- インデックスを追加（ステータス別の検索を高速化）
CREATE INDEX IF NOT EXISTS idx_violation_reports_status ON violation_reports(status);