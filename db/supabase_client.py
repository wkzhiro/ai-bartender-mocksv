import os
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv
import uuid

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
            recipe_prompt_id INTEGER REFERENCES prompts(id),
            image_prompt_id INTEGER REFERENCES prompts(id),
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
        
        prompts_sql = """
        CREATE TABLE IF NOT EXISTS prompts (
            id SERIAL PRIMARY KEY,
            prompt_type VARCHAR(50) NOT NULL,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            prompt_text TEXT NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        
        cocktail_prompts_sql = """
        CREATE TABLE IF NOT EXISTS cocktail_prompts (
            id SERIAL PRIMARY KEY,
            cocktail_id INTEGER NOT NULL REFERENCES cocktails(id) ON DELETE CASCADE,
            prompt_id INTEGER NOT NULL REFERENCES prompts(id) ON DELETE CASCADE,
            prompt_type VARCHAR(50) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            UNIQUE(cocktail_id, prompt_type)
        );
        """
        
        try:
            self.client.postgrest.rpc('exec_sql', {'sql': cocktails_sql}).execute()
            self.client.postgrest.rpc('exec_sql', {'sql': poured_cocktails_sql}).execute()
            self.client.postgrest.rpc('exec_sql', {'sql': prompts_sql}).execute()
            self.client.postgrest.rpc('exec_sql', {'sql': cocktail_prompts_sql}).execute()
            print("Supabaseテーブル作成完了")
        except Exception as e:
            print(f"テーブル作成エラー: {e}")
            # RPCが使えない場合は手動でテーブル作成が必要
            print("SupabaseダッシュボードでSQLエディタを使用してテーブルを作成してください:")
            print(cocktails_sql)
            print(poured_cocktails_sql)
            print(prompts_sql)
            print(cocktail_prompts_sql)
    
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
    
    def get_all_cocktails(self, limit: int = None, offset: int = 0, event_id: Union[str, uuid.UUID] = None) -> Dict[str, Any]:
        """全カクテルを取得（作成日時降順）、event_idでフィルター可能"""
        try:
            # データを取得（limit+1で次のページの存在を確認）
            extra_limit = limit + 1 if limit else None
            query = self.client.table('cocktails').select('*').eq('is_visible', True).order('created_at', desc=True)
            
            # イベントIDでフィルター
            if event_id is not None:
                # UUIDの場合は文字列に変換
                event_id_str = str(event_id) if isinstance(event_id, uuid.UUID) else event_id
                query = query.eq('event_id', event_id_str)
            
            if extra_limit is not None:
                query = query.limit(extra_limit)
            if offset > 0:
                query = query.offset(offset)
                
            print(f"デバッグ: クエリ実行 - limit={limit}, offset={offset}, extra_limit={extra_limit}")
            result = query.execute()
            data = result.data or []
            print(f"デバッグ: 取得件数={len(data)}")
            
            # 次のページがあるかを判定
            has_next = False
            if limit and len(data) > limit:
                has_next = True
                data = data[:limit]  # 余分な1件を削除
                print(f"デバッグ: 次ページあり、データを{limit}件に調整")
            
            # 前のページがあるかを判定
            has_prev = offset > 0
            
            print(f"デバッグ: 結果 - データ件数={len(data)}, has_next={has_next}, has_prev={has_prev}")
            
            # 安全な方法で全件数を取得
            total_count = self._get_total_count_safe(event_id=event_id)
            
            return {
                'data': data,
                'total_count': total_count,
                'limit': limit,
                'offset': offset,
                'has_next': has_next,
                'has_prev': has_prev
            }
        except Exception as e:
            print(f"Supabase全件取得エラー: {e}")
            # エラー時も件数取得を試行
            total_count = self._get_total_count_safe(event_id=event_id)
            
            return {
                'data': [],
                'total_count': total_count,
                'limit': limit,
                'offset': offset,
                'has_next': False,
                'has_prev': False
            }
    
    def _get_total_count_safe(self, event_id: Union[str, uuid.UUID] = None) -> int:
        """安全に全件数を取得（タイムアウト対応）、event_idでフィルター可能"""
        try:
            # 方法1: 最も軽量なカウントクエリ（IDのみ、制限なし）
            query = self.client.table('cocktails').select('id', count='exact').eq('is_visible', True).limit(1)
            if event_id is not None:
                # UUIDの場合は文字列に変換
                event_id_str = str(event_id) if isinstance(event_id, uuid.UUID) else event_id
                query = query.eq('event_id', event_id_str)
            count_result = query.execute()
            count = count_result.count
            if count is not None:
                print(f"デバッグ: 全件数取得成功 = {count}")
                return count
        except Exception as e:
            print(f"軽量カウントクエリエラー: {e}")
        
        try:
            # 方法2: さらに軽量なクエリ（created_atのみ）
            count_result = self.client.table('cocktails').select('created_at', count='exact').eq('is_visible', True).limit(1).execute()
            count = count_result.count
            if count is not None:
                print(f"デバッグ: created_atカウント成功 = {count}")
                return count
        except Exception as e:
            print(f"created_atカウントエラー: {e}")
        
        try:
            # 方法3: 複数回に分けて概算取得（1000件ずつ）
            total_estimated = 0
            limit_chunk = 1000
            for i in range(10):  # 最大10000件まで
                offset_chunk = i * limit_chunk
                chunk_result = self.client.table('cocktails').select('id').eq('is_visible', True).limit(limit_chunk).offset(offset_chunk).execute()
                chunk_count = len(chunk_result.data) if chunk_result.data else 0
                total_estimated += chunk_count
                
                if chunk_count < limit_chunk:  # 最後のチャンクに到達
                    break
            
            print(f"デバッグ: チャンク方式で概算取得 = {total_estimated}")
            return total_estimated
            
        except Exception as e:
            print(f"チャンク方式エラー: {e}")
            
        # すべて失敗した場合はNone
        print("デバッグ: すべての件数取得方式が失敗")
        return None
    
    def _get_total_count_efficient(self) -> int:
        """効率的に全件数を取得"""
        try:
            # IDのみを取得してカウント（軽量なクエリ）
            count_result = self.client.table('cocktails').select('id', count='exact').limit(1).execute()
            return count_result.count or 0
        except Exception as e:
            print(f"件数取得エラー: {e}")
            # エラー時は概算値として、現在取得できている最大ID+オフセットを返す
            try:
                # 最新の1件だけ取得してIDベースで概算
                latest = self.client.table('cocktails').select('id').order('created_at', desc=True).limit(1).execute()
                if latest.data and len(latest.data) > 0:
                    # 概算として適当な値を返す（実際のプロダクションでは要調整）
                    return 1000  # 仮の概算値
                return 0
            except:
                return 0
    
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
    
    def get_prompts(self, prompt_type: str = None, is_active: bool = True) -> List[Dict[str, Any]]:
        """プロンプトを取得"""
        try:
            query = self.client.table('prompts').select('*')
            if prompt_type:
                query = query.eq('prompt_type', prompt_type)
            if is_active:
                query = query.eq('is_active', True)
            result = query.order('created_at', desc=True).execute()
            return result.data or []
        except Exception as e:
            print(f"プロンプト取得エラー: {e}")
            return []
    
    def get_prompt_by_id(self, prompt_id: int) -> Optional[Dict[str, Any]]:
        """IDでプロンプトを取得"""
        try:
            result = self.client.table('prompts').select('*').eq('id', prompt_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"プロンプト取得エラー: {e}")
            return None
    
    def insert_prompt(self, data: Dict[str, Any]) -> Optional[int]:
        """プロンプトを挿入"""
        try:
            result = self.client.table('prompts').insert(data).execute()
            if result.data:
                return result.data[0]['id']
            return None
        except Exception as e:
            print(f"プロンプト挿入エラー: {e}")
            return None
    
    def update_prompt(self, prompt_id: int, data: Dict[str, Any]) -> bool:
        """プロンプトを更新"""
        try:
            data['updated_at'] = datetime.now().isoformat()
            result = self.client.table('prompts').update(data).eq('id', prompt_id).execute()
            return bool(result.data)
        except Exception as e:
            print(f"プロンプト更新エラー: {e}")
            return False
    
    def link_cocktail_prompt(self, cocktail_id: int, prompt_id: int, prompt_type: str) -> bool:
        """カクテルとプロンプトを関連付け"""
        try:
            # 既存のレコードを削除してから新しいレコードを挿入（UPSERT的な動作）
            self.client.table('cocktail_prompts').delete().eq('cocktail_id', cocktail_id).eq('prompt_type', prompt_type).execute()
            
            data = {
                'cocktail_id': cocktail_id,
                'prompt_id': prompt_id,
                'prompt_type': prompt_type
            }
            result = self.client.table('cocktail_prompts').insert(data).execute()
            return bool(result.data)
        except Exception as e:
            print(f"カクテル-プロンプト関連付けエラー: {e}")
            return False
    
    def get_cocktail_prompts(self, cocktail_id: int) -> List[Dict[str, Any]]:
        """カクテルに関連付けられたプロンプトを取得"""
        try:
            result = self.client.table('cocktail_prompts').select(
                'prompt_id, prompt_type, prompts(id, prompt_type, title, description, prompt_text)'
            ).eq('cocktail_id', cocktail_id).execute()
            return result.data or []
        except Exception as e:
            print(f"カクテル-プロンプト取得エラー: {e}")
            return []
    
    def get_cocktail_prompt_by_type(self, cocktail_id: int, prompt_type: str) -> Optional[Dict[str, Any]]:
        """カクテルの特定タイプのプロンプトを取得"""
        try:
            result = self.client.table('cocktail_prompts').select(
                'prompt_id, prompt_type, prompts(id, prompt_type, title, description, prompt_text)'
            ).eq('cocktail_id', cocktail_id).eq('prompt_type', prompt_type).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"カクテル-プロンプト取得エラー: {e}")
            return None
    
    def initialize_default_prompts(self):
        """デフォルトプロンプトの初期化"""
        try:
            # 既存のプロンプトが存在するかチェック
            existing = self.get_prompts()
            if existing:
                print("プロンプトが既に存在します")
                return
            
            # デフォルトプロンプトを挿入
            default_prompts = [
                {
                    'prompt_type': 'recipe',
                    'title': 'デフォルトレシピ生成プロンプト',
                    'description': 'カクテルレシピ生成用のベースプロンプト',
                    'prompt_text': 'あなたはプロのバーテンダーです。以下のシロップ情報を参考に、入力された情報からカクテル風の名前（日本語で20文字以内）、そのカクテルのコンセプト文（日本語で1文）、生成AIでカクテルの画像を生成するためのメインカラー（液体の色）を表現する文章とメインカラーのRGB値、およびレシピ（シロップ名と比率のリスト、合計25%以内、色や味のイメージに合うように最大4種まで混ぜてOK）を考えてください。'
                },
                {
                    'prompt_type': 'image',
                    'title': 'デフォルト画像生成プロンプト',
                    'description': 'カクテル画像生成用のベースプロンプト',
                    'prompt_text': '背景は完全な透明（透過PNG）、カクテル以外は描かず、カクテルそのものだけをリアルな質感の写真風イラストとして生成してください。必ず生成画像の液体部分の色が指定されたメインカラーのRGB値の色味に近くなるようにしてください'
                }
            ]
            
            for prompt_data in default_prompts:
                self.insert_prompt(prompt_data)
            
            print("デフォルトプロンプトを初期化しました")
            
        except Exception as e:
            print(f"デフォルトプロンプト初期化エラー: {e}")
    
    # イベント関連のメソッド
    def get_events(self, is_active: bool = None) -> List[Dict[str, Any]]:
        """イベント一覧を取得"""
        try:
            query = self.client.table('events').select('*')
            if is_active is not None:
                query = query.eq('is_active', is_active)
            result = query.order('created_at', desc=True).execute()
            return result.data or []
        except Exception as e:
            print(f"イベント取得エラー: {e}")
            return []
    
    def get_event_by_id(self, event_id: Union[str, uuid.UUID]) -> Optional[Dict[str, Any]]:
        """IDでイベントを取得"""
        try:
            # UUIDの場合は文字列に変換
            event_id_str = str(event_id) if isinstance(event_id, uuid.UUID) else event_id
            result = self.client.table('events').select('*').eq('id', event_id_str).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"イベント取得エラー: {e}")
            return None
    
    def get_event_by_name(self, event_name: str) -> Optional[Dict[str, Any]]:
        """名前でイベントを取得"""
        try:
            result = self.client.table('events').select('*').eq('name', event_name).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"イベント取得エラー: {e}")
            return None
    
    def insert_event(self, data: Dict[str, Any]) -> Optional[str]:
        """イベントを挿入"""
        try:
            result = self.client.table('events').insert(data).execute()
            if result.data:
                return str(result.data[0]['id'])
            return None
        except Exception as e:
            print(f"イベント挿入エラー: {e}")
            return None
    
    def update_event(self, event_id: Union[str, uuid.UUID], data: Dict[str, Any]) -> bool:
        """イベントを更新"""
        try:
            data['updated_at'] = datetime.now().isoformat()
            # UUIDの場合は文字列に変換
            event_id_str = str(event_id) if isinstance(event_id, uuid.UUID) else event_id
            result = self.client.table('events').update(data).eq('id', event_id_str).execute()
            return bool(result.data)
        except Exception as e:
            print(f"イベント更新エラー: {e}")
            return False

# グローバルインスタンス
supabase_client = SupabaseClient()
