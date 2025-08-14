from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import base64
import random
from typing import Union, Optional
from pydantic import BaseModel
import uuid
from PIL import Image
import io

# SupabaseのDBモジュールを使用
from db import database as dbmodule
from db.supabase_client import supabase_client

app = FastAPI()

# CORS設定: React(Vite)のデフォルトポート8080を許可
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# カクテル保存用リクエストモデル
class SaveCocktailRequest(BaseModel):
    order_id: str
    status: int = 200
    name: str
    image: str
    comment: str
    recent_event: str = ""
    event_name: str = ""
    user_name: str = ""
    career: str = ""
    hobby: str = ""

# 画像フォルダのパス
IMAGE_FOLDER = Path("./images")

class OrderRequest(BaseModel):
    order_id: Union[int, str]

class DeriveryRequest(BaseModel):
    poured:Union[int, str]
    name:str
    flavor_name1:str
    flavor_ratio1:str
    flavor_name2:str
    flavor_ratio2:str
    flavor_name3:str
    flavor_ratio3:str
    flavor_name4:str
    flavor_ratio4:str
    comment:str

def encode_image_to_base64(image_path: Path) -> str:
    try:
        with image_path.open("rb") as f:
            image_data = f.read()
        encoded_image = base64.b64encode(image_data).decode("utf-8")
        return f"data:image/png;base64,{encoded_image}"
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"画像のエンコードに失敗しました: {e}")

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

@app.get("/")
def status_check():
    return "Hello"

@app.get("/status_check")
def status_check():
    return "ready"

def generate_response(order_id_str: str) -> dict:
    # Supabaseから取得
    cocktail_data = dbmodule.get_cocktail_by_order_id(order_id_str)
    if not cocktail_data:
        raise HTTPException(status_code=404, detail="注文番号が無効です。")

    # 画像はDBのbase64をそのまま返す
    encoded_image = cocktail_data.get('image', '')

    response_data = {
        "status": cocktail_data.get('status', 200),
        "name": cocktail_data.get('name', ''),
        "image": encoded_image,
        "flavor_name1": "ベリー",
        "flavor_ratio1": cocktail_data.get('flavor_ratio1', ''),
        "flavor_name2": "青りんご",
        "flavor_ratio2": cocktail_data.get('flavor_ratio2', ''),
        "flavor_name3": "シトラス",
        "flavor_ratio3": cocktail_data.get('flavor_ratio3', ''),
        "flavor_name4": "ホワイト",
        "flavor_ratio4": cocktail_data.get('flavor_ratio4', ''),
        "comment": cocktail_data.get('comment', '')
    }
    return response_data

import json

@app.post("/order/")
async def post_order(order: OrderRequest):
    order_id_str = str(order.order_id)
    response = generate_response(order_id_str)
    try:
        json_bytes = json.dumps(response, ensure_ascii=False).encode("utf-8")
        print("UTF-8エンコード成功")
    except Exception as e:
        print(f"UTF-8エンコード失敗: {e}")
    return response

