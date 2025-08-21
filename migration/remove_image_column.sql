-- 画像カラム削除マイグレーション
-- 実行日: 2025-01-21
-- 説明: cocktailsテーブルからimageカラムを削除（Supabase Storageに移行完了のため）

-- 1. cocktailsテーブルからimageカラムを削除
ALTER TABLE cocktails DROP COLUMN IF EXISTS image;

-- 実行完了ログ
SELECT 'Image column removed successfully' as status;