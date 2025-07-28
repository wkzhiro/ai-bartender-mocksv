-- イベントベース機能追加のためのマイグレーションSQL
-- 実行日: 2025-01-28

-- 1. eventsテーブルの作成
CREATE TABLE IF NOT EXISTS events (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. cocktailsテーブルにevent_idカラムを追加
ALTER TABLE cocktails 
ADD COLUMN IF NOT EXISTS event_id BIGINT REFERENCES events(id) ON DELETE SET NULL;

-- 3. インデックスの作成
CREATE INDEX IF NOT EXISTS idx_cocktails_event_id ON cocktails(event_id);
CREATE INDEX IF NOT EXISTS idx_events_name ON events(name);
CREATE INDEX IF NOT EXISTS idx_events_is_active ON events(is_active);

-- 4. 既存データのマイグレーション用のスクリプト
-- 既存のevent_nameから一意のイベントを抽出してeventsテーブルに挿入
INSERT INTO events (name, description)
SELECT DISTINCT 
    COALESCE(NULLIF(event_name, ''), 'デフォルトイベント') as name,
    '既存データから自動生成されたイベント' as description
FROM cocktails 
WHERE COALESCE(NULLIF(event_name, ''), 'デフォルトイベント') NOT IN (SELECT name FROM events)
ON CONFLICT (name) DO NOTHING;

-- 5. 既存のcocktailsレコードにevent_idを設定
UPDATE cocktails 
SET event_id = events.id
FROM events 
WHERE events.name = COALESCE(NULLIF(cocktails.event_name, ''), 'デフォルトイベント');

-- 6. デフォルトイベントの作成（event_nameが空の場合用）
INSERT INTO events (name, description, is_active)
VALUES ('デフォルトイベント', 'イベント名が指定されていないカクテル用のデフォルトイベント', true)
ON CONFLICT (name) DO NOTHING;

-- 7. event_nameが空のレコードにデフォルトイベントのIDを設定
UPDATE cocktails 
SET event_id = (SELECT id FROM events WHERE name = 'デフォルトイベント')
WHERE event_id IS NULL;

-- 8. 更新用のトリガー関数とトリガーの作成（updated_atの自動更新）
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_events_updated_at 
    BEFORE UPDATE ON events 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- 9. データ整合性チェック用のビュー
CREATE OR REPLACE VIEW cocktails_with_events AS
SELECT 
    c.*,
    e.name as event_name_resolved,
    e.description as event_description,
    e.is_active as event_is_active
FROM cocktails c
LEFT JOIN events e ON c.event_id = e.id;

-- 10. 統計情報用のビュー
CREATE OR REPLACE VIEW event_statistics AS
SELECT 
    e.id,
    e.name,
    e.description,
    e.is_active,
    COUNT(c.id) as cocktail_count,
    MIN(c.created_at) as first_cocktail_date,
    MAX(c.created_at) as last_cocktail_date,
    e.created_at as event_created_at
FROM events e
LEFT JOIN cocktails c ON e.id = c.event_id
GROUP BY e.id, e.name, e.description, e.is_active, e.created_at
ORDER BY cocktail_count DESC, e.created_at DESC;

-- 実行後の確認クエリ
-- SELECT * FROM event_statistics;
-- SELECT COUNT(*) as total_cocktails, COUNT(event_id) as cocktails_with_event FROM cocktails;