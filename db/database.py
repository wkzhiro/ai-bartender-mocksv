import os
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from dotenv import load_dotenv
from .supabase_client import supabase_client
import uuid

load_dotenv(override=True)

def create_tables():
    """テーブル作成"""
    try:
        supabase_client.create_tables()
        print("Supabaseテーブルの作成が完了しました。")
    except Exception as e:
        print(f"テーブル作成中にエラーが発生しました: {e}")
        raise

def insert_cocktail(data: dict) -> Optional[int]:
    """カクテルデータを挿入"""
    return supabase_client.insert_cocktail(data)

def get_cocktail_by_order_id(order_id: str) -> Optional[Dict[str, Any]]:
    """注文IDでカクテルを取得"""
    return supabase_client.get_cocktail_by_order_id(order_id)

def get_all_cocktails(limit: int = None, offset: int = 0, event_id: Union[str, uuid.UUID] = None) -> Dict[str, Any]:
    """全カクテルを取得（ページネーション対応）、event_idでフィルター可能"""
    return supabase_client.get_all_cocktails(limit=limit, offset=offset, event_id=event_id)

def insert_poured_cocktail(data: dict) -> Optional[int]:
    """注がれたカクテルデータを挿入"""
    return supabase_client.insert_poured_cocktail(data)

def table_exists(table_name: str) -> bool:
    """指定したテーブルが存在するか確認する"""
    return supabase_client.table_exists(table_name)

# 既存のコードとの互換性のために追加
class MockCocktail:
    """MySQLのCocktailモデルと互換性を保つためのモック"""
    def __init__(self, data: dict):
        for key, value in data.items():
            setattr(self, key, value)

def get_cocktail_mock(order_id: str) -> Optional[MockCocktail]:
    """MySQLのクエリ結果と同じ形式で返す"""
    data = get_cocktail_by_order_id(order_id)
    if data:
        return MockCocktail(data)
    return None

# プロンプト関連の関数
def get_prompts(prompt_type: str = None, is_active: bool = True):
    """プロンプトを取得"""
    return supabase_client.get_prompts(prompt_type=prompt_type, is_active=is_active)

def get_prompt_by_id(prompt_id: int):
    """IDでプロンプトを取得"""
    return supabase_client.get_prompt_by_id(prompt_id)

def insert_prompt(data: dict):
    """プロンプトを挿入"""
    return supabase_client.insert_prompt(data)

def update_prompt(prompt_id: int, data: dict):
    """プロンプトを更新"""
    return supabase_client.update_prompt(prompt_id, data)

def link_cocktail_prompt(cocktail_id: int, prompt_id: int, prompt_type: str):
    """カクテルとプロンプトを関連付け"""
    return supabase_client.link_cocktail_prompt(cocktail_id, prompt_id, prompt_type)

def get_cocktail_prompts(cocktail_id: int):
    """カクテルに関連付けられたプロンプトを取得"""
    return supabase_client.get_cocktail_prompts(cocktail_id)

def get_cocktail_prompt_by_type(cocktail_id: int, prompt_type: str):
    """カクテルの特定タイプのプロンプトを取得"""
    return supabase_client.get_cocktail_prompt_by_type(cocktail_id, prompt_type)

def initialize_default_prompts():
    """デフォルトプロンプトの初期化"""
    return supabase_client.initialize_default_prompts()

# イベント関連の関数
def get_events(is_active: bool = None):
    """イベント一覧を取得"""
    return supabase_client.get_events(is_active=is_active)

def get_event_by_id(event_id: Union[str, uuid.UUID]):
    """IDでイベントを取得"""
    return supabase_client.get_event_by_id(event_id)

def get_event_by_name(event_name: str):
    """名前でイベントを取得"""
    return supabase_client.get_event_by_name(event_name)

def insert_event(data: dict):
    """イベントを挿入"""
    return supabase_client.insert_event(data)

def update_event(event_id: Union[str, uuid.UUID], data: dict):
    """イベントを更新"""
    return supabase_client.update_event(event_id, data)