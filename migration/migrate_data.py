#!/usr/bin/env python3
"""
MySQLからSupabaseへのデータ移行スクリプト

使用方法:
1. requirements.txtの依存関係をインストール
2. .envファイルにMySQL情報とSupabase情報を設定
3. python migration/migrate_data.py を実行
"""

import os
import sys
from typing import List, Dict, Any
from datetime import datetime
import traceback

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from supabase import create_client, Client
import mysql.connector
from mysql.connector import Error

# 環境変数の読み込み
load_dotenv()
load_dotenv(".env.supabase", override=True)

class DataMigrator:
    def __init__(self):
        # MySQL接続設定
        self.mysql_config = {
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'host': os.getenv('DB_HOST'),
            'port': int(os.getenv('DB_PORT', 3306)),
            'database': os.getenv('DB_NAME')
        }
        
        # Supabase接続設定
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URLまたはSUPABASE_SERVICE_ROLE_KEYが設定されていません")
        
        self.supabase: Client = create_client(supabase_url, supabase_key)
        print("Supabase接続設定完了")
    
    def connect_mysql(self):
        """MySQLに接続"""
        try:
            connection = mysql.connector.connect(**self.mysql_config)
            if connection.is_connected():
                print(f"MySQL接続成功: {self.mysql_config['host']}")
                return connection
        except Error as e:
            print(f"MySQL接続エラー: {e}")
            return None
    
    def fetch_mysql_data(self, table_name: str) -> List[Dict[str, Any]]:
        """MySQLからデータを取得"""
        connection = self.connect_mysql()
        if not connection:
            return []
        
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(f"SELECT * FROM {table_name} ORDER BY id")
            data = cursor.fetchall()
            print(f"{table_name}から{len(data)}件のデータを取得")
            return data
        except Error as e:
            print(f"{table_name}のデータ取得エラー: {e}")
            return []
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    def convert_datetime(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """datetime型をISO文字列に変換"""
        for row in data:
            for key, value in row.items():
                if isinstance(value, datetime):
                    row[key] = value.isoformat()
        return data
    
    def migrate_cocktails(self):
        """cocktailsテーブルの移行"""
        print("\n=== cocktailsテーブルの移行開始 ===")
        
        # MySQLからデータ取得
        mysql_data = self.fetch_mysql_data("cocktails")
        if not mysql_data:
            print("cocktailsテーブルにデータがありません")
            return
        
        # datetime変換
        mysql_data = self.convert_datetime(mysql_data)
        
        # Supabaseに挿入
        try:
            # バッチサイズを小さくして、画像データを考慮
            batch_size = 10  # 画像データがあるため小さなバッチサイズ
            success_count = 0
            
            for i in range(0, len(mysql_data), batch_size):
                batch = mysql_data[i:i + batch_size]
                
                # idフィールドを除去（Supabaseで自動生成）
                for row in batch:
                    if 'id' in row:
                        del row['id']
                
                # 1件ずつ挿入（画像データが大きい場合の対策）
                for idx, row in enumerate(batch):
                    try:
                        result = self.supabase.table('cocktails').insert(row).execute()
                        success_count += 1
                        if success_count % 5 == 0:  # 5件ごとに進捗表示
                            print(f"cocktails: {success_count}/{len(mysql_data)}件挿入完了")
                    except Exception as row_error:
                        print(f"行 {i + idx + 1} の挿入エラー: {row_error}")
                        # order_idをログに出力してどの行でエラーが起きたか特定
                        print(f"エラー行のorder_id: {row.get('order_id', 'N/A')}")
                        # 画像データのサイズをチェック
                        image_size = len(row.get('image', ''))
                        print(f"画像データサイズ: {image_size} 文字")
                        continue
            
            print(f"cocktailsテーブル移行完了: {success_count}/{len(mysql_data)}件成功")
            
        except Exception as e:
            print(f"cocktailsテーブル移行エラー: {e}")
            traceback.print_exc()
    
    def migrate_poured_cocktails(self):
        """poured_cocktailsテーブルの移行"""
        print("\n=== poured_cocktailsテーブルの移行開始 ===")
        
        # MySQLからデータ取得
        mysql_data = self.fetch_mysql_data("poured_cocktails")
        if not mysql_data:
            print("poured_cocktailsテーブルにデータがありません")
            return
        
        # datetime変換
        mysql_data = self.convert_datetime(mysql_data)
        
        # Supabaseに挿入
        try:
            # バッチ挿入（1000件ずつ）
            batch_size = 1000
            for i in range(0, len(mysql_data), batch_size):
                batch = mysql_data[i:i + batch_size]
                
                # idフィールドを除去（Supabaseで自動生成）
                for row in batch:
                    if 'id' in row:
                        del row['id']
                
                result = self.supabase.table('poured_cocktails').insert(batch).execute()
                print(f"poured_cocktails: {len(batch)}件挿入完了 ({i + 1}-{min(i + batch_size, len(mysql_data))})")
            
            print(f"poured_cocktailsテーブル移行完了: 総{len(mysql_data)}件")
            
        except Exception as e:
            print(f"poured_cocktailsテーブル移行エラー: {e}")
            traceback.print_exc()
    
    def verify_migration(self):
        """移行データの検証"""
        print("\n=== 移行データの検証 ===")
        
        try:
            # Supabaseのデータ件数確認
            cocktails_result = self.supabase.table('cocktails').select('id', count='exact').execute()
            poured_cocktails_result = self.supabase.table('poured_cocktails').select('id', count='exact').execute()
            
            print(f"Supabase cocktails件数: {cocktails_result.count}")
            print(f"Supabase poured_cocktails件数: {poured_cocktails_result.count}")
            
            # MySQLのデータ件数確認
            connection = self.connect_mysql()
            if connection:
                cursor = connection.cursor()
                
                cursor.execute("SELECT COUNT(*) FROM cocktails")
                mysql_cocktails_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM poured_cocktails")
                mysql_poured_count = cursor.fetchone()[0]
                
                print(f"MySQL cocktails件数: {mysql_cocktails_count}")
                print(f"MySQL poured_cocktails件数: {mysql_poured_count}")
                
                # 件数比較
                if cocktails_result.count == mysql_cocktails_count:
                    print("✅ cocktailsテーブルの移行件数が一致しています")
                else:
                    print("❌ cocktailsテーブルの移行件数が一致しません")
                
                if poured_cocktails_result.count == mysql_poured_count:
                    print("✅ poured_cocktailsテーブルの移行件数が一致しています")
                else:
                    print("❌ poured_cocktailsテーブルの移行件数が一致しません")
                
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"検証エラー: {e}")
            traceback.print_exc()
    
    def run_migration(self):
        """移行処理の実行"""
        print("MySQLからSupabaseへのデータ移行を開始します...")
        print(f"MySQL: {self.mysql_config['host']}")
        print(f"Supabase: {os.getenv('SUPABASE_URL')}")
        
        try:
            # テーブルごとに移行実行
            self.migrate_cocktails()
            # self.migrate_poured_cocktails()
            
            # 移行結果の検証
            self.verify_migration()
            
            print("\n🎉 データ移行が完了しました！")
            
        except Exception as e:
            print(f"\n❌ 移行中にエラーが発生しました: {e}")
            traceback.print_exc()

def main():
    """メイン関数"""
    try:
        migrator = DataMigrator()
        migrator.run_migration()
    except Exception as e:
        print(f"移行スクリプト実行エラー: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()