import uuid
from database import get_connection


def register_waste(ingredient_id: str, quantity: float, reason: str) -> dict:
    """폐기(로스)를 기록하고 재고를 차감한다."""
    with get_connection() as conn:
        ing = conn.execute(
            "SELECT name, current_stock, base_unit FROM ingredients WHERE id = ?",
            (ingredient_id,),
        ).fetchone()
        if not ing:
            return {"success": False, "error": f"존재하지 않는 재료 ID: '{ingredient_id}'"}

        waste_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO waste_logs (id, ingredient_id, quantity, reason) VALUES (?, ?, ?, ?)",
            (waste_id, ingredient_id, quantity, reason),
        )
        conn.execute(
            "UPDATE ingredients SET current_stock = current_stock - ? WHERE id = ?",
            (quantity, ingredient_id),
        )

        return {
            "success": True,
            "waste_id": waste_id,
            "ingredient_name": ing["name"],
            "quantity": quantity,
            "unit": ing["base_unit"],
            "reason": reason,
        }


def adjust_inventory(ingredient_id: str, new_amount: float, reason: str) -> dict:
    """
    실사(재고 실사) 결과로 재고를 보정한다.
    차이(조정량)를 inventory_adjustments에 기록한다.
    """
    with get_connection() as conn:
        ing = conn.execute(
            "SELECT name, current_stock, base_unit FROM ingredients WHERE id = ?",
            (ingredient_id,),
        ).fetchone()
        if not ing:
            return {"success": False, "error": f"존재하지 않는 재료 ID: '{ingredient_id}'"}

        diff = new_amount - ing["current_stock"]
        adj_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO inventory_adjustments (id, ingredient_id, adjustment_amount, reason) VALUES (?, ?, ?, ?)",
            (adj_id, ingredient_id, diff, reason),
        )
        conn.execute(
            "UPDATE ingredients SET current_stock = ? WHERE id = ?",
            (new_amount, ingredient_id),
        )

        return {
            "success": True,
            "adjustment_id": adj_id,
            "ingredient_name": ing["name"],
            "old_stock": ing["current_stock"],
            "new_stock": new_amount,
            "diff": diff,
            "unit": ing["base_unit"],
        }


def get_dashboard_data() -> dict:
    """대시보드용 통합 데이터를 반환한다 (재고 현황, 폐기 누계, 입고 누계)."""
    with get_connection() as conn:
        stock = conn.execute(
            "SELECT name, current_stock, safety_stock, base_unit FROM ingredients ORDER BY name"
        ).fetchall()

        waste = conn.execute(
            """
            SELECT i.name, SUM(w.quantity) AS total_waste, i.base_unit
            FROM waste_logs w
            JOIN ingredients i ON w.ingredient_id = i.id
            GROUP BY w.ingredient_id
            ORDER BY total_waste DESC
            """
        ).fetchall()

        incoming = conn.execute(
            """
            SELECT i.name, SUM(l.quantity) AS total_incoming, i.base_unit
            FROM incoming_logs l
            JOIN ingredients i ON l.ingredient_id = i.id
            GROUP BY l.ingredient_id
            ORDER BY i.name
            """
        ).fetchall()

        return {
            "stock": [dict(row) for row in stock],
            "waste": [dict(row) for row in waste],
            "incoming": [dict(row) for row in incoming],
        }
