import sys
import random
from pathlib import Path
import base64

sys.path.append(str(Path(__file__).parent))
from database import insert_cocktail

# 画像ファイルとレシピ情報
cocktail_data = [
    {
        "order_id": "123456",
        "cocktail_name": "バジル・ブリーズ",
        "concept": "鮮やかなエメラルドグリーンのカクテルで、フレッシュバジルの香りが引き立つ爽やかな味わい。ジンとライムリキュールをベースにしたハーバルな一杯。",
        "image_path": Path("images/123456.png"),
        "recipe": [
            {"syrup": "Syrup1", "ratio": f"{random.randint(5,10)}%"},
            {"syrup": "Syrup2", "ratio": f"{random.randint(5,10)}%"},
            {"syrup": "Syrup3", "ratio": f"{random.randint(1,5)}%"},
            {"syrup": "Syrup4", "ratio": f"{random.randint(1,5)}%"}
        ]
    },
    {
        "order_id": "234567",
        "cocktail_name": "ゴールデン・サンセット",
        "concept": "黄金色に輝くフルーティーなカクテル。パッションフルーツとアプリコットの甘酸っぱさが際立ち、チェリーのガーニッシュがアクセント。",
        "image_path": Path("images/234567.png"),
        "recipe": [
            {"syrup": "Syrup3", "ratio": f"{random.randint(10,15)}%"},
            {"syrup": "Syrup1", "ratio": f"{random.randint(5,10)}%"},
            {"syrup": "Syrup2", "ratio": f"{random.randint(1,5)}%"},
            {"syrup": "Syrup4", "ratio": f"{random.randint(1,5)}%"}
        ]
    },
    {
        "order_id": "345678",
        "cocktail_name": "ディープ・ブルー・ナイト",
        "concept": "濃厚なブルーの美しいカクテル。ブルーキュラソーとバイオレットリキュールを使った幻想的な味わいで、ブラックベリーのトッピングが深みを添える。",
        "image_path": Path("images/345678.png"),
        "recipe": [
            {"syrup": "Syrup2", "ratio": f"{random.randint(10,15)}%"},
            {"syrup": "Syrup1", "ratio": f"{random.randint(5,10)}%"},
            {"syrup": "Syrup3", "ratio": f"{random.randint(1,5)}%"},
            {"syrup": "Syrup4", "ratio": f"{random.randint(1,5)}%"}
        ]
    }
]

for c in cocktail_data:
    # 画像base64エンコード
    if not c["image_path"].exists():
        print(f"画像が見つかりません: {c['image_path']}")
        continue
    with open(c["image_path"], "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("utf-8")
    # flavor_ratio
    ratios = [item["ratio"] for item in c["recipe"]]
    # 必ず4つ
    ratios += ["0%"] * 4
    ratios = ratios[:4]
    db_data = {
        "order_id": c["order_id"],
        "status": 200,
        "name": c["cocktail_name"],
        "image": f"data:image/png;base64,{img_b64}",
        "flavor_ratio1": ratios[0],
        "flavor_ratio2": ratios[1],
        "flavor_ratio3": ratios[2],
        "flavor_ratio4": ratios[3],
        "comment": c["concept"]
    }
    inserted_id = insert_cocktail(db_data)
    if inserted_id:
        print(f"DB登録成功: order_id={c['order_id']} (id={inserted_id})")
    else:
        print(f"DB登録失敗: order_id={c['order_id']}")
