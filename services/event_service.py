"""
イベント管理関連のビジネスロジック
"""
from typing import List, Dict, Optional, Any
from datetime import datetime

from models.requests import EventRequest
from db import database as dbmodule


class EventService:
    """イベント管理サービス"""
    
    @staticmethod
    def get_all_events() -> List[Dict[str, Any]]:
        """全イベント取得"""
        try:
            print("[DEBUG] 全イベント取得開始")
            events = dbmodule.get_all_events()
            print(f"[DEBUG] イベント取得完了: {len(events)}件")
            return events
        except Exception as e:
            print(f"[ERROR] イベント取得エラー: {e}")
            return []
    
    @staticmethod
    def get_event_by_id(event_id: str) -> Optional[Dict[str, Any]]:
        """特定イベント取得"""
        try:
            print(f"[DEBUG] イベント取得開始: {event_id}")
            event = dbmodule.get_event_by_id(event_id)
            if event:
                print(f"[DEBUG] イベント取得成功: {event.get('name', 'Unknown')}")
            else:
                print(f"[DEBUG] イベントが見つかりません: {event_id}")
            return event
        except Exception as e:
            print(f"[ERROR] イベント取得エラー: {e}")
            return None
    
    @staticmethod
    def create_event(event_data: EventRequest) -> Optional[str]:
        """新規イベント作成"""
        try:
            print(f"[DEBUG] イベント作成開始: {event_data.name}")
            
            # 重複チェック
            existing_event = dbmodule.get_event_by_name(event_data.name)
            if existing_event:
                print(f"[WARNING] 同名イベントが既に存在: {event_data.name}")
                return None
            
            # イベントデータ準備
            db_data = {
                'name': event_data.name,
                'description': event_data.description,
                'is_active': event_data.is_active
            }
            
            # DB挿入
            event_id = dbmodule.insert_event(db_data)
            if event_id:
                print(f"[DEBUG] イベント作成完了: {event_id}")
                return event_id
            else:
                print("[ERROR] イベント作成失敗")
                return None
                
        except Exception as e:
            print(f"[ERROR] イベント作成エラー: {e}")
            return None
    
    @staticmethod
    def update_event(event_id: str, event_data: EventRequest) -> bool:
        """イベント更新"""
        try:
            print(f"[DEBUG] イベント更新開始: {event_id}")
            
            # 既存イベントの確認
            existing_event = dbmodule.get_event_by_id(event_id)
            if not existing_event:
                print(f"[WARNING] 更新対象イベントが見つかりません: {event_id}")
                return False
            
            # 更新データ準備
            update_data = {
                'name': event_data.name,
                'description': event_data.description,
                'is_active': event_data.is_active,
                'updated_at': datetime.now().isoformat()
            }
            
            # DB更新
            success = dbmodule.update_event(event_id, update_data)
            if success:
                print(f"[DEBUG] イベント更新完了: {event_id}")
                return True
            else:
                print(f"[ERROR] イベント更新失敗: {event_id}")
                return False
                
        except Exception as e:
            print(f"[ERROR] イベント更新エラー: {e}")
            return False
    
    @staticmethod
    def delete_event(event_id: str) -> bool:
        """イベント削除（論理削除）"""
        try:
            print(f"[DEBUG] イベント削除開始: {event_id}")
            
            # 既存イベントの確認
            existing_event = dbmodule.get_event_by_id(event_id)
            if not existing_event:
                print(f"[WARNING] 削除対象イベントが見つかりません: {event_id}")
                return False
            
            # 論理削除（is_activeをFalseに）
            update_data = {
                'is_active': False,
                'updated_at': datetime.now().isoformat()
            }
            
            success = dbmodule.update_event(event_id, update_data)
            if success:
                print(f"[DEBUG] イベント削除完了: {event_id}")
                return True
            else:
                print(f"[ERROR] イベント削除失敗: {event_id}")
                return False
                
        except Exception as e:
            print(f"[ERROR] イベント削除エラー: {e}")
            return False
    
    @staticmethod
    def get_active_events() -> List[Dict[str, Any]]:
        """アクティブなイベントのみ取得"""
        try:
            print("[DEBUG] アクティブイベント取得開始")
            events = dbmodule.get_all_events()
            active_events = [event for event in events if event.get('is_active', False)]
            print(f"[DEBUG] アクティブイベント取得完了: {len(active_events)}件")
            return active_events
        except Exception as e:
            print(f"[ERROR] アクティブイベント取得エラー: {e}")
            return []
    
    @staticmethod
    def get_event_statistics(event_id: str) -> Dict[str, Any]:
        """イベント統計情報取得"""
        try:
            print(f"[DEBUG] イベント統計取得開始: {event_id}")
            
            # 基本情報
            event = dbmodule.get_event_by_id(event_id)
            if not event:
                return {}
            
            # 統計情報を取得（実装は使用するDBモジュールに依存）
            stats = {
                'event_id': event_id,
                'event_name': event.get('name', ''),
                'is_active': event.get('is_active', False),
                'created_at': event.get('created_at', ''),
                'cocktails_count': 0,
                'surveys_count': 0,
                'responses_count': 0
            }
            
            # カクテル数を取得（該当するDBメソッドがある場合）
            try:
                cocktails_count = dbmodule.get_cocktails_count_by_event(event_id)
                stats['cocktails_count'] = cocktails_count
            except AttributeError:
                # メソッドが存在しない場合はスキップ
                pass
            
            # アンケート関連統計
            try:
                surveys = dbmodule.get_surveys_by_event(event_id)
                stats['surveys_count'] = len(surveys) if surveys else 0
                
                # 回答数の集計
                total_responses = 0
                if surveys:
                    for survey in surveys:
                        responses = dbmodule.get_survey_responses(survey['id'])
                        total_responses += len(responses) if responses else 0
                stats['responses_count'] = total_responses
                
            except Exception:
                # エラーの場合はデフォルト値を使用
                pass
            
            print(f"[DEBUG] イベント統計取得完了: {event_id}")
            return stats
            
        except Exception as e:
            print(f"[ERROR] イベント統計取得エラー: {e}")
            return {}