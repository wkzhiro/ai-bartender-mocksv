#!/usr/bin/env python3
"""
ユーザー名の置換スクリプト
木添博仁（空白あり/なし）と飯田アサヒを適当な名前に置き換える
"""

import re
import random
import time
from db.database import get_all_cocktails
from db.supabase_client import supabase_client

# randomのシードを現在時刻で初期化
random.seed(time.time())

# 置換する適当な名前のリスト
REPLACEMENT_NAMES = [
    "田中太郎",
    "佐藤花子",
    "山田次郎",
    "鈴木美咲",
    "高橋健太",
    "伊藤由美",
    "渡辺大輔",
    "中村麻衣",
    "小林正雄",
    "加藤真理",
    "松本和也",
    "井上静香",
    "木村翔太",
    "林美穂",
    "清水拓海",
    "森田結衣",
    "池田雅人",
    "岡本彩乃",
    "橋本慎一",
    "斎藤綾香",
    "吉田直樹",
    "山口美奈",
    "石川晃司",
    "近藤愛美",
    "青木康弘",
    "竹内真央",
    "西村雄介",
    "原田莉奈",
    "藤田昭夫",
    "村上千春",
    "前田光一",
    "長谷川優子",
    "野村隆志",
    "堀江桃子",
    "上田智也",
    "平野美紀",
    "大野聡",
    "安田理恵",
    "増田亮太",
    "坂本なつみ",
    "内田裕介",
    "小野寺美保",
    "三浦健治",
    "今井香織",
    "菅原達也",
    "小川美佳",
    "新井勇気",
    "谷口恵子",
    "片山博之",
    "中島典子"
]

def check_usernames():
    """現在のデータベースのユーザー名を確認"""
    print("=== データベース内のユーザー名確認 ===")
    print("データベースに接続中...")
    
    try:
        # 全カクテルデータを少量ずつ取得（タイムアウト回避）
        print("カクテルデータを取得中...")
        all_cocktails = []
        offset = 0
        limit = 100  # 100件ずつ取得
        
        while True:
            print(f"  取得中: offset={offset}, limit={limit}")
            result = get_all_cocktails(limit=limit, offset=offset)
            batch_cocktails = result['data']
            
            if not batch_cocktails:
                break
                
            all_cocktails.extend(batch_cocktails)
            print(f"  累計取得数: {len(all_cocktails)}件")
            
            # 次のページがない場合は終了
            if not result.get('has_next', False):
                break
                
            offset += limit
        
        cocktails = all_cocktails
        print(f"取得完了: {len(cocktails)}件のカクテルデータを取得しました")
        
        target_names = set()
        all_user_names = set()
        
        print("ユーザー名を分析中...")
        processed_count = 0
        for cocktail in cocktails:
            processed_count += 1
            if processed_count % 100 == 0:  # 100件ごとに進行状況を表示
                print(f"  処理済み: {processed_count}/{len(cocktails)}件")
            
            user_name = cocktail.get('user_name', '')
            if user_name:
                all_user_names.add(user_name)
                
                # 木添博仁（空白あり/なし）をチェック - より柔軟なパターン
                if re.search(r'木.*添.*博.*仁', user_name) or '木添博仁' in user_name:
                    target_names.add(user_name)
                    print(f"⭐対象発見: '{user_name}' (order_id: {cocktail.get('order_id')})")
                
                # 飯田アサヒをチェック
                if '飯田アサヒ' in user_name or '飯田' in user_name and 'アサヒ' in user_name:
                    target_names.add(user_name)
                    print(f"⭐対象発見: '{user_name}' (order_id: {cocktail.get('order_id')})")
                
                # 加藤真理をチェック
                if '加藤真理' in user_name:
                    target_names.add(user_name)
                    print(f"⭐対象発見: '{user_name}' (order_id: {cocktail.get('order_id')})")
                
                # 鈴木美咲をチェック
                if '鈴木美咲' in user_name:
                    target_names.add(user_name)
                    print(f"⭐対象発見: '{user_name}' (order_id: {cocktail.get('order_id')})")
                
                # 井上静香をチェック
                if '井上静香' in user_name:
                    target_names.add(user_name)
                    print(f"⭐対象発見: '{user_name}' (order_id: {cocktail.get('order_id')})")
                
                # 田中太郎をチェック
                if '田中太郎' in user_name:
                    target_names.add(user_name)
                    print(f"⭐対象発見: '{user_name}' (order_id: {cocktail.get('order_id')})")
                
                # 佐藤花子をチェック
                if '佐藤花子' in user_name:
                    target_names.add(user_name)
                    print(f"⭐対象発見: '{user_name}' (order_id: {cocktail.get('order_id')})")
                
                # 飲田アサヒをチェック
                if '飲田アサヒ' in user_name:
                    target_names.add(user_name)
                    print(f"⭐対象発見: '{user_name}' (order_id: {cocktail.get('order_id')})")
                
                # nanashiをチェック
                if 'nanashi' in user_name:
                    target_names.add(user_name)
                    print(f"⭐対象発見: '{user_name}' (order_id: {cocktail.get('order_id')})")
        
        print(f"分析完了: {processed_count}件を処理しました")
        
        print(f"\n全ユーザー名数: {len(all_user_names)}")
        print("全ユーザー名:")
        for name in sorted(all_user_names):
            print(f"  - '{name}'")
        
        print(f"\n置換対象の名前: {len(target_names)}")
        for name in target_names:
            print(f"  - '{name}'")
        
        return target_names, cocktails
        
    except Exception as e:
        print(f"❌ エラー発生: {e}")
        import traceback
        print(f"詳細: {traceback.format_exc()}")
        return set(), []

