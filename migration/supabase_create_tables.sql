-- Supabaseでテーブルを作成するSQL

-- 1. cocktailsテーブルの作成
CREATE TABLE IF NOT EXISTS cocktails (
    id BIGSERIAL PRIMARY KEY,
    order_id VARCHAR(32) UNIQUE NOT NULL,
    status INTEGER,
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
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. poured_cocktailsテーブルの作成
CREATE TABLE IF NOT EXISTS poured_cocktails (
    id BIGSERIAL PRIMARY KEY,
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

-- 3. インデックスの作成（パフォーマンス向上のため）
CREATE INDEX IF NOT EXISTS idx_cocktails_order_id ON cocktails(order_id);
CREATE INDEX IF NOT EXISTS idx_cocktails_created_at ON cocktails(created_at);
CREATE INDEX IF NOT EXISTS idx_poured_cocktails_created_at ON poured_cocktails(created_at);

-- 4. Row Level Security (RLS) の設定（オプション）
-- 注意: 必要に応じて有効化してください
-- ALTER TABLE cocktails ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE poured_cocktails ENABLE ROW LEVEL SECURITY;

-- 5. 公開読み取りポリシー（必要に応じて）
-- CREATE POLICY "Enable read access for all users" ON cocktails FOR SELECT USING (true);
-- CREATE POLICY "Enable read access for all users" ON poured_cocktails FOR SELECT USING (true);

-- 使用方法:
-- 1. Supabaseダッシュボードにログイン
-- 2. SQL Editor を開く
-- 3. 上記のSQLを貼り付けて実行