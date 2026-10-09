from decimal import Decimal
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.session import SessionLocal
from app.models.canteen import Canteen
from app.models.dish import Dish
from app.models.category import DishCategory

CATEGORY_DEFINITIONS = [
    ("盖饭", 1),
    ("面食", 2),
    ("特色菜", 3),
    ("轻食", 4),
    ("主食", 5),
    ("蒸饭", 6),
    ("粥品", 7),
]

MENU_TEMPLATES = {
    "北区食堂": [
        {"name": "奥尔良鸡腿饭", "price": "16.80", "original_price": "19.80", "desc": "整只奥尔良鸡腿现烤现切，配时蔬和溏心蛋。", "stock": 58, "category": "盖饭", "spicy": 1},
        {"name": "黑椒牛柳盖饭", "price": "18.80", "original_price": "22.80", "desc": "黑椒牛柳鲜嫩入味，搭配洋葱和彩椒。", "stock": 42, "category": "盖饭", "spicy": 0},
        {"name": "香菇滑鸡饭", "price": "15.80", "original_price": "18.80", "desc": "鸡腿肉配香菇小火焖煮，口感鲜香下饭。", "stock": 47, "category": "盖饭", "spicy": 0},
        {"name": "番茄肥牛面", "price": "17.80", "original_price": "20.80", "desc": "酸甜番茄汤底，肥牛卷现煮更开胃。", "stock": 33, "category": "面食", "spicy": 0},
        {"name": "麻辣香锅套餐", "price": "21.80", "original_price": "25.80", "desc": "荤素搭配可口过瘾，香辣浓郁适合重口味。", "stock": 26, "category": "特色菜", "spicy": 3},
        {"name": "鱼香肉丝饭", "price": "14.80", "original_price": "17.80", "desc": "经典川味小炒，酸甜鲜辣层次分明。", "stock": 61, "category": "盖饭", "spicy": 2},
        {"name": "照烧鸡排饭", "price": "16.80", "original_price": "19.80", "desc": "厚切鸡排外酥里嫩，照烧酱汁浓郁。", "stock": 39, "category": "盖饭", "spicy": 0},
        {"name": "青椒肉丝饭", "price": "15.20", "original_price": "18.20", "desc": "现炒青椒肉丝锅气足，家常口味更耐吃。", "stock": 44, "category": "盖饭", "spicy": 1},
        {"name": "红烧排骨饭", "price": "19.80", "original_price": "23.80", "desc": "排骨软烂入味，搭配卤汁米饭更香。", "stock": 28, "category": "盖饭", "spicy": 0},
        {"name": "双拼时蔬套餐", "price": "13.80", "original_price": "16.80", "desc": "两样时蔬加溏心蛋，清爽低负担。", "stock": 52, "category": "轻食", "spicy": 0},
    ],
    "中区食堂": [
        {"name": "台式卤肉饭", "price": "15.80", "original_price": "18.80", "desc": "卤汁浓香拌饭，肥瘦相间更有满足感。", "stock": 66, "category": "盖饭", "spicy": 0},
        {"name": "藤椒鸡块饭", "price": "16.80", "original_price": "19.80", "desc": "藤椒风味清麻鲜香，鸡块嫩滑弹牙。", "stock": 37, "category": "盖饭", "spicy": 2},
        {"name": "黄焖鸡米饭", "price": "17.80", "original_price": "20.80", "desc": "砂锅慢炖更入味，汤汁拌饭非常下饭。", "stock": 49, "category": "盖饭", "spicy": 1},
        {"name": "酸菜肉丝米线", "price": "14.80", "original_price": "17.80", "desc": "酸菜开胃，汤底清爽，适合午间快餐。", "stock": 31, "category": "面食", "spicy": 1},
        {"name": "椒盐鸡柳饭", "price": "16.20", "original_price": "19.20", "desc": "外酥里嫩的鸡柳搭配椒盐风味，越吃越香。", "stock": 40, "category": "盖饭", "spicy": 0},
        {"name": "宫保鸡丁饭", "price": "15.80", "original_price": "18.80", "desc": "微辣微甜的经典做法，花生增香更过瘾。", "stock": 55, "category": "盖饭", "spicy": 2},
        {"name": "咖喱土豆牛肉饭", "price": "18.80", "original_price": "22.80", "desc": "日式咖喱顺滑浓郁，牛肉软嫩土豆绵密。", "stock": 29, "category": "盖饭", "spicy": 0},
        {"name": "鲜椒肥肠面", "price": "19.80", "original_price": "23.80", "desc": "鲜椒香辣十足，肥肠处理干净无异味。", "stock": 22, "category": "面食", "spicy": 3},
        {"name": "肉末茄子饭", "price": "14.20", "original_price": "17.20", "desc": "茄子软糯吸汁，肉末浓香很适合拌饭。", "stock": 45, "category": "盖饭", "spicy": 1},
        {"name": "鸡蛋火腿炒饭", "price": "13.80", "original_price": "15.80", "desc": "粒粒分明的家常炒饭，出餐快适合赶时间。", "stock": 63, "category": "主食", "spicy": 0},
    ],
    "南区食堂": [
        {"name": "招牌猪脚饭", "price": "18.80", "original_price": "22.80", "desc": "猪脚软糯胶质丰富，卤香浓郁不腻口。", "stock": 34, "category": "盖饭", "spicy": 0},
        {"name": "蒜香鸡扒饭", "price": "17.20", "original_price": "20.20", "desc": "鸡扒现煎香气足，蒜香酱汁很提味。", "stock": 41, "category": "盖饭", "spicy": 0},
        {"name": "泡椒牛肉饭", "price": "18.20", "original_price": "21.20", "desc": "泡椒酸辣开胃，牛肉嫩滑有嚼劲。", "stock": 27, "category": "盖饭", "spicy": 3},
        {"name": "酸辣土豆丝饭", "price": "12.80", "original_price": "14.80", "desc": "家常快炒酸辣爽口，适合想吃清爽口味。", "stock": 59, "category": "盖饭", "spicy": 2},
        {"name": "老坛酸菜鱼片面", "price": "17.80", "original_price": "20.80", "desc": "鱼片嫩滑，酸菜汤底鲜爽有层次。", "stock": 25, "category": "面食", "spicy": 2},
        {"name": "香酥鸡排饭", "price": "16.80", "original_price": "19.80", "desc": "大块鸡排现炸现切，外酥内嫩口感扎实。", "stock": 38, "category": "盖饭", "spicy": 0},
        {"name": "梅菜扣肉饭", "price": "17.80", "original_price": "20.80", "desc": "扣肉肥而不腻，梅菜咸香特别下饭。", "stock": 32, "category": "盖饭", "spicy": 0},
        {"name": "番茄鸡蛋盖饭", "price": "13.20", "original_price": "15.20", "desc": "酸甜番茄搭配嫩滑鸡蛋，经典又百搭。", "stock": 57, "category": "盖饭", "spicy": 0},
        {"name": "豉汁排骨蒸饭", "price": "18.80", "original_price": "21.80", "desc": "豉汁香气浓厚，排骨软嫩，米饭吸满肉汁。", "stock": 24, "category": "蒸饭", "spicy": 0},
        {"name": "鲜蔬鸡丝粥套餐", "price": "12.80", "original_price": "14.80", "desc": "口味清淡顺口，适合早餐或晚间轻食。", "stock": 46, "category": "粥品", "spicy": 0},
    ],
    "嘉园食堂": [
        {"name": "铁板黑椒鸡柳饭", "price": "17.80", "original_price": "20.80", "desc": "铁板现炒香气扑鼻，鸡柳鲜嫩多汁。", "stock": 36, "category": "盖饭", "spicy": 1},
        {"name": "照烧肥牛饭", "price": "19.80", "original_price": "23.80", "desc": "肥牛片搭配照烧洋葱汁，咸甜平衡更开胃。", "stock": 28, "category": "盖饭", "spicy": 0},
        {"name": "川香辣子鸡饭", "price": "18.80", "original_price": "21.80", "desc": "鸡块酥香配干辣椒，香辣过瘾更下饭。", "stock": 30, "category": "盖饭", "spicy": 3},
        {"name": "菌菇鸡汤面", "price": "15.80", "original_price": "18.80", "desc": "菌菇鲜香融入鸡汤，口感温润适合四季。", "stock": 43, "category": "面食", "spicy": 0},
        {"name": "香辣烤肠炒饭", "price": "14.80", "original_price": "16.80", "desc": "烤肠粒搭配青豆玉米，炒饭颗粒分明。", "stock": 54, "category": "主食", "spicy": 1},
        {"name": "金汤肥牛米线", "price": "18.20", "original_price": "21.20", "desc": "金汤酸辣浓郁，肥牛和米线搭配很过瘾。", "stock": 26, "category": "面食", "spicy": 2},
        {"name": "蒜苔肉丝饭", "price": "15.20", "original_price": "17.20", "desc": "蒜苔清脆，肉丝滑嫩，经典快炒锅气十足。", "stock": 48, "category": "盖饭", "spicy": 1},
        {"name": "香辣鸡米花盖饭", "price": "16.80", "original_price": "19.80", "desc": "鸡米花酥脆可口，搭配甜辣酱更受欢迎。", "stock": 39, "category": "盖饭", "spicy": 2},
        {"name": "双椒鸡杂饭", "price": "17.20", "original_price": "20.20", "desc": "鸡杂爽脆，双椒香辣，适合喜欢重口味。", "stock": 21, "category": "盖饭", "spicy": 3},
        {"name": "皮蛋瘦肉粥套餐", "price": "12.80", "original_price": "14.80", "desc": "米香浓郁，皮蛋瘦肉搭配油条更经典。", "stock": 51, "category": "粥品", "spicy": 0},
    ],
}


