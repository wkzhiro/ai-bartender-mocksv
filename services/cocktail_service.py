"""
カクテル生成関連のビジネスロジック
"""
import uuid
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime

from models.requests import CreateCocktailRequest, CreateCocktailResponse, RecipeItem
from config.settings import settings
from utils.text_utils import (
    load_syrup_info_txt, load_fusion_filter_words, validate_cocktail_name,
    build_recipe_system_prompt, extract_json_from_text, generate_order_id,
    regenerate_cocktail_name_with_mini_llm, regenerate_name_with_alternative_prompt
)
from utils.image_utils import crop_and_resize_base64_image, upload_image_to_storage
from db import database as dbmodule


class CocktailService:
    """カクテル生成サービス"""
    
    @staticmethod
    async def create_cocktail(
        req: CreateCocktailRequest, 
        save_user_info: bool = True, 
        use_storage: bool = True
    ) -> CreateCocktailResponse:
        """カクテル作成メイン処理"""
        try:
            print(f"[DEBUG] カクテル作成開始 - event_id: {req.event_id}")
            
            # 1. イベント処理
            event_id = await CocktailService._handle_event(req)
            
            # 2. レシピ生成
            recipe_data = await CocktailService._generate_recipe(req, event_id)
            if recipe_data["result"] != "success":
                return CreateCocktailResponse(result="error", detail=recipe_data["detail"])
            
            # 3. 注文IDとUUID生成
            order_id = generate_order_id()
            if not order_id:
                return CreateCocktailResponse(result="error", detail="注文番号の生成に失敗しました")
            
            # カクテル用のUUIDを生成
            cocktail_uuid = str(uuid.uuid4())
            print(f"[DEBUG] 生成されたUUID: {cocktail_uuid}")
            
            # 4. 画像生成（UUIDを使用）
            image_data = await CocktailService._generate_image(
                recipe_data["data"], req, use_storage, cocktail_uuid
            )
            if image_data["result"] != "success":
                return CreateCocktailResponse(result="error", detail=image_data["detail"])
            
            # 5. データベース保存（UUIDを含む）
            db_result = await CocktailService._save_to_database(
                recipe_data["data"], image_data, order_id, req, 
                event_id, save_user_info, cocktail_uuid
            )
            if db_result["result"] != "success":
                return CreateCocktailResponse(result="error", detail=db_result["detail"])
            
            # 6. レスポンス作成
            response = CreateCocktailResponse(
                result="success",
                id=cocktail_uuid,  # UUIDを返すように修正
                order_id=str(order_id),  # 6桁の注文番号も含める
                cocktail_name=recipe_data["data"]["cocktail_name"],
                concept=recipe_data["data"]["concept"],
                color=recipe_data["data"]["color"],
                recipe=[RecipeItem(**item) for item in recipe_data["data"]["recipe"]],
                detail="",
                requires_copyright_confirmation=True  # 著作権確認が必要
            )
            
            # 画像データの設定
            if use_storage and "url" in image_data:
                response.image_url = image_data["url"]
                response.image_base64 = ""  # URLを使用する場合はbase64は空に
            else:
                response.image_base64 = image_data.get("image", "")
                response.image_url = ""
            
            return response
            
        except Exception as e:
            error_msg = f"カクテル作成処理で予期しないエラー: {str(e)}"
            print(f"[ERROR] {error_msg}")
            import traceback
            tb = traceback.format_exc()
            print(f"[ERROR] Traceback: {tb}")
            return CreateCocktailResponse(result="error", detail=f"{error_msg}\\n{tb}")
    
    @staticmethod
    async def _handle_event(req: CreateCocktailRequest) -> Optional[str]:
        """イベント関連処理"""
        event_id = req.event_id
        
        if not event_id and req.event_name:
            # event_nameからevent_idを取得、または新規作成
            existing_event = dbmodule.get_event_by_name(req.event_name)
            if existing_event:
                event_id = existing_event['id']
            else:
                # 新しいイベントを作成
                new_event_data = {
                    'name': req.event_name,
                    'description': f'自動生成されたイベント: {req.event_name}',
                    'is_active': True
                }
                event_id = dbmodule.insert_event(new_event_data)
        
        return event_id
    
    @staticmethod
    async def _generate_recipe(req: CreateCocktailRequest, event_id: Optional[str]) -> Dict[str, Any]:
        """レシピ生成処理"""
        try:
            print(f"[DEBUG] レシピ生成開始")
            
            # シロップ情報読み込み
            syrup_dict = load_syrup_info_txt()
            
            # プロンプト準備
            custom_recipe_prompt = None
            if req.recipe_prompt_id:
                prompt_data = dbmodule.get_prompt_by_id(req.recipe_prompt_id)
                if prompt_data and prompt_data['prompt_type'] == 'recipe':
                    custom_recipe_prompt = prompt_data['prompt_text']
            
            system_prompt = build_recipe_system_prompt(syrup_dict, custom_recipe_prompt)
            user_prompt = CocktailService._build_user_prompt(req, event_id)
            
            # OpenAI API呼び出し
            api_result = await CocktailService._call_openai_api(system_prompt, user_prompt)
            if api_result["result"] != "success":
                return api_result
            
            # JSON解析
            recipe_data = extract_json_from_text(api_result["content"])
            if not recipe_data:
                return {
                    "result": "error",
                    "detail": f"ChatGPT出力からJSON抽出失敗: {api_result['content'][:200]}"
                }
            
            # カクテル名の検証とフィルタリング
            cocktail_name = recipe_data.get("cocktail_name", "")
            filter_words = load_fusion_filter_words()
            
            print(f"[DEBUG] 初期カクテル名: '{cocktail_name}'")
            print(f"[DEBUG] フィルター単語数: {len(filter_words)}個")
            print(f"[DEBUG] 初期検証実行中...")
            
            initial_validation = validate_cocktail_name(cocktail_name, filter_words)
            print(f"[DEBUG] 初期検証結果: {initial_validation}")
            
            if not initial_validation:
                print(f"[WARNING] カクテル名「{cocktail_name}」がフィルタに引っかかりました")
                
                # まず既存の簡易的な再生成を試みる
                retry_success = False
                for retry in range(settings.MAX_NAME_RETRIES):
                    print(f"[DEBUG] 簡易再生成試行 {retry + 1}/{settings.MAX_NAME_RETRIES}")
                    new_name = regenerate_cocktail_name_with_mini_llm(recipe_data, filter_words)
                    print(f"[DEBUG] 簡易再生成結果: {new_name}")
                    if new_name and validate_cocktail_name(new_name, filter_words):
                        print(f"[DEBUG] 簡易再生成成功: {new_name}")
                        recipe_data["cocktail_name"] = new_name
                        retry_success = True
                        break
                    else:
                        print(f"[DEBUG] 簡易再生成失敗: {new_name} (検証結果: {validate_cocktail_name(new_name, filter_words) if new_name else 'None'})")
                
                if not retry_success:
                    # 簡易的な再生成に失敗した場合、別のプロンプト戦略で再生成
                    print(f"[INFO] 別のプロンプト戦略でカクテル名再生成を試みます")
                    new_name = regenerate_name_with_alternative_prompt(
                        recipe_data, filter_words, cocktail_name
                    )
                    if new_name:
                        print(f"[DEBUG] 別プロンプトで新しいカクテル名生成成功: {new_name}")
                        recipe_data["cocktail_name"] = new_name
                    else:
                        # それでも失敗した場合は、より創造的な汎用名を生成
                        print(f"[WARNING] 別プロンプトでも失敗しました。最終手段として創造的汎用名を生成します。")
                        timestamp = datetime.now().strftime("%H%M%S")
                        # 汎用名パターンを回避するために、創造的な最終案を生成
                        creative_fallback = f"今宵のインスピレーション{timestamp[-2:]}"
                        recipe_data["cocktail_name"] = creative_fallback
                        print(f"[WARNING] 全ての再生成失敗、創造的汎用名使用: {recipe_data['cocktail_name']}")
                else:
                    print(f"[INFO] 簡易再生成でカクテル名決定完了")
            else:
                print(f"[INFO] 初期カクテル名が検証を通過: {cocktail_name}")
            
            final_name = recipe_data.get('cocktail_name', 'Unknown')
            print(f"[DEBUG] レシピ生成完了 - 最終カクテル名: '{final_name}'")
            return {"result": "success", "data": recipe_data}
            
        except Exception as e:
            error_msg = f"レシピ生成エラー: {str(e)}"
            print(f"[ERROR] {error_msg}")
            return {"result": "error", "detail": error_msg}
    
    @staticmethod
    def _build_user_prompt(req: CreateCocktailRequest, event_id: Optional[str]) -> str:
        """ユーザープロンプトを構築"""
        # アンケート回答データを処理
        survey_info = ""
        if req.survey_responses and event_id:
            try:
                print(f"[DEBUG] アンケート情報処理開始")
                surveys = dbmodule.get_surveys_by_event(event_id, is_active=True)
                if surveys:
                    survey = dbmodule.get_survey_with_questions(surveys[0]['id'])
                    if survey and survey.get('questions'):
                        event_data = dbmodule.get_event_by_id(event_id)
                        event_name = event_data.get('name', req.event_name) if event_data else req.event_name
                        
                        survey_info = f"\\n【イベント: {event_name}】\\n"
                        survey_info += f"アンケート: {survey.get('title', '')}\\n"
                        if survey.get('description'):
                            survey_info += f"{survey['description']}\\n"
                        survey_info += "\\n【回答内容】\\n"
                        
                        # 質問IDと質問情報のマッピング
                        question_map = {q['id']: q for q in survey['questions']}
                        
                        # 回答を整形
                        for response in req.survey_responses:
                            question_id = response.get('question_id', '')
                            answer_text = response.get('answer_text', '')
                            selected_option_ids = response.get('selected_option_ids', [])
                            
                            if question_id in question_map:
                                question = question_map[question_id]
                                survey_info += f"\\n質問: {question['question_text']}\\n"
                                
                                if answer_text:
                                    survey_info += f"回答: {answer_text}\\n"
                                elif selected_option_ids and question.get('options'):
                                    selected_texts = [
                                        option['option_text'] 
                                        for option in question['options'] 
                                        if option['id'] in selected_option_ids
                                    ]
                                    if selected_texts:
                                        survey_info += f"回答: {', '.join(selected_texts)}\\n"
                print(f"[DEBUG] アンケート情報処理完了")
            except Exception as e:
                print(f"[ERROR] アンケート情報処理エラー: {e}")
                # エラー時は基本情報で続行
                survey_info = "\\n【アンケート回答】\\n"
                for i, response in enumerate(req.survey_responses, 1):
                    answer_text = response.get('answer_text', '')
                    if answer_text:
                        survey_info += f"回答{i}: {answer_text}\\n"
        
        # プロンプト構築
        if survey_info:
            return (
                f"{survey_info}\\n"
                f"上記のアンケート回答から、この方の個性、感情、体験を読み取り、"
                f"世界に一つだけの特別なカクテルを創造してください。"
            )
        else:
            # アンケートがない場合の従来のプロンプト
            event_name = req.event_name
            if event_id:
                event_data = dbmodule.get_event_by_id(event_id)
                if event_data:
                    event_name = event_data.get('name', req.event_name)
            
            return (
                f"イベント: {event_name}\\n"
                f"最近の出来事: {req.recent_event}\\n"
                f"キャリア: {req.career}\\n"
                f"趣味: {req.hobby}\\n\\n"
                f"上記の情報から、この方だけの特別なカクテルを創造してください。"
            )
    
    @staticmethod
    async def _call_openai_api(system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """OpenAI API呼び出し"""
        try:
            # API設定チェック
            api_key = settings.get_llm_api_key()
            endpoint_url = settings.get_llm_url()
            
            print(f"[DEBUG] OpenAI API設定確認 - api_key: {'設定済み' if api_key else '未設定'}")
            print(f"[DEBUG] AZURE_OPENAI_API_KEY_LLM: {'設定済み' if settings.AZURE_OPENAI_API_KEY_LLM else '未設定'}")
            print(f"[DEBUG] OPENAI_API_KEY: {'設定済み' if settings.OPENAI_API_KEY else '未設定'}")
            print(f"[DEBUG] get_llm_api_key(): {settings.get_llm_api_key()[:10] if settings.get_llm_api_key() else 'None'}...")
            print(f"[DEBUG] endpoint_url: {'設定済み' if endpoint_url else '未設定'}")
            
            if not api_key or not endpoint_url:
                validation = settings.validate_api_keys()
                error_msg = f"OpenAI API設定エラー - {validation}"
                return {"result": "error", "detail": error_msg}
            
            print(f"[DEBUG] OpenAI APIリクエスト開始")
            
            headers = {
                "api-key": api_key,
                "Content-Type": "application/json"
            }
            body = {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": 400,
                "temperature": 0.7
            }
            
            response = requests.post(
                endpoint_url, 
                headers=headers, 
                json=body, 
                timeout=settings.LLM_TIMEOUT
            )
            
            print(f"[DEBUG] OpenAI APIレスポンス - status_code: {response.status_code}")
            
            if not response.ok:
                error_detail = f"OpenAI API通信エラー - Status: {response.status_code}, Response: {response.text[:500]}"
                return {"result": "error", "detail": error_detail}
            
            result = response.json()
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            print(f"[DEBUG] OpenAI APIレスポンス内容: {content[:200]}...")
            
            return {"result": "success", "content": content}
            
        except requests.exceptions.Timeout:
            error_msg = f"OpenAI API通信タイムアウト（{settings.LLM_TIMEOUT}秒）"
            return {"result": "error", "detail": error_msg}
        except Exception as e:
            error_msg = f"OpenAI API通信例外: {str(e)}"
            return {"result": "error", "detail": error_msg}
    
    @staticmethod
    async def _generate_image(
        recipe_data: Dict, 
        req: CreateCocktailRequest, 
        use_storage: bool, 
        cocktail_uuid: str
    ) -> Dict[str, Any]:
        """画像生成処理"""
        try:
            print(f"[DEBUG] 画像生成開始 - use_storage: {use_storage}")
            
            # プロンプト構築
            color = recipe_data.get("color", "")
            concept = recipe_data.get("concept", "")
            target_rgb = color.get("target_rgb", "") if isinstance(color, dict) else ""
            
            # カスタムプロンプトチェック
            custom_image_prompt = None
            if req.image_prompt_id:
                prompt_data = dbmodule.get_prompt_by_id(req.image_prompt_id)
                if prompt_data and prompt_data['prompt_type'] == 'image':
                    custom_image_prompt = prompt_data['prompt_text']
            
            if custom_image_prompt:
                prompt_full = f"{color}のカクテル。メインカラーのRGBは{target_rgb}。{concept}。{req.prompt}。{custom_image_prompt}"
            else:
                prompt_full = (
                    f"{color}のカクテル。メインカラーのRGBは{target_rgb}。{concept}。{req.prompt}。"
                    f"背景は完全な透明（透過PNG）、カクテル以外は描かず、カクテルそのものだけを"
                    f"リアルな質感の写真風イラストとして生成してください。必ず生成画像の液体部分の色が"
                    f"指定されたメインカラーのRGB値の色味に近くなるようにしてください"
                )
            
            # API設定チェック
            api_key = settings.get_image_api_key()
            if not api_key:
                return {"result": "error", "detail": "画像生成API キーが設定されていません"}
            
            # API呼び出し
            client_url = "https://api.openai.com/v1/images/generations"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            body = {
                "model": settings.IMAGE_MODEL,
                "prompt": prompt_full,
                "size": settings.IMAGE_SIZE,
                "quality": settings.IMAGE_QUALITY,
            }
            
            print(f"[DEBUG] 画像生成APIリクエスト開始")
            response = requests.post(
                client_url, 
                headers=headers, 
                json=body, 
                timeout=settings.IMAGE_TIMEOUT
            )
            
            print(f"[DEBUG] 画像生成APIレスポンス - status_code: {response.status_code}")
            
            if not response.ok:
                error_detail = f"画像生成API通信エラー - Status: {response.status_code}, Response: {response.text[:500]}"
                return {"result": "error", "detail": error_detail}
            
            result_img = response.json()
            image_base64 = result_img.get("data", [{}])[0].get("b64_json", "")
            
            if not image_base64:
                return {
                    "result": "error", 
                    "detail": f"画像生成APIレスポンス異常: {str(result_img)[:200]}"
                }
            
            print(f"[DEBUG] 画像生成完了 - サイズ: {len(image_base64)} 文字")
            
            # 画像加工
            full_image_base64 = f"data:image/png;base64,{image_base64}"
            processed_image = crop_and_resize_base64_image(full_image_base64)
            
            # 保存方法による分岐
            print(f"[DEBUG] use_storage判定: {use_storage}")
            if use_storage:
                print(f"[DEBUG] Supabaseストレージアップロード開始 - UUID: {cocktail_uuid}")
                try:
                    url = upload_image_to_storage(processed_image, cocktail_uuid)
                    print(f"[DEBUG] Supabaseストレージアップロード完了 - URL: {url}")
                    return {"result": "success", "image": processed_image, "url": url}
                except Exception as storage_error:
                    print(f"[ERROR] Supabaseストレージアップロード失敗: {storage_error}")
                    # ストレージアップロードに失敗した場合はbase64で返す
                    return {"result": "success", "image": processed_image}
            else:
                print(f"[DEBUG] base64形式で返却")
                return {"result": "success", "image": processed_image}
            
        except requests.exceptions.Timeout:
            error_msg = f"画像生成API通信タイムアウト（{settings.IMAGE_TIMEOUT}秒）"
            return {"result": "error", "detail": error_msg}
        except Exception as e:
            error_msg = f"画像生成処理エラー: {str(e)}"
            print(f"[ERROR] {error_msg}")
            return {"result": "error", "detail": error_msg}
    
    @staticmethod
    async def _save_to_database(
        recipe_data: Dict,
        image_data: Dict,
        order_id: str,
        req: CreateCocktailRequest,
        event_id: Optional[str],
        save_user_info: bool,
        cocktail_uuid: str
    ) -> Dict[str, Any]:
        """データベース保存処理"""
        try:
            print(f"[DEBUG] DB保存開始")
            
            # ユーザー情報処理
            if not save_user_info:
                recent_event = ""
                event_name = ""
                user_name = ""
                career = ""
                hobby = ""
            else:
                recent_event = req.recent_event
                event_name = req.event_name
                user_name = req.name
                career = req.career
                hobby = req.hobby
            
            # レシピから各比率を抽出
            flavor_ratios = ["0%", "0%", "0%", "0%"]
            recipe = recipe_data.get("recipe", [])
            for item in recipe:
                syrup = item.get("syrup", "")
                ratio = item.get("ratio", "0%")
                if syrup == "ベリー":
                    flavor_ratios[0] = ratio
                elif syrup == "青りんご":
                    flavor_ratios[1] = ratio
                elif syrup == "シトラス":
                    flavor_ratios[2] = ratio
                elif syrup == "ホワイト":
                    flavor_ratios[3] = ratio
            
            # DB保存データ構築（IDをプライマリキーとして使用）
            db_data = {
                "id": cocktail_uuid,  # IDをプライマリキーとして指定
                "order_id": order_id,
                "status": 200,
                "name": recipe_data.get("cocktail_name", ""),
                "flavor_ratio1": flavor_ratios[0],
                "flavor_ratio2": flavor_ratios[1],
                "flavor_ratio3": flavor_ratios[2],
                "flavor_ratio4": flavor_ratios[3],
                "comment": recipe_data.get("concept", ""),
                "recent_event": recent_event,
                "event_name": event_name,
                "user_name": user_name,
                "career": career,
                "hobby": hobby,
                "event_id": event_id,
            }
            
            print(f"[DEBUG] DB挿入データ準備完了: order_id={order_id}, name={recipe_data.get('cocktail_name', '')}, uuid={cocktail_uuid}")
            
            # DB挿入
            inserted_uuid = dbmodule.insert_cocktail(db_data)
            if not inserted_uuid:
                error_msg = f"DB挿入失敗 - inserted_uuid: {inserted_uuid}"
                print(f"[ERROR] {error_msg}")
                return {"result": "error", "detail": error_msg}
            
            print(f"[DEBUG] DB保存完了 - inserted_uuid: {inserted_uuid}")
            
            # アンケート回答保存
            if req.survey_responses and event_id:
                try:
                    surveys = dbmodule.get_surveys_by_event(event_id, is_active=True)
                    if surveys:
                        survey_id = surveys[0]['id']
                        answers_data = [
                            {
                                'question_id': response.get('question_id', ''),
                                'answer_text': response.get('answer_text'),
                                'selected_option_ids': response.get('selected_option_ids', [])
                            }
                            for response in req.survey_responses
                        ]
                        
                        survey_response_id = dbmodule.submit_survey_response(
                            survey_id, inserted_uuid, answers_data  # UUIDを使用
                        )
                        if survey_response_id:
                            print(f"[DEBUG] アンケート回答保存完了: {survey_response_id}")
                except Exception as survey_error:
                    print(f"[WARNING] アンケート回答保存エラー（継続）: {survey_error}")
            
            # プロンプトリンク処理
            try:
                CocktailService._link_prompts(inserted_uuid, req)  # UUIDを使用
            except Exception as prompt_error:
                print(f"[WARNING] プロンプトリンクエラー（継続）: {prompt_error}")
            
            return {"result": "success", "inserted_uuid": inserted_uuid}
            
        except Exception as e:
            error_msg = f"DB保存例外: {str(e)}"
            print(f"[ERROR] {error_msg}")
            import traceback
            tb = traceback.format_exc()
            print(f"[ERROR] Traceback: {tb}")
            return {"result": "error", "detail": f"{error_msg}\n{tb}"}
    
    @staticmethod
    def _link_prompts(inserted_uuid: str, req: CreateCocktailRequest):
        """プロンプトリンク処理（UUID対応）"""
        # レシピプロンプト
        if req.recipe_prompt_id:
            dbmodule.link_cocktail_prompt(inserted_uuid, req.recipe_prompt_id, 'recipe')
        else:
            default_recipe_prompts = dbmodule.get_prompts('recipe', True)
            if default_recipe_prompts:
                default_prompt_id = default_recipe_prompts[0]['id']
                dbmodule.link_cocktail_prompt(inserted_uuid, default_prompt_id, 'recipe')
        
        # 画像プロンプト
        if req.image_prompt_id:
            dbmodule.link_cocktail_prompt(inserted_uuid, req.image_prompt_id, 'image')
        else:
            default_image_prompts = dbmodule.get_prompts('image', True)
            if default_image_prompts:
                default_prompt_id = default_image_prompts[0]['id']
                dbmodule.link_cocktail_prompt(inserted_uuid, default_prompt_id, 'image')

    @staticmethod
    def get_all_cocktails(limit: Optional[int] = None, offset: int = 0, event_id: Optional[str] = None) -> Dict[str, Any]:
        """全カクテル取得（ページネーション対応）"""
        try:
            print(f"[DEBUG] 全カクテル取得開始 - limit: {limit}, offset: {offset}, event_id: {event_id}")
            result = dbmodule.get_all_cocktails(limit=limit, offset=offset, event_id=event_id)
            print(f"[DEBUG] カクテル取得完了: {result.get('total', 0)}件")
            return result
        except Exception as e:
            print(f"[ERROR] カクテル取得エラー: {e}")
            return {"data": [], "total": 0}
    
    @staticmethod
    def get_cocktail_by_order_id(order_id: str) -> Optional[Dict[str, Any]]:
        """注文IDによるカクテル取得"""
        try:
            print(f"[DEBUG] カクテル取得開始: {order_id}")
            cocktail = dbmodule.get_cocktail_by_order_id(order_id)
            if cocktail:
                print(f"[DEBUG] カクテル取得成功: {cocktail.get('name', 'Unknown')}")
            else:
                print(f"[DEBUG] カクテルが見つかりません: {order_id}")
            return cocktail
        except Exception as e:
            print(f"[ERROR] カクテル取得エラー: {e}")
            return None
    
    @staticmethod
    def insert_poured_cocktail(db_data: Dict[str, Any]) -> Optional[str]:
        """注入済みカクテル情報の保存"""
        try:
            print(f"[DEBUG] 注入済みカクテル保存開始: {db_data.get('name')}")
            inserted_id = dbmodule.insert_poured_cocktail(db_data)
            print(f"[DEBUG] 注入済みカクテル保存完了: {inserted_id}")
            return inserted_id
        except Exception as e:
            print(f"[ERROR] 注入済みカクテル保存エラー: {e}")
            return None
    
    @staticmethod
    def get_cocktails_count_debug() -> Dict[str, Any]:
        """デバッグ用：カクテル件数確認"""
        try:
            print("[DEBUG] カクテル件数取得開始")
            
            # 複数の方法で件数取得を試行
            result = {
                "total_cocktails": 0,
                "active_cocktails": 0,
                "poured_cocktails": 0,
                "methods": {},
                "status": "success"
            }
            
            try:
                # 全件数
                all_data = dbmodule.get_all_cocktails()
                result["total_cocktails"] = all_data.get("total", 0)
                result["methods"]["get_all_cocktails"] = "success"
            except Exception as e:
                result["methods"]["get_all_cocktails"] = f"error: {str(e)}"
            
            try:
                # アクティブ件数（仮実装）
                result["active_cocktails"] = result["total_cocktails"]
                result["methods"]["active_count"] = "estimated"
            except Exception as e:
                result["methods"]["active_count"] = f"error: {str(e)}"
            
            try:
                # 注入済み件数（仮実装）
                result["poured_cocktails"] = 0  # 実際のDBクエリが必要
                result["methods"]["poured_count"] = "placeholder"
            except Exception as e:
                result["methods"]["poured_count"] = f"error: {str(e)}"
            
            print(f"[DEBUG] カクテル件数取得完了: {result['total_cocktails']}件")
            return result
            
        except Exception as e:
            print(f"[ERROR] カクテル件数取得エラー: {e}")
            return {
                "total_cocktails": 0,
                "active_cocktails": 0,
                "poured_cocktails": 0,
                "methods": {},
                "status": f"error: {str(e)}"
            }
    
    @staticmethod
    def confirm_copyright(cocktail_id: str) -> Dict[str, Any]:
        """著作権確認を行う"""
        try:
            print(f"[DEBUG] 著作権確認開始 - cocktail_id: {cocktail_id}")
            
            # カクテルの存在確認
            cocktail = dbmodule.get_cocktail_by_uuid(cocktail_id)
            if not cocktail:
                return {
                    "success": False,
                    "message": f"カクテルが見つかりません: {cocktail_id}"
                }
            
            # 既に確認済みかチェック
            if cocktail.get('copyright_confirmed', False):
                return {
                    "success": True,
                    "cocktail_id": cocktail_id,
                    "confirmed_at": cocktail.get('copyright_confirmed_at'),
                    "message": "既に著作権確認済みです"
                }
            
            # 著作権確認を更新
            success = dbmodule.update_copyright_confirmation(cocktail_id, True)
            if not success:
                return {
                    "success": False,
                    "message": "著作権確認の更新に失敗しました"
                }
            
            # 更新後のデータを取得
            updated_cocktail = dbmodule.get_cocktail_by_uuid(cocktail_id)
            confirmed_at = updated_cocktail.get('copyright_confirmed_at') if updated_cocktail else None
            
            print(f"[DEBUG] 著作権確認完了 - cocktail_id: {cocktail_id}")
            
            # confirmed_atがdatetimeオブジェクトの場合はisoformat()を呼び出し、文字列の場合はそのまま使用
            confirmed_at_str = None
            if confirmed_at:
                if hasattr(confirmed_at, 'isoformat'):
                    confirmed_at_str = confirmed_at.isoformat()
                else:
                    confirmed_at_str = str(confirmed_at)
            
            return {
                "success": True,
                "cocktail_id": cocktail_id,
                "confirmed_at": confirmed_at_str,
                "message": "著作権確認が完了しました"
            }
            
        except Exception as e:
            error_msg = f"著作権確認エラー: {str(e)}"
            print(f"[ERROR] {error_msg}")
            return {
                "success": False,
                "message": error_msg
            }
    
    @staticmethod
    def get_copyright_status(cocktail_id: str) -> Dict[str, Any]:
        """著作権確認ステータスを取得"""
        try:
            print(f"[DEBUG] 著作権ステータス取得開始 - cocktail_id: {cocktail_id}")
            
            # カクテルの取得
            cocktail = dbmodule.get_cocktail_by_uuid(cocktail_id)
            if not cocktail:
                return {
                    "success": False,
                    "message": f"カクテルが見つかりません: {cocktail_id}"
                }
            
            confirmed_at = cocktail.get('copyright_confirmed_at')
            
            # confirmed_atがdatetimeオブジェクトの場合はisoformat()を呼び出し、文字列の場合はそのまま使用
            confirmed_at_str = None
            if confirmed_at:
                if hasattr(confirmed_at, 'isoformat'):
                    confirmed_at_str = confirmed_at.isoformat()
                else:
                    confirmed_at_str = str(confirmed_at)
            
            return {
                "success": True,
                "cocktail_id": cocktail_id,
                "copyright_confirmed": cocktail.get('copyright_confirmed', False),
                "confirmed_at": confirmed_at_str
            }
            
        except Exception as e:
            error_msg = f"著作権ステータス取得エラー: {str(e)}"
            print(f"[ERROR] {error_msg}")
            return {
                "success": False,
                "message": error_msg
            }
