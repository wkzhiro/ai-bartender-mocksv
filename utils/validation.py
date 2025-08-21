"""
バリデーション関連ユーティリティ
"""
from typing import Dict, List, Optional
from fastapi import Request

from config.settings import settings


def get_client_ip(request: Request) -> str:
    """クライアントIPアドレスを取得"""
    # X-Forwarded-For ヘッダーからIPを取得（プロキシ経由の場合）
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # 複数のIPがある場合は最初のもの（クライアントIP）を使用
        return forwarded_for.split(",")[0].strip()
    
    # X-Real-IP ヘッダーから取得（Nginx等）
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    
    # 直接アクセスの場合
    return request.client.host if request.client else "unknown"


def validate_api_configuration() -> Dict[str, bool]:
    """API設定の検証"""
    return settings.validate_api_keys()


def validate_recipe_ratios(recipe: List[Dict[str, str]]) -> bool:
    """レシピの比率の合計が100%になるかチェック"""
    try:
        total = 0
        for item in recipe:
            ratio_str = item.get("ratio", "0%")
            ratio_value = int(ratio_str.replace("%", ""))
            total += ratio_value
        
        return total == 100
        
    except Exception as e:
        print(f"[ERROR] レシピ比率検証エラー: {e}")
        return False


def sanitize_text_input(text: str, max_length: int = 500) -> str:
    """テキスト入力のサニタイズ"""
    if not text:
        return ""
    
    # 長さ制限
    text = text[:max_length]
    
    # 基本的なHTMLタグ除去
    import re
    text = re.sub(r'<[^>]*>', '', text)
    
    # 連続する空白を単一に
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


def validate_survey_response(response_data: Dict) -> bool:
    """アンケート回答データの検証"""
    try:
        required_fields = ['question_id']
        for field in required_fields:
            if field not in response_data:
                return False
        
        # 回答テキストまたは選択肢IDのいずれかが存在することを確認
        has_answer = (
            response_data.get('answer_text') or 
            response_data.get('selected_option_ids')
        )
        
        return bool(has_answer)
        
    except Exception as e:
        print(f"[ERROR] アンケート回答検証エラー: {e}")
        return False