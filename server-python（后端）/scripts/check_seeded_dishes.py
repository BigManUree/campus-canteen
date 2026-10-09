from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.session import SessionLocal
from app.models.canteen import Canteen
from app.models.dish import Dish


def main():
    db = SessionLocal()
    try:
        canteens = db.query(Canteen).filter(Canteen.status == 1).order_by(Canteen.canteen_id.asc()).all()
        total = db.query(Dish).count()
        per_canteen = []
        for canteen in canteens:
            count = db.query(Dish).filter(Dish.canteen_id == canteen.canteen_id).count()
            per_canteen.append({
                "canteen_id": canteen.canteen_id,
                "canteen_name": canteen.canteen_name,
                "window_no": canteen.window_no,
                "dish_count": count,
            })
        print({
            "total_dishes": total,
            "active_canteens": len(canteens),
            "per_canteen": per_canteen,
        })
    finally:
        db.close()


if __name__ == "__main__":
    main()

