#!/usr/bin/env python3
"""
画像ファイル名をUUID形式に変更するマイグレーションスクリプト
実行前に必ずバックアップを取ってください。
"""

import os
import sys
import csv
from pathlib import Path
from dotenv import load_dotenv

# プロジェクトルートを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.supabase_client import supabase_client

def migrate_storage_images():
    """Supabase Storageの画像ファイル名をUUID形式に変更"""
    try:
        print("Supabase Storageの画像マイグレーション開始...")
        
        # データベースから既存のカクテル情報を取得
        cocktails_result = supabase_client.client.table('cocktails').select('uuid, order_id').execute()
        
        if not cocktails_result.data:
            print("マイグレーション対象のカクテルが見つかりません")
            return
        
        print(f"マイグレーション対象: {len(cocktails_result.data)}件のカクテル")
        
        success_count = 0
        error_count = 0
        
        for cocktail in cocktails_result.data:
            cocktail_uuid = cocktail['uuid']
            order_id = cocktail['order_id']
            
            try:
                # 古いファイル名（order_id.png）
                old_filename = f"cocktails/{order_id}.png"
                # 新しいファイル名（UUID.png）  
                new_filename = f"cocktails/{cocktail_uuid}.png"
                
                print(f"画像リネーム: {old_filename} -> {new_filename}")
                
                # 古いファイルの存在確認
                try:
                    old_file_response = supabase_client.client.storage.from_("cocktail-images").download(old_filename)
                    if not old_file_response:
                        print(f"  スキップ: 古いファイルが存在しません ({old_filename})")
                        continue
                except Exception as download_error:
                    print(f"  スキップ: ダウンロード失敗 - {download_error}")
                    continue
                
                # 新しいファイル名でアップロード
                upload_response = supabase_client.client.storage.from_("cocktail-images").upload(
                    new_filename, old_file_response, {"content-type": "image/png"}
                )
                
                # アップロード結果の確認
                if hasattr(upload_response, 'error') and upload_response.error:
                    print(f"  エラー: アップロード失敗 - {upload_response.error}")
                    error_count += 1
                    continue
                
                # 古いファイルを削除
                try:
                    delete_response = supabase_client.client.storage.from_("cocktail-images").remove([old_filename])
                    print(f"  成功: {old_filename} -> {new_filename}")
                    success_count += 1
                except Exception as delete_error:
                    print(f"  警告: 古いファイル削除失敗 - {delete_error}")
                    success_count += 1  # アップロードは成功しているのでカウントする
                
            except Exception as e:
                print(f"  エラー: カクテル {order_id} の処理失敗 - {e}")
                error_count += 1
                continue
        
        print(f"\nマイグレーション完了:")
        print(f"  成功: {success_count}件")
        print(f"  エラー: {error_count}件")
        print(f"  合計: {len(cocktails_result.data)}件")
        
        return success_count, error_count
        
    except Exception as e:
        print(f"マイグレーション実行エラー: {e}")
        return 0, 0

def create_uuid_mapping_file():
    """order_id <-> UUID のマッピングファイルを作成（デバッグ用）"""
    try:
        print("UUIDマッピングファイル作成中...")
        
        # データベースから情報を取得
        cocktails_result = supabase_client.client.table('cocktails').select('uuid, order_id, name').execute()
        
        if not cocktails_result.data:
            print("マッピング対象のカクテルが見つかりません")
            return
        
        mapping_file = Path(__file__).parent / "uuid_mapping.csv"
        
        with open(mapping_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['order_id', 'uuid', 'name'])
            
            for cocktail in cocktails_result.data:
                writer.writerow([
                    cocktail['order_id'], 
                    cocktail['uuid'], 
                    cocktail['name']
                ])
        
        print(f"マッピングファイル作成完了: {mapping_file}")
        print(f"レコード数: {len(cocktails_result.data)}件")
        
    except Exception as e:
        print(f"マッピングファイル作成エラー: {e}")

if __name__ == "__main__":
    import argparse
    
    # コマンドライン引数の処理
    parser = argparse.ArgumentParser(description="画像ファイルをUUID形式にマイグレーション")
    parser.add_argument("-y", "--yes", action="store_true", help="確認なしで実行")
    args = parser.parse_args()
    
    load_dotenv()
    
    print("=== 画像UUIDマイグレーション ===")
    print("⚠️ 実行前に必ずSupabase Storageのバックアップを取ってください！")
    
    # 確認プロンプト（-yフラグがない場合のみ）
    if not args.yes:
        try:
            response = input("続行しますか？ [y/N]: ")
            if response.lower() != 'y':
                print("マイグレーションをキャンセルしました。")
                sys.exit(0)
        except (EOFError, KeyboardInterrupt):
            print("\nマイグレーションをキャンセルしました。")
            sys.exit(0)
    
    try:
        # 1. UUIDマッピングファイル作成
        create_uuid_mapping_file()
        
        # 2. 画像ファイルマイグレーション
        success, error = migrate_storage_images()
        
        if error == 0:
            print("\n✅ 全ての画像マイグレーションが成功しました！")
        else:
            print(f"\n⚠️ マイグレーション完了（エラー: {error}件）")
            print("エラーが発生したファイルについては手動確認が必要です。")
            
    except KeyboardInterrupt:
        print("\n❌ マイグレーションが中断されました")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ マイグレーション実行エラー: {e}")
        sys.exit(1)