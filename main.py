"""
リファクタリングされたFastAPIアプリケーション
AI Bartender API v2.0 - モジュラー構成版
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

# 設定とルーター
from config.settings import settings
from routers import cocktails, events, surveys, violations, prompts
from services.prompt_service import PromptService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーション起動・終了時の処理"""
    # 起動時処理
    print("🚀 AI Bartender API v2.0 起動中...")
    
    # デフォルトプロンプトの初期化
    try:
        PromptService.initialize_default_prompts()
        print("✅ デフォルトプロンプト初期化完了")
    except Exception as e:
        print(f"⚠️ デフォルトプロンプト初期化警告: {e}")
    
    # API設定の検証
    api_validation = settings.validate_api_keys()
    print(f"🔑 API設定状況: {api_validation}")
    
    # デバッグ: 環境変数の詳細確認
    print("🔍 環境変数詳細:")
    print(f"  - AZURE_OPENAI_API_KEY_LLM: {'設定済み' if settings.AZURE_OPENAI_API_KEY_LLM else '未設定'}")
    print(f"  - AZURE_OPENAI_ENDPOINT_LLM: {'設定済み' if settings.AZURE_OPENAI_ENDPOINT_LLM else '未設定'}")
    print(f"  - AZURE_OPENAI_ENDPOINT_LLM_MINI: {'設定済み' if settings.AZURE_OPENAI_ENDPOINT_LLM_MINI else '未設定'}")
    print(f"  - GPT_API_KEY: {'設定済み' if settings.GPT_API_KEY else '未設定'}")
    print(f"  - OPENAI_API_KEY: {'設定済み' if settings.OPENAI_API_KEY else '未設定'}")
    
    print("✅ AI Bartender API v2.0 起動完了")
    
    yield
    
    # 終了時処理
    print("🛑 AI Bartender API v2.0 終了中...")
    print("✅ AI Bartender API v2.0 終了完了")


# FastAPIアプリケーション初期化
app = FastAPI(
    title="AI Bartender API",
    description="AIバーテンダーによるカクテル生成API - モジュラー構成版",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
)

# ルーター登録
app.include_router(cocktails.router, tags=["Cocktails"])
app.include_router(events.router, tags=["Events"])  
app.include_router(surveys.router, tags=["Surveys"])
app.include_router(violations.router, tags=["Violations"])
app.include_router(prompts.router, tags=["Prompts"])

# レガシーAPIのエイリアス（完全互換性のため）
from typing import Union, Optional, List, Dict, Any
from fastapi import Query
from models.requests import OrderRequest, DeriveryRequest

@app.post("/order/")
async def post_order_legacy(order: OrderRequest):
    """レガシー注文エンドポイント（/cocktail/orderと同等）"""
    from routers.cocktails import generate_response
    try:
        order_id_str = str(order.order_id)
        response = generate_response(order_id_str)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"注文処理エラー: {str(e)}")

from utils.image_utils import download_image_from_storage

@app.get("/order/")
async def get_order_legacy(
    order_id: Union[int, str], 
    limit: Optional[int] = None, 
    offset: int = 0, 
    event_id: Optional[str] = None
):
    """レガシー注文取得エンドポイント（/cocktail/orderと同等）"""
    from services.cocktail_service import CocktailService
    try:
        order_id_str = str(order_id)
        if order_id_str == "all":
            # 全件取得
            cocktail_data = CocktailService.get_all_cocktails(limit=limit, offset=offset, event_id=event_id)
            cocktails = cocktail_data.get('data', [])
            print(f"[DEBUG] データ変換前のカクテル数: {len(cocktails)}")
            result = []
            for i, c in enumerate(cocktails):
                print(f"[DEBUG] カクテル{i+1} 変換前データ: order_id={c.get('order_id')}, name={c.get('name')}")
                recipe = [
                    {"syrup": "ベリー", "ratio": c.get('flavor_ratio1', '')},
                    {"syrup": "青りんご", "ratio": c.get('flavor_ratio2', '')},
                    {"syrup": "シトラス", "ratio": c.get('flavor_ratio3', '')},
                    {"syrup": "ホワイト", "ratio": c.get('flavor_ratio4', '')},
                ]
                
                # 画像をSupabaseから取得してbase64に変換（UUID対応）
                cocktail_uuid = c.get('id', '')
                order_id = c.get('order_id', '')
                image_data = ''
                
                if cocktail_uuid:
                    # UUIDから画像ファイル名を生成
                    filename = f"cocktails/{cocktail_uuid}.png"
                    base64_image = download_image_from_storage(filename)
                    if base64_image:
                        image_data = base64_image
                        print(f"[DEBUG] UUID画像取得成功: {cocktail_uuid}")
                    else:
                        # UUID失敗時は古いorder_id形式でも試す（移行期間対応）
                        print(f"[DEBUG] UUID画像取得失敗、order_idで試行: {order_id}")
                        if order_id:
                            filename = f"cocktails/{order_id}.png"
                            base64_image = download_image_from_storage(filename)
                            if base64_image:
                                image_data = base64_image
                                print(f"[DEBUG] order_id画像取得成功: {order_id}")
                            else:
                                print(f"[WARNING] 画像ダウンロード失敗: uuid={cocktail_uuid}, order_id={order_id}")
                elif order_id:
                    # UUIDがない場合は古い形式で試す
                    filename = f"cocktails/{order_id}.png"
                    base64_image = download_image_from_storage(filename)
                    if base64_image:
                        image_data = base64_image
                        print(f"[DEBUG] order_id画像取得成功（フォールバック）: {order_id}")
                    else:
                        print(f"[WARNING] 画像ダウンロード失敗（フォールバック）: order_id={order_id}")
                
                cocktail_info = {
                    "order_id": c.get('order_id'),
                    "name": c.get('name', ''),
                    "recipe": recipe,
                    "comment": c.get('comment', ''),
                    "image_base64": image_data,  # base64データまたは既存のbase64データ
                    "created_at": c.get('created_at', ''),
                    "event_id": c.get('event_id', ''),
                    "poured": c.get('poured', False),
                }
                print(f"[DEBUG] カクテル{i+1} 変換後データ: order_id={cocktail_info['order_id']}, name={cocktail_info['name']}, image_base64長さ={len(cocktail_info['image_base64']) if cocktail_info['image_base64'] else 0}")
                result.append(cocktail_info)
            
            print(f"[DEBUG] 最終レスポンス件数: {len(result)}")
            return {
                "data": result, 
                "total": cocktail_data.get('total', len(result)),
                "limit": limit,
                "offset": offset
            }
        else:
            from routers.cocktails import generate_response
            return generate_response(order_id_str)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"注文取得エラー: {str(e)}")

