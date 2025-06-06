from db import database

if __name__ == "__main__":
    database.create_tables()
    print("Cocktailsテーブルを作成しました。")
