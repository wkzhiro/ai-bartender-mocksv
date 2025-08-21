"""
プロンプト管理関連のビジネスロジック
"""
from typing import List, Dict, Optional, Any
from datetime import datetime

from models.requests import PromptRequest
from db import database as dbmodule


class PromptService:
    """プロンプト管理サービス"""
    
    @staticmethod
    def get_prompts(
        prompt_type: Optional[str] = None, 
        is_active: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """プロンプト一覧取得"""
        try:
            print(f"[DEBUG] プロンプト取得開始 - type: {prompt_type}, active: {is_active}")
            prompts = dbmodule.get_prompts(prompt_type, is_active)
            print(f"[DEBUG] プロンプト取得完了: {len(prompts)}件")
            return prompts
        except Exception as e:
            print(f"[ERROR] プロンプト取得エラー: {e}")
            return []
    
    @staticmethod
    def get_prompt_by_id(prompt_id: str) -> Optional[Dict[str, Any]]:
        """特定プロンプト取得"""
        try:
            print(f"[DEBUG] プロンプト詳細取得開始: {prompt_id}")
            prompt = dbmodule.get_prompt_by_id(prompt_id)
            if prompt:
                print(f"[DEBUG] プロンプト取得成功: {prompt.get('name', 'Unknown')}")
            else:
                print(f"[DEBUG] プロンプトが見つかりません: {prompt_id}")
            return prompt
        except Exception as e:
            print(f"[ERROR] プロンプト取得エラー: {e}")
            return None
    
    @staticmethod
    def create_prompt(prompt_data: PromptRequest) -> Optional[str]:
        """新規プロンプト作成"""
        try:
            print(f"[DEBUG] プロンプト作成開始: {prompt_data.name}")
            
            # 重複チェック
            existing_prompts = dbmodule.get_prompts(prompt_data.prompt_type)
            for existing in existing_prompts:
                if existing.get('name') == prompt_data.name:
                    print(f"[WARNING] 同名プロンプトが既に存在: {prompt_data.name}")
                    return None
            
            # プロンプトデータ準備
            db_data = {
                'name': prompt_data.name,
                'prompt_text': prompt_data.prompt_text,
                'prompt_type': prompt_data.prompt_type,
                'is_active': prompt_data.is_active,
                'description': prompt_data.description
            }
            
            # DB挿入
            prompt_id = dbmodule.create_prompt(db_data)
            if prompt_id:
                print(f"[DEBUG] プロンプト作成完了: {prompt_id}")
                return prompt_id
            else:
                print("[ERROR] プロンプト作成失敗")
                return None
                
        except Exception as e:
            print(f"[ERROR] プロンプト作成エラー: {e}")
            return None
    
    @staticmethod
    def update_prompt(prompt_id: str, prompt_data: PromptRequest) -> bool:
        """プロンプト更新"""
        try:
            print(f"[DEBUG] プロンプト更新開始: {prompt_id}")
            
            # 既存プロンプト確認
            existing_prompt = dbmodule.get_prompt_by_id(prompt_id)
            if not existing_prompt:
                print(f"[WARNING] 更新対象プロンプトが見つかりません: {prompt_id}")
                return False
            
            # 更新データ準備
            update_data = {
                'name': prompt_data.name,
                'prompt_text': prompt_data.prompt_text,
                'prompt_type': prompt_data.prompt_type,
                'is_active': prompt_data.is_active,
                'description': prompt_data.description,
                'updated_at': datetime.now().isoformat()
            }
            
            # DB更新
            success = dbmodule.update_prompt(prompt_id, update_data)
            if success:
                print(f"[DEBUG] プロンプト更新完了: {prompt_id}")
                return True
            else:
                print(f"[ERROR] プロンプト更新失敗: {prompt_id}")
                return False
                
        except Exception as e:
            print(f"[ERROR] プロンプト更新エラー: {e}")
            return False
    
    @staticmethod
    def delete_prompt(prompt_id: str) -> bool:
        """プロンプト削除（論理削除）"""
        try:
            print(f"[DEBUG] プロンプト削除開始: {prompt_id}")
            
            # 既存プロンプト確認
            existing_prompt = dbmodule.get_prompt_by_id(prompt_id)
            if not existing_prompt:
                print(f"[WARNING] 削除対象プロンプトが見つかりません: {prompt_id}")
                return False
            
            # 論理削除（is_activeをFalseに）
            update_data = {
                'is_active': False,
                'updated_at': datetime.now().isoformat()
            }
            
            success = dbmodule.update_prompt(prompt_id, update_data)
            if success:
                print(f"[DEBUG] プロンプト削除完了: {prompt_id}")
                return True
            else:
                print(f"[ERROR] プロンプト削除失敗: {prompt_id}")
                return False
                
        except Exception as e:
            print(f"[ERROR] プロンプト削除エラー: {e}")
            return False
    
    @staticmethod
    def initialize_default_prompts() -> bool:
        """デフォルトプロンプトの初期化"""
        try:
            print("[DEBUG] デフォルトプロンプト初期化開始")
            
            # レシピ用デフォルトプロンプト
            recipe_prompts = [
                {
                    'name': 'デフォルトレシピプロンプト',
                    'prompt_text': 'お客様の情報を基に、心に響く特別なカクテルレシピを創造してください。',
                    'prompt_type': 'recipe',
                    'is_active': True,
                    'description': 'カクテルレシピ生成用のデフォルトプロンプト'
                }
            ]
            
            # 画像用デフォルトプロンプト
            image_prompts = [
                {
                    'name': 'デフォルト画像プロンプト',
                    'prompt_text': 'リアルな質感の写真風イラストとして生成してください。背景は透明で、カクテルのみを描写してください。',
                    'prompt_type': 'image',
                    'is_active': True,
                    'description': 'カクテル画像生成用のデフォルトプロンプト'
                }
            ]
            
            default_prompts = recipe_prompts + image_prompts
            created_count = 0
            
            for prompt_data in default_prompts:
                # 既存チェック
                existing_prompts = dbmodule.get_prompts(prompt_data['prompt_type'])
                name_exists = any(p.get('name') == prompt_data['name'] for p in existing_prompts)
                
                if not name_exists:
                    prompt_id = dbmodule.create_prompt(prompt_data)
                    if prompt_id:
                        created_count += 1
                        print(f"[DEBUG] デフォルトプロンプト作成: {prompt_data['name']}")
                    else:
                        print(f"[ERROR] デフォルトプロンプト作成失敗: {prompt_data['name']}")
                else:
                    print(f"[INFO] デフォルトプロンプト既存: {prompt_data['name']}")
            
            print(f"[DEBUG] デフォルトプロンプト初期化完了: {created_count}件作成")
            return True
            
        except Exception as e:
            print(f"[ERROR] デフォルトプロンプト初期化エラー: {e}")
            return False
    
    @staticmethod
    def get_prompt_usage_statistics(prompt_id: str) -> Dict[str, Any]:
        """プロンプト使用統計取得"""
        try:
            print(f"[DEBUG] プロンプト使用統計取得開始: {prompt_id}")
            
            # プロンプト基本情報
            prompt = dbmodule.get_prompt_by_id(prompt_id)
            if not prompt:
                return {}
            
            # 使用統計を取得（実装は使用するDBモジュールに依存）
            stats = {
                'prompt_id': prompt_id,
                'prompt_name': prompt.get('name', ''),
                'prompt_type': prompt.get('prompt_type', ''),
                'is_active': prompt.get('is_active', False),
                'created_at': prompt.get('created_at', ''),
                'usage_count': 0,
                'last_used_at': None
            }
            
            # カクテル生成での使用回数を取得
            try:
                if prompt.get('prompt_type') == 'recipe':
                    usage_count = dbmodule.get_recipe_prompt_usage_count(prompt_id)
                elif prompt.get('prompt_type') == 'image':
                    usage_count = dbmodule.get_image_prompt_usage_count(prompt_id)
                else:
                    usage_count = 0
                    
                stats['usage_count'] = usage_count
            except AttributeError:
                # メソッドが存在しない場合はスキップ
                pass
            
            print(f"[DEBUG] プロンプト使用統計取得完了: {prompt_id}")
            return stats
            
        except Exception as e:
            print(f"[ERROR] プロンプト使用統計取得エラー: {e}")
            return {}
    
    @staticmethod
    def get_all_prompt_statistics() -> Dict[str, Any]:
        """全プロンプトの統計情報取得"""
        try:
            print("[DEBUG] 全プロンプト統計取得開始")
            
            # 全プロンプト取得
            all_prompts = dbmodule.get_prompts()
            
            # タイプ別集計
            type_counts = {
                'recipe': 0,
                'image': 0
            }
            
            active_counts = {
                'active': 0,
                'inactive': 0
            }
            
            for prompt in all_prompts:
                # タイプ別カウント
                prompt_type = prompt.get('prompt_type', 'unknown')
                if prompt_type in type_counts:
                    type_counts[prompt_type] += 1
                
                # アクティブ状態別カウント
                is_active = prompt.get('is_active', False)
                if is_active:
                    active_counts['active'] += 1
                else:
                    active_counts['inactive'] += 1
            
            stats = {
                'total_prompts': len(all_prompts),
                'type_breakdown': type_counts,
                'active_breakdown': active_counts,
                'generated_at': datetime.now().isoformat()
            }
            
            print("[DEBUG] 全プロンプト統計取得完了")
            return stats
            
        except Exception as e:
            print(f"[ERROR] 全プロンプト統計取得エラー: {e}")
            return {}