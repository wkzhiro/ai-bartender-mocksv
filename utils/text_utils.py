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
            lines = [line.strip() for line in f.readlines() if line.strip()]
            
        syrup_dict = {}
        syrup_names = ['ベリー', '青りんご', 'シトラス', 'ホワイト']
        
        for i in range(len(lines)):
            line = lines[i]
            # 日本語のシロップ名の行をチェック
            if line in syrup_names:
                if i + 1 < len(lines):
                    syrup_dict[line] = lines[i + 1]
                    print(f"[DEBUG] シロップ登録: {line} -> {lines[i + 1][:50]}...")
                    
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


def is_generic_name(name: str) -> bool:
    """汎用的な名前かどうかを判定"""
    import re
    if not name:
        return False
    
    # 汎用的なパターンをチェック
    generic_patterns = [
        r'^特製カクテル\d*$',
        r'^カクテル\d+$',
        r'^オリジナル.*\d*$',
        r'^ミックス.*\d*$',
        r'^今日のカクテル\d*$',
        r'^本日のカクテル\d*$'
    ]
    
    for pattern in generic_patterns:
        if re.match(pattern, name):
            print(f"[DEBUG] 汎用名パターンにマッチ: {name} -> {pattern}")
            return True
    
    return False

def validate_cocktail_name(name: str, filter_words: List[str]) -> bool:
    """カクテル名がフィルター単語に引っかからないかチェック"""
    if not name:
        print("[DEBUG] 空の名前は無効")
        return False
    
    # 1. 汎用名チェック（新規追加）
    if is_generic_name(name):
        print(f"[DEBUG] 汎用名として拒否: {name}")
        return False
    
    # 2. フィルター単語チェック（既存ロジック）
    if not filter_words:
        return True
        
    name_lower = name.lower()
    for word in filter_words:
        if word.lower() in name_lower:
            print(f"[DEBUG] フィルター単語にマッチ: {name} -> 単語: {word}")
            return False
    
    print(f"[DEBUG] カクテル名検証通過: {name}")
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
- 4種類のシロップの合計が25%になるように調整してください
- 各シロップの使用量は1%刻みで指定してください。ただし、ホワイトは最大15％として下さい。
- 0%のシロップがあっても構いません
-アニメや商品等の著作権を害する固有名詞をカクテル名には使用しないこと。

出力は以下のJSON形式で返してください:
{{
  "cocktail_name": "カクテル名",
  "concept": "このカクテルのコンセプトや込めた想いを50〜100文字程度で",
  "color": {{
    "name": "色の名前",
    "description": "色の詳細説明",
    "target_rgb": "RGB(r,g,b)形式"
  }},
  "recipe": [
    {{"syrup": "ベリー", "ratio": "5%"}},
    {{"syrup": "青りんご", "ratio": "10%"}},
    {{"syrup": "シトラス", "ratio": "5%"}},
    {{"syrup": "ホワイト", "ratio": "5%"}}
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
    """ミニLLMを使用してカクテル名を再生成（改善版）"""
    try:
        print("[DEBUG] 簡易再生成開始 - 汎用名回避版")
        
        # コンセプトや色から創造的な単語を抽出
        concept = cocktail_data.get('concept', '')
        color_info = cocktail_data.get('color', {})
        color_name = color_info.get('name', '') if isinstance(color_info, dict) else str(color_info)
        
        # より創造的な名前の候補を生成
        creative_prefixes = [
            '夢見る', '輝く', '煌めく', '風の', '星空の', '虹色の', '心の', 
            '愛の', '希望の', '幸福の', '魔法の', '神秘の', '天使の'
        ]
        
        creative_suffixes = [
            'ブレンド', 'エリクサー', 'ドリーム', 'ハーモニー', 'シンフォニー',
            'ラプソディ', 'セレナーデ', 'メロディ', 'フィナーレ', 'アンサンブル'
        ]
        
        # 色名からインスピレーションを得た名前
        color_inspired = []
        if color_name:
            color_inspired = [f'{color_name}の調べ', f'{color_name}ワルツ', f'{color_name}ミスト']
        
        # 候補リストを作成
        candidates = []
        import random
        
        # 創造的な組み合わせを生成
        for prefix in creative_prefixes[:5]:  # 最初の5個
            for suffix in creative_suffixes[:3]:  # 最初の3個
                candidates.append(f'{prefix}{suffix}')
        
        # 色にインスパイアされた名前を追加
        candidates.extend(color_inspired)
        
        # ランダムに並び替え
        random.shuffle(candidates)
        
        print(f"[DEBUG] 生成した候補: {len(candidates)}個")
        
        # 各候補をテスト
        for candidate in candidates:
            print(f"[DEBUG] 候補テスト: {candidate}")
            if validate_cocktail_name(candidate, filter_words):
                print(f"[DEBUG] 簡易再生成成功: {candidate}")
                return candidate
            else:
                print(f"[DEBUG] 候補拒否: {candidate}")
                
        print("[DEBUG] 全ての候補が拒否されました")
        return None
        
    except Exception as e:
        print(f"[ERROR] カクテル名再生成エラー: {e}")
        return None


def regenerate_name_with_alternative_prompt(
    cocktail_data: Dict, 
    filter_words: List[str],
    original_name: str
) -> Optional[str]:
    """別のプロンプト戦略でフィルターを回避したカクテル名を生成"""
    from utils.openai_direct import generate_chat_completion_direct
    
    # 別のアプローチのプロンプト（フィルター単語を明示的に避ける）
    prompt = f"""
あなたは創造的なバーテンダーです。以下のカクテルに新しい名前をつけてください。

カクテル情報:
- 元の名前: {original_name}（この名前は使用できません）
- コンセプト: {cocktail_data.get('concept', '')}
- 色: {cocktail_data.get('color', {}).get('name', '')}
- 色の説明: {cocktail_data.get('color', {}).get('description', '')}

制約事項:
- 次の単語は絶対に使用しないでください: {', '.join(filter_words[:10])}...
- 上記の禁止単語を含まない、全く新しい名前を考えてください
- カクテルのコンセプトや色から連想される、詩的で魅力的な名前にしてください
- 日本語でお願いします
- 回答は名前のみ（説明や理由は不要）

名前:"""
    
    try:
        print(f"[DEBUG] 別プロンプトでAPI呼び出し開始")
        result = generate_chat_completion_direct(prompt, temperature=0.9)
        print(f"[DEBUG] API結果: {result.get('result', 'N/A')}")
        if result["result"] == "success":
            new_name = result["content"].strip().strip('"').strip('「').strip('」')
            print(f"[DEBUG] 生成された候補名: {new_name}")
            # 生成された名前も検証
            if validate_cocktail_name(new_name, filter_words):
                print(f"[DEBUG] 候補名が検証を通過: {new_name}")
                return new_name
            else:
                print(f"[DEBUG] 候補名が検証に失敗: {new_name}")
    except Exception as e:
        print(f"[ERROR] 別プロンプトでの名前再生成エラー: {e}")
    
    return None