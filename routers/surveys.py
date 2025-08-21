"""
アンケート関連APIルーター
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional

from models.requests import SurveyRequest, SurveyUpdateRequest, SurveyResponseRequest
from services.survey_service import SurveyService

router = APIRouter(prefix="/surveys", tags=["surveys"])


@router.post("/", response_model=Dict[str, Any])
def create_survey(survey_data: SurveyRequest):
    """新規アンケート作成"""
    try:
        survey_id = SurveyService.create_survey(survey_data)
        if not survey_id:
            raise HTTPException(
                status_code=400, 
                detail="アンケート作成失敗（指定されたイベントが存在しない可能性があります）"
            )
        
        # 作成されたアンケートを取得して返す
        created_survey = SurveyService.get_survey_with_questions(survey_id)
        return {
            "result": "success",
            "message": "アンケートが作成されました",
            "survey_id": survey_id,
            "survey": created_survey
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"アンケート作成エラー: {str(e)}")


@router.get("/{survey_id}", response_model=Dict[str, Any])
def get_survey(survey_id: str):
    """アンケート詳細取得（質問・選択肢込み）"""
    try:
        survey = SurveyService.get_survey_with_questions(survey_id)
        if not survey:
            raise HTTPException(status_code=404, detail="アンケートが見つかりません")
        # フロントエンドが期待する形式に合わせる
        return {"survey": survey}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"アンケート取得エラー: {str(e)}")


@router.put("/{survey_id}", response_model=Dict[str, Any])
def update_survey(survey_id: str, update_data: SurveyUpdateRequest):
    """アンケート更新"""
    try:
        success = SurveyService.update_survey(survey_id, update_data)
        if not success:
            raise HTTPException(
                status_code=404, 
                detail="更新対象のアンケートが見つかりません"
            )
        
        # 更新されたアンケートを取得して返す
        updated_survey = SurveyService.get_survey_with_questions(survey_id)
        return {
            "result": "success",
            "message": "アンケートが更新されました",
            "survey": updated_survey
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"アンケート更新エラー: {str(e)}")


@router.delete("/{survey_id}", response_model=Dict[str, Any])
def delete_survey(survey_id: str):
    """アンケート削除（論理削除）"""
    try:
        success = SurveyService.delete_survey(survey_id)
        if not success:
            raise HTTPException(
                status_code=404, 
                detail="削除対象のアンケートが見つかりません"
            )
        
        return {
            "result": "success",
            "message": "アンケートが削除されました",
            "survey_id": survey_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"アンケート削除エラー: {str(e)}")


@router.post("/{survey_id}/responses", response_model=Dict[str, Any])
def submit_survey_response(survey_id: str, response_data: SurveyResponseRequest):
    """アンケート回答提出"""
    try:
        # パスパラメータのsurvey_idを使用
        response_data.survey_id = survey_id
        
        response_id = SurveyService.submit_survey_response(response_data)
        if not response_id:
            raise HTTPException(
                status_code=400, 
                detail="アンケート回答提出失敗（アンケートが存在しないか、無効な回答データです）"
            )
        
        return {
            "result": "success",
            "message": "アンケート回答が提出されました",
            "response_id": response_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"アンケート回答提出エラー: {str(e)}")


@router.get("/{survey_id}/responses", response_model=List[Dict[str, Any]])
def get_survey_responses(survey_id: str):
    """アンケート回答一覧取得"""
    try:
        responses = SurveyService.get_survey_responses(survey_id)
        return responses
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"アンケート回答取得エラー: {str(e)}")


@router.get("/{survey_id}/statistics", response_model=Dict[str, Any])
def get_survey_statistics(survey_id: str):
    """アンケート統計情報取得"""
    try:
        stats = SurveyService.get_survey_statistics(survey_id)
        if not stats:
            raise HTTPException(status_code=404, detail="アンケートが見つかりません")
        
        return {
            "result": "success",
            "statistics": stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"統計情報取得エラー: {str(e)}")


# イベント関連のアンケートエンドポイント
@router.get("/events/{event_id}/surveys", response_model=List[Dict[str, Any]])
def get_surveys_by_event(
    event_id: str, 
    is_active: Optional[bool] = Query(None, description="アクティブなアンケートのみ取得する場合はTrue")
):
    """イベントに紐づくアンケート一覧取得"""
    try:
        surveys = SurveyService.get_surveys_by_event(event_id, is_active)
        return surveys
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"イベントアンケート取得エラー: {str(e)}")


# フォーム表示用のエンドポイント（読み取り専用）
@router.get("/{survey_id}/form", response_model=Dict[str, Any])
def get_survey_form(survey_id: str):
    """アンケートフォーム表示用データ取得"""
    try:
        survey = SurveyService.get_survey_with_questions(survey_id)
        if not survey:
            raise HTTPException(status_code=404, detail="アンケートが見つかりません")
        
        if not survey.get('is_active', False):
            raise HTTPException(status_code=403, detail="このアンケートは現在利用できません")
        
        # フォーム表示に必要な情報のみを返す
        form_data = {
            "survey_id": survey["id"],
            "title": survey.get("title", ""),
            "description": survey.get("description", ""),
            "questions": []
        }
        
        for question in survey.get("questions", []):
            question_data = {
                "question_id": question["id"],
                "question_text": question["question_text"],
                "question_type": question["question_type"],
                "is_required": question.get("is_required", False),
                "options": []
            }
            
            # 選択肢がある場合は追加
            for option in question.get("options", []):
                question_data["options"].append({
                    "option_id": option["id"],
                    "option_text": option["option_text"]
                })
            
            form_data["questions"].append(question_data)
        
        return {"survey": form_data}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"アンケートフォーム取得エラー: {str(e)}")