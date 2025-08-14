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

# 違反報告関連の関数

def report_violation(cocktail_id: int, reporter_ip: str, report_reason: str, report_category: str = 'inappropriate'):
    """カクテルに対する違反報告を追加（IPアドレスベース）"""
    try:
        # 既に同じIPアドレスから報告済みかチェック
        existing = supabase_client.client.table('violation_reports').select('id').eq('cocktail_id', cocktail_id).eq('reporter_id', reporter_ip).execute()
        if existing.data:
            return False  # 既に報告済み
        
        # 違反報告を追加
        result = supabase_client.client.table('violation_reports').insert({
            'cocktail_id': cocktail_id,
            'reporter_id': reporter_ip,
            'report_reason': report_reason,
            'report_category': report_category
        }).execute()
        
        if result.data:
            # カクテルの違反報告数を更新し、自動非表示処理を実行
            count = update_violation_count(cocktail_id)
            
            # 違反報告があった場合は即座に非表示にする
            if count >= 1:
                hide_cocktail(cocktail_id, f"違反報告により非表示（報告数: {count}）")
            
            return True
        return False
    except Exception as e:
        print(f"違反報告エラー: {e}")
        return False

def update_violation_count(cocktail_id: int):
    """カクテルの違反報告数を更新"""
    try:
        # 違反報告数をカウント
        count_result = supabase_client.client.table('violation_reports').select('id', count='exact').eq('cocktail_id', cocktail_id).execute()
        count = count_result.count or 0
        
        # カクテルテーブルの違反報告数を更新
        supabase_client.client.table('cocktails').update({'violation_reports_count': count}).eq('id', cocktail_id).execute()
        
        return count
    except Exception as e:
        print(f"違反報告数更新エラー: {e}")
        return 0

def hide_cocktail(cocktail_id: int, reason: str = '違反報告により非表示'):
    """カクテルを非表示にする"""
    try:
        from datetime import datetime
        result = supabase_client.client.table('cocktails').update({
            'is_visible': False,
            'hidden_at': datetime.now().isoformat(),
            'hidden_reason': reason
        }).eq('id', cocktail_id).execute()
        
        return len(result.data) > 0
    except Exception as e:
        print(f"カクテル非表示エラー: {e}")
        return False

def show_cocktail(cocktail_id: int):
    """カクテルを再表示する"""
    try:
        result = supabase_client.client.table('cocktails').update({
            'is_visible': True,
            'hidden_at': None,
            'hidden_reason': None
        }).eq('id', cocktail_id).execute()
        
        return len(result.data) > 0
    except Exception as e:
        print(f"カクテル再表示エラー: {e}")
        return False

