import uuid
from database import get_connection
from ocr_matcher import find_best_match


def process_incoming(scanned_name: str, quantity: float, unit_name: str, total_price: int = None) -> dict:
    """
    OCR로 스캔된 입고 데이터를 처리한다.
    - 식재료명 AI 매칭 -> 단위 환산 -> incoming_logs 저장 -> 재고 증가
    """
    with get_connection() as conn:
        ingredient_id = find_best_match(scanned_name, conn=conn)
        if not ingredient_id:
            return {"success": False, "error": f"등록되지 않은 재료: '{scanned_name}'"}

        row = conn.execute(
            "SELECT conversion_factor FROM ingredient_conversions WHERE ingredient_id = ? AND unit_name = ?",
            (ingredient_id, unit_name),
        ).fetchone()
        conversion_factor = row["conversion_factor"] if row else 1.0
        converted_quantity = quantity * conversion_factor

        log_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO incoming_logs (id, ingredient_id, quantity, total_price) VALUES (?, ?, ?, ?)",
            (log_id, ingredient_id, converted_quantity, total_price),
        )
        conn.execute(
            "UPDATE ingredients SET current_stock = current_stock + ? WHERE id = ?",
            (converted_quantity, ingredient_id),
        )

        ing = conn.execute(
            "SELECT name, current_stock, base_unit FROM ingredients WHERE id = ?",
            (ingredient_id,),
        ).fetchone()

        return {
            "success": True,
            "log_id": log_id,
            "ingredient_id": ingredient_id,
            "ingredient_name": ing["name"],
            "converted_quantity": converted_quantity,
            "new_stock": ing["current_stock"],
            "unit": ing["base_unit"],
        }


def register_ingredient(name: str, base_unit: str, safety_stock: float = 0) -> dict:
    """새 식재료를 마스터에 등록한다."""
    with get_connection() as conn:
        existing = conn.execute("SELECT id FROM ingredients WHERE name = ?", (name,)).fetchone()
        if existing:
            return {"success": False, "error": f"이미 등록된 재료: '{name}'"}

        ing_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO ingredients (id, name, base_unit, safety_stock) VALUES (?, ?, ?, ?)",
            (ing_id, name, base_unit, safety_stock),
        )
        return {"success": True, "ingredient_id": ing_id, "name": name}


def register_conversion(ingredient_id: str, unit_name: str, conversion_factor: float) -> dict:
    """식재료의 입고 단위 환산 비율을 등록한다. (예: '망' -> 5000g)"""
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT id FROM ingredient_conversions WHERE ingredient_id = ? AND unit_name = ?",
            (ingredient_id, unit_name),
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE ingredient_conversions SET conversion_factor = ? WHERE id = ?",
                (conversion_factor, existing["id"]),
            )
            return {"success": True, "updated": True}

        conv_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO ingredient_conversions (id, ingredient_id, unit_name, conversion_factor) VALUES (?, ?, ?, ?)",
            (conv_id, ingredient_id, unit_name, conversion_factor),
        )
        return {"success": True, "conversion_id": conv_id}
