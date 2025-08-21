"""
アンケート管理関連のビジネスロジック
"""
from typing import List, Dict, Optional, Any
from datetime import datetime

from models.requests import SurveyRequest, SurveyUpdateRequest, SurveyResponseRequest
from utils.validation import validate_survey_response
from db import database as dbmodule


class SurveyService:
    """アンケート管理サービス"""
    
    @staticmethod
    def create_survey(survey_data: SurveyRequest) -> Optional[str]:
        """新規アンケート作成"""
        try:
            print(f"[DEBUG] アンケート作成開始: {survey_data.title}")
            
            # イベント存在確認
            event = dbmodule.get_event_by_id(survey_data.event_id)
            if not event:
                print(f"[ERROR] 指定されたイベントが見つかりません: {survey_data.event_id}")
                return None
            
            # アンケートデータ準備
            survey_db_data = {
                'event_id': survey_data.event_id,
                'title': survey_data.title,
                'description': survey_data.description,
                'is_active': survey_data.is_active
            }
            
            # アンケート作成
            survey_id = dbmodule.create_survey(survey_db_data)
            if not survey_id:
                print("[ERROR] アンケート作成失敗")
                return None
            
            # 質問作成
            for question in survey_data.questions:
                question_data = {
                    'survey_id': survey_id,
                    'question_text': question.question_text,
                    'question_type': question.question_type,
                    'is_required': question.is_required,
                    'order_index': question.order_index
                }
                
                question_id = dbmodule.create_survey_question(question_data)
                if not question_id:
                    print(f"[ERROR] 質問作成失敗: {question.question_text}")
                    continue
                
                # 選択肢作成（multiple_choice または single_choice の場合）
                if question.options and question.question_type in ['multiple_choice', 'single_choice']:
                    for option in question.options:
                        option_data = {
                            'question_id': question_id,
                            'option_text': option.option_text,
                            'order_index': option.order_index
                        }
                        
                        option_id = dbmodule.create_question_option(option_data)
                        if not option_id:
                            print(f"[ERROR] 選択肢作成失敗: {option.option_text}")
            
            print(f"[DEBUG] アンケート作成完了: {survey_id}")
            return survey_id
            
        except Exception as e:
            print(f"[ERROR] アンケート作成エラー: {e}")
            return None
    
    @staticmethod
    def get_surveys_by_event(event_id: str, is_active: Optional[bool] = None) -> List[Dict[str, Any]]:
        """イベントに紐づくアンケート取得"""
        try:
            print(f"[DEBUG] イベントアンケート取得開始: {event_id}")
            surveys = dbmodule.get_surveys_by_event(event_id, is_active)
            print(f"[DEBUG] アンケート取得完了: {len(surveys)}件")
            return surveys
        except Exception as e:
            print(f"[ERROR] アンケート取得エラー: {e}")
            return []
    
    @staticmethod
    def get_survey_with_questions(survey_id: str) -> Optional[Dict[str, Any]]:
        """アンケートを質問と選択肢込みで取得"""
        try:
            print(f"[DEBUG] 詳細アンケート取得開始: {survey_id}")
            survey = dbmodule.get_survey_with_questions(survey_id)
            if survey:
                print(f"[DEBUG] アンケート取得成功: {survey.get('title', 'Unknown')}")
            else:
                print(f"[DEBUG] アンケートが見つかりません: {survey_id}")
            return survey
        except Exception as e:
            print(f"[ERROR] アンケート取得エラー: {e}")
            return None
    
    @staticmethod
    def update_survey(survey_id: str, update_data: SurveyUpdateRequest) -> bool:
        """アンケート更新"""
        try:
            print(f"[DEBUG] アンケート更新開始: {survey_id}")
            
            # 既存アンケート確認
            existing_survey = dbmodule.get_survey_with_questions(survey_id)
            if not existing_survey:
                print(f"[WARNING] 更新対象アンケートが見つかりません: {survey_id}")
                return False
            
            # 基本情報の更新
            survey_updates = {}
            if update_data.title is not None:
                survey_updates['title'] = update_data.title
            if update_data.description is not None:
                survey_updates['description'] = update_data.description
            if update_data.is_active is not None:
                survey_updates['is_active'] = update_data.is_active
            
            if survey_updates:
                survey_updates['updated_at'] = datetime.now().isoformat()
                success = dbmodule.update_survey(survey_id, survey_updates)
                if not success:
                    print(f"[ERROR] アンケート基本情報更新失敗: {survey_id}")
                    return False
            
            # 質問の更新（提供されている場合）
            if update_data.questions is not None:
                # 既存の質問を削除
                dbmodule.delete_survey_questions(survey_id)
                
                # 新しい質問を作成
                for question in update_data.questions:
                    question_data = {
                        'survey_id': survey_id,
                        'question_text': question.question_text,
                        'question_type': question.question_type,
                        'is_required': question.is_required,
                        'order_index': question.order_index
                    }
                    
                    question_id = dbmodule.create_survey_question(question_data)
                    if question_id and question.options:
                        for option in question.options:
                            option_data = {
                                'question_id': question_id,
                                'option_text': option.option_text,
                                'order_index': option.order_index
                            }
                            dbmodule.create_question_option(option_data)
            
            print(f"[DEBUG] アンケート更新完了: {survey_id}")
            return True
            
        except Exception as e:
            print(f"[ERROR] アンケート更新エラー: {e}")
            return False
    
    @staticmethod
    def delete_survey(survey_id: str) -> bool:
        """アンケート削除（論理削除）"""
        try:
            print(f"[DEBUG] アンケート削除開始: {survey_id}")
            
            # 既存アンケート確認
            existing_survey = dbmodule.get_survey_with_questions(survey_id)
            if not existing_survey:
                print(f"[WARNING] 削除対象アンケートが見つかりません: {survey_id}")
                return False
            
            # 論理削除（is_activeをFalseに）
            update_data = {
                'is_active': False,
                'updated_at': datetime.now().isoformat()
            }
            
            success = dbmodule.update_survey(survey_id, update_data)
            if success:
                print(f"[DEBUG] アンケート削除完了: {survey_id}")
                return True
            else:
                print(f"[ERROR] アンケート削除失敗: {survey_id}")
                return False
                
        except Exception as e:
            print(f"[ERROR] アンケート削除エラー: {e}")
            return False
    
    @staticmethod
    def submit_survey_response(response_data: SurveyResponseRequest) -> Optional[str]:
        """アンケート回答提出"""
        try:
            print(f"[DEBUG] アンケート回答提出開始: {response_data.survey_id}")
            
            # アンケート存在確認
            survey = dbmodule.get_survey_with_questions(response_data.survey_id)
            if not survey:
                print(f"[ERROR] 指定されたアンケートが見つかりません: {response_data.survey_id}")
                return None
            
            if not survey.get('is_active', False):
                print(f"[ERROR] 指定されたアンケートは非アクティブです: {response_data.survey_id}")
                return None
            
            # 回答データの検証
            validated_answers = []
            for answer in response_data.answers:
                if validate_survey_response(answer.dict()):
                    validated_answers.append({
                        'question_id': answer.question_id,
                        'answer_text': answer.answer_text,
                        'selected_option_ids': answer.selected_option_ids or []
                    })
                else:
                    print(f"[WARNING] 無効な回答データをスキップ: {answer.question_id}")
            
            if not validated_answers:
                print("[ERROR] 有効な回答データがありません")
                return None
            
            # DB保存
            response_id = dbmodule.submit_survey_response(
                response_data.survey_id, 
                response_data.cocktail_id, 
                validated_answers
            )
            
            if response_id:
                print(f"[DEBUG] アンケート回答提出完了: {response_id}")
                return response_id
            else:
                print("[ERROR] アンケート回答提出失敗")
                return None
                
        except Exception as e:
            print(f"[ERROR] アンケート回答提出エラー: {e}")
            return None
    
    @staticmethod
    def get_survey_responses(survey_id: str) -> List[Dict[str, Any]]:
        """アンケート回答一覧取得"""
        try:
            print(f"[DEBUG] アンケート回答取得開始: {survey_id}")
            responses = dbmodule.get_survey_responses(survey_id)
            print(f"[DEBUG] アンケート回答取得完了: {len(responses)}件")
            return responses
        except Exception as e:
            print(f"[ERROR] アンケート回答取得エラー: {e}")
            return []
    
    @staticmethod
    def get_survey_statistics(survey_id: str) -> Dict[str, Any]:
        """アンケート統計情報取得"""
        try:
            print(f"[DEBUG] アンケート統計取得開始: {survey_id}")
            
            # アンケート基本情報
            survey = dbmodule.get_survey_with_questions(survey_id)
            if not survey:
                return {}
            
            # 回答取得
            responses = dbmodule.get_survey_responses(survey_id)
            
            # 統計情報構築
            stats = {
                'survey_id': survey_id,
                'survey_title': survey.get('title', ''),
                'total_responses': len(responses),
                'questions_count': len(survey.get('questions', [])),
                'is_active': survey.get('is_active', False),
                'created_at': survey.get('created_at', ''),
                'question_stats': []
            }
            
            # 質問別統計
            for question in survey.get('questions', []):
                question_stats = {
                    'question_id': question['id'],
                    'question_text': question['question_text'],
                    'question_type': question['question_type'],
                    'responses_count': 0,
                    'answers': []
                }
                
                # この質問に対する回答を集計
                question_responses = []
                for response in responses:
                    for answer in response.get('answers', []):
                        if answer.get('question_id') == question['id']:
                            question_responses.append(answer)
                
                question_stats['responses_count'] = len(question_responses)
                
                # 回答内容の集計
                if question['question_type'] == 'text':
                    # テキスト回答の一覧
                    text_answers = [
                        ans.get('answer_text', '') 
                        for ans in question_responses 
                        if ans.get('answer_text')
                    ]
                    question_stats['answers'] = text_answers
                else:
                    # 選択肢回答の集計
                    option_counts = {}
                    for ans in question_responses:
                        selected_ids = ans.get('selected_option_ids', [])
                        for option_id in selected_ids:
                            option_counts[option_id] = option_counts.get(option_id, 0) + 1
                    
                    # 選択肢名と回答数
                    option_stats = []
                    for option in question.get('options', []):
                        option_stats.append({
                            'option_id': option['id'],
                            'option_text': option['option_text'],
                            'count': option_counts.get(option['id'], 0)
                        })
                    question_stats['answers'] = option_stats
                
                stats['question_stats'].append(question_stats)
            
            print(f"[DEBUG] アンケート統計取得完了: {survey_id}")
            return stats
            
        except Exception as e:
            print(f"[ERROR] アンケート統計取得エラー: {e}")
            return {}

    @staticmethod
    def create_survey_with_questions(survey_data: Dict[str, Any], questions_data: List[Dict[str, Any]]) -> Optional[str]:
        """アンケートと質問を同時に作成"""
        try:
            print(f"[DEBUG] アンケート作成開始（質問付き）: {survey_data.get('title')}")
            survey_id = dbmodule.create_survey_with_questions(survey_data, questions_data)
            print(f"[DEBUG] アンケート作成完了（質問付き）: {survey_id}")
            return survey_id
        except Exception as e:
            print(f"[ERROR] アンケート作成エラー（質問付き）: {e}")
            return None
