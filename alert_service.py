from database import get_connection


def check_inventory_alerts() -> list[dict]:
    """안전재고 미달 품목을 조회하고 권장 발주량을 포함하여 반환한다."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, name, current_stock, safety_stock, base_unit
            FROM ingredients
            WHERE current_stock <= safety_stock
            ORDER BY (current_stock - safety_stock) ASC
            """
        ).fetchall()

        alerts = []
        for row in rows:
            alerts.append({
                "ingredient_id": row["id"],
                "name": row["name"],
                "current_stock": row["current_stock"],
                "safety_stock": row["safety_stock"],
                "unit": row["base_unit"],
                "order_recommendation": row["safety_stock"] * 2,
            })
        return alerts


def get_stock_summary() -> list[dict]:
    """전체 식재료의 재고 현황을 반환한다."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, name, current_stock, safety_stock, base_unit FROM ingredients ORDER BY name"
        ).fetchall()
        return [dict(row) for row in rows]


def print_alerts():
    """콘솔에 재고 부족 알림 및 발주 추천을 출력한다."""
    alerts = check_inventory_alerts()
    if alerts:
        print("--- [알림] 재고 부족 품목 발생 ---")
        for a in alerts:
            print(
                f"  품목: {a['name']} | "
                f"현재고: {a['current_stock']}{a['unit']} | "
                f"안전재고: {a['safety_stock']}{a['unit']}"
            )
            print(f"  --> 권장 발주량: {a['order_recommendation']}{a['unit']}")
    else:
        print("  모든 재고가 안전 수준입니다.")
    return alerts