@app.get("/order/")
async def get_order(order_id: Union[int, str], limit: int = None, offset: int = 0, event_id: str = None):
    order_id_str = str(order_id)
    if order_id_str == "all":
        # ページネーション対応の全件取得（event_idでフィルター可能）
        cocktail_data = dbmodule.get_all_cocktails(limit=limit, offset=offset, event_id=event_id)
        cocktails = cocktail_data['data']
        result = []
        for c in cocktails:
            # recipe配列を生成
            recipe = [
                {"syrup": "ベリー", "ratio": c.get('flavor_ratio1', '')},
                {"syrup": "青りんご", "ratio": c.get('flavor_ratio2', '')},
                {"syrup": "シトラス", "ratio": c.get('flavor_ratio3', '')},
                {"syrup": "ホワイト", "ratio": c.get('flavor_ratio4', '')},
            ]
            
            # プロンプト情報を取得
            cocktail_id = c.get('id')
            prompts_info = {}
            if cocktail_id:
                cocktail_prompts = dbmodule.get_cocktail_prompts(cocktail_id)
                for cp in cocktail_prompts:
                    prompt_type = cp.get('prompt_type')
                    prompts_info[f'{prompt_type}_prompt'] = cp.get('prompts', {})
            
            result.append({
                "id": c.get('id', ''),  # データベースのPrimary Keyを追加
                "order_id": c.get('order_id', ''),
                "name": c.get('name', ''),
                "concept": c.get('comment', ''),
                "image_base64": c.get('image', ''),
                "flavor_ratio1": c.get('flavor_ratio1', ''),
                "flavor_ratio2": c.get('flavor_ratio2', ''),
                "flavor_ratio3": c.get('flavor_ratio3', ''),
                "flavor_ratio4": c.get('flavor_ratio4', ''),
                "recent_event": c.get('recent_event', ''),
                "event_name": c.get('event_name', ''),
                "user_name": c.get('user_name', ''),
                "career": c.get('career', ''),
                "hobby": c.get('hobby', ''),
                "created_at": c.get('created_at', ''),
                "recipe": recipe,
                "prompts": prompts_info,
            })
        
        # ページネーション情報を含むレスポンス
        return {
            "data": result,
            "total_count": cocktail_data.get('total_count'),
            "limit": limit,
            "offset": offset,
            "has_next": cocktail_data.get('has_next', False),
            "has_prev": cocktail_data.get('has_prev', False)
        }
    else:
        return generate_response(order_id_str)

from datetime import datetime

# デバッグ用エンドポイント
@app.get("/debug/cocktails-count")
async def debug_cocktails_count():
    """デバッグ用：カクテル件数確認"""
    try:
        # 実際のデータ件数を複数の方法で取得
        
        # 方法1: 全件取得（古い方式）
        try:
            all_data = supabase_client.client.table('cocktails').select('*').execute()
            all_count = len(all_data.data) if all_data.data else 0
        except Exception as e:
            all_count = f"エラー: {e}"
        
        # 方法2: COUNT クエリ
        try:
            count_result = supabase_client.client.table('cocktails').select('id', count='exact').limit(1).execute()
            count_exact = count_result.count
        except Exception as e:
            count_exact = f"エラー: {e}"
        
        # 方法3: 最初の100件だけ取得
        try:
            sample_data = supabase_client.client.table('cocktails').select('*').limit(100).execute()
            sample_count = len(sample_data.data) if sample_data.data else 0
        except Exception as e:
            sample_count = f"エラー: {e}"
            
        # 最新の10件のorder_idを確認
        try:
            latest_data = supabase_client.client.table('cocktails').select('order_id, created_at').order('created_at', desc=True).limit(10).execute()
            latest_orders = [{"order_id": item.get('order_id'), "created_at": item.get('created_at')} for item in latest_data.data] if latest_data.data else []
        except Exception as e:
            latest_orders = f"エラー: {e}"
        
        return {
            "all_count": all_count,
            "count_exact": count_exact, 
            "sample_count": sample_count,
            "latest_orders": latest_orders,
            "table_name": "cocktails"
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/delivery/")
async def order_(deriver: DeriveryRequest):
    # 受け取ったデータをdictに変換
    print("start")
    print("deliver", deriver)
    db_data = {
        "poured": str(deriver.poured),
        "name": deriver.name,
        "flavor_name1": deriver.flavor_name1,
        "flavor_ratio1": deriver.flavor_ratio1,
        "flavor_name2": deriver.flavor_name2,
        "flavor_ratio2": deriver.flavor_ratio2,
        "flavor_name3": deriver.flavor_name3,
        "flavor_ratio3": deriver.flavor_ratio3,
        "flavor_name4": deriver.flavor_name4,
        "flavor_ratio4": deriver.flavor_ratio4,
        "comment": deriver.comment,
    }
    # DB保存
    try:
        inserted_id = dbmodule.insert_poured_cocktail(db_data)
        print(f"inserted_id: {inserted_id} (type: {type(inserted_id)})")
        if inserted_id:
            return {"result": "success", "id": str(inserted_id)}
        else:
            return {"result": "error", "detail": "DB insert failed"}
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        return {"result": "error", "detail": f"{e}\n{tb}"}

# === ここから追加 ===

# レシピ生成・画像生成・DB保存を統合するAPI
import os
import openai

class RecipeItem(BaseModel):
    syrup: str
    ratio: str

class CreateCocktailRequest(BaseModel):
    recent_event: str
    event_name: str
    name: str = ""
    career: str
    hobby: str
    prompt: str = ""  # 画像生成用プロンプト（省略可）
    save_user_info: bool = True  # ユーザー情報を保存するかどうか（デフォルトTrue）
    recipe_prompt_id: Optional[int] = None  # レシピ生成用プロンプトID（省略可）
    image_prompt_id: Optional[int] = None  # 画像生成用プロンプトID（省略可）
    event_id: Optional[str] = None  # イベントID（省略可）

class CreateCocktailAnonymousRequest(BaseModel):
    recent_event: str
    event_name: str
    name: str = ""
    career: str
    hobby: str
    prompt: str = ""  # 画像生成用プロンプト（省略可）
    recipe_prompt_id: Optional[int] = None  # レシピ生成用プロンプトID（省略可）
    image_prompt_id: Optional[int] = None  # 画像生成用プロンプトID（省略可）
    event_id: Optional[str] = None  # イベントID（省略可）

class CreateCocktailResponse(BaseModel):
    result: str
    id: str = ""
    cocktail_name: str = ""
    concept: str = ""
    color: str = ""
    recipe: list[RecipeItem] = []
    image_base64: str = ""
    detail: str = ""

def load_syrup_info_txt(path="storage/syrup.txt"):
    syrup_dict = {}
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.read().splitlines()
        names = ["ベリー", "青りんご", "シトラス", "ホワイト"]
        descs = []
        color_map = {}
        for name in names:
            for i, line in enumerate(lines):
                if line.strip() == name:
                    desc = lines[i+1] if i+1 < len(lines) else ""
                    descs.append(desc)
                    color = ""
                    if "The color is" in desc:
                        color = desc.split("The color is")[-1].strip().replace(".", "")
                    elif "The color is" in lines[i+1]:
                        color = lines[i+1].split("The color is")[-1].strip().replace(".", "")
                    color_map[name] = color
        for i, name in enumerate(names):
            syrup_dict[name] = {"desc": descs[i] if i < len(descs) else "", "color": color_map.get(name, "")}
    except Exception as e:
        print(f"syrup.txtの読み込みエラー: {e}")
    return syrup_dict

def upload_image_to_storage(image_base64: str, order_id: str) -> str:
    """画像をSupabase Storageにアップロードし、公開URLを返す"""
    try:
        # base64から画像データを抽出
        if "," in image_base64:
            image_data = base64.b64decode(image_base64.split(",")[1])
        else:
            image_data = base64.b64decode(image_base64)
        
        # ファイル名を生成
        file_name = f"cocktails/{order_id}.png"
        
        # バケットが存在するか確認・作成
        try:
            buckets = supabase_client.client.storage.list_buckets()
            bucket_exists = any(getattr(bucket, 'name', None) == 'cocktail-images' for bucket in buckets)
            if not bucket_exists:
                # public引数を削除してバケット作成
                supabase_client.client.storage.create_bucket('cocktail-images')
                print("cocktail-imagesバケットを作成しました")
        except Exception as bucket_error:
            print(f"バケット確認/作成エラー: {bucket_error}")

        # バケット作成後、バケットが存在するか再確認
        buckets = supabase_client.client.storage.list_buckets()
        bucket_exists = any(getattr(bucket, 'name', None) == 'cocktail-images' for bucket in buckets)
        if not bucket_exists:
            print("バケット作成に失敗しました")
            return image_base64

        # Supabase Storageにアップロード
        result = supabase_client.client.storage.from_("cocktail-images").upload(
            file_name, 
            image_data,
            {"content-type": "image/png"}
        )

        # 公開URLを取得
        public_url = supabase_client.client.storage.from_("cocktail-images").get_public_url(file_name)
        print(f"画像アップロード成功: {public_url}")
        return public_url

    except Exception as e:
        print(f"画像アップロードエラー: {e}")
        # アップロードに失敗した場合はbase64をそのまま返す
        return image_base64

def build_recipe_system_prompt(syrup_dict, custom_prompt=None):
    """レシピ生成用システムプロンプトを構築"""
    syrupDesc = "\n".join([f"{k}: {v['desc']}（色: {v['color']}）" for k, v in syrup_dict.items()])
    
    if custom_prompt:
        # カスタムプロンプトがある場合は、それをベースに使用
        base_prompt = custom_prompt
    else:
        # デフォルトプロンプト
        base_prompt = (
            "あなたはプロのバーテンダーです。お客様の「最近の出来事」「キャリア」「趣味」の3つの要素を均等に重視し、バランス良くカクテルに反映させてください。"
            "カクテル名の作成時は、3つの要素から1つずつ特徴を取り入れるか、または全体のイメージを統合した名前にしてください。"
            "コンセプトも同様に、最近の出来事だけでなく、キャリアや趣味の要素も含めて総合的な印象を表現してください。"
            "以下のシロップ情報を参考に、入力された情報からカクテル風の名前（日本語で20文字以内）、"
            "そのカクテルのコンセプト文（日本語で1文）、生成AIでカクテルの画像を生成するためのメインカラー（液体の色）を表現する文章とメインカラーのRGB値、およびレシピ（シロップ名と比率のリスト、合計25%以内、色や味のイメージに合うように最大4種まで混ぜてOK）を考えてください。"
            "メインカラーは、4種のシロップの任意の比率での混合で作成できる色にしてください。"
            "以下に記載するシロップの情報を元に、必ず上記のメインカラーの表現に合うようにシロップ比率を考えてください。"
            "シロップのホワイトは0~10%で混ぜるようにしてください。また、出力は必ず次のJSON形式で返してください。"
            "0％でも、ベリー、青りんご、シトラス、ホワイトの4つの配合はそれぞれ示すようにしてください。"
            "colorはstring型（例: \"春の陽だまりのような黄色（(246, 236, 55)）\"）で返してください。"
        )
    
    json_format = (
        "```json\\n"
            "{\n"
            "  \"cocktail_name\": \"...\",\n"
            "  \"concept\": \"...\",\n"
            "  \"color\": \"春の陽だまりのような黄色（(246, 236, 55)）\",\n"
            "  \"recipe\": [\n"
            "    {\"syrup\": \"ベリー\", \"ratio\": \"15%\"},\n"
            "    {\"syrup\": \"青りんご\", \"ratio\": \"10%\"},\n"
            "    {\"syrup\": \"シトラス\", \"ratio\": \"0%\"},\n"
            "    {\"syrup\": \"ホワイト\", \"ratio\": \"10%\"}\n"
            "  ]\n"
            "}\n"
        "```"
    )
    
    systemPrompt = base_prompt + json_format + "\\n\\n[シロップ情報]\\n" + syrupDesc
    return systemPrompt

@app.post("/cocktail/", response_model=CreateCocktailResponse)
async def create_cocktail(req: CreateCocktailRequest):
    """カクテル作成（ユーザー情報を保存、画像はbase64でDB保存）"""
    print("post request / test")
    return await _create_cocktail_internal(req, save_user_info=req.save_user_info, use_storage=False)

@app.post("/cocktail/anonymous/", response_model=CreateCocktailResponse)
async def create_cocktail_anonymous(req: CreateCocktailAnonymousRequest):
    """カクテル作成（ユーザー情報を保存しない、画像はStorageに保存）"""
    # CreateCocktailRequestと同じ形式に変換（全ての情報を使ってレシピ生成）
    full_req = CreateCocktailRequest(
        recent_event=req.recent_event,
        event_name=req.event_name,
        name=req.name,
        career=req.career,
        hobby=req.hobby,
        prompt=req.prompt,
        save_user_info=False,
        recipe_prompt_id=req.recipe_prompt_id,
        image_prompt_id=req.image_prompt_id,
        event_id=req.event_id
    )
    return await _create_cocktail_internal(full_req, save_user_info=False, use_storage=True)

async def _create_cocktail_internal(req: CreateCocktailRequest, save_user_info: bool = True, use_storage: bool = False):
    # 0. イベント関連の処理
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
    
    # 1. レシピ生成
    syrup_dict = load_syrup_info_txt()
    
    # プロンプトIDが指定されている場合は、DBからプロンプトを取得
    custom_recipe_prompt = None
    if req.recipe_prompt_id:
        prompt_data = dbmodule.get_prompt_by_id(req.recipe_prompt_id)
        if prompt_data and prompt_data['prompt_type'] == 'recipe':
            custom_recipe_prompt = prompt_data['prompt_text']
    
    systemPrompt = build_recipe_system_prompt(syrup_dict, custom_recipe_prompt)
    userPrompt = (
        f"【最近の出来事】（カクテルの雰囲気や感情面に反映）: {req.recent_event}\n"
        f"【キャリア】（カクテルの力強さや構造に反映）: {req.career}\n"
        f"【趣味】（カクテルの個性や独創性に反映）: {req.hobby}\n"
        f"イベント名: {req.event_name}\n"
        f"名前: {req.name}\n\n"
        f"上記の3つの要素をそれぞれ活かし、バランスの取れたオリジナルカクテルを作成してください。"
    )
    api_key = os.environ.get("AZURE_OPENAI_API_KEY_LLM") or os.environ.get("OPENAI_API_KEY")
    endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT_LLM")
    deployment_id = "gpt-4.1"
    if not api_key or not endpoint:
        return CreateCocktailResponse(result="error", detail="OpenAI APIキーまたはエンドポイントが設定されていません。")
    url = f"{endpoint}/openai/deployments/{deployment_id}/chat/completions?api-version=2023-12-01-preview"
    import requests
    headers = {
        "api-key": api_key,
        "Content-Type": "application/json"
    }
    body = {
        "messages": [
            {"role": "system", "content": systemPrompt},
            {"role": "user", "content": userPrompt}
        ],
        "max_tokens": 400,
        "temperature": 0.7
    }
    res = requests.post(url, headers=headers, json=body)
    if not res.ok:
        return CreateCocktailResponse(result="error", detail="OpenAI API通信エラー")
    result = res.json()
    content = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
    import re
    jsonMatch = re.search(r"\{[\s\S]+\}", content)
    if not jsonMatch:
        return CreateCocktailResponse(result="error", detail="ChatGPT出力からJSONが抽出できませんでした: " + content)
    import json as pyjson
    data = pyjson.loads(jsonMatch.group(0))
    recipe = data.get("recipe", [])
    cocktail_name = data.get("cocktail_name", "")
    concept = data.get("concept", "")
    color = data.get("color", "")
    if isinstance(color, dict):
        target_rgb = color.get("target_rgb", "")
    else:
        target_rgb = ""

    # 3. order_idを6桁ランダムで生成（重複チェック付き）
    import random
    max_attempts = 10
    for _ in range(max_attempts):
        order_id = str(random.randint(100000, 999999))
        # DBに同じorder_idが存在しないかチェック
        if not dbmodule.get_cocktail_by_order_id(order_id):
            break
    else:
        return CreateCocktailResponse(result="error", detail="注文番号の重複が解消できませんでした。")

    # 2. 画像生成
    # プロンプトIDが指定されている場合は、DBからプロンプトを取得
    custom_image_prompt = None
    if req.image_prompt_id:
        prompt_data = dbmodule.get_prompt_by_id(req.image_prompt_id)
        if prompt_data and prompt_data['prompt_type'] == 'image':
            custom_image_prompt = prompt_data['prompt_text']
    
    if custom_image_prompt:
        prompt_full = f"{color}のカクテル。メインカラーのRGBは{target_rgb}。{concept}。{req.prompt}。{custom_image_prompt}"
    else:
        prompt_full = (
            f"{color}のカクテル。メインカラーのRGBは{target_rgb}。{concept}。{req.prompt}。背景は完全な透明（透過PNG）、カクテル以外は描かず、カクテルそのものだけをリアルな質感の写真風イラストとして生成してください。必ず生成画像の液体部分の色が指定されたメインカラーのRGB値の色味に近くなるようにしてください"
        )
    api_key_img = os.environ.get("GPT_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key_img:
        return CreateCocktailResponse(result="error", detail="gpt-image APIキー(GPT_API_KEY)が設定されていません。")
    clientUrl = "https://api.openai.com/v1/images/generations"
    headers_img = {
        "Authorization": f"Bearer {api_key_img}",
        "Content-Type": "application/json"
    }
    body_img = {
        "model": "gpt-image-1",
        "prompt": prompt_full,
        "size": "1024x1536",
        "quality": "low",
    }
    res_img = requests.post(clientUrl, headers=headers_img, json=body_img)
    if not res_img.ok:
        errorText = res_img.text
        return CreateCocktailResponse(result="error", detail="gpt-image API通信エラー: " + errorText)
    result_img = res_img.json()
    image_base64 = result_img.get("data", [{}])[0].get("b64_json", "")
    if not image_base64:
        return CreateCocktailResponse(result="error", detail="画像生成APIレスポンス異常: " + str(result_img))
    image_base64 = f"data:image/png;base64,{image_base64}"

    # === 画像を中央クロップ＆リサイズ（720x1080） ===
    def crop_and_resize_base64_image(base64_str: str, target_width: int = 720, target_height: int = 1080) -> str:
        # base64ヘッダー除去
        if "," in base64_str:
            base64_str = base64_str.split(",")[1]
        img_bytes = base64.b64decode(base64_str)
        with Image.open(io.BytesIO(img_bytes)) as img:
            src_width, src_height = img.size
            target_aspect = target_width / target_height
            src_aspect = src_width / src_height

            # クロップ範囲計算
            if src_aspect > target_aspect:
                # 横長→左右をカット
                new_width = int(src_height * target_aspect)
                left = (src_width - new_width) // 2
                box = (left, 0, left + new_width, src_height)
            else:
                # 縦長→上下をカット
                new_height = int(src_width / target_aspect)
                top = (src_height - new_height) // 2
                box = (0, top, src_width, top + new_height)
            img_cropped = img.crop(box)
            img_resized = img_cropped.resize((target_width, target_height), Image.LANCZOS)
            buf = io.BytesIO()
            img_resized.save(buf, format="PNG")
            b64_png = base64.b64encode(buf.getvalue()).decode("utf-8")
            return f"data:image/png;base64,{b64_png}"

    image_base64 = crop_and_resize_base64_image(image_base64, 720, 1080)
    
    # 画像保存方法の分岐
    if use_storage:
        # Supabase Storageに画像をアップロード
        image_data = upload_image_to_storage(image_base64, order_id)
    else:
        # base64エンコードをそのまま使用
        image_data = image_base64

    # 4. DB保存
    # save_user_infoがFalseの時はユーザー情報を空文字で保存
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

    db_data = {
        "order_id": order_id,
        "status": 200,
        "name": cocktail_name,
        "image": image_data,
        "flavor_ratio1": flavor_ratios[0],
        "flavor_ratio2": flavor_ratios[1],
        "flavor_ratio3": flavor_ratios[2],
        "flavor_ratio4": flavor_ratios[3],
        "comment": concept,
        "recent_event": recent_event,
        "event_name": event_name,
        "user_name": user_name,
        "career": career,
        "hobby": hobby,
        "event_id": event_id,
    }
    try:
        inserted_id = dbmodule.insert_cocktail(db_data)
        if not inserted_id:
            # 失敗時のデバッグ情報を出力
            print("DB insert failed")
            # print("db_data:", db_data)
            return CreateCocktailResponse(
                result="error",
                detail=f"DB insert failed. db_data={db_data}, inserted_id={inserted_id}"
            )
        
        # 使用したプロンプトIDをカクテルと関連付け
        if req.recipe_prompt_id:
            dbmodule.link_cocktail_prompt(inserted_id, req.recipe_prompt_id, 'recipe')
        else:
            # デフォルトプロンプトを使用した場合は、デフォルトプロンプトのIDを取得して保存
            default_recipe_prompts = dbmodule.get_prompts('recipe', True)
            if default_recipe_prompts:
                # 最初のアクティブなレシピプロンプトをデフォルトとして使用
                default_prompt_id = default_recipe_prompts[0]['id']
                dbmodule.link_cocktail_prompt(inserted_id, default_prompt_id, 'recipe')
        
        if req.image_prompt_id:
            dbmodule.link_cocktail_prompt(inserted_id, req.image_prompt_id, 'image')
        else:
            # デフォルトプロンプトを使用した場合は、デフォルトプロンプトのIDを取得して保存
            default_image_prompts = dbmodule.get_prompts('image', True)
            if default_image_prompts:
                # 最初のアクティブな画像プロンプトをデフォルトとして使用
                default_prompt_id = default_image_prompts[0]['id']
                dbmodule.link_cocktail_prompt(inserted_id, default_prompt_id, 'image')
        
        # use_storageのときはimage_base64にURLを返す
        if use_storage:
            image_base64_value = image_data  # URL
        else:
            image_base64_value = image_base64  # base64
        return CreateCocktailResponse(
            result="success",
            id=str(order_id),
            cocktail_name=cocktail_name,
            concept=concept,
            color=color,
            recipe=[RecipeItem(**item) for item in recipe],
            image_base64=image_base64_value,
            detail="",
        )
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        # print("DB insert exception:", tb)
        # print("db_data:", db_data)
        return CreateCocktailResponse(result="error", detail=f"{e}\n{tb}\ndb_data={db_data}")

# プロンプト管理API
@app.get("/prompts/")
async def get_prompts(prompt_type: str = None):
    """プロンプト一覧を取得"""
    try:
        prompts = dbmodule.get_prompts(prompt_type=prompt_type)
        return {"result": "success", "prompts": prompts}
    except Exception as e:
        return {"result": "error", "detail": str(e)}

@app.get("/prompts/{prompt_id}")
async def get_prompt(prompt_id: int):
    """プロンプトを取得"""
    try:
        prompt = dbmodule.get_prompt_by_id(prompt_id)
        if not prompt:
            return {"result": "error", "detail": "プロンプトが見つかりません"}
        return {"result": "success", "prompt": prompt}
    except Exception as e:
        return {"result": "error", "detail": str(e)}

class PromptRequest(BaseModel):
    prompt_type: str
    title: str
    description: str = ""
    prompt_text: str
    is_active: bool = True

@app.post("/prompts/")
async def create_prompt(req: PromptRequest):
    """プロンプトを作成"""
    try:
        data = {
            "prompt_type": req.prompt_type,
            "title": req.title,
            "description": req.description,
            "prompt_text": req.prompt_text,
            "is_active": req.is_active
        }
        prompt_id = dbmodule.insert_prompt(data)
        if not prompt_id:
            return {"result": "error", "detail": "プロンプトの作成に失敗しました"}
        return {"result": "success", "id": prompt_id}
    except Exception as e:
        return {"result": "error", "detail": str(e)}

@app.put("/prompts/{prompt_id}")
async def update_prompt(prompt_id: int, req: PromptRequest):
    """プロンプトを更新"""
    try:
        data = {
            "prompt_type": req.prompt_type,
            "title": req.title,
            "description": req.description,
            "prompt_text": req.prompt_text,
            "is_active": req.is_active
        }
        success = dbmodule.update_prompt(prompt_id, data)
        if not success:
            return {"result": "error", "detail": "プロンプトの更新に失敗しました"}
        return {"result": "success"}
    except Exception as e:
        return {"result": "error", "detail": str(e)}

@app.post("/prompts/initialize")
async def initialize_prompts():
    """デフォルトプロンプトを初期化"""
    try:
        dbmodule.initialize_default_prompts()
        return {"result": "success", "detail": "デフォルトプロンプトを初期化しました"}
    except Exception as e:
        return {"result": "error", "detail": str(e)}

# イベント管理API
@app.get("/events/")
async def get_events(is_active: bool = None):
    """イベント一覧を取得"""
    try:
        events = dbmodule.get_events(is_active=is_active)
        return {"result": "success", "events": events}
    except Exception as e:
        return {"result": "error", "detail": str(e)}

@app.get("/events/{event_id}")
async def get_event(event_id: str):
    """イベントを取得"""
    try:
        event = dbmodule.get_event_by_id(event_id)
        if not event:
            return {"result": "error", "detail": "イベントが見つかりません"}
        return {"result": "success", "event": event}
    except Exception as e:
        return {"result": "error", "detail": str(e)}

class EventRequest(BaseModel):
    name: str
    description: str = ""
    is_active: bool = True

@app.post("/events/")
async def create_event(req: EventRequest):
    """イベントを作成"""
    try:
        data = {
            "name": req.name,
            "description": req.description,
            "is_active": req.is_active
        }
        event_id = dbmodule.insert_event(data)
        if not event_id:
            return {"result": "error", "detail": "イベントの作成に失敗しました"}
        return {"result": "success", "id": event_id}
    except Exception as e:
        return {"result": "error", "detail": str(e)}

@app.put("/events/{event_id}")
async def update_event(event_id: str, req: EventRequest):
    """イベントを更新"""
    try:
        data = {
            "name": req.name,
            "description": req.description,
            "is_active": req.is_active
        }
        success = dbmodule.update_event(event_id, data)
        if not success:
            return {"result": "error", "detail": "イベントの更新に失敗しました"}
        return {"result": "success"}
    except Exception as e:
        return {"result": "error", "detail": str(e)}

# 違反報告関連API

def get_client_ip(request: Request) -> str:
    """クライアントのIPアドレスを取得"""
    # X-Forwarded-Forヘッダーをチェック（プロキシ経由の場合）
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # 最初のIPアドレスを取得（カンマ区切りの場合）
        return forwarded_for.split(",")[0].strip()
    
    # X-Real-IPヘッダーをチェック（Nginx等のリバースプロキシ）
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    
    # 直接接続の場合
    client_host = request.client.host if request.client else "unknown"
    return client_host

class ViolationReportRequest(BaseModel):
    cocktail_id: int
    report_reason: str
    report_category: str = 'inappropriate'  # 'inappropriate', 'offensive', 'spam', 'other'

class HideCocktailRequest(BaseModel):
    cocktail_id: int
    reason: str = '違反報告により非表示'

@app.post("/report-violation/")
async def report_violation(req: ViolationReportRequest, request: Request):
    """カクテルの違反を報告"""
    try:
        # クライアントのIPアドレスを取得
        client_ip = get_client_ip(request)
        print(f"違反報告: cocktail_id={req.cocktail_id}, client_ip={client_ip}")
        
        success = dbmodule.report_violation(
            cocktail_id=req.cocktail_id,
            reporter_ip=client_ip,
            report_reason=req.report_reason,
            report_category=req.report_category
        )
        
        if success:
            return {"result": "success", "message": "違反報告を受け付けました"}
        else:
            return {"result": "error", "detail": "既にこのIPアドレスから報告済みか、報告に失敗しました"}
    except Exception as e:
        return {"result": "error", "detail": str(e)}

@app.post("/hide-cocktail/")
async def hide_cocktail(req: HideCocktailRequest):
    """カクテルを非表示にする"""
    try:
        success = dbmodule.hide_cocktail(req.cocktail_id, req.reason)
        
        if success:
            return {"result": "success", "message": "カクテルを非表示にしました"}
        else:
            return {"result": "error", "detail": "カクテルの非表示に失敗しました"}
    except Exception as e:
        return {"result": "error", "detail": str(e)}

@app.post("/show-cocktail/{cocktail_id}")
async def show_cocktail(cocktail_id: int):
    """カクテルを再表示する"""
    try:
        success = dbmodule.show_cocktail(cocktail_id)
        
        if success:
            return {"result": "success", "message": "カクテルを再表示しました"}
        else:
            return {"result": "error", "detail": "カクテルの再表示に失敗しました"}
    except Exception as e:
        return {"result": "error", "detail": str(e)}

@app.get("/violation-reports/")
async def get_violation_reports(cocktail_id: int = None):
    """違反報告一覧を取得"""
    try:
        reports = dbmodule.get_violation_reports(cocktail_id)
        return {"result": "success", "reports": reports}
    except Exception as e:
        return {"result": "error", "detail": str(e)}

# === ここまで追加 ===
