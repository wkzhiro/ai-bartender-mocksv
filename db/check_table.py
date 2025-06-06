from db import database
import sys

def main():
    if len(sys.argv) > 1:
        table_name = sys.argv[1]
    else:
        table_name = "cocktails"
    exists = database.table_exists(table_name)
    if exists:
        print(f"テーブル '{table_name}' は存在します。")
    else:
        print(f"テーブル '{table_name}' は存在しません。")

if __name__ == "__main__":
    main()