def replace_usernames(dry_run=True):
    """ユーザー名を置換"""
    print(f"\n=== ユーザー名置換{'（dry run）' if dry_run else ''} ===")
    
    print("対象ユーザー名を再確認中...")
    target_names, cocktails = check_usernames()
    
    if not target_names:
        print("置換対象のユーザー名が見つかりませんでした。")
        return
    
    # 置換マッピングを生成
    print(f"\n置換マッピングを生成中... （対象: {len(target_names)}件）")
    replacement_mapping = {}
    name_index = 0  # インデックスを0から開始
    
    for i, target_name in enumerate(target_names, 1):
        print(f"  [{i}/{len(target_names)}] 処理中: '{target_name}'")
        
        # インデックスを使って順番に名前を選択
        replacement_name = REPLACEMENT_NAMES[name_index]
        replacement_mapping[target_name] = replacement_name
        
        print(f"    ✓ '{target_name}' → '{replacement_name}' (インデックス: {name_index})")
        
        # 次のインデックスに進む（リストの最後に達したら0に戻る）
        name_index = (name_index + 1) % len(REPLACEMENT_NAMES)
    
    print(f"置換マッピング生成完了")
    
    # 実際の置換処理
    print(f"\n{'Dry Run' if dry_run else '実際の'}置換処理を開始...")
    updated_count = 0
    target_cocktails = [c for c in cocktails if c.get('user_name') in replacement_mapping]
    
    if not target_cocktails:
        print("置換対象のカクテルが見つかりませんでした。")
        return
    
    print(f"置換対象カクテル数: {len(target_cocktails)}件")
    
    # 各カクテルに対して個別に名前を割り当て
    name_index = 0
    for i, cocktail in enumerate(target_cocktails, 1):
        user_name = cocktail.get('user_name', '')
        # 各カクテルに順番に異なる名前を割り当て
        new_name = REPLACEMENT_NAMES[name_index]
        order_id = cocktail.get('order_id')
        
        print(f"  [{i}/{len(target_cocktails)}] 処理中: order_id={order_id}")
        
        if dry_run:
            print(f"    [Dry Run] '{user_name}' → '{new_name}' (インデックス: {name_index})")
            updated_count += 1
        else:
            try:
                print(f"    データベース更新中...")
                # Supabaseでuser_nameを更新
                result = supabase_client.client.table('cocktails').update({
                    'user_name': new_name
                }).eq('order_id', order_id).execute()
                
                if result.data:
                    print(f"    ✓ 更新完了: '{user_name}' → '{new_name}' (インデックス: {name_index})")
                    updated_count += 1
                else:
                    print(f"    ❌ 更新失敗: order_id: {order_id}")
                    
            except Exception as e:
                print(f"    ❌ 更新エラー: order_id: {order_id}, エラー: {e}")
        
        # 次のインデックスに進む（リストの最後に達したら0に戻る）
        name_index = (name_index + 1) % len(REPLACEMENT_NAMES)
    
    if not dry_run:
        print(f"\n✅ 更新完了: {updated_count}件のレコードを更新しました。")
    else:
        print(f"\n✅ Dry Run完了: {len([c for c in cocktails if c.get('user_name') in replacement_mapping])}件のレコードが更新対象です。")

def main():
    """メイン処理"""
    print("🍸 ユーザー名置換ツール")
    print("対象: 木添博仁（空白あり/なし）、飯田アサヒ、加藤真理、鈴木美咲、井上静香、田中太郎、佐藤花子、飲田アサヒ、nanashi")
    print("=" * 50)
    
    print("\n📊 データベース接続テスト中...")
    try:
        # 接続テスト
        print("Supabaseクライアントを初期化中...")
        from db.supabase_client import supabase_client
        print("✓ Supabaseクライアント初期化完了")
    except Exception as e:
        print(f"❌ データベース接続エラー: {e}")
        return
    
    print("\n🔍 データベース分析を開始...")
    # まずは確認のみ
    target_names, cocktails = check_usernames()
    
    if not target_names:
        print("\n✅ 置換対象のユーザー名は見つかりませんでした。処理完了。")
        return
    
    print("\n" + "=" * 50)
    print("🚀 自動置換を実行します...")
    
    # 自動で置換実行
    replace_usernames(dry_run=False)
    print("\n🎉 置換処理が完了しました！")

if __name__ == "__main__":
    main()