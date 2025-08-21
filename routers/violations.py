"""
違反報告関連APIルーター
"""
from fastapi import APIRouter, HTTPException, Request, Query
from typing import List, Dict, Any, Optional

from models.requests import ViolationReportRequest, HideCocktailRequest
from services.violation_service import ViolationService
from utils.validation import get_client_ip

router = APIRouter(prefix="/violations", tags=["violations"])


@router.post("/report-violation/", response_model=Dict[str, Any])
def report_violation(report_data: ViolationReportRequest, request: Request):
    """違反報告提出"""
    try:
        # IPアドレス取得
        client_ip = get_client_ip(request)
        print(f"[DEBUG] 違反報告リクエスト - order_id: {report_data.order_id}, client_ip: {client_ip}")
        
        success = ViolationService.report_violation(report_data, client_ip)
        if not success:
            raise HTTPException(
                status_code=400, 
                detail="違反報告に失敗しました（既に報告済みか、存在しない注文番号です）"
            )
        
        return {
            "result": "success",
            "message": "違反報告を受け付けました",
            "order_id": report_data.order_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"違反報告エラー: {str(e)}")


@router.post("/hide-cocktail/", response_model=Dict[str, Any])
def hide_cocktail(hide_data: HideCocktailRequest):
    """カクテル手動非表示"""
    try:
        success = ViolationService.hide_cocktail(hide_data.order_id, hide_data.reason)
        if not success:
            raise HTTPException(
                status_code=400, 
                detail="カクテル非表示に失敗しました（存在しない注文番号です）"
            )
        
        return {
            "result": "success",
            "message": "カクテルを非表示にしました",
            "order_id": hide_data.order_id,
            "reason": hide_data.reason
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"カクテル非表示エラー: {str(e)}")


@router.post("/show-cocktail/{order_id}", response_model=Dict[str, Any])
def show_cocktail(order_id: str):
    """カクテル再表示"""
    try:
        success = ViolationService.show_cocktail(order_id)
        if not success:
            raise HTTPException(
                status_code=400, 
                detail="カクテル再表示に失敗しました（存在しない注文番号です）"
            )
        
        return {
            "result": "success",
            "message": "カクテルを再表示しました",
            "order_id": order_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"カクテル再表示エラー: {str(e)}")


@router.get("/violation-reports/", response_model=List[Dict[str, Any]])
def get_violation_reports(
    cocktail_id: Optional[str] = Query(None, description="特定カクテルの報告のみ取得"),
    status: Optional[str] = Query(None, description="特定ステータスの報告のみ取得"),
    show_all: bool = Query(False, description="全ステータスの報告を取得")
):
    """違反報告一覧取得"""
    try:
        print(f"[DEBUG] 違反報告API呼び出し - cocktail_id: {cocktail_id}, status: {status}, show_all: {show_all}")
        
        reports = ViolationService.get_violation_reports(cocktail_id, status, show_all)
        
        print(f"[DEBUG] API戻り値: {len(reports)}件の報告")
        return reports
        
    except Exception as e:
        print(f"[ERROR] 違反報告API取得エラー: {e}")
        raise HTTPException(status_code=500, detail=f"違反報告取得エラー: {str(e)}")


@router.put("/violation-reports/{report_id}/status", response_model=Dict[str, Any])
def update_violation_report_status(report_id: int, status_data: dict):
    """違反報告ステータス更新"""
    try:
        status = status_data.get('status')
        if not status:
            raise HTTPException(status_code=400, detail="ステータスが指定されていません")
        
        success = ViolationService.update_violation_report_status(report_id, status)
        if not success:
            raise HTTPException(
                status_code=404, 
                detail="指定された違反報告が見つからないか、無効なステータスです"
            )
        
        return {
            "result": "success",
            "message": f"違反報告ステータスを'{status}'に更新しました",
            "report_id": report_id,
            "status": status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ステータス更新エラー: {str(e)}")


@router.get("/statistics", response_model=Dict[str, Any])
def get_violation_statistics():
    """違反報告統計情報取得"""
    try:
        stats = ViolationService.get_violation_statistics()
        return {
            "result": "success",
            "statistics": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"統計情報取得エラー: {str(e)}")


# 管理者向けエンドポイント
@router.get("/reports/pending", response_model=List[Dict[str, Any]])
def get_pending_reports():
    """未処理の違反報告取得（管理者向け）"""
    try:
        reports = ViolationService.get_violation_reports(status_filter='pending')
        return reports
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"未処理報告取得エラー: {str(e)}")


@router.get("/reports/reviewing", response_model=List[Dict[str, Any]])
def get_reviewing_reports():
    """確認中の違反報告取得（管理者向け）"""
    try:
        reports = ViolationService.get_violation_reports(status_filter='reviewing')
        return reports
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"確認中報告取得エラー: {str(e)}")


@router.post("/batch-update", response_model=Dict[str, Any])
def batch_update_reports(update_data: Dict[str, Any]):
    """複数の違反報告を一括更新（管理者向け）"""
    try:
        report_ids = update_data.get('report_ids', [])
        status = update_data.get('status')
        
        if not report_ids or not status:
            raise HTTPException(
                status_code=400, 
                detail="report_idsとstatusが必要です"
            )
        
        success_count = 0
        failure_count = 0
        
        for report_id in report_ids:
            try:
                success = ViolationService.update_violation_report_status(report_id, status)
                if success:
                    success_count += 1
                else:
                    failure_count += 1
            except Exception:
                failure_count += 1
        
        return {
            "result": "completed",
            "message": f"一括更新完了: 成功{success_count}件、失敗{failure_count}件",
            "success_count": success_count,
            "failure_count": failure_count,
            "total_count": len(report_ids)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"一括更新エラー: {str(e)}")