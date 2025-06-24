import os
from typing import Optional, Dict, Any, List
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv(override=True)

class SupabaseClient:
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        # サービスロールキーがあれば優先して使う
        self.key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        if not self.url or not self.key:
            raise ValueError("SUPABASE_URLとSUPABASE_SERVICE_ROLE_KEYまたはSUPABASE_ANON_KEYが設定されていません")
        self.client: Client = create_client(self.url, self.key)
    
    def create_tables(self):
        """テーブル作成SQLをSupabaseで実行"""
        # SQLクエリでテーブル作成
        cocktails_sql = """
        CREATE TABLE IF NOT EXISTS cocktails (
            id SERIAL PRIMARY KEY,
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
        """
        
        poured_cocktails_sql = """
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
        """
        
        try:
            self.client.postgrest.rpc('exec_sql', {'sql': cocktails_sql}).execute()
            self.client.postgrest.rpc('exec_sql', {'sql': poured_cocktails_sql}).execute()
            print("Supabaseテーブル作成完了")
        except Exception as e:
            print(f"テーブル作成エラー: {e}")
            # RPCが使えない場合は手動でテーブル作成が必要
            print("SupabaseダッシュボードでSQLエディタを使用してテーブルを作成してください:")
            print(cocktails_sql)
            print(poured_cocktails_sql)
    
    def insert_cocktail(self, data: Dict[str, Any]) -> Optional[int]:
        """カクテルデータを挿入"""
        try:
            result = self.client.table('cocktails').insert(data).execute()
            if result.data:
                return result.data[0]['id']
            return None
        except Exception as e:
            print(f"Supabase挿入エラー(cocktails): {e}")
            return None
    
    def get_cocktail_by_order_id(self, order_id: str) -> Optional[Dict[str, Any]]:
        """注文IDでカクテルを取得"""
        try:
            result = self.client.table('cocktails').select('*').eq('order_id', order_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Supabase取得エラー: {e}")
            return None
    
    def get_all_cocktails(self) -> List[Dict[str, Any]]:
        """全カクテルを取得（作成日時降順）"""
        try:
            result = self.client.table('cocktails').select('*').order('created_at', desc=True).execute()
            return result.data or []
        except Exception as e:
            print(f"Supabase全件取得エラー: {e}")
            return []
    
    def insert_poured_cocktail(self, data: Dict[str, Any]) -> Optional[int]:
        """注がれたカクテルデータを挿入"""
        try:
            result = self.client.table('poured_cocktails').insert(data).execute()
            if result.data:
                return result.data[0]['id']
            return None
        except Exception as e:
            print(f"Supabase挿入エラー(poured_cocktails): {e}")
            return None
    
    def table_exists(self, table_name: str) -> bool:
        """テーブルの存在確認"""
        try:
            result = self.client.table(table_name).select('id').limit(1).execute()
            return True
        except:
            return False

# グローバルインスタンス
supabase_client = SupabaseClient()
