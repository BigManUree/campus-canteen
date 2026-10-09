import sys
sys.path.insert(0, r"C:/Users/BigMan/Desktop/server-python")

from sqlalchemy import create_engine, text
from app.core.config import get_settings

engine = create_engine(get_settings().database_url)

statements = [
    "UPDATE dish_categories SET canteen_id = 136 WHERE category_id IN (146, 148, 149, 150, 151) AND canteen_id IS NULL",
    "UPDATE dish_categories SET canteen_id = 136 WHERE category_id = 163 AND canteen_id IS NULL",
    "UPDATE dish_categories SET canteen_id = 136 WHERE category_id = 164 AND canteen_id IS NULL",
    "UPDATE dish_categories SET canteen_id = 137 WHERE category_id = 167 AND canteen_id IS NULL",
    "INSERT INTO dish_categories (category_name, canteen_id) SELECT '盖饭', 137 FROM DUAL WHERE NOT EXISTS (SELECT 1 FROM dish_categories WHERE category_name = '盖饭' AND canteen_id = 137)",
    "INSERT INTO dish_categories (category_name, canteen_id) SELECT '盖饭', 138 FROM DUAL WHERE NOT EXISTS (SELECT 1 FROM dish_categories WHERE category_name = '盖饭' AND canteen_id = 138)",
    "INSERT INTO dish_categories (category_name, canteen_id) SELECT '盖饭', 148 FROM DUAL WHERE NOT EXISTS (SELECT 1 FROM dish_categories WHERE category_name = '盖饭' AND canteen_id = 148)",
    "INSERT INTO dish_categories (category_name, canteen_id) SELECT '面食', 137 FROM DUAL WHERE NOT EXISTS (SELECT 1 FROM dish_categories WHERE category_name = '面食' AND canteen_id = 137)",
    "INSERT INTO dish_categories (category_name, canteen_id) SELECT '面食', 138 FROM DUAL WHERE NOT EXISTS (SELECT 1 FROM dish_categories WHERE category_name = '面食' AND canteen_id = 138)",
    "INSERT INTO dish_categories (category_name, canteen_id) SELECT '面食', 148 FROM DUAL WHERE NOT EXISTS (SELECT 1 FROM dish_categories WHERE category_name = '面食' AND canteen_id = 148)",
    "INSERT INTO dish_categories (category_name, canteen_id) SELECT '主食', 148 FROM DUAL WHERE NOT EXISTS (SELECT 1 FROM dish_categories WHERE category_name = '主食' AND canteen_id = 148)",
    "UPDATE dishes d JOIN dish_categories old_dc ON old_dc.category_id = d.category_id JOIN dish_categories new_dc ON new_dc.category_name = old_dc.category_name AND new_dc.canteen_id = d.canteen_id SET d.category_id = new_dc.category_id WHERE d.category_id IN (163, 164, 167) AND d.canteen_id <> old_dc.canteen_id",
]

with engine.begin() as conn:
    for stmt in statements:
        conn.execute(text(stmt))

    mismatch = conn.execute(text("SELECT COUNT(*) FROM dishes d JOIN dish_categories dc ON d.category_id = dc.category_id WHERE dc.canteen_id IS NOT NULL AND d.canteen_id != dc.canteen_id")).scalar()
    nulls = conn.execute(text("SELECT COUNT(*) FROM dish_categories WHERE canteen_id IS NULL")).scalar()
    remaining = conn.execute(text("SELECT category_id, category_name FROM dish_categories WHERE canteen_id IS NULL ORDER BY category_id")).fetchall()

print(f"mismatch_count={mismatch}")
print(f"null_count={nulls}")
if remaining:
    print("remaining_null_categories=")
    for row in remaining:
        print(f"  {row.category_id} {row.category_name}")

