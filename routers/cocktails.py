"""
カクテル関連APIルーター
"""
from fastapi import APIRouter, HTTPException, Request
from pathlib import Path
import base64
from typing import Dict, Any

from models.requests import (
    CreateCocktailRequest, 
    CreateCocktailAnonymousRequest, 
    CreateCocktailResponse,
    SaveCocktailRequest,
    OrderRequest,
    DeriveryRequest,
    CopyrightConfirmationRequest,
    CopyrightConfirmationResponse,
    CopyrightStatusResponse
)
from services.cocktail_service import CocktailService
from utils.image_utils import encode_image_to_base64, download_image_from_storage
from utils.validation import get_client_ip
from config.settings import settings
from db import database as dbmodule

router = APIRouter(prefix="/cocktail", tags=["cocktails"])

# 注文番号に対応するレシピ情報（順不同）
recipe_info = {
    "123456": {
        "name": "バジル・ブリーズ",
        "comment": "鮮やかなエメラルドグリーンのカクテルで、フレッシュバジルの香りが引き立つ爽やかな味わい。ジンとライムリキュールをベースにしたハーバルな一杯。"
    },
    "234567": {
        "name": "ゴールデン・サンセット",
        "comment": "黄金色に輝くフルーティーなカクテル。パッションフルーツとアプリコットの甘酸っぱさが際立ち、チェリーのガーニッシュがアクセント。"
    },
    "345678": {
        "name": "ディープ・ブルー・ナイト",
        "comment": "濃厚なブルーの美しいカクテル。ブルーキュラソーとバイオレットリキュールを使った幻想的な味わいで、ブラックベリーのトッピングが深みを添える。"
    }
}


def generate_response(order_id_str: str) -> dict:
    """注文IDに対応するレスポンスを生成"""
    
    # Supabaseから取得
    cocktail_data = dbmodule.get_cocktail_by_order_id(order_id_str)
    if not cocktail_data:
        raise HTTPException(status_code=404, detail="注文番号が無効です。")
    
    # 画像をSupabaseから取得してbase64に変換（UUID対応）
    image_data = ''
    cocktail_uuid = cocktail_data.get('id', '')
    
    if cocktail_uuid:
        # UUIDから画像ファイル名を生成
        filename = f"cocktails/{cocktail_uuid}.png"
        base64_image = download_image_from_storage(filename)
        if base64_image:
            image_data = base64_image
            print(f"[DEBUG] UUID画像取得成功: {cocktail_uuid}")
        else:
            # UUID失敗時は古いorder_id形式でも試す（移行期間対応）
            print(f"[DEBUG] UUID画像取得失敗、order_idで試行: {order_id_str}")
            filename = f"cocktails/{order_id_str}.png"
            base64_image = download_image_from_storage(filename)
            if base64_image:
                image_data = base64_image
                print(f"[DEBUG] order_id画像取得成功: {order_id_str}")
            else:
                print(f"[WARNING] 画像ダウンロード失敗: uuid={cocktail_uuid}, order_id={order_id_str}")
    elif order_id_str:
        # UUIDがない場合は古い形式で試す（フォールバック）
        filename = f"cocktails/{order_id_str}.png"
        base64_image = download_image_from_storage(filename)
        if base64_image:
            image_data = base64_image
            print(f"[DEBUG] order_id画像取得成功（フォールバック）: {order_id_str}")
        else:
            print(f"[WARNING] 画像ダウンロード失敗（フォールバック）: order_id={order_id_str}")
    
    # データベースから取得した情報でレスポンスを構築
    return {
        "result": "success",
        "id": cocktail_data.get('order_id', ''),
        "name": cocktail_data.get('name', '不明なカクテル'),
        "poured": 1,
        "flavor_name1": "ベリー",
        "flavor_ratio1": cocktail_data.get('flavor_ratio1', '0%'),
        "flavor_name2": "青りんご", 
        "flavor_ratio2": cocktail_data.get('flavor_ratio2', '0%'),
        "flavor_name3": "シトラス",
        "flavor_ratio3": cocktail_data.get('flavor_ratio3', '0%'),
        "flavor_name4": "ホワイト",
        "flavor_ratio4": cocktail_data.get('flavor_ratio4', '0%'),
        "comment": cocktail_data.get('comment', ''),
        "image_base64": image_data,
    }


