-- イベントIDをUUIDに変更するマイグレーションSQL
-- 実行日: 2025-01-28

-- 1. UUID拡張を有効化（まだ有効化されていない場合）
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. 新しいeventsテーブルを作成（UUIDをプライマリキーとして使用）
CREATE TABLE IF NOT EXISTS events_new (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. 既存のeventsテーブルからデータを移行（新しいUUIDを生成）
INSERT INTO events_new (name, description, is_active, created_at, updated_at)
SELECT name, description, is_active, created_at, updated_at
FROM events;

-- 4. 依存するビューを先に削除
DROP VIEW IF EXISTS cocktails_with_events CASCADE;
DROP VIEW IF EXISTS event_statistics CASCADE;

-- 5. cocktailsテーブルのevent_id参照を一時的に削除
ALTER TABLE cocktails DROP CONSTRAINT IF EXISTS cocktails_event_id_fkey;
ALTER TABLE cocktails DROP COLUMN IF EXISTS event_id;

-- 6. 古いeventsテーブルを削除
DROP TABLE IF EXISTS events;

-- 7. 新しいテーブルの名前を変更
ALTER TABLE events_new RENAME TO events;

-- 8. cocktailsテーブルに新しいevent_id列を追加（UUID型）
ALTER TABLE cocktails 
ADD COLUMN event_id UUID REFERENCES events(id) ON DELETE SET NULL;

-- 9. 既存のcocktailsレコードにevent_idを設定（event_nameを使用してマッピング）
UPDATE cocktails 
SET event_id = events.id
FROM events 
WHERE events.name = COALESCE(NULLIF(cocktails.event_name, ''), 'デフォルトイベント');

-- 10. インデックスの再作成
CREATE INDEX IF NOT EXISTS idx_cocktails_event_id ON cocktails(event_id);
CREATE INDEX IF NOT EXISTS idx_events_name ON events(name);
CREATE INDEX IF NOT EXISTS idx_events_is_active ON events(is_active);

-- 11. 更新用のトリガー関数とトリガーの再作成
DROP TRIGGER IF EXISTS update_events_updated_at ON events;

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

-- 12. データ整合性チェック用のビューを更新
DROP VIEW IF EXISTS cocktails_with_events;
CREATE OR REPLACE VIEW cocktails_with_events AS
SELECT 
    c.*,
    e.name as event_name_resolved,
    e.description as event_description,
    e.is_active as event_is_active
FROM cocktails c
LEFT JOIN events e ON c.event_id = e.id;

-- 13. 統計情報用のビューを更新
DROP VIEW IF EXISTS event_statistics;
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
-- SELECT 'Events table structure:' as info;
-- \d events;