def ensure_categories(db):
    category_map = {}
    existing = {c.category_name: c for c in db.query(DishCategory).all()}
    for sort_order, (name, parent_id) in enumerate(CATEGORY_DEFINITIONS, start=1):
        category = existing.get(name)
        if not category:
            category = DishCategory(category_name=name, parent_id=parent_id, sort_order=sort_order)
            db.add(category)
            db.flush()
        else:
            category.parent_id = parent_id
            category.sort_order = sort_order
        category_map[name] = category.category_id
    return category_map


def main():
    db = SessionLocal()
    try:
        category_map = ensure_categories(db)
        canteens = db.query(Canteen).filter(Canteen.status == 1).order_by(Canteen.canteen_id.asc()).all()

        summary = []
        for canteen in canteens:
            dishes = db.query(Dish).filter(Dish.canteen_id == canteen.canteen_id).order_by(Dish.dish_id.asc()).all()
            templates = MENU_TEMPLATES.get(canteen.canteen_name, MENU_TEMPLATES.get('北区食堂', []))

            for dish, template in zip(dishes, templates):
                dish.name = template['name']
                dish.price = Decimal(template['price'])
                dish.original_price = Decimal(template['original_price'])
                dish.description = template['desc']
                dish.category_id = category_map[template['category']]
                dish.stock = template['stock']
                dish.spicy_level = template['spicy']

            summary.append({
                'canteen_id': canteen.canteen_id,
                'canteen_name': canteen.canteen_name,
                'updated_dishes': min(len(dishes), len(templates)),
            })

        db.commit()
        print({
            'updated_canteens': len(summary),
            'summary': summary,
            'category_map': category_map,
        })
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == '__main__':
    main()
