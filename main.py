from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import base64
import random
from typing import Union
from pydantic import BaseModel
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
async def get_order(order_id: Union[int, str]):
    order_id_str = str(order_id)
    if order_id_str == "all":
        # 全件取得
        cocktails = dbmodule.get_all_cocktails()
        result = []
        for c in cocktails:
            # recipe配列を生成
            recipe = [
                {"syrup": "ベリー", "ratio": c.get('flavor_ratio1', '')},
                {"syrup": "青りんご", "ratio": c.get('flavor_ratio2', '')},
                {"syrup": "シトラス", "ratio": c.get('flavor_ratio3', '')},
                {"syrup": "ホワイト", "ratio": c.get('flavor_ratio4', '')},
            ]
            result.append({
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
            })
        return result
    else:
        return generate_response(order_id_str)

from datetime import datetime

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

class CreateCocktailAnonymousRequest(BaseModel):
    recent_event: str
    event_name: str
    name: str = ""
    career: str
    hobby: str
    prompt: str = ""  # 画像生成用プロンプト（省略可）

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

def build_recipe_system_prompt(syrup_dict):
    syrupDesc = "\n".join([f"{k}: {v['desc']}（色: {v['color']}）" for k, v in syrup_dict.items()])
    systemPrompt = (
        "あなたはプロのバーテンダーです。"
        "以下のシロップ情報を参考に、入力された情報からカクテル風の名前（日本語で20文字以内）、"
        "そのカクテルのコンセプト文（日本語で1文）、生成AIでカクテルの画像を生成するためのメインカラー（液体の色）を表現する文章とメインカラーのRGB値、およびレシピ（シロップ名と比率のリスト、合計25%以内、色や味のイメージに合うように最大4種まで混ぜてOK）を考えてください。"
        "メインカラーは、4種のシロップの任意の比率での混合で作成できる色にしてください。"
        "以下に記載するシロップの情報を元に、必ず上記のメインカラーの表現に合うようにシロップ比率を考えてください。"
        "シロップのホワイトは0~10%で混ぜるようにしてください。また、出力は必ず次のJSON形式で返してください。"
        "0％でも、ベリー、青りんご、シトラス、ホワイトの4つの配合はそれぞれ示すようにしてください。"
        "```json\\n"
            "{\n"
            "  \"cocktail_name\": \"...\",\n"
            "  \"concept\": \"...\",\n"
            "  \"color\": {\n"
            "    \"description\": \"...\",\n"
            "    \"target_rgb\": \"(R,G,B)\"\n"
            "  },\n"
            "  \"recipe\": [\n"
            "    {\"syrup\": \"ベリー\", \"ratio\": \"15%\"},\n"
            "    {\"syrup\": \"青りんご\", \"ratio\": \"10%\"},\n"
            "    {\"syrup\": \"シトラス\", \"ratio\": \"0%\"},\n"
            "    {\"syrup\": \"ホワイト\", \"ratio\": \"10%\"}\n"
            "  ]\n"
            "}\n"
        "```"
    "\\n\\n[シロップ情報]\\n" + syrupDesc
    )
    return systemPrompt

@app.post("/cocktail/", response_model=CreateCocktailResponse)
async def create_cocktail(req: CreateCocktailRequest):
    """カクテル作成（ユーザー情報を保存、画像はbase64でDB保存）"""
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
        save_user_info=False
    )
    return await _create_cocktail_internal(full_req, save_user_info=False, use_storage=True)

async def _create_cocktail_internal(req: CreateCocktailRequest, save_user_info: bool = True, use_storage: bool = False):
    # 1. レシピ生成
    syrup_dict = load_syrup_info_txt()
    systemPrompt = build_recipe_system_prompt(syrup_dict)
    userPrompt = (
        f"最近の出来事: {req.recent_event}\n"
        f"イベント名: {req.event_name}\n"
        f"名前: {req.name}\n"
        f"キャリア: {req.career}\n"
        f"趣味: {req.hobby}"
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
    }
    try:
        inserted_id = dbmodule.insert_cocktail(db_data)
        if not inserted_id:
            # 失敗時のデバッグ情報を出力
            print("DB insert failed")
            print("db_data:", db_data)
            return CreateCocktailResponse(
                result="error",
                detail=f"DB insert failed. db_data={db_data}, inserted_id={inserted_id}"
            )
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
        print("DB insert exception:", tb)
        print("db_data:", db_data)
        return CreateCocktailResponse(result="error", detail=f"{e}\n{tb}\ndb_data={db_data}")

# === ここまで追加 ===
