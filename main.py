from fastapi import FastAPI, HTTPException
from pathlib import Path
import base64
import random
from typing import Union
from pydantic import BaseModel

app = FastAPI()

# 画像フォルダのパス
IMAGE_FOLDER = Path("./images")

class OrderRequest(BaseModel):
    order_id: Union[int, str]

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
    return "ready"

def generate_response(order_id_str: str) -> dict:
    if order_id_str not in recipe_info:
        raise HTTPException(status_code=404, detail="注文番号が無効です。")
        
    image_file = IMAGE_FOLDER / f"{order_id_str}.png"
    if not image_file.exists():
        raise HTTPException(status_code=404, detail="注文番号に紐づく画像が見つかりません。")
    
    encoded_image = encode_image_to_base64(image_file)
    recipe = recipe_info[order_id_str]
    
    # ランダムな比率（％表示）を設定
    flavor_ratio1 = f"{random.randint(1, 10)}%"
    flavor_ratio2 = f"{random.randint(1, 10)}%"
    flavor_ratio3 = f"{random.randint(1, 10)}%"
    flavor_ratio4 = f"{random.randint(1, 10)}%"
    
    response_data = {
        "status": 200,
        "name": recipe["name"],
        "image": encoded_image,
        "flavor_name1": "もも",
        "flavor_ratio1": flavor_ratio1,
        "flavor_name2": "⻘りんご",
        "flavor_ratio2": flavor_ratio2,
        "flavor_name3": "ゆず",
        "flavor_ratio3": flavor_ratio3,
        "flavor_name4": "レモン",
        "flavor_ratio4": flavor_ratio4,
        "comment": recipe["comment"]
    }
    
    return response_data

@app.post("/")
async def post_order(order: OrderRequest):
    order_id_str = str(order.order_id)
    return generate_response(order_id_str)

@app.get("/")
async def get_order(order_id: Union[int, str]):
    order_id_str = str(order_id)
    return generate_response(order_id_str)