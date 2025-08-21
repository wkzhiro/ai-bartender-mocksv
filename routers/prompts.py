"""
プロンプト管理関連APIルーター
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional

from models.requests import PromptRequest
from services.prompt_service import PromptService

router = APIRouter(prefix="/prompts", tags=["prompts"])


@router.get("/", response_model=List[Dict[str, Any]])
def get_prompts(
    prompt_type: Optional[str] = Query(None, description="プロンプトタイプでフィルタ (recipe, image)"),
    is_active: Optional[bool] = Query(None, description="アクティブ状態でフィルタ")
):
    """プロンプト一覧取得"""
    try:
        prompts = PromptService.get_prompts(prompt_type, is_active)
        return prompts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"プロンプト取得エラー: {str(e)}")


@router.get("/active", response_model=List[Dict[str, Any]])
def get_active_prompts(
    prompt_type: Optional[str] = Query(None, description="プロンプトタイプでフィルタ (recipe, image)")
):
    """アクティブなプロンプトのみ取得"""
    try:
        prompts = PromptService.get_prompts(prompt_type, is_active=True)
        return prompts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"アクティブプロンプト取得エラー: {str(e)}")


@router.get("/{prompt_id}", response_model=Dict[str, Any])
def get_prompt(prompt_id: str):
    """特定プロンプト取得"""
    try:
        prompt = PromptService.get_prompt_by_id(prompt_id)
        if not prompt:
            raise HTTPException(status_code=404, detail="プロンプトが見つかりません")
        return prompt
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"プロンプト取得エラー: {str(e)}")


@router.post("/", response_model=Dict[str, Any])
def create_prompt(prompt_data: PromptRequest):
    """新規プロンプト作成"""
    try:
        prompt_id = PromptService.create_prompt(prompt_data)
        if not prompt_id:
            raise HTTPException(
                status_code=400, 
                detail="プロンプト作成失敗（同名のプロンプトが既に存在する可能性があります）"
            )
        
        # 作成されたプロンプトを取得して返す
        created_prompt = PromptService.get_prompt_by_id(prompt_id)
        return {
            "result": "success",
            "message": "プロンプトが作成されました",
            "prompt_id": prompt_id,
            "prompt": created_prompt
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"プロンプト作成エラー: {str(e)}")


@router.put("/{prompt_id}", response_model=Dict[str, Any])
def update_prompt(prompt_id: str, prompt_data: PromptRequest):
    """プロンプト更新"""
    try:
        success = PromptService.update_prompt(prompt_id, prompt_data)
        if not success:
            raise HTTPException(
                status_code=404, 
                detail="更新対象のプロンプトが見つかりません"
            )
        
        # 更新されたプロンプトを取得して返す
        updated_prompt = PromptService.get_prompt_by_id(prompt_id)
        return {
            "result": "success",
            "message": "プロンプトが更新されました",
            "prompt": updated_prompt
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"プロンプト更新エラー: {str(e)}")


@router.delete("/{prompt_id}", response_model=Dict[str, Any])
def delete_prompt(prompt_id: str):
    """プロンプト削除（論理削除）"""
    try:
        success = PromptService.delete_prompt(prompt_id)
        if not success:
            raise HTTPException(
                status_code=404, 
                detail="削除対象のプロンプトが見つかりません"
            )
        
        return {
            "result": "success",
            "message": "プロンプトが削除されました",
            "prompt_id": prompt_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"プロンプト削除エラー: {str(e)}")


@router.post("/initialize-defaults", response_model=Dict[str, Any])
def initialize_default_prompts():
    """デフォルトプロンプト初期化"""
    try:
        success = PromptService.initialize_default_prompts()
        if not success:
            raise HTTPException(status_code=500, detail="デフォルトプロンプト初期化に失敗しました")
        
        return {
            "result": "success",
            "message": "デフォルトプロンプトが初期化されました"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"プロンプト初期化エラー: {str(e)}")


@router.get("/{prompt_id}/statistics", response_model=Dict[str, Any])
def get_prompt_statistics(prompt_id: str):
    """プロンプト使用統計取得"""
    try:
        stats = PromptService.get_prompt_usage_statistics(prompt_id)
        if not stats:
            raise HTTPException(status_code=404, detail="プロンプトが見つかりません")
        
        return {
            "result": "success",
            "statistics": stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"統計情報取得エラー: {str(e)}")


@router.get("/statistics/overview", response_model=Dict[str, Any])
def get_all_prompt_statistics():
    """全プロンプト統計情報取得"""
    try:
        stats = PromptService.get_all_prompt_statistics()
        return {
            "result": "success",
            "statistics": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"統計情報取得エラー: {str(e)}")


# タイプ別プロンプト取得の便利エンドポイント
@router.get("/recipe/active", response_model=List[Dict[str, Any]])
def get_active_recipe_prompts():
    """アクティブなレシピプロンプト取得"""
    try:
        prompts = PromptService.get_prompts(prompt_type="recipe", is_active=True)
        return prompts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"レシピプロンプト取得エラー: {str(e)}")


@router.get("/image/active", response_model=List[Dict[str, Any]])
def get_active_image_prompts():
    """アクティブな画像プロンプト取得"""
    try:
        prompts = PromptService.get_prompts(prompt_type="image", is_active=True)
        return prompts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"画像プロンプト取得エラー: {str(e)}")


# プロンプトテンプレート関連
@router.get("/templates/recipe", response_model=List[Dict[str, str]])
def get_recipe_prompt_templates():
    """レシピプロンプトテンプレート取得"""
    try:
        templates = [
            {
                "name": "基本レシピプロンプト",
                "template": "お客様の情報を基に、心に響く特別なカクテルレシピを創造してください。色彩豊かで味わい深い組み合わせを提案してください。"
            },
            {
                "name": "感情重視レシピプロンプト", 
                "template": "お客様の感情や体験に寄り添い、その瞬間にぴったりのカクテルを創造してください。ストーリー性のあるレシピを重視してください。"
            },
            {
                "name": "季節感重視レシピプロンプト",
                "template": "現在の季節や時期を考慮し、季節感あふれるカクテルレシピを提案してください。自然の移ろいを表現してください。"
            }
        ]
        return templates
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"テンプレート取得エラー: {str(e)}")


@router.get("/templates/image", response_model=List[Dict[str, str]])
def get_image_prompt_templates():
    """画像プロンプトテンプレート取得"""
    try:
        templates = [
            {
                "name": "基本画像プロンプト",
                "template": "リアルな質感の写真風イラストとして生成してください。背景は透明で、カクテルのみを美しく描写してください。"
            },
            {
                "name": "芸術的画像プロンプト",
                "template": "芸術的で幻想的な雰囲気のカクテル画像を生成してください。光の表現や色彩のグラデーションを重視してください。"
            },
            {
                "name": "シンプル画像プロンプト",
                "template": "シンプルで洗練されたカクテル画像を生成してください。ミニマルなデザインを心がけてください。"
            }
        ]
        return templates
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"テンプレート取得エラー: {str(e)}")