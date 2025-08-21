"""
画像処理ユーティリティ
"""
import base64
import io
from pathlib import Path
from PIL import Image
from fastapi import HTTPException
from typing import Optional

from db.supabase_client import supabase_client
from config.settings import settings


def encode_image_to_base64(image_path: Path) -> str:
    """画像ファイルをbase64エンコードする"""
    try:
        with image_path.open("rb") as f:
            image_data = f.read()
        encoded_image = base64.b64encode(image_data).decode("utf-8")
        return f"data:image/png;base64,{encoded_image}"
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"画像のエンコードに失敗しました: {e}")


def crop_and_resize_base64_image(
    base64_str: str, 
    target_width: int = None, 
    target_height: int = None
) -> str:
    """base64画像を中央クロップ＆リサイズする"""
    if target_width is None:
        target_width = settings.TARGET_WIDTH
    if target_height is None:
        target_height = settings.TARGET_HEIGHT
        
    try:
        # base64ヘッダー除去
        if "," in base64_str:
            base64_str = base64_str.split(",")[1]
        
        img_bytes = base64.b64decode(base64_str)
        with Image.open(io.BytesIO(img_bytes)) as img:
            src_width, src_height = img.size
            target_aspect = target_width / target_height
            src_aspect = src_width / src_height

            # クロップ範囲計算
            if src_aspect > target_aspect:
                # 横長→左右をカット
                new_width = int(src_height * target_aspect)
                left = (src_width - new_width) // 2
                box = (left, 0, left + new_width, src_height)
            else:
                # 縦長→上下をカット
                new_height = int(src_width / target_aspect)
                top = (src_height - new_height) // 2
                box = (0, top, src_width, top + new_height)
                
            img_cropped = img.crop(box)
            img_resized = img_cropped.resize((target_width, target_height), Image.LANCZOS)
            buf = io.BytesIO()
            img_resized.save(buf, format="PNG")
            b64_png = base64.b64encode(buf.getvalue()).decode("utf-8")
            return f"data:image/png;base64,{b64_png}"
            
    except Exception as e:
        raise Exception(f"画像加工エラー: {str(e)}")


def upload_image_to_storage(image_base64: str, cocktail_id: str) -> str:
    """Supabase Storageに画像をアップロードし、URLを返す（UUID使用）"""
    try:
        print(f"[DEBUG] upload_image_to_storage開始 - cocktail_id: {cocktail_id}")
        
        # base64ヘッダーを除去
        if "," in image_base64:
            image_base64 = image_base64.split(",")[1]
        
        # base64をバイナリに変換
        image_bytes = base64.b64decode(image_base64)
        print(f"[DEBUG] 画像バイナリサイズ: {len(image_bytes)} bytes")
        
        # ファイル名をUUIDベースで生成
        filename = f"cocktails/{cocktail_id}.png"
        print(f"[DEBUG] アップロードファイル名: {filename}")
        
        # Supabase Storageにアップロード
        print(f"[DEBUG] Supabase Storageアップロード実行中...")
        response = supabase_client.client.storage.from_("cocktail-images").upload(
            filename, image_bytes, {"content-type": "image/png"}
        )
        
        print(f"[DEBUG] Supabase Storageレスポンス: {response}")
        
        # 新しいSupabase SDKのレスポンス構造に対応
        # アップロードが成功した場合、pathまたはfull_pathが存在する
        if hasattr(response, 'path') or hasattr(response, 'full_path'):
            print(f"[DEBUG] アップロード成功: path={getattr(response, 'path', 'N/A')}")
        elif hasattr(response, 'error') and response.error:
            print(f"[ERROR] Storage upload error: {response.error}")
            raise Exception(f"Storage upload error: {response.error}")
        else:
            # レスポンスの属性を確認
            response_attrs = [attr for attr in dir(response) if not attr.startswith('_')]
            print(f"[DEBUG] レスポンス属性: {response_attrs}")
            
            # エラーがなければ成功とみなす（レスポンス構造が不明な場合の安全策）
            print(f"[DEBUG] レスポンス構造確認: {type(response)}")
        
        # 公開URLを取得
        print(f"[DEBUG] 公開URL取得中...")
        url_response = supabase_client.client.storage.from_("cocktail-images").get_public_url(filename)
        
        print(f"[DEBUG] 公開URL: {url_response}")
        
        # URLレスポンスの構造を確認
        if hasattr(url_response, 'public_url'):
            public_url = url_response.public_url
        elif hasattr(url_response, 'publicURL'):
            public_url = url_response.publicURL
        elif isinstance(url_response, str):
            public_url = url_response
        else:
            # レスポンスがdict形式の場合
            if isinstance(url_response, dict):
                public_url = url_response.get('public_url') or url_response.get('publicURL')
            else:
                print(f"[WARNING] 予期しないURL形式: {type(url_response)}, {url_response}")
                public_url = str(url_response)
        
        # URLの末尾に余分な?がある場合は削除
        if public_url and public_url.endswith('?'):
            public_url = public_url.rstrip('?')
            print(f"[DEBUG] 末尾の?を削除: {public_url}")
        
        print(f"[DEBUG] 最終公開URL: {public_url}")
        return public_url
        
    except Exception as e:
        print(f"[ERROR] upload_image_to_storage失敗: {str(e)}")
        # より詳細なエラー情報を表示
        import traceback
        traceback.print_exc()
        raise Exception(f"画像アップロードエラー: {str(e)}")

