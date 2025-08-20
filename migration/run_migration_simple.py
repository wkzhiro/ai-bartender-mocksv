#!/usr/bin/env python3
"""
簡単なマイグレーション実行スクリプト
各テーブルを個別に作成
"""

import os
from dotenv import load_dotenv
from db.supabase_client import supabase_client

load_dotenv(override=True)

def test_connection():
    """接続テスト"""
    try:
        # 簡単なクエリでテスト
        result = supabase_client.client.table('_schema').select('*').limit(1).execute()
        print("✅ Supabase接続成功")
        return True
    except Exception as e:
        print(f"❌ Supabase接続失敗: {e}")
        return False

def create_events_table():
    """eventsテーブル作成"""
    sql = """
    CREATE TABLE IF NOT EXISTS events (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name VARCHAR(255) NOT NULL UNIQUE,
        description TEXT,
        is_active BOOLEAN DEFAULT true,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    """
    try:
        print("eventsテーブル作成中...")
        # テーブル作成は手動実行を推奨
        print("⚠️  以下のSQLをSupabaseダッシュボードで実行してください:")
        print(sql)
        return True
    except Exception as e:
        print(f"❌ eventsテーブル作成失敗: {e}")
        return False

def main():
    print("🚀 簡単マイグレーション実行")
    
    if not test_connection():
        return
    
    # Supabaseダッシュボードでの手動実行を案内
    print("\n📋 マイグレーション実行手順:")
    print("1. https://zlhijsompozymqhjubdi.supabase.co/project/zlhijsompozymqhjubdi にアクセス")
    print("2. 左メニューから 'SQL Editor' を選択")
    print("3. 以下のファイルの内容を順番にコピー&ペーストして実行:")
    
    migration_files = [
        "migration/20250130_01_create_base_tables.sql",
        "migration/20250130_02_create_prompt_tables.sql",
        "migration/20250130_03_create_violation_tables.sql", 
        "migration/20250130_04_create_survey_tables.sql",
        "migration/20250130_05_create_indexes.sql",
        "migration/20250130_06_create_triggers.sql"
    ]
    
    for i, file_path in enumerate(migration_files, 1):
        print(f"   {i}. {file_path}")
    
    print("\n4. 各ファイル実行後、成功ログが表示されることを確認")
    print("5. 全て完了後、アプリケーションを起動")
    
    print("\n💡 ヒント:")
    print("- 一度に全部実行せず、1つずつ実行して結果を確認してください")
    print("- エラーが出た場合は、既にテーブルが存在する可能性があります")

if __name__ == "__main__":
    main()