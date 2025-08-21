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
        """新しいマイグレーションファイルを使用してテーブル作成"""
        print("⚠️  新しいSupabaseプロジェクトでは、マイグレーションファイルを手動実行してください:")
        print("\n📋 実行手順:")
        print("1. Supabaseダッシュボード → SQL Editor")
        print("2. 以下のファイルを順番に実行:")
        print("   - migration/20250130_01_create_base_tables.sql")
        print("   - migration/20250130_02_create_prompt_tables.sql") 
        print("   - migration/20250130_03_create_violation_tables.sql")
        print("   - migration/20250130_04_create_survey_tables.sql")
        print("   - migration/20250130_05_create_indexes.sql")
        print("   - migration/20250130_06_create_triggers.sql")
        print("\n詳細は migration/migration_history.md を参照してください。")
    
    def insert_cocktail(self, data: Dict[str, Any]) -> Optional[str]:
        """カクテルデータを挿入（UUIDプライマリキー使用）"""
        try:
            # idが指定されていない場合、データベース側でgen_random_uuid()が自動生成される
            print(f"[DEBUG] カクテル挿入 - id: {data.get('id', 'auto-generate')}")
            
            result = self.client.table('cocktails').insert(data).execute()
            if result.data:
                return result.data[0]['id']  # ID文字列を返す
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

    def get_cocktail_by_id(self, cocktail_id: str) -> Optional[Dict[str, Any]]:
        """UUIDでカクテルを取得（プライマリキーがUUIDに変更済み）"""
        try:
            result = self.client.table('cocktails').select('*').eq('id', cocktail_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"カクテル取得エラー: {e}")
            return None

    def get_uuid_from_order_id(self, order_id: str) -> Optional[str]:
        """order_idからUUIDを取得"""
        try:
            result = self.client.table('cocktails').select('uuid').eq('order_id', order_id).execute()
            return result.data[0]['uuid'] if result.data else None
        except Exception as e:
            print(f"UUID取得エラー: {e}")
            return None

    def get_order_id_from_uuid(self, uuid_id: str) -> Optional[str]:
        """UUIDからorder_idを取得"""
        try:
            result = self.client.table('cocktails').select('order_id').eq('id', uuid_id).execute()
            return result.data[0]['order_id'] if result.data else None
        except Exception as e:
            print(f"order_id取得エラー: {e}")
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
            # 方法1: 最も軽量なカウントクエリ（UUIDのみ、制限なし）
            query = self.client.table('cocktails').select('uuid', count='exact').eq('is_visible', True).limit(1)
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
                chunk_result = self.client.table('cocktails').select('uuid').eq('is_visible', True).limit(limit_chunk).offset(offset_chunk).execute()
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
            # UUIDのみを取得してカウント（軽量なクエリ）
            count_result = self.client.table('cocktails').select('uuid', count='exact').limit(1).execute()
            return count_result.count or 0
        except Exception as e:
            print(f"件数取得エラー: {e}")
            # エラー時は概算値として、現在取得できている最大ID+オフセットを返す
            try:
                # 最新の1件だけ取得してIDベースで概算
                latest = self.client.table('cocktails').select('uuid').order('created_at', desc=True).limit(1).execute()
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
            result = self.client.table(table_name).select('*').limit(1).execute()
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
    
    def link_cocktail_prompt(self, cocktail_uuid: str, prompt_id: int, prompt_type: str) -> bool:
        """カクテルとプロンプトを関連付け（UUID使用）"""
        try:
            # 既存のレコードを削除してから新しいレコードを挿入（UPSERT的な動作）
            self.client.table('cocktail_prompts').delete().eq('cocktail_id', cocktail_uuid).eq('prompt_type', prompt_type).execute()
            
            data = {
                'cocktail_id': cocktail_uuid,  # UUIDを使用
                'prompt_id': prompt_id,
                'prompt_type': prompt_type
            }
            result = self.client.table('cocktail_prompts').insert(data).execute()
            return bool(result.data)
        except Exception as e:
            print(f"カクテル-プロンプト関連付けエラー: {e}")
            return False
    
    def get_cocktail_prompts(self, cocktail_uuid: str) -> List[Dict[str, Any]]:
        """カクテルに関連付けられたプロンプトを取得（UUID使用）"""
        try:
            result = self.client.table('cocktail_prompts').select(
                'prompt_id, prompt_type, prompts(id, prompt_type, title, description, prompt_text)'
            ).eq('cocktail_id', cocktail_uuid).execute()
            return result.data or []
        except Exception as e:
            print(f"カクテル-プロンプト取得エラー: {e}")
            return []
    
    def get_cocktail_prompt_by_type(self, cocktail_uuid: str, prompt_type: str) -> Optional[Dict[str, Any]]:
        """カクテルの特定タイプのプロンプトを取得（UUID使用）"""
        try:
            result = self.client.table('cocktail_prompts').select(
                'prompt_id, prompt_type, prompts(id, prompt_type, title, description, prompt_text)'
            ).eq('cocktail_id', cocktail_uuid).eq('prompt_type', prompt_type).execute()
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
                    'name': 'デフォルトレシピ生成プロンプト',
                    'description': 'カクテルレシピ生成用のベースプロンプト',
                    'prompt_text': 'あなたはプロのバーテンダーです。以下のシロップ情報を参考に、入力された情報からカクテル風の名前（日本語で20文字以内）、そのカクテルのコンセプト文（日本語で1文）、生成AIでカクテルの画像を生成するためのメインカラー（液体の色）を表現する文章とメインカラーのRGB値、およびレシピ（シロップ名と比率のリスト、合計25%以内、色や味のイメージに合うように最大4種まで混ぜてOK）を考えてください。',
                    'is_active': True
                },
                {
                    'prompt_type': 'image',
                    'name': 'デフォルト画像生成プロンプト',
                    'description': 'カクテル画像生成用のベースプロンプト',
                    'prompt_text': '背景は完全な透明（透過PNG）、カクテル以外は描かず、カクテルそのものだけをリアルな質感の写真風イラストとして生成してください。必ず生成画像の液体部分の色が指定されたメインカラーのRGB値の色味に近くなるようにしてください',
                    'is_active': True
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
            print(f"[SUPABASE] イベント取得クエリ実行: event_id='{event_id_str}'")
            print(f"[SUPABASE] 元のevent_id: '{event_id}', 型: {type(event_id)}")
            
            result = self.client.table('events').select('*').eq('id', event_id_str).execute()
            
            print(f"[SUPABASE] クエリ結果: データ数={len(result.data) if result.data else 0}")
            if result.data:
                print(f"[SUPABASE] 取得したイベント: {result.data[0]}")
                return result.data[0]
            else:
                print(f"[SUPABASE] イベントが見つかりません: '{event_id_str}'")
                
                # デバッグのために少数のイベントIDを確認
                try:
                    sample_result = self.client.table('events').select('id, name').limit(5).execute()
                    if sample_result.data:
                        print(f"[SUPABASE] サンプルイベント: {sample_result.data}")
                    else:
                        print(f"[SUPABASE] eventsテーブルにデータがありません")
                except Exception as debug_e:
                    print(f"[SUPABASE] サンプル取得エラー: {debug_e}")
                
                return None
                
        except Exception as e:
            print(f"[SUPABASE] イベント取得エラー: {e}")
            print(f"[SUPABASE] エラー詳細: {type(e).__name__}: {str(e)}")
            import traceback
            print(f"[SUPABASE] スタックトレース: {traceback.format_exc()}")
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
    
    # アンケート関連メソッド
    def create_survey(self, data: Dict[str, Any]) -> Optional[str]:
        """アンケートを作成"""
        try:
            result = self.client.table('surveys').insert(data).execute()
            if result.data:
                return str(result.data[0]['id'])
            return None
        except Exception as e:
            print(f"アンケート作成エラー: {e}")
            return None
    
    def create_survey_with_questions(self, survey_data: Dict[str, Any], questions: List[Dict[str, Any]]) -> Optional[str]:
        """アンケートを質問と選択肢とともに一括作成"""
        try:
            # アンケート作成
            survey_result = self.client.table('surveys').insert(survey_data).execute()
            if not survey_result.data:
                return None
            
            survey_id = str(survey_result.data[0]['id'])
            
            # 質問と選択肢を作成
            for question_data in questions:
                question_insert_data = {
                    'survey_id': survey_id,
                    'question_type': question_data['question_type'],
                    'question_text': question_data['question_text'],
                    'is_required': question_data.get('is_required', False),
                    'display_order': question_data['display_order']
                }
                
                question_result = self.client.table('survey_questions').insert(question_insert_data).execute()
                if not question_result.data:
                    continue
                
                question_id = str(question_result.data[0]['id'])
                
                # 選択肢がある場合は作成
                if question_data.get('options'):
                    options_data = []
                    for i, option in enumerate(question_data['options']):
                        options_data.append({
                            'question_id': question_id,
                            'option_text': option['option_text'],
                            'display_order': option.get('display_order', i + 1)
                        })
                    
                    if options_data:
                        self.client.table('survey_question_options').insert(options_data).execute()
            
            return survey_id
            
        except Exception as e:
            print(f"アンケート一括作成エラー: {e}")
            return None
    
    def get_surveys_by_event(self, event_id: str, is_active: bool = None) -> List[Dict[str, Any]]:
        """イベントのアンケート一覧を取得"""
        try:
            query = self.client.table('surveys').select('*').eq('event_id', event_id)
            if is_active is not None:
                query = query.eq('is_active', is_active)
            result = query.order('created_at', desc=True).execute()
            return result.data or []
        except Exception as e:
            print(f"アンケート一覧取得エラー: {e}")
            return []
    
    def get_survey_with_questions(self, survey_id: str) -> Optional[Dict[str, Any]]:
        """アンケート詳細を質問と選択肢とともに取得"""
        try:
            # アンケート基本情報取得
            survey_result = self.client.table('surveys').select('*').eq('id', survey_id).execute()
            if not survey_result.data:
                return None
            
            survey = survey_result.data[0]
            
            # 質問一覧取得
            questions_result = self.client.table('survey_questions').select('*').eq('survey_id', survey_id).order('display_order').execute()
            questions = questions_result.data or []
            
            # 各質問の選択肢を取得
            for question in questions:
                options_result = self.client.table('survey_question_options').select('*').eq('question_id', question['id']).order('display_order').execute()
                question['options'] = options_result.data or []
            
            survey['questions'] = questions
            return survey
            
        except Exception as e:
            print(f"アンケート詳細取得エラー: {e}")
            return None
    
    def update_survey(self, survey_id: str, data: Dict[str, Any]) -> bool:
        """アンケートを更新"""
        try:
            data['updated_at'] = datetime.now().isoformat()
            result = self.client.table('surveys').update(data).eq('id', survey_id).execute()
            return bool(result.data)
        except Exception as e:
            print(f"アンケート更新エラー: {e}")
            return False
    
    def delete_survey(self, survey_id: str) -> bool:
        """アンケートを削除"""
        try:
            result = self.client.table('surveys').delete().eq('id', survey_id).execute()
            return bool(result.data)
        except Exception as e:
            print(f"アンケート削除エラー: {e}")
            return False
    
    def delete_survey_questions(self, survey_id: str) -> bool:
        """アンケートの質問項目をすべて削除"""
        try:
            # まず既存の質問項目を取得
            questions_result = self.client.table('survey_questions').select('id').eq('survey_id', survey_id).execute()
            
            for question in questions_result.data:
                # 各質問の選択肢を削除
                self.client.table('survey_question_options').delete().eq('question_id', question['id']).execute()
                # 各質問の回答を削除
                self.client.table('survey_answers').delete().eq('question_id', question['id']).execute()
            
            # 質問項目を削除
            self.client.table('survey_questions').delete().eq('survey_id', survey_id).execute()
            
            print(f"アンケート{survey_id}の質問項目削除完了")
            return True
        except Exception as e:
            print(f"質問項目削除エラー: {e}")
            return False
    
    def create_survey_question(self, question_data: dict) -> Optional[str]:
        """アンケート質問項目を作成"""
        try:
            import uuid
            
            # 質問項目データの準備
            question_insert_data = {
                'id': str(uuid.uuid4()),
                'survey_id': question_data['survey_id'],
                'question_type': question_data['question_type'],
                'question_text': question_data['question_text'],
                'is_required': question_data.get('is_required', False),
                'display_order': question_data.get('display_order', 1)
            }
            
            # 質問項目を挿入
            question_result = self.client.table('survey_questions').insert(question_insert_data).execute()
            
            if not question_result.data:
                return None
            
            question_id = question_result.data[0]['id']
            print(f"質問項目作成成功: {question_id}")
            
            # 選択肢がある場合は追加
            options = question_data.get('options', [])
            print(f"デバッグ: 選択肢データ = {options}")
            print(f"デバッグ: 選択肢の型 = {type(options)}")
            
            if options and question_data['question_type'] in ['single_choice', 'multiple_choice']:
                print(f"デバッグ: 選択肢作成開始 - {len(options)}個の選択肢")
                for i, option in enumerate(options):
                    print(f"デバッグ: 選択肢{i+1} = {option}, 型 = {type(option)}")
                    
                    # オプション属性の安全な取得
                    if hasattr(option, 'option_text'):
                        option_text = option.option_text
                    elif isinstance(option, dict):
                        option_text = option.get('option_text', '')
                    else:
                        option_text = ''
                    
                    if hasattr(option, 'display_order'):
                        display_order = option.display_order
                    elif isinstance(option, dict):
                        display_order = option.get('display_order', i + 1)
                    else:
                        display_order = i + 1
                    
                    option_data = {
                        'id': str(uuid.uuid4()),
                        'question_id': question_id,
                        'option_text': option_text,
                        'display_order': display_order
                    }
                    
                    print(f"デバッグ: 挿入する選択肢データ = {option_data}")
                    
                    try:
                        option_result = self.client.table('survey_question_options').insert(option_data).execute()
                        print(f"デバッグ: 選択肢挿入結果 = {option_result}")
                        
                        if option_result.data:
                            print(f"選択肢作成成功: {option_data['option_text']}")
                        else:
                            print(f"選択肢作成失敗: {option_data['option_text']}")
                    except Exception as option_error:
                        print(f"選択肢作成エラー: {option_error}")
                        import traceback
                        traceback.print_exc()
            else:
                print(f"デバッグ: 選択肢作成をスキップ - options={bool(options)}, type={question_data['question_type']}")
            
            return question_id
            
        except Exception as e:
            print(f"質問項目作成エラー: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def submit_survey_response(self, survey_id: str, cocktail_uuid: Optional[str], answers: List[Dict[str, Any]]) -> Optional[str]:
        """アンケート回答を送信（UUID使用）"""
        try:
            # 回答レコード作成
            response_data = {
                'survey_id': survey_id,
                'cocktail_id': cocktail_uuid  # UUIDを使用
            }
            response_result = self.client.table('survey_responses').insert(response_data).execute()
            if not response_result.data:
                return None
            
            response_id = str(response_result.data[0]['id'])
            
            # 個別回答を保存
            answers_data = []
            for answer in answers:
                answer_data = {
                    'response_id': response_id,
                    'question_id': answer['question_id'],
                    'answer_text': answer.get('answer_text'),
                    'selected_option_ids': answer.get('selected_option_ids', [])
                }
                answers_data.append(answer_data)
            
            if answers_data:
                self.client.table('survey_answers').insert(answers_data).execute()
            
            return response_id
            
        except Exception as e:
            print(f"アンケート回答送信エラー: {e}")
            return None
    
    def get_survey_responses(self, survey_id: str, limit: int = None, offset: int = 0) -> Dict[str, Any]:
        """アンケート回答一覧を取得"""
        try:
            query = self.client.table('survey_responses').select(
                '*, survey_answers(*, survey_questions(question_text, question_type), survey_question_options(option_text))'
            ).eq('survey_id', survey_id).order('submitted_at', desc=True)
            
            if limit:
                query = query.limit(limit)
            if offset > 0:
                query = query.offset(offset)
            
            result = query.execute()
            
            # 総数取得
            count_result = self.client.table('survey_responses').select('id', count='exact').eq('survey_id', survey_id).execute()
            total_count = count_result.count or 0
            
            return {
                'data': result.data or [],
                'total_count': total_count,
                'limit': limit,
                'offset': offset
            }
            
        except Exception as e:
            print(f"アンケート回答一覧取得エラー: {e}")
            return {
                'data': [],
                'total_count': 0,
                'limit': limit,
                'offset': offset
            }
    
    def get_survey_statistics(self, survey_id: str) -> Dict[str, Any]:
        """アンケート集計結果を取得"""
        try:
            # 回答総数
            total_responses_result = self.client.table('survey_responses').select('id', count='exact').eq('survey_id', survey_id).execute()
            total_responses = total_responses_result.count or 0
            
            # 質問一覧取得
            questions_result = self.client.table('survey_questions').select('*').eq('survey_id', survey_id).order('display_order').execute()
            questions = questions_result.data or []
            
            statistics = {
                'survey_id': survey_id,
                'total_responses': total_responses,
                'questions': []
            }
            
            for question in questions:
                question_stat = {
                    'question_id': question['id'],
                    'question_text': question['question_text'],
                    'question_type': question['question_type'],
                    'responses': []
                }
                
                if question['question_type'] == 'text':
                    # テキスト回答の取得
                    text_answers_result = self.client.table('survey_answers').select('answer_text').eq('question_id', question['id']).execute()
                    question_stat['responses'] = [answer['answer_text'] for answer in (text_answers_result.data or []) if answer.get('answer_text')]
                    
                else:
                    # 選択式の場合の集計
                    options_result = self.client.table('survey_question_options').select('*').eq('question_id', question['id']).order('display_order').execute()
                    options = options_result.data or []
                    
                    option_counts = {}
                    for option in options:
                        option_counts[option['id']] = {
                            'option_text': option['option_text'],
                            'count': 0
                        }
                    
                    # 選択回答の集計
                    choice_answers_result = self.client.table('survey_answers').select('selected_option_ids').eq('question_id', question['id']).execute()
                    for answer in (choice_answers_result.data or []):
                        if answer.get('selected_option_ids'):
                            for option_id in answer['selected_option_ids']:
                                if option_id in option_counts:
                                    option_counts[option_id]['count'] += 1
                    
                    question_stat['option_statistics'] = option_counts
                
                statistics['questions'].append(question_stat)
            
            return statistics
            
        except Exception as e:
            print(f"アンケート集計エラー: {e}")
            return {
                'survey_id': survey_id,
                'total_responses': 0,
                'questions': []
            }

# グローバルインスタンス
supabase_client = SupabaseClient()
