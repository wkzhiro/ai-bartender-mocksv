-- MySQLからデータをエクスポートするためのSQL

-- 1. cocktailsテーブルのデータをCSV形式でエクスポート
SELECT 
    id,
    order_id,
    status,
    name,
    image,
    flavor_ratio1,
    flavor_ratio2,
    flavor_ratio3,
    flavor_ratio4,
    comment,
    recent_event,
    event_name,
    user_name,
    career,
    hobby,
    created_at
FROM cocktails
ORDER BY id;

-- 2. poured_cocktailsテーブルのデータをCSV形式でエクスポート
SELECT 
    id,
    poured,
    name,
    flavor_name1,
    flavor_ratio1,
    flavor_name2,
    flavor_ratio2,
    flavor_name3,
    flavor_ratio3,
    flavor_name4,
    flavor_ratio4,
    comment,
    created_at
FROM poured_cocktails
ORDER BY id;

-- MySQLWorkbenchでの使用方法:
-- 1. 上記のSELECT文を実行
-- 2. 結果タブで右クリック > "Export Recordset to an External File"
-- 3. CSV形式で保存