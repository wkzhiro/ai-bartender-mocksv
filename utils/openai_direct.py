"""
OpenAI APIを直接呼び出すユーティリティ
"""
import os
from typing import Dict, Optional, Any
from config.settings import settings
import requests
import json


def generate_chat_completion_direct(prompt: str, temperature: float = 0.7) -> Dict[str, Any]:
    """同期的にChatGPT APIを呼び出す（Azure OpenAI Mini使用）"""
    try:
        # Azure OpenAI API設定を取得
        api_key = settings.AZURE_OPENAI_API_KEY_LLM
        endpoint_url = settings.AZURE_OPENAI_ENDPOINT_LLM_MINI
        
        if not api_key:
            return {"result": "error", "error": "Azure OpenAI APIキーが設定されていません"}
        if not endpoint_url:
            return {"result": "error", "error": "Azure OpenAI Mini エンドポイントが設定されていません"}
            
        # ヘッダーとボディの準備（Azure OpenAI用）
        headers = {
            "api-key": api_key,
            "Content-Type": "application/json"
        }
        
        body = {
            "messages": [
                {"role": "system", "content": "You are a creative assistant."},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": 500
        }
        
        print(f"[DEBUG] Azure OpenAI Mini API呼び出し: endpoint={endpoint_url[:50]}...")
        
        # APIリクエスト（Azure OpenAI）
        response = requests.post(
            endpoint_url,
            headers=headers,
            json=body,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            return {"result": "success", "content": content}
        else:
            return {"result": "error", "error": f"API Error {response.status_code}: {response.text}"}
                    
    except Exception as e:
        return {"result": "error", "error": str(e)}