@router.post("/save")
def save_cocktail(request: SaveCocktailRequest):
    """カクテルデータを保存"""
    try:
        # データベースに保存（画像はSupabase Storageに保存済みのため除外）
        db_data = {
            "order_id": request.order_id,
            "status": request.status,
            "name": request.name,
            "comment": request.comment,
            "recent_event": request.recent_event,
            "event_name": request.event_name,
            "user_name": request.user_name,
            "career": request.career,
            "hobby": request.hobby
        }
        
        inserted_id = dbmodule.insert_cocktail(db_data)
        if inserted_id:
            return {"result": "success", "message": "カクテルが保存されました。", "id": inserted_id}
        else:
            raise HTTPException(status_code=500, detail="データベースへの保存に失敗しました。")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存中にエラーが発生しました: {e}")


@router.post("/order")
def post_order(request: OrderRequest):
    """注文処理"""
    order_id_str = str(request.order_id)
    return generate_response(order_id_str)


@router.get("/order")
def get_order(order_id: str):
    """注文取得"""
    return generate_response(order_id)


@router.post("/delivery")
def deliver_cocktail(request: DeriveryRequest):
    """カクテル配送処理"""
    try:
        # 配送情報をデータベースに保存
        delivery_data = {
            "poured": request.poured,
            "name": request.name,
            "flavor_name1": request.flavor_name1,
            "flavor_ratio1": request.flavor_ratio1,
            "flavor_name2": request.flavor_name2,
            "flavor_ratio2": request.flavor_ratio2,
            "flavor_name3": request.flavor_name3,
            "flavor_ratio3": request.flavor_ratio3,
            "flavor_name4": request.flavor_name4,
            "flavor_ratio4": request.flavor_ratio4,
            "comment": request.comment
        }
        
        # 注文IDを生成して保存（実際の実装では注文IDの管理が必要）
        import random
        order_id = str(random.randint(100000, 999999))
        
        response_data = {
            "result": "success",
            "id": order_id,
            "name": request.name,
            "poured": request.poured,
            **{f"flavor_name{i}": getattr(request, f"flavor_name{i}") for i in range(1, 5)},
            **{f"flavor_ratio{i}": getattr(request, f"flavor_ratio{i}") for i in range(1, 5)},
            "comment": request.comment
        }
        
        return response_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"配送処理中にエラーが発生しました: {e}")


@router.get("/image/{order_id}")
def get_cocktail_image(order_id: str):
    """カクテル画像取得（UUID対応）"""
    try:
        # データベースからカクテル情報を取得してUUIDを確認
        cocktail_data = dbmodule.get_cocktail_by_order_id(order_id)
        cocktail_uuid = cocktail_data.get('id', '') if cocktail_data else ''
        
        # まず静的ファイルから検索（古いファイルの場合）
        image_path = Path(settings.IMAGE_FOLDER) / f"{order_id}.png"
        if image_path.exists():
            return {"image_base64": encode_image_to_base64(image_path)}
        
        # UUIDが利用可能な場合はUUID形式で取得を試みる
        if cocktail_uuid:
            filename = f"cocktails/{cocktail_uuid}.png"
            base64_image = download_image_from_storage(filename)
            if base64_image:
                return {"image_base64": base64_image}
        
        # フォールバック：古いorder_id形式で試す
        filename = f"cocktails/{order_id}.png"
        base64_image = download_image_from_storage(filename)
        if base64_image:
            return {"image_base64": base64_image}
        
        raise HTTPException(status_code=404, detail="画像が見つかりません。")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"画像取得中にエラーが発生しました: {e}")


