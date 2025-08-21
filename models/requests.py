"""
API リクエスト・レスポンスモデル定義
"""
from pydantic import BaseModel
from typing import Union, Optional, List, Dict, Any, Literal
from datetime import datetime


# カクテル関連モデル
class SaveCocktailRequest(BaseModel):
    order_id: str
    status: int = 200
    name: str
    comment: str
    recent_event: str = ""
    event_name: str = ""
    user_name: str = ""
    career: str = ""
    hobby: str = ""


class OrderRequest(BaseModel):
    order_id: Union[int, str]


class DeriveryRequest(BaseModel):
    poured: Union[int, str]
    name: str
    flavor_name1: str
    flavor_ratio1: str
    flavor_name2: str
    flavor_ratio2: str
    flavor_name3: str
    flavor_ratio3: str
    flavor_name4: str
    flavor_ratio4: str
    comment: str


class RecipeItem(BaseModel):
    syrup: str
    ratio: str


class CreateCocktailRequest(BaseModel):
    recent_event: str
    event_name: str = ""
    name: str
    career: str
    hobby: str
    prompt: str = "カジュアルで親しみやすい印象"
    save_user_info: bool = True
    recipe_prompt_id: Optional[str] = None
    image_prompt_id: Optional[str] = None
    event_id: Optional[str] = None
    survey_responses: Optional[List[Dict[str, Any]]] = None


class CreateCocktailAnonymousRequest(BaseModel):
    recent_event: str
    event_name: str = ""
    career: str
    hobby: str
    prompt: str = "カジュアルで親しみやすい印象"
    recipe_prompt_id: Optional[str] = None
    image_prompt_id: Optional[str] = None
    event_id: Optional[str] = None
    survey_responses: Optional[List[Dict[str, Any]]] = None


class CreateCocktailResponse(BaseModel):
    result: str
    id: str = ""  # カクテルのUUID
    order_id: str = ""  # 6桁の注文番号
    cocktail_name: str = ""
    concept: str = ""
    color: Union[str, dict] = ""
    recipe: List[RecipeItem] = []
    image_base64: str = ""
    image_url: str = ""
    detail: str = ""
    requires_copyright_confirmation: bool = True  # 著作権確認が必要かどうか（常にTrue）


# プロンプト関連モデル
class PromptRequest(BaseModel):
    name: str
    prompt_text: str
    prompt_type: Literal["recipe", "image"]
    is_active: bool = True
    description: Optional[str] = None


# イベント関連モデル
class EventRequest(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True


class QuestionOption(BaseModel):
    option_text: str
    order_index: int = 0


class SurveyQuestion(BaseModel):
    question_text: str
    question_type: Literal["text", "multiple_choice", "single_choice"]
    is_required: bool = True
    options: Optional[List[QuestionOption]] = None
    order_index: int = 0


class SurveyRequest(BaseModel):
    event_id: str
    title: str
    description: Optional[str] = None
    is_active: bool = True
    questions: List[SurveyQuestion]


class SurveyUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    questions: Optional[List[SurveyQuestion]] = None


class AnswerData(BaseModel):
    question_id: str
    answer_text: Optional[str] = None
    selected_option_ids: Optional[List[str]] = None


class SurveyResponseRequest(BaseModel):
    survey_id: str
    cocktail_id: Optional[str] = None  # UUID文字列に変更
    answers: List[AnswerData]


# 違反報告関連モデル
class ViolationReportRequest(BaseModel):
    order_id: str  # 外部API互換性のため6桁の注文番号を維持
    report_reason: str
    report_category: str = "inappropriate"


class ViolationReportUuidRequest(BaseModel):
    cocktail_id: str  # 内部処理用UUID
    report_reason: str
    report_category: str = "inappropriate"


class HideCocktailRequest(BaseModel):
    order_id: str  # 外部API互換性のため6桁の注文番号を維持
    reason: str


class HideCocktailUuidRequest(BaseModel):
    cocktail_id: str  # 内部処理用UUID
    reason: str


# 著作権確認関連モデル
class CopyrightConfirmationRequest(BaseModel):
    cocktail_id: str  # カクテルのUUID
    confirmed: bool = True  # 常にTrueを想定


class CopyrightConfirmationResponse(BaseModel):
    success: bool
    cocktail_id: str
    confirmed_at: Optional[str] = None  # ISO8601フォーマットの日時文字列
    message: str = ""


class CopyrightStatusResponse(BaseModel):
    cocktail_id: str
    copyright_confirmed: bool
    confirmed_at: Optional[str] = None  # ISO8601フォーマットの日時文字列