def get_violation_reports(cocktail_id: int = None, status_filter: str = None, show_all: bool = False):
    """違反報告一覧を取得（カクテル情報を含む）"""
    try:
        print(f"違反報告取得開始 - cocktail_id: {cocktail_id}, status_filter: {status_filter}, show_all: {show_all}")
        
        # まず全レコード数を確認
        all_count = supabase_client.client.table('violation_reports').select('id', count='exact').execute()
        print(f"violation_reports テーブル全体のレコード数: {all_count.count}")
        
        # 非表示カクテルの数も確認
        try:
            hidden_count = supabase_client.client.table('cocktails').select('id', count='exact').eq('is_visible', False).execute()
            print(f"非表示カクテル数: {hidden_count.count}")
        except Exception as e:
            print(f"非表示カクテル数取得エラー: {e}")
        
        # カクテル情報も含めて取得
        query = supabase_client.client.table('violation_reports').select('''
            *,
            cocktails (
                id,
                name,
                comment,
                image,
                flavor_ratio1,
                flavor_ratio2,
                flavor_ratio3,
                flavor_ratio4,
                user_name,
                is_visible
            )
        ''')
        
        if cocktail_id:
            query = query.eq('cocktail_id', cocktail_id)
        
        # ステータスフィルター処理
        if show_all:
            print("すべてのステータスを表示")
            # ステータスフィルターなし
        elif status_filter:
            print(f"特定ステータスフィルター適用: {status_filter}")
            query = query.eq('status', status_filter)
        else:
            print("デフォルトフィルター適用: pending, reviewing")
            query = query.in_('status', ['pending', 'reviewing'])
        
        result = query.order('created_at', desc=True).execute()
        print(f"クエリ結果: {len(result.data) if result.data else 0}件")
        if result.data:
            for report in result.data[:3]:  # 最初の3件だけログ出力
                print(f"  報告ID: {report.get('id')}, ステータス: {report.get('status', 'None')}")
        
        # ステータス別の件数も確認
        try:
            status_counts = supabase_client.client.table('violation_reports').select('status').execute()
            statuses = [r.get('status') for r in status_counts.data] if status_counts.data else []
            print(f"実際のステータス値: {set(statuses)}")
        except Exception as e:
            print(f"ステータス確認エラー: {e}")
        
        # データを整形
        formatted_reports = []
        for report in result.data:
            cocktail = report.get('cocktails', {})
            
            # レシピを構築
            recipe = []
            if cocktail.get('flavor_ratio1', '0%') != '0%':
                recipe.append({'syrup': 'ベリー', 'ratio': cocktail.get('flavor_ratio1', '0%')})
            if cocktail.get('flavor_ratio2', '0%') != '0%':
                recipe.append({'syrup': '青りんご', 'ratio': cocktail.get('flavor_ratio2', '0%')})
            if cocktail.get('flavor_ratio3', '0%') != '0%':
                recipe.append({'syrup': 'シトラス', 'ratio': cocktail.get('flavor_ratio3', '0%')})
            if cocktail.get('flavor_ratio4', '0%') != '0%':
                recipe.append({'syrup': 'ホワイト', 'ratio': cocktail.get('flavor_ratio4', '0%')})
            
            # 画像URLの処理（base64またはURLを判定）
            image_data = cocktail.get('image', '')
            if image_data.startswith('data:image') or image_data.startswith('http'):
                image_url = image_data
            else:
                # base64の場合はdata URLに変換
                image_url = f"data:image/png;base64,{image_data}" if image_data else ''
            
            formatted_report = {
                'id': report['id'],
                'cocktail_id': report['cocktail_id'],
                'cocktail_name': cocktail.get('name', ''),
                'cocktail_creator': cocktail.get('user_name', ''),
                'cocktail_concept': cocktail.get('comment', ''),
                'cocktail_image': image_url,
                'cocktail_recipe': recipe,
                'report_category': report['report_category'],
                'report_reason': report['report_reason'],
                'status': report.get('status', 'pending'),
                'created_at': report['created_at'],
                'updated_at': report.get('updated_at', report['created_at'])
            }
            formatted_reports.append(formatted_report)
        
        return formatted_reports
    except Exception as e:
        print(f"違反報告取得エラー: {e}")
        return []

def update_violation_report_status(report_id: int, status: str):
    """違反報告のステータスを更新"""
    try:
        valid_statuses = ['pending', 'reviewing', 'resolved', 'rejected']
        if status not in valid_statuses:
            raise ValueError(f"無効なステータス: {status}")
        
        # まず報告を取得してカクテルIDを確認
        report_result = supabase_client.client.table('violation_reports').select('cocktail_id').eq('id', report_id).execute()
        if not report_result.data:
            raise ValueError(f"違反報告が見つかりません: {report_id}")
        
        cocktail_id = report_result.data[0]['cocktail_id']
        
        from datetime import datetime
        result = supabase_client.client.table('violation_reports').update({
            'status': status,
            'updated_at': datetime.now().isoformat()
        }).eq('id', report_id).execute()
        
        # ステータスがrejectedまたはresolvedの場合、カクテルを再表示する
        # rejected: 違反ではないと判断された場合
        # resolved: 対応済み（問題が解決され、カクテルは表示されるべき）
        if status in ['rejected', 'resolved'] and result.data:
            print(f"違反報告が{status}になりました。カクテルID {cocktail_id} を再表示します。")
            show_cocktail_result = supabase_client.client.table('cocktails').update({
                'is_visible': True
            }).eq('id', cocktail_id).execute()
            print(f"カクテル再表示結果: {bool(show_cocktail_result.data)}")
        
        return bool(result.data)
    except Exception as e:
        print(f"違反報告ステータス更新エラー: {e}")
        return False