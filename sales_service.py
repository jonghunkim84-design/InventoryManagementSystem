import uuid
from database import get_connection


def process_sale(menu_name: str, order_count: int) -> dict:
    """
    POS 판매 데이터를 입력받아 recipes(BOM) 기반으로 재고를 자동 차감한다.
    재고 부족 시 처리하지 않고 에러를 반환한다.
    """
    with get_connection() as conn:
        recipes = conn.execute(
            "SELECT ingredient_id, usage_amount FROM recipes WHERE menu_name = ?",
            (menu_name,),
        ).fetchall()

        if not recipes:
            return {"success": False, "error": f"등록되지 않은 메뉴: '{menu_name}'"}

        deductions = []
        for row in recipes:
            ingredient_id = row["ingredient_id"]
            total_usage = row["usage_amount"] * order_count

            ing = conn.execute(
                "SELECT name, current_stock, base_unit FROM ingredients WHERE id = ?",
                (ingredient_id,),
            ).fetchone()

            if ing["current_stock"] < total_usage:
                return {
                    "success": False,
                    "error": (
                        f"재고 부족 - {ing['name']}: "
                        f"필요 {total_usage}{ing['base_unit']}, "
                        f"현재 {ing['current_stock']}{ing['base_unit']}"
                    ),
                }
            deductions.append({
                "ingredient_id": ingredient_id,
                "name": ing["name"],
                "used": total_usage,
                "unit": ing["base_unit"],
            })

        for d in deductions:
            conn.execute(
                "UPDATE ingredients SET current_stock = current_stock - ? WHERE id = ?",
                (d["used"], d["ingredient_id"]),
            )

        return {"success": True, "menu": menu_name, "count": order_count, "deductions": deductions}


def add_recipe(menu_name: str, ingredient_id: str, usage_amount: float) -> dict:
    """메뉴에 식재료 BOM 항목을 추가한다."""
    with get_connection() as conn:
        ing = conn.execute("SELECT name FROM ingredients WHERE id = ?", (ingredient_id,)).fetchone()
        if not ing:
            return {"success": False, "error": f"존재하지 않는 재료 ID: '{ingredient_id}'"}

        existing = conn.execute(
            "SELECT id FROM recipes WHERE menu_name = ? AND ingredient_id = ?",
            (menu_name, ingredient_id),
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE recipes SET usage_amount = ? WHERE id = ?",
                (usage_amount, existing["id"]),
            )
            return {"success": True, "updated": True, "menu": menu_name, "ingredient": ing["name"]}

        recipe_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO recipes (id, menu_name, ingredient_id, usage_amount) VALUES (?, ?, ?, ?)",
            (recipe_id, menu_name, ingredient_id, usage_amount),
        )
        return {"success": True, "recipe_id": recipe_id, "menu": menu_name, "ingredient": ing["name"]}


def get_recipe(menu_name: str) -> list[dict]:
    """메뉴의 BOM 목록을 반환한다."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT r.usage_amount, i.name, i.base_unit
            FROM recipes r
            JOIN ingredients i ON r.ingredient_id = i.id
            WHERE r.menu_name = ?
            """,
            (menu_name,),
        ).fetchall()
        return [dict(row) for row in rows]
