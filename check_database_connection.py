#!/usr/bin/env python3
"""
データベース接続とテーブル存在確認スクリプト
"""
import os
from dotenv import load_dotenv
from supabase import create_client, Client

# 環境変数を読み込む
load_dotenv()

def check_database_connection():
    """データベース接続確認"""
    try:
        # Supabaseクライアント作成
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not url or not key:
            print("エラー: SUPABASE_URLまたはSUPABASE_SERVICE_ROLE_KEYが設定されていません")
            return False
            
        print(f"Supabase URL: {url}")
        
        supabase: Client = create_client(url, key)
        
        # 1. イベントテーブルの確認
        print("\n=== 1. eventsテーブルの確認 ===")
        try:
            events_result = supabase.table('events').select('id, name').limit(5).execute()
            print(f"イベント数: {len(events_result.data)}")
            for event in events_result.data:
                print(f"  - ID: {event['id']}, 名前: {event['name']}")
        except Exception as e:
            print(f"eventsテーブルエラー: {e}")
        
        # 2. surveysテーブルの確認
        print("\n=== 2. surveysテーブルの確認 ===")
        try:
            surveys_result = supabase.table('surveys').select('id, title, event_id').limit(5).execute()
            print(f"アンケート数: {len(surveys_result.data)}")
            for survey in surveys_result.data:
                print(f"  - ID: {survey['id']}, タイトル: {survey['title']}, イベントID: {survey['event_id']}")
        except Exception as e:
            print(f"surveysテーブルエラー: {e}")
        
        # 3. survey_questionsテーブルの確認
        print("\n=== 3. survey_questionsテーブルの確認 ===")
        try:
            questions_result = supabase.table('survey_questions').select('id, question_text').limit(5).execute()
            print(f"質問数: {len(questions_result.data)}")
            for question in questions_result.data:
                print(f"  - ID: {question['id']}, 質問: {question['question_text'][:50]}...")
        except Exception as e:
            print(f"survey_questionsテーブルエラー: {e}")
        
        # 4. survey_question_optionsテーブルの確認
        print("\n=== 4. survey_question_optionsテーブルの確認 ===")
        try:
            options_result = supabase.table('survey_question_options').select('id, option_text').limit(5).execute()
            print(f"選択肢数: {len(options_result.data)}")
            for option in options_result.data:
                print(f"  - ID: {option['id']}, 選択肢: {option['option_text']}")
        except Exception as e:
            print(f"survey_question_optionsテーブルエラー: {e}")
        
        # 5. テーブル情報取得（PostgreSQLのメタ情報）
        print("\n=== 5. テーブル一覧確認 ===")
        try:
            # PostgreSQLのinformation_schemaからテーブル情報を取得
            table_query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE '%survey%'
            ORDER BY table_name;
            """
            tables_result = supabase.rpc('exec_sql', {'sql': table_query}).execute()
            print(f"アンケート関連テーブル: {tables_result.data}")
        except Exception as e:
            print(f"テーブル一覧取得エラー: {e}")
        
        return True
        
    except Exception as e:
        print(f"データベース接続エラー: {e}")
        return False

if __name__ == "__main__":
    print("=== データベース接続確認開始 ===")
    success = check_database_connection()
    if success:
        print("\n=== 接続確認完了 ===")
    else:
        print("\n=== 接続確認失敗 ===")