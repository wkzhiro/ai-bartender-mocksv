import os
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, UniqueConstraint
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(override=True)

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME")
print(DB_USER,DB_PASSWORD, DB_HOST,DB_PORT, DB_NAME)

DATABASE_URL = f'mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
print("DATABASE_URL:", DATABASE_URL) 

engine = create_engine(DATABASE_URL, echo=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

class Cocktail(Base):
    __tablename__ = "cocktails"
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String(32), unique=True, nullable=False)  # ← 16→32文字に拡張
    status = Column(Integer)
    name = Column(String(128))
    image = Column(LONGTEXT)  # base64
    flavor_ratio1 = Column(String(16))
    flavor_ratio2 = Column(String(16))
    flavor_ratio3 = Column(String(16))
    flavor_ratio4 = Column(String(16))
    comment = Column(Text)
    recent_event = Column(Text)
    event_name = Column(String(128))
    user_name = Column(String(128))
    career = Column(String(128))
    hobby = Column(String(128))
    created_at = Column(DateTime, default=datetime.utcnow)

class PouredCocktail(Base):
    __tablename__ = "poured_cocktails"
    id = Column(Integer, primary_key=True, autoincrement=True)
    poured = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    flavor_name1 = Column(String(255), nullable=False)
    flavor_ratio1 = Column(String(32), nullable=False)
    flavor_name2 = Column(String(32), nullable=False)
    flavor_ratio2 = Column(String(32), nullable=False)
    flavor_name3 = Column(String(32), nullable=False)
    flavor_ratio3 = Column(String(32), nullable=False)
    flavor_name4 = Column(String(32), nullable=False)
    flavor_ratio4 = Column(String(32), nullable=False)
    comment = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

import traceback

def create_tables():
    try:
        print("全テーブルを削除します...")
        Base.metadata.drop_all(bind=engine)
        print("全テーブルを再作成します...")
        Base.metadata.create_all(bind=engine)
        print("テーブルの再作成が完了しました。")
    except Exception as e:
        print("テーブル作成中にエラーが発生しました:")
        traceback.print_exc()
        raise

def insert_cocktail(data: dict):
    session = SessionLocal()
    try:
        cocktail = Cocktail(**data)
        session.add(cocktail)
        session.commit()
        return cocktail.id
    except Exception as e:
        session.rollback()
        print(f"DB挿入エラー: {e}")
        return None
    finally:
        session.close()

def get_cocktail_by_order_id(order_id: str):
    session = SessionLocal()
    try:
        return session.query(Cocktail).filter(Cocktail.order_id == order_id).first()
    finally:
        session.close()

def insert_poured_cocktail(data: dict):
    session = SessionLocal()
    try:
        poured_cocktail = PouredCocktail(**data)
        session.add(poured_cocktail)
        session.flush()  # ここでIDを確定
        inserted_id = poured_cocktail.id
        session.commit()
        return inserted_id
    except Exception as e:
        session.rollback()
        print(f"DB挿入エラー(poured_cocktails): {e}")
        return None
    finally:
        session.close()

from sqlalchemy import inspect

def table_exists(table_name: str) -> bool:
    """指定したテーブルが存在するか確認する"""
    return inspect(engine).has_table(table_name)