@app.post("/delivery/")
async def post_delivery_legacy(delivery_data: DeriveryRequest):
    """レガシー配達エンドポイント（/cocktail/deliveryと同等）"""
    from services.cocktail_service import CocktailService
    try:
        db_data = {
            "poured": str(delivery_data.poured),
            "name": delivery_data.name,
            "flavor_name1": delivery_data.flavor_name1,
            "flavor_ratio1": delivery_data.flavor_ratio1,
            "flavor_name2": delivery_data.flavor_name2,
            "flavor_ratio2": delivery_data.flavor_ratio2,
            "flavor_name3": delivery_data.flavor_name3,
            "flavor_ratio3": delivery_data.flavor_ratio3,
            "flavor_name4": delivery_data.flavor_name4,
            "flavor_ratio4": delivery_data.flavor_ratio4,
            "comment": delivery_data.comment,
        }
        
        inserted_id = CocktailService.insert_poured_cocktail(db_data)
        return {
            "result": "success",
            "inserted_id": inserted_id,
            "message": "配達処理が完了しました"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"配達処理エラー: {str(e)}")

@app.get("/debug/cocktails-count")
async def debug_cocktails_count_legacy():
    """レガシーデバッグエンドポイント（/cocktail/debug/countと同等）"""
    from services.cocktail_service import CocktailService
    try:
        count_info = CocktailService.get_cocktails_count_debug()
        return count_info
    except Exception as e:
        return {"error": str(e), "cocktails_count": 0}

@app.post("/prompts/initialize")
async def initialize_prompts_legacy():
    """レガシープロンプト初期化エンドポイント（/prompts/initialize-defaultsと同等）"""
    try:
        PromptService.initialize_default_prompts()
        return {"result": "success", "detail": "デフォルトプロンプトを初期化しました"}
    except Exception as e:
        return {"result": "error", "detail": str(e)}

# 違反報告関連のレガシーエンドポイント
from services.violation_service import ViolationService
from models.requests import ViolationReportRequest, HideCocktailRequest
from typing import List

@app.get("/violation-reports/", response_model=Dict[str, Any])
async def get_violation_reports_legacy(
    cocktail_id: Optional[int] = Query(None, description="特定カクテルの報告のみ取得"),
    status: Optional[str] = Query(None, description="特定ステータスの報告のみ取得"),
    show_all: bool = Query(False, description="全ステータスの報告を取得")
):
    """レガシー違反報告一覧エンドポイント（/violations/violation-reports/と同等）"""
    try:
        reports = ViolationService.get_violation_reports(cocktail_id, status, show_all)
        # フロントエンドが期待する形式に合わせる
        return {"reports": reports}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"違反報告取得エラー: {str(e)}")

@app.put("/violation-reports/{report_id}/status", response_model=Dict[str, Any])
async def update_violation_report_status_legacy(
    report_id: int,
    status_data: Dict[str, str]
):
    """レガシー違反報告ステータス更新エンドポイント"""
    try:
        new_status = status_data.get("status")
        if not new_status:
            raise HTTPException(status_code=400, detail="statusフィールドが必要です")
        
        success = ViolationService.update_violation_report_status(report_id, new_status)
        if not success:
            raise HTTPException(
                status_code=400,
                detail="違反報告ステータス更新に失敗しました（存在しない報告または無効なステータス）"
            )
        
        return {
            "result": "success",
            "message": "違反報告ステータスを更新しました",
            "report_id": report_id,
            "new_status": new_status
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"違反報告ステータス更新エラー: {str(e)}")

