#!/usr/bin/env python3
"""
既存データをUUIDに移行し、画像ファイル名をリネームするスクリプト
実行前に必ずデータベースのバックアップを取ってください。
"""

import sys
import shutil
from pathlib import Path
from typing import Dict, List, Tuple

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from config.settings import Settings
from db.supabase_client import SupabaseClient

def get_cocktail_mappings(supabase_client: SupabaseClient) -> List[Dict]:
    """
    既存のカクテルデータからorder_id → UUID のマッピングを取得
    """
    try:
        result = supabase_client.client.table('cocktails').select('id, order_id').execute()
        return result.data if result.data else []
    except Exception as e:
        print(f"[ERROR] カクテルマッピングの取得に失敗しました: {e}")
        return []

def rename_image_files(mappings: List[Dict]) -> List[Tuple[str, str, bool]]:
    """
    画像ファイルを order_id.png から uuid.png にリネーム
    
    Returns:
        List[Tuple[str, str, bool]]: (old_filename, new_filename, success)のリスト
    """
    results = []
    image_folder = Path(Settings.IMAGE_FOLDER)
    
    for mapping in mappings:
        order_id = mapping.get('order_id')
        uuid_id = mapping.get('id')
        
        if not order_id or not uuid_id:
            continue
            
        old_path = image_folder / f"{order_id}.png"
        new_path = image_folder / f"{uuid_id}.png"
        
        try:
            if old_path.exists():
                shutil.move(str(old_path), str(new_path))
                results.append((old_path.name, new_path.name, True))
                print(f"[SUCCESS] 画像ファイルリネーム完了: {old_path.name} → {new_path.name}")
            else:
                print(f"[WARNING] 画像ファイルが見つかりません: {old_path}")
                results.append((old_path.name, new_path.name, False))
        except Exception as e:
            print(f"[ERROR] 画像ファイルリネーム失敗: {old_path.name} → {new_path.name}, エラー: {e}")
            results.append((old_path.name, new_path.name, False))
    
    return results

def create_migration_log(mappings: List[Dict], rename_results: List[Tuple[str, str, bool]]):
    """
    マイグレーション結果のログファイルを作成
    """
    log_path = Path(__file__).parent / "uuid_migration_log.txt"
    
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write("UUID移行ログ\n")
        f.write("=" * 50 + "\n\n")
        
        f.write("1. データベースマッピング:\n")
        for mapping in mappings:
            f.write(f"   order_id: {mapping.get('order_id')} → UUID: {mapping.get('id')}\n")
        
        f.write(f"\n2. 画像ファイルリネーム結果:\n")
        successful_renames = [r for r in rename_results if r[2]]
        failed_renames = [r for r in rename_results if not r[2]]
        
        f.write(f"   成功: {len(successful_renames)}件\n")
        for old, new, _ in successful_renames:
            f.write(f"     {old} → {new}\n")
            
        f.write(f"   失敗: {len(failed_renames)}件\n")
        for old, new, _ in failed_renames:
            f.write(f"     {old} → {new} (失敗)\n")
    
    print(f"[INFO] マイグレーションログを作成しました: {log_path}")

def main():
    print("UUID移行スクリプトを開始します...")
    
    # データベース接続
    try:
        supabase_client = SupabaseClient()
        print("[INFO] データベースに接続しました")
    except Exception as e:
        print(f"[ERROR] データベース接続に失敗しました: {e}")
        return False
    
    # 既存データの確認
    print("\n1. 既存データのマッピングを取得中...")
    mappings = get_cocktail_mappings(supabase_client)
    
    if not mappings:
        print("[WARNING] 移行対象のデータが見つかりません")
        return True
    
    print(f"[INFO] {len(mappings)}件のカクテルデータを発見しました")
    
    # 画像ファイルのリネーム
    print("\n2. 画像ファイルをリネーム中...")
    rename_results = rename_image_files(mappings)
    
    # ログ作成
    print("\n3. マイグレーションログを作成中...")
    create_migration_log(mappings, rename_results)
    
    # 結果サマリー
    successful_renames = len([r for r in rename_results if r[2]])
    failed_renames = len([r for r in rename_results if not r[2]])
    
    print("\n=== 移行結果サマリー ===")
    print(f"データベースマッピング: {len(mappings)}件")
    print(f"画像ファイルリネーム成功: {successful_renames}件")
    print(f"画像ファイルリネーム失敗: {failed_renames}件")
    
    if failed_renames > 0:
        print(f"\n[WARNING] {failed_renames}件の画像ファイルリネームに失敗しました。詳細はログを確認してください。")
    
    print("\nUUID移行スクリプトが完了しました。")
    return failed_renames == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)