@router.get("/debug/count")
def debug_cocktails_count():
    """カクテル数のデバッグ情報"""
    try:
        count = dbmodule.get_cocktails_count()
        return {"cocktails_count": count}
    except Exception as e:
        return {"error": str(e), "cocktails_count": 0}


@router.post("/", response_model=CreateCocktailResponse)
async def create_cocktail(req: CreateCocktailRequest):
    """カクテル作成（ユーザー情報を保存、画像はSupabaseバケットに保存）"""
    print("post request / test")
    return await CocktailService.create_cocktail(req, save_user_info=req.save_user_info, use_storage=True)


@router.post("/anonymous", response_model=CreateCocktailResponse)
async def create_cocktail_anonymous(req: CreateCocktailAnonymousRequest):
    """匿名カクテル作成（ユーザー情報は保存しない）"""
    print("post request / anonymous")
    # CreateCocktailRequestに変換（nameを空文字に）
    cocktail_req = CreateCocktailRequest(
        recent_event=req.recent_event,
        event_name=req.event_name,
        name="",  # 匿名なので空文字
        career=req.career,
        hobby=req.hobby,
        prompt=req.prompt,
        recipe_prompt_id=req.recipe_prompt_id,
        image_prompt_id=req.image_prompt_id,
        event_id=req.event_id,
        survey_responses=req.survey_responses
    )
    return await CocktailService.create_cocktail(cocktail_req, save_user_info=False, use_storage=False)


# 既存のorder_エンドポイント（互換性のため残す）
@router.get("/order_")
def order_(order_id: str):
    """注文取得（レガシーエンドポイント）"""
    return generate_response(order_id)


# 著作権確認関連エンドポイント
@router.post("/{cocktail_id}/copyright-confirm", response_model=CopyrightConfirmationResponse)
async def confirm_copyright(cocktail_id: str, req: CopyrightConfirmationRequest):
    """著作権確認を行う"""
    try:
        print(f"[DEBUG] 著作権確認API呼び出し - cocktail_id: {cocktail_id}")
        
        # リクエストのカクテルIDとパスパラメータの一致チェック
        if req.cocktail_id != cocktail_id:
            raise HTTPException(
                status_code=400, 
                detail="リクエストのカクテルIDとパスパラメータが一致しません"
            )
        
        # 著作権確認を実行
        result = CocktailService.confirm_copyright(cocktail_id)
        
        if not result.get("success", False):
            raise HTTPException(
                status_code=400, 
                detail=result.get("message", "著作権確認に失敗しました")
            )
        
        return CopyrightConfirmationResponse(
            success=True,
            cocktail_id=cocktail_id,
            confirmed_at=result.get("confirmed_at"),
            message=result.get("message", "著作権確認が完了しました")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] 著作権確認APIエラー: {e}")
        raise HTTPException(status_code=500, detail=f"内部サーバーエラー: {str(e)}")


@router.get("/{cocktail_id}/copyright-status", response_model=CopyrightStatusResponse)
async def get_copyright_status(cocktail_id: str):
    """著作権確認ステータスを取得"""
    try:
        print(f"[DEBUG] 著作権ステータス取得API呼び出し - cocktail_id: {cocktail_id}")
        
        # ステータスを取得
        result = CocktailService.get_copyright_status(cocktail_id)
        
        if not result.get("success", False):
            raise HTTPException(
                status_code=404, 
                detail=result.get("message", "カクテルが見つかりません")
            )
        
        return CopyrightStatusResponse(
            cocktail_id=cocktail_id,
            copyright_confirmed=result.get("copyright_confirmed", False),
            confirmed_at=result.get("confirmed_at")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] 著作権ステータス取得APIエラー: {e}")
        raise HTTPException(status_code=500, detail=f"内部サーバーエラー: {str(e)}")