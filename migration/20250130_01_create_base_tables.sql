-- 基本テーブル作成マイグレーション
-- 実行日: 2025-01-30
-- 説明: イベント、カクテル、注いだカクテル記録の基本テーブルを作成

-- 1. eventsテーブルの作成
CREATE TABLE IF NOT EXISTS events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. cocktailsテーブルの作成
CREATE TABLE IF NOT EXISTS cocktails (
    id SERIAL PRIMARY KEY,
    order_id VARCHAR(32) UNIQUE NOT NULL,
    event_id UUID REFERENCES events(id) ON DELETE SET NULL,
    status INTEGER DEFAULT 200,
    name VARCHAR(128),
    image TEXT,
    flavor_ratio1 VARCHAR(16),
    flavor_ratio2 VARCHAR(16),
    flavor_ratio3 VARCHAR(16),
    flavor_ratio4 VARCHAR(16),
    comment TEXT,
    recent_event TEXT,
    event_name VARCHAR(128),
    user_name VARCHAR(128),
    career VARCHAR(128),
    hobby VARCHAR(128),
    is_visible BOOLEAN DEFAULT true,
    violation_reports_count INTEGER DEFAULT 0,
    hidden_at TIMESTAMP WITH TIME ZONE,
    hidden_reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. poured_cocktailsテーブルの作成
CREATE TABLE IF NOT EXISTS poured_cocktails (
    id SERIAL PRIMARY KEY,
    poured VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    flavor_name1 VARCHAR(255) NOT NULL,
    flavor_ratio1 VARCHAR(32) NOT NULL,
    flavor_name2 VARCHAR(32) NOT NULL,
    flavor_ratio2 VARCHAR(32) NOT NULL,
    flavor_name3 VARCHAR(32) NOT NULL,
    flavor_ratio3 VARCHAR(32) NOT NULL,
    flavor_name4 VARCHAR(32) NOT NULL,
    flavor_ratio4 VARCHAR(32) NOT NULL,
    comment TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- デフォルトイベントの作成
INSERT INTO events (name, description, is_active)
VALUES ('デフォルトイベント', 'イベント名が指定されていないカクテル用のデフォルトイベント', true)
ON CONFLICT (name) DO NOTHING;

-- 実行完了ログ
SELECT 'Base tables created successfully' as status;