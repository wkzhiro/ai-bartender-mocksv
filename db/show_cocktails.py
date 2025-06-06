from db import database

def show_all_cocktails():
    session = database.SessionLocal()
    try:
        cocktails = session.query(database.Cocktail).order_by(database.Cocktail.created_at.desc()).all()
        for c in cocktails:
            print(f"order_id: {c.order_id}")
            print(f"  name: {c.name}")
            print(f"  status: {c.status}")
            print(f"  flavor_ratio1: {c.flavor_ratio1}")
            print(f"  flavor_ratio2: {c.flavor_ratio2}")
            print(f"  flavor_ratio3: {c.flavor_ratio3}")
            print(f"  flavor_ratio4: {c.flavor_ratio4}")
            print(f"  comment: {c.comment}")
            print(f"  created_at: {c.created_at}")
            print("-" * 40)
    finally:
        session.close()

if __name__ == "__main__":
    show_all_cocktails()
