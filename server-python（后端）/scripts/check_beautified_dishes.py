from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.session import SessionLocal
from app.models.canteen import Canteen
from app.models.dish import Dish
from app.models.category import DishCategory


def main():
    db = SessionLocal()
    try:
        category_map = {c.category_id: c.category_name for c in db.query(DishCategory).all()}
        canteens = db.query(Canteen).filter(Canteen.status == 1).order_by(Canteen.canteen_id.asc()).all()
        result = []
        for canteen in canteens:
            dishes = db.query(Dish).filter(Dish.canteen_id == canteen.canteen_id).order_by(Dish.dish_id.asc()).limit(3).all()
            result.append({
                'canteen_name': canteen.canteen_name,
                'samples': [
                    {
                        'dish_id': dish.dish_id,
                        'name': dish.name,
                        'price': float(dish.price),
                        'description': dish.description,
                        'category_id': dish.category_id,
                        'category_name': category_map.get(dish.category_id),
                        'stock': dish.stock,
                    }
                    for dish in dishes
                ]
            })
        print(result)
    finally:
        db.close()


if __name__ == '__main__':
    main()

