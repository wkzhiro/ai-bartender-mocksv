import os
from typing import Optional, Dict, Any, List
from datetime import datetime
from dotenv import load_dotenv
from .supabase_client import supabase_client

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

def get_all_cocktails(limit: int = None, offset: int = 0) -> Dict[str, Any]:
    """全カクテルを取得（ページネーション対応）"""
    return supabase_client.get_all_cocktails(limit=limit, offset=offset)

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