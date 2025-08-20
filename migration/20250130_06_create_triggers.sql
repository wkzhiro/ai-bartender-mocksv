-- トリガー作成マイグレーション
-- 実行日: 2025-01-30
-- 説明: updated_atの自動更新トリガーを作成

-- 更新用のトリガー関数を作成
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- eventsテーブル用トリガー
DROP TRIGGER IF EXISTS update_events_updated_at ON events;
CREATE TRIGGER update_events_updated_at
    BEFORE UPDATE ON events
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- promptsテーブル用トリガー
DROP TRIGGER IF EXISTS update_prompts_updated_at ON prompts;
CREATE TRIGGER update_prompts_updated_at
    BEFORE UPDATE ON prompts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- violation_reportsテーブル用トリガー
DROP TRIGGER IF EXISTS update_violation_reports_updated_at ON violation_reports;
CREATE TRIGGER update_violation_reports_updated_at
    BEFORE UPDATE ON violation_reports
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- surveysテーブル用トリガー
DROP TRIGGER IF EXISTS update_surveys_updated_at ON surveys;
CREATE TRIGGER update_surveys_updated_at
    BEFORE UPDATE ON surveys
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 実行完了ログ
SELECT 'Triggers created successfully' as status;