def upload_image_by_order_id(image_base64: str, order_id: str) -> str:
    """order_idを使用した外部API互換性のための画像アップロード"""
    from db import database as dbmodule
    
    try:
        # order_idからUUIDを取得
        cocktail_id = dbmodule.get_uuid_from_order_id(order_id)
        if not cocktail_id:
            raise Exception(f"order_id {order_id} に対応するカクテルが見つかりません")
        
        # UUIDベースでアップロード
        return upload_image_to_storage(image_base64, cocktail_id)
    except Exception as e:
        print(f"[ERROR] upload_image_by_order_id失敗: {str(e)}")
        raise

def get_image_url_by_uuid(cocktail_id: str) -> Optional[str]:
    """UUID IDで画像URLを取得"""
    try:
        filename = f"cocktails/{cocktail_id}.png"
        url_response = supabase_client.client.storage.from_("cocktail-images").get_public_url(filename)
        
        if hasattr(url_response, 'public_url'):
            return url_response.public_url
        elif hasattr(url_response, 'publicURL'):
            return url_response.publicURL
        elif isinstance(url_response, str):
            return url_response
        elif isinstance(url_response, dict):
            return url_response.get('public_url') or url_response.get('publicURL')
        else:
            return str(url_response)
    except Exception as e:
        print(f"[ERROR] UUID画像URL取得エラー: {e}")
        return None

def get_image_url_by_order_id(order_id: str) -> Optional[str]:
    """order_idで画像URLを取得（外部API互換性）"""
    from db import database as dbmodule
    
    try:
        # order_idからUUIDを取得
        cocktail_id = dbmodule.get_uuid_from_order_id(order_id)
        if not cocktail_id:
            return None
        
        # UUIDベースで画像URL取得
        return get_image_url_by_uuid(cocktail_id)
    except Exception as e:
        print(f"[ERROR] order_id画像URL取得エラー: {e}")
        return None


def download_image_from_storage(filename_or_url: str) -> Optional[str]:
    """Supabase Storageから画像をダウンロードしてbase64エンコードする"""
    try:
        # URLから画像名を抽出（URLが渡された場合）
        if filename_or_url.startswith('http'):
            # URLから画像名を抽出
            import re
            match = re.search(r'cocktails/(\d+\.png)', filename_or_url)
            if match:
                filename = match.group(0)
            else:
                print(f"[WARNING] URLから画像名を抽出できません: {filename_or_url}")
                return None
        elif filename_or_url.startswith('cocktails/'):
            filename = filename_or_url
        else:
            filename = f"cocktails/{filename_or_url}"
            
        print(f"[DEBUG] 画像ダウンロード開始 - filename: {filename}")
        
        # Supabase Storageから画像をダウンロード
        response = supabase_client.client.storage.from_("cocktail-images").download(filename)
        
        if response:
            # バイナリデータをbase64エンコード
            image_base64 = base64.b64encode(response).decode('utf-8')
            # data:image/png;base64, プレフィックスを追加
            full_base64 = f"data:image/png;base64,{image_base64}"
            print(f"[DEBUG] 画像ダウンロード成功 - サイズ: {len(full_base64)} 文字")
            return full_base64
        else:
            print(f"[WARNING] 画像ダウンロード失敗: レスポンスが空")
            return None
            
    except Exception as e:
        print(f"[WARNING] 画像ダウンロードエラー: {str(e)}")
        # エラーが発生した場合はNoneを返す（既存のbase64データを使用するため）
        return None
