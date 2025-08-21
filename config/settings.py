"""
アプリケーション設定管理
"""
import os
from typing import Optional


class Settings:
    """アプリケーション設定クラス"""
    
    # OpenAI API設定
    AZURE_OPENAI_API_KEY_LLM: Optional[str] = os.environ.get("AZURE_OPENAI_API_KEY_LLM")
    AZURE_OPENAI_ENDPOINT_LLM: Optional[str] = os.environ.get("AZURE_OPENAI_ENDPOINT_LLM")
    OPENAI_API_KEY: Optional[str] = os.environ.get("OPENAI_API_KEY")
    GPT_API_KEY: Optional[str] = os.environ.get("GPT_API_KEY")
    
    # Azure OpenAI設定
    DEPLOYMENT_ID: str = "gpt-4.1"
    API_VERSION: str = "2023-12-01-preview"
    
    # 画像生成設定
    IMAGE_MODEL: str = "gpt-image-1"
    IMAGE_SIZE: str = "1024x1536"
    IMAGE_QUALITY: str = "low"
    
    # タイムアウト設定
    LLM_TIMEOUT: int = 30
    IMAGE_TIMEOUT: int = 60
    
    # 画像処理設定
    TARGET_WIDTH: int = 720
    TARGET_HEIGHT: int = 1080
    
    # リトライ設定
    MAX_NAME_RETRIES: int = 3
    MAX_ORDER_ID_ATTEMPTS: int = 10
    
    # 注文ID設定
    ORDER_ID_MIN: int = 100000
    ORDER_ID_MAX: int = 999999
    
    # ファイルパス
    SYRUP_INFO_FILE: str = "syrup.txt"
    FILTER_WORDS_FILE: str = "storage/fusion_filter_words.txt"
    IMAGE_FOLDER: str = "images"
    
    # CORS設定
    CORS_ORIGINS: list = ["*"]
    CORS_METHODS: list = ["*"]
    CORS_HEADERS: list = ["*"]
    
    @classmethod
    def get_llm_api_key(cls) -> Optional[str]:
        """LLM用のAPIキーを取得"""
        return cls.AZURE_OPENAI_API_KEY_LLM or cls.OPENAI_API_KEY
    
    @classmethod
    def get_image_api_key(cls) -> Optional[str]:
        """画像生成用のAPIキーを取得"""
        return cls.GPT_API_KEY or cls.OPENAI_API_KEY
    
    @classmethod
    def get_llm_url(cls) -> Optional[str]:
        """LLM APIのURLを生成"""
        if cls.AZURE_OPENAI_ENDPOINT_LLM:
            return f"{cls.AZURE_OPENAI_ENDPOINT_LLM}/openai/deployments/{cls.DEPLOYMENT_ID}/chat/completions?api-version={cls.API_VERSION}"
        return None
    
    @classmethod
    def validate_api_keys(cls) -> dict:
        """APIキーの設定状況を検証"""
        return {
            "llm_api_key": bool(cls.get_llm_api_key()),
            "llm_endpoint": bool(cls.AZURE_OPENAI_ENDPOINT_LLM),
            "image_api_key": bool(cls.get_image_api_key())
        }


# グローバル設定インスタンス
settings = Settings()