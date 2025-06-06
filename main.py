from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import base64
import random
from typing import Union
from pydantic import BaseModel

# DBからレシピ情報を取得して返す
import sys
from db import database as dbmodule

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
    flavor_ratio1: str
    flavor_ratio2: str
    flavor_ratio3: str
    flavor_ratio4: str
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
    # DBから取得
    cocktail = dbmodule.get_cocktail_by_order_id(order_id_str)
    if not cocktail:
        raise HTTPException(status_code=404, detail="注文番号が無効です。")

    # 画像はDBのbase64をそのまま返す
    encoded_image = cocktail.image

    response_data = {
        "status": cocktail.status if cocktail.status is not None else 200,
        "name": cocktail.name,
        "image": encoded_image,
        "flavor_name1": "ベリー",
        "flavor_ratio1": cocktail.flavor_ratio1,
        "flavor_name2": "青りんご",
        "flavor_ratio2": cocktail.flavor_ratio2,
        "flavor_name3": "シトラス",
        "flavor_ratio3": cocktail.flavor_ratio3,
        "flavor_name4": "ホワイト",
        "flavor_ratio4": cocktail.flavor_ratio4,
        "comment": cocktail.comment
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
        cocktails = dbmodule.SessionLocal().query(dbmodule.Cocktail).order_by(dbmodule.Cocktail.created_at.desc()).all()
        result = []
        for c in cocktails:
            # recipe配列を生成
            recipe = [
                {"syrup": "ベリー", "ratio": c.flavor_ratio1},
                {"syrup": "青りんご", "ratio": c.flavor_ratio2},
                {"syrup": "シトラス", "ratio": c.flavor_ratio3},
                {"syrup": "ホワイト", "ratio": c.flavor_ratio4},
            ]
            result.append({
                "order_id": c.order_id,
                "name": c.name,
                "concept": c.comment,
                "image_base64": c.image,
                "flavor_ratio1": c.flavor_ratio1,
                "flavor_ratio2": c.flavor_ratio2,
                "flavor_ratio3": c.flavor_ratio3,
                "flavor_ratio4": c.flavor_ratio4,
                "recent_event": getattr(c, "recent_event", ""),
                "event_name": getattr(c, "event_name", ""),
                "user_name": getattr(c, "user_name", ""),
                "career": getattr(c, "career", ""),
                "hobby": getattr(c, "hobby", ""),
                "created_at": c.created_at.isoformat() if c.created_at else "",
                "recipe": recipe,
            })
        return result
    else:
        return generate_response(order_id_str)

from datetime import datetime

@app.post("/cocktail/")
async def save_cocktail(req: SaveCocktailRequest):
    from db import database as dbmodule
    db_data = req.dict()
    print("=== /cocktail/ 受信データ ===")
    print(db_data)
    try:
        inserted_id = dbmodule.insert_cocktail(db_data)
        print(f"insert_cocktailの返り値: {inserted_id}")
        # 保存後、最新レコードを取得してprint
        if inserted_id:
            latest = dbmodule.get_cocktail_by_order_id(db_data["order_id"])
            print("=== DB最新レコード ===")
            print({
                "id": latest.id,
                "order_id": latest.order_id,
                "name": latest.name,
                "created_at": latest.created_at,
                "comment": latest.comment,
            })
            return {"result": "success", "id": str(inserted_id)}
        else:
            print("DB insert failed")
            return {"result": "error", "detail": "DB insert failed"}
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print("DB保存例外:", tb)
        return {"result": "error", "detail": f"{e}\n{tb}"}

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
