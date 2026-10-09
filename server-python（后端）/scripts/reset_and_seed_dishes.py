from decimal import Decimal
from pathlib import Path
import sys

from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.session import SessionLocal
from app.models.canteen import Canteen
from app.models.dish import Dish


def build_dishes_for_canteen(canteen: Canteen):
    label = canteen.canteen_name or f"食堂{canteen.canteen_id}"
    window = canteen.window_no or "默认档口"
    base_names = [
        "招牌盖饭",
        "香辣鸡腿饭",
        "黑椒牛柳饭",
        "番茄鸡蛋面",
        "土豆烧肉饭",
        "鱼香肉丝饭",
        "麻辣香锅",
        "青椒肉丝饭",
        "红烧排骨饭",
        "时蔬套餐",
    ]

    dishes = []
    for index, base_name in enumerate(base_names, start=1):
        price = Decimal(str(10 + index * 1.5)).quantize(Decimal("0.00"))
        original_price = (price + Decimal("2.00")).quantize(Decimal("0.00"))
        dishes.append(
            Dish(
                canteen_id=canteen.canteen_id,
                category_id=0,
                name=f"{window}-{base_name}{index}",
                description=f"{label}{window}测试菜品 {index}，图片待上传",
                price=price,
                original_price=original_price,
                spicy_level=index % 4,
                allergen=None,
                calorie=350 + index * 20,
                images=None,
                stock=100,
                sales=0,
                status=1,
                media_path=None,
                media_type=None,
                view_count=0,
                favorite_count=0,
            )
        )
    return dishes


def main():
    db = SessionLocal()
    try:
        db.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        deleted = db.query(Dish).delete(synchronize_session=False)
        db.execute(text("SET FOREIGN_KEY_CHECKS = 1"))

        canteens = db.query(Canteen).filter(Canteen.status == 1).order_by(Canteen.canteen_id.asc()).all()

        created = 0
        for canteen in canteens:
            dishes = build_dishes_for_canteen(canteen)
            db.add_all(dishes)
            created += len(dishes)

        db.commit()
        print({
            "deleted_dishes": deleted,
            "active_canteens": len(canteens),
            "created_dishes": created,
        })
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