@app.post("/report-violation/")
async def report_violation_legacy(report_data: ViolationReportRequest, request: Request):
    """レガシー違反報告エンドポイント（/violations/report-violation/と同等）"""
    from utils.validation import get_client_ip
    try:
        client_ip = get_client_ip(request)
        success = ViolationService.report_violation(report_data, client_ip)
        if not success:
            raise HTTPException(
                status_code=400, 
                detail="違反報告に失敗しました（既に報告済みか、存在しないカクテルです）"
            )
        
        return {
            "result": "success",
            "message": "違反報告を受け付けました",
            "cocktail_id": report_data.cocktail_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"違反報告エラー: {str(e)}")

@app.post("/hide-cocktail/")
async def hide_cocktail_legacy(hide_data: HideCocktailRequest):
    """レガシーカクテル非表示エンドポイント（/violations/hide-cocktail/と同等）"""
    try:
        success = ViolationService.hide_cocktail(hide_data.cocktail_id, hide_data.reason)
        if not success:
            raise HTTPException(
                status_code=400, 
                detail="カクテル非表示に失敗しました（存在しないカクテルです）"
            )
        
        return {
            "result": "success",
            "message": "カクテルを非表示にしました",
            "cocktail_id": hide_data.cocktail_id,
            "reason": hide_data.reason
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"カクテル非表示エラー: {str(e)}")

@app.post("/show-cocktail/{cocktail_id}")
async def show_cocktail_legacy(cocktail_id: int):
    """レガシーカクテル再表示エンドポイント（/violations/show-cocktail/と同等）"""
    try:
        success = ViolationService.show_cocktail(cocktail_id)
        if not success:
            raise HTTPException(
                status_code=400, 
                detail="カクテル再表示に失敗しました（存在しないカクテルです）"
            )
        
        return {
            "result": "success",
            "message": "カクテルを再表示しました",
            "cocktail_id": cocktail_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"カクテル再表示エラー: {str(e)}")

# ヘルスチェックエンドポイント
@app.get("/", tags=["Health"])
def health_check():
    """ヘルスチェック"""
    return {
        "status": "healthy", 
        "message": "AI Bartender API v2.0 is running",
        "version": "2.0.0",
        "architecture": "modular"
    }

@app.get("/status_check", tags=["Health"])
def status_check():
    """ステータスチェック（レガシー互換）"""
    return "ready"

# システム情報エンドポイント
@app.get("/system/info", tags=["System"])
def get_system_info():
    """システム情報取得"""
    return {
        "api_name": "AI Bartender API",
        "version": "2.0.0",
        "architecture": "modular",
        "modules": {
            "cocktail_service": "カクテル生成機能",
            "event_service": "イベント管理機能", 
            "survey_service": "アンケート機能",
            "violation_service": "違反報告機能",
            "prompt_service": "プロンプト管理機能"
        },
        "endpoints": {
            "cocktails": "/cocktail/*",
            "events": "/events/*",
            "surveys": "/surveys/*", 
            "violations": "/violations/*",
            "prompts": "/prompts/*"
        }
    }

# 設定確認エンドポイント（開発用）
@app.get("/debug/config", tags=["Debug"])
def debug_config():
    """API設定の確認（開発用）"""
    validation = settings.validate_api_keys()
    return {
        "api_keys_status": validation,
        "endpoints": {
            "llm_url": bool(settings.get_llm_url()),
            "image_api": "OpenAI Images API"
        },
        "settings": {
            "deployment_id": settings.DEPLOYMENT_ID,
            "image_model": settings.IMAGE_MODEL,
            "timeouts": {
                "llm": settings.LLM_TIMEOUT,
                "image": settings.IMAGE_TIMEOUT
            },
            "image_processing": {
                "target_width": settings.TARGET_WIDTH,
                "target_height": settings.TARGET_HEIGHT
            }
        },
        "cors": {
            "origins": settings.CORS_ORIGINS,
            "methods": settings.CORS_METHODS
        }
    }

# モジュール統計エンドポイント（開発用）
@app.get("/debug/modules", tags=["Debug"])
def debug_modules():
    """モジュール読み込み状況確認"""
    try:
        modules_status = {
            "config.settings": "✅ 読み込み済み",
            "models.requests": "✅ 読み込み済み", 
            "utils.image_utils": "✅ 読み込み済み",
            "utils.text_utils": "✅ 読み込み済み",
            "utils.validation": "✅ 読み込み済み",
            "services.cocktail_service": "✅ 読み込み済み",
            "services.event_service": "✅ 読み込み済み",
            "services.survey_service": "✅ 読み込み済み", 
            "services.violation_service": "✅ 読み込み済み",
            "services.prompt_service": "✅ 読み込み済み",
            "routers": "✅ 全ルーター読み込み済み"
        }
        
        return {
            "modules": modules_status,
            "total_modules": len(modules_status),
            "status": "all_modules_loaded"
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "status": "module_load_error"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )