"""
テキスト処理ユーティリティ
"""
import os
import re
import json
import random
from pathlib import Path
from typing import List, Dict, Optional

from config.settings import settings


def load_syrup_info_txt() -> Dict[str, str]:
    """syrup.txtファイルからシロップ情報を読み込む"""
    try:
        syrup_file = Path(settings.SYRUP_INFO_FILE)
        if not syrup_file.exists():
            print(f"[WARNING] {settings.SYRUP_INFO_FILE}が見つかりません")
            return {}
            
        with syrup_file.open('r', encoding='utf-8') as f:
            content = f.read()
            
        syrup_dict = {}
        lines = content.strip().split('\n')
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                syrup_dict[key.strip()] = value.strip()
                
        print(f"[DEBUG] シロップ情報読み込み完了: {len(syrup_dict)}種類")
        return syrup_dict
        
    except Exception as e:
        print(f"[ERROR] シロップ情報読み込みエラー: {e}")
        return {}


def load_fusion_filter_words() -> List[str]:
    """フィルター単語リストを読み込む"""
    try:
        filter_file = Path(settings.FILTER_WORDS_FILE)
        if not filter_file.exists():
            print(f"[WARNING] {settings.FILTER_WORDS_FILE}が見つかりません")
            return []
            
        with filter_file.open('r', encoding='utf-8') as f:
            words = [line.strip() for line in f if line.strip()]
            
        print(f"[DEBUG] フィルター単語読み込み完了: {len(words)}語")
        return words
        
    except Exception as e:
        print(f"[ERROR] フィルター単語読み込みエラー: {e}")
        return []


def validate_cocktail_name(name: str, filter_words: List[str]) -> bool:
    """カクテル名がフィルター単語に引っかからないかチェック"""
    if not name or not filter_words:
        return True
        
    name_lower = name.lower()
    for word in filter_words:
        if word.lower() in name_lower:
            return False
    return True


def build_recipe_system_prompt(syrup_dict: Dict[str, str], custom_prompt: Optional[str] = None) -> str:
    """レシピ生成用のシステムプロンプトを構築"""
    syrup_info = ""
    for syrup, description in syrup_dict.items():
        syrup_info += f"- {syrup}: {description}\n"
    
    base_prompt = f"""
あなたは創造性豊かなバーテンダーです。以下の4種類のシロップを使用して、お客様だけの特別なカクテルを作成してください。

利用可能なシロップ:
{syrup_info}

レシピの制約:
- 4種類のシロップの合計が100%になるように調整してください
- 各シロップの使用量は0%～100%の範囲で、5%刻みで指定してください
- 0%のシロップがあっても構いません

出力は以下のJSON形式で返してください:
{{
  "cocktail_name": "カクテル名",
  "concept": "このカクテルのコンセプトや込めた想いを50文字程度で",
  "color": {{
    "name": "色の名前",
    "description": "色の詳細説明",
    "target_rgb": "RGB(r,g,b)形式"
  }},
  "recipe": [
    {{"syrup": "ベリー", "ratio": "30%"}},
    {{"syrup": "青りんご", "ratio": "25%"}},
    {{"syrup": "シトラス", "ratio": "25%"}},
    {{"syrup": "ホワイト", "ratio": "20%"}}
  ]
}}

お客様の情報を読み取り、心に響く特別なカクテルを創造してください。
"""
    
    if custom_prompt:
        base_prompt += f"\n\n追加指示:\n{custom_prompt}"
        
    return base_prompt


def extract_json_from_text(text: str) -> Optional[Dict]:
    """テキストからJSON部分を抽出してパース"""
    try:
        json_match = re.search(r'\{[\s\S]+\}', text)
        if not json_match:
            return None
            
        json_str = json_match.group(0)
        return json.loads(json_str)
        
    except Exception as e:
        print(f"[ERROR] JSON抽出エラー: {e}")
        return None


def generate_order_id() -> Optional[str]:
    """6桁のランダム注文IDを生成（重複チェック付き）"""
    from db import database as dbmodule
    
    for attempt in range(settings.MAX_ORDER_ID_ATTEMPTS):
        order_id = str(random.randint(settings.ORDER_ID_MIN, settings.ORDER_ID_MAX))
        
        # DBに同じorder_idが存在しないかチェック
        if not dbmodule.get_cocktail_by_order_id(order_id):
            print(f"[DEBUG] 注文ID生成完了: {order_id} (試行{attempt+1}回)")
            return order_id
            
        print(f"[DEBUG] 注文ID重複 (試行{attempt+1}): {order_id}")
    
    print(f"[ERROR] {settings.MAX_ORDER_ID_ATTEMPTS}回試行しても注文IDが生成できませんでした")
    return None


def regenerate_cocktail_name_with_mini_llm(
    cocktail_data: Dict, 
    filter_words: List[str]
) -> Optional[str]:
    """ミニLLMを使用してカクテル名を再生成"""
    try:
        # 簡単なルールベースでの名前生成（実装例）
        concept = cocktail_data.get('concept', '')
        color = cocktail_data.get('color', '')
        
        # キーワードから安全な単語を抽出
        safe_words = ['特製', '香り', '味わい', '一杯', 'カクテル', '美味', '上質']
        
        # ランダムに組み合わせる
        import datetime
        timestamp = datetime.datetime.now().strftime("%H%M%S")
        
        for word in safe_words:
            candidate = f"{word}カクテル{timestamp[-3:]}"
            if validate_cocktail_name(candidate, filter_words):
                return candidate
                
        return None
        
    except Exception as e:
        print(f"[ERROR] カクテル名再生成エラー: {e}")
        return None