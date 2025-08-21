"""
違反報告関連のビジネスロジック
"""
from typing import List, Dict, Optional, Any
from datetime import datetime

from models.requests import ViolationReportRequest, HideCocktailRequest
from utils.validation import get_client_ip
from db import database as dbmodule


class ViolationService:
    """違反報告サービス"""
    
    @staticmethod
    def report_violation(report_data: ViolationReportRequest, reporter_ip: str) -> bool:
        """違反報告提出"""
        try:
            print(f"[DEBUG] 違反報告開始 - order_id: {report_data.order_id}, ip: {reporter_ip}")
            
            # 注文番号からカクテル情報を取得
            cocktail = dbmodule.get_cocktail_by_order_id(report_data.order_id)
            if not cocktail:
                print(f"[ERROR] 指定された注文番号のカクテルが見つかりません: {report_data.order_id}")
                return False
            
            cocktail_id = cocktail.get('id')
            if not cocktail_id:
                print(f"[ERROR] カクテルのIDが取得できません: {report_data.order_id}")
                return False
            
            print(f"[DEBUG] 注文番号 {report_data.order_id} → カクテルID {cocktail_id}")
            
            # 重複報告チェック
            existing_report = dbmodule.get_violation_report_by_cocktail_and_reporter(
                cocktail_id, reporter_ip
            )
            if existing_report:
                print(f"[WARNING] 同じIPからの重複報告: {reporter_ip}")
                return False
            
            # 違反報告を保存
            success = dbmodule.report_violation(
                cocktail_id,
                reporter_ip,
                report_data.report_reason,
                report_data.report_category
            )
            
            if success:
                print(f"[DEBUG] 違反報告提出成功")
                
                # 違反報告数に応じた自動処理
                violation_count = dbmodule.get_violation_reports_count(cocktail_id)
                print(f"[DEBUG] カクテルの違反報告数: {violation_count}")
                
                # 閾値を超えた場合の自動非表示処理
                auto_hide_threshold = 1  # 1件の報告で自動非表示
                if violation_count >= auto_hide_threshold:
                    hide_reason = f"違反報告により自動非表示（報告数: {violation_count}）"
                    ViolationService.hide_cocktail_by_id(cocktail_id, hide_reason)
                
                return True
            else:
                print(f"[ERROR] 違反報告提出失敗")
                return False
                
        except Exception as e:
            print(f"[ERROR] 違反報告エラー: {e}")
            return False
    
    @staticmethod
    def hide_cocktail_by_id(cocktail_id: int, reason: str) -> bool:
        """カクテルを非表示にする（内部ID使用）"""
        try:
            print(f"[DEBUG] カクテル非表示処理開始（ID使用): {cocktail_id}")
            
            # カクテル存在確認
            cocktail = dbmodule.get_cocktail_by_id(cocktail_id)
            if not cocktail:
                print(f"[ERROR] 指定されたカクテルが見つかりません（ID）: {cocktail_id}")
                return False
            
            # 既に非表示の場合はスキップ
            if not cocktail.get('is_visible', True):
                print(f"[INFO] カクテルは既に非表示です（ID）: {cocktail_id}")
                return True
            
            # 非表示処理
            success = dbmodule.hide_cocktail(cocktail_id, reason)
            
            if success:
                print(f"[DEBUG] カクテル非表示完了（ID）: {cocktail_id}")
                return True
            else:
                print(f"[ERROR] カクテル非表示失敗（ID）: {cocktail_id}")
                return False
                
        except Exception as e:
            print(f"[ERROR] カクテル非表示エラー（ID）: {e}")
            return False
    
    @staticmethod
    def hide_cocktail(order_id: str, reason: str) -> bool:
        """カクテルを非表示にする（注文番号使用）"""
        try:
            print(f"[DEBUG] カクテル非表示処理開始: {order_id}")
            
            # 注文番号からカクテル情報を取得
            cocktail = dbmodule.get_cocktail_by_order_id(order_id)
            if not cocktail:
                print(f"[ERROR] 指定された注文番号のカクテルが見つかりません: {order_id}")
                return False
            
            cocktail_id = cocktail.get('id')
            if not cocktail_id:
                print(f"[ERROR] カクテルのIDが取得できません: {order_id}")
                return False
            
            # 既に非表示の場合はスキップ
            if not cocktail.get('is_visible', True):
                print(f"[INFO] カクテルは既に非表示です: {order_id}")
                return True
            
            # 非表示処理
            success = dbmodule.hide_cocktail(cocktail_id, reason)
            
            if success:
                print(f"[DEBUG] カクテル非表示完了: {order_id}")
                return True
            else:
                print(f"[ERROR] カクテル非表示失敗: {order_id}")
                return False
                
        except Exception as e:
            print(f"[ERROR] カクテル非表示エラー: {e}")
            return False
    
    @staticmethod
    def show_cocktail(order_id: str) -> bool:
        """カクテルを再表示する（注文番号使用）"""
        try:
            print(f"[DEBUG] カクテル再表示処理開始: {order_id}")
            
            # 注文番号からカクテル情報を取得
            cocktail = dbmodule.get_cocktail_by_order_id(order_id)
            if not cocktail:
                print(f"[ERROR] 指定された注文番号のカクテルが見つかりません: {order_id}")
                return False
            
            cocktail_id = cocktail.get('id')
            if not cocktail_id:
                print(f"[ERROR] カクテルのIDが取得できません: {order_id}")
                return False
            
            # 既に表示中の場合はスキップ
            if cocktail.get('is_visible', True):
                print(f"[INFO] カクテルは既に表示中です: {order_id}")
                return True
            
            # 再表示処理
            success = dbmodule.show_cocktail(cocktail_id)
            
            if success:
                print(f"[DEBUG] カクテル再表示完了: {order_id}")
                return True
            else:
                print(f"[ERROR] カクテル再表示失敗: {order_id}")
                return False
                
        except Exception as e:
            print(f"[ERROR] カクテル再表示エラー: {e}")
            return False
    
    @staticmethod
    def get_violation_reports(
        cocktail_id: Optional[int] = None,
        status_filter: Optional[str] = None,
        show_all: bool = False
    ) -> List[Dict[str, Any]]:
        """違反報告一覧取得"""
        try:
            print(f"[DEBUG] 違反報告取得開始 - cocktail_id: {cocktail_id}, status: {status_filter}, show_all: {show_all}")
            
            reports = dbmodule.get_violation_reports(cocktail_id, status_filter, show_all)
            print(f"[DEBUG] 違反報告取得完了: {len(reports)}件")
            return reports
            
        except Exception as e:
            print(f"[ERROR] 違反報告取得エラー: {e}")
            return []
    
    @staticmethod
    def update_violation_report_status(report_id: int, status: str) -> bool:
        """違反報告ステータス更新"""
        try:
            print(f"[DEBUG] 違反報告ステータス更新開始 - report_id: {report_id}, status: {status}")
            
            # 有効なステータスかチェック
            valid_statuses = ['pending', 'reviewing', 'resolved', 'rejected']
            if status not in valid_statuses:
                print(f"[ERROR] 無効なステータス: {status}")
                return False
            
            # 報告存在確認
            report = dbmodule.get_violation_report_by_id(report_id)
            if not report:
                print(f"[ERROR] 指定された違反報告が見つかりません: {report_id}")
                return False
            
            # ステータス更新
            success = dbmodule.update_violation_report_status(report_id, status)
            
            if success:
                print(f"[DEBUG] 違反報告ステータス更新完了: {report_id}")
                
                # ステータスに応じた追加処理
                cocktail_id = report.get('cocktail_id')
                if cocktail_id:
                    # カクテルIDから注文番号を取得
                    cocktail = dbmodule.get_cocktail_by_id(cocktail_id)
                    if cocktail and cocktail.get('order_id'):
                        order_id = cocktail.get('order_id')
                        if status == 'resolved':
                            # 解決済みの場合、カクテルを非表示にする
                            ViolationService.hide_cocktail(order_id, f"違反報告解決により非表示（報告ID: {report_id}）")
                        elif status == 'rejected':
                            # 却下された場合、カクテルを再表示する
                            ViolationService.show_cocktail(order_id)
                
                return True
            else:
                print(f"[ERROR] 違反報告ステータス更新失敗: {report_id}")
                return False
                
        except Exception as e:
            print(f"[ERROR] 違反報告ステータス更新エラー: {e}")
            return False
    
    @staticmethod
    def get_violation_statistics() -> Dict[str, Any]:
        """違反報告統計情報取得"""
        try:
            print("[DEBUG] 違反報告統計取得開始")
            
            # 全違反報告を取得
            all_reports = dbmodule.get_violation_reports(show_all=True)
            
            # ステータス別集計
            status_counts = {
                'pending': 0,
                'reviewing': 0,
                'resolved': 0,
                'rejected': 0
            }
            
            category_counts = {}
            cocktail_violation_counts = {}
            
            for report in all_reports:
                # ステータス集計
                status = report.get('status', 'pending')
                if status in status_counts:
                    status_counts[status] += 1
                
                # カテゴリ集計
                category = report.get('report_category', 'other')
                category_counts[category] = category_counts.get(category, 0) + 1
                
                # カクテル別違反数集計
                cocktail_id = report.get('cocktail_id')
                if cocktail_id:
                    cocktail_violation_counts[cocktail_id] = cocktail_violation_counts.get(cocktail_id, 0) + 1
            
            # 非表示カクテル数
            try:
                hidden_cocktails_count = dbmodule.get_hidden_cocktails_count()
            except AttributeError:
                hidden_cocktails_count = 0
            
            stats = {
                'total_reports': len(all_reports),
                'status_breakdown': status_counts,
                'category_breakdown': category_counts,
                'hidden_cocktails_count': hidden_cocktails_count,
                'most_reported_cocktails': [
                    {'cocktail_id': k, 'report_count': v}
                    for k, v in sorted(cocktail_violation_counts.items(), key=lambda x: x[1], reverse=True)[:10]
                ],
                'generated_at': datetime.now().isoformat()
            }
            
            print("[DEBUG] 違反報告統計取得完了")
            return stats
            
        except Exception as e:
            print(f"[ERROR] 違反報告統計取得エラー: {e}")
            return {}