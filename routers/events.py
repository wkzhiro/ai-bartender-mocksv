"""
イベント関連APIルーター
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional

from models.requests import EventRequest, SurveyRequest
from services.event_service import EventService
from services.survey_service import SurveyService

router = APIRouter(prefix="/events", tags=["events"])


@router.get("/", response_model=Dict[str, Any])
def get_events(is_active: Optional[bool] = Query(None)):
    """全イベント取得（is_activeパラメータ対応）"""
    try:
        if is_active is not None:
            # is_activeが指定された場合はアクティブイベントのみ
            events = EventService.get_active_events() if is_active else EventService.get_all_events()
        else:
            # パラメータが未指定の場合は全イベント
            events = EventService.get_all_events()
        
        # フロントエンドが期待する形式に合わせる
        return {"events": events}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"イベント取得エラー: {str(e)}")


@router.get("/active", response_model=Dict[str, Any])
def get_active_events():
    """アクティブなイベントのみ取得"""
    try:
        events = EventService.get_active_events()
        # フロントエンドが期待する形式に合わせる
        return {"events": events}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"アクティブイベント取得エラー: {str(e)}")


@router.get("/{event_id}", response_model=Dict[str, Any])
def get_event(event_id: str):
    """特定イベント取得"""
    try:
        event = EventService.get_event_by_id(event_id)
        if not event:
            raise HTTPException(status_code=404, detail="イベントが見つかりません")
        # フロントエンドが期待する形式に合わせる
        return {"event": event}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"イベント取得エラー: {str(e)}")


@router.post("/", response_model=Dict[str, Any])
def create_event(event_data: EventRequest):
    """新規イベント作成"""
    try:
        event_id = EventService.create_event(event_data)
        if not event_id:
            raise HTTPException(
                status_code=400, 
                detail="イベント作成失敗（同名のイベントが既に存在する可能性があります）"
            )
        
        # 作成されたイベントを取得して返す
        created_event = EventService.get_event_by_id(event_id)
        if created_event:
            return {
                "result": "success",
                "message": "イベントが作成されました",
                "event": created_event
            }
        else:
            return {
                "result": "success",
                "message": "イベントが作成されました",
                "event_id": event_id
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"イベント作成エラー: {str(e)}")


@router.put("/{event_id}", response_model=Dict[str, Any])
def update_event(event_id: str, event_data: EventRequest):
    """イベント更新"""
    try:
        success = EventService.update_event(event_id, event_data)
        if not success:
            raise HTTPException(
                status_code=404, 
                detail="更新対象のイベントが見つかりません"
            )
        
        # 更新されたイベントを取得して返す
        updated_event = EventService.get_event_by_id(event_id)
        return {
            "result": "success",
            "message": "イベントが更新されました",
            "event": updated_event
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"イベント更新エラー: {str(e)}")


@router.delete("/{event_id}", response_model=Dict[str, Any])
def delete_event(event_id: str):
    """イベント削除（論理削除）"""
    try:
        success = EventService.delete_event(event_id)
        if not success:
            raise HTTPException(
                status_code=404, 
                detail="削除対象のイベントが見つかりません"
            )
        
        return {
            "result": "success",
            "message": "イベントが削除されました",
            "event_id": event_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"イベント削除エラー: {str(e)}")


@router.get("/{event_id}/surveys/", response_model=Dict[str, Any])
def get_surveys_by_event(event_id: str, is_active: Optional[bool] = Query(None)):
    """イベントに紐づくアンケート一覧取得"""
    try:
        # イベント存在確認
        event = EventService.get_event_by_id(event_id)
        if not event:
            raise HTTPException(status_code=404, detail="イベントが見つかりません")
        
        # アンケート取得
        surveys = SurveyService.get_surveys_by_event(event_id, is_active)
        return {"surveys": surveys}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"アンケート取得エラー: {str(e)}")

@router.post("/{event_id}/surveys/", response_model=Dict[str, Any])
def create_survey_for_event(event_id: str, survey_data: SurveyRequest):
    """イベントのアンケートを作成（質問含む）"""
    try:
        # イベント存在確認
        event = EventService.get_event_by_id(event_id)
        if not event:
            raise HTTPException(status_code=404, detail="イベントが見つかりません")
        
        # アンケート基本情報
        survey_data_dict = {
            'event_id': event_id,
            'title': survey_data.title,
            'description': survey_data.description,
            'is_active': survey_data.is_active
            # start_date、end_dateは現在サポートしていないため除外
        }
        
        # 質問データの準備
        questions_data = []
        for question in survey_data.questions:
            question_data = {
                'question_type': question.question_type,
                'question_text': question.question_text,
                'is_required': question.is_required,
                'display_order': question.order_index  # バックエンドモデルのフィールド名を使用
            }
            
            # 選択肢がある場合
            if question.options:
                question_data['options'] = [
                    {
                        'option_text': opt.option_text,
                        'display_order': opt.order_index  # バックエンドモデルのフィールド名を使用
                    }
                    for opt in question.options
                ]
            
            questions_data.append(question_data)
        
        survey_id = SurveyService.create_survey_with_questions(survey_data_dict, questions_data)
        if not survey_id:
            raise HTTPException(status_code=500, detail="アンケートの作成に失敗しました")
        
        return {"result": "success", "survey_id": survey_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"アンケート作成エラー: {str(e)}")


@router.get("/{event_id}/statistics", response_model=Dict[str, Any])
def get_event_statistics(event_id: str):
    """イベント統計情報取得"""
    try:
        stats = EventService.get_event_statistics(event_id)
        if not stats:
            raise HTTPException(status_code=404, detail="イベントが見つかりません")
        
        return {
            "result": "success",
            "statistics": stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"統計情報取得エラー: {str(e)}")