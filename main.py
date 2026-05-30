# -*- coding: utf-8 -*-
"""
스마트 재고 관리 AI 시스템 - 소상공인 F&B용
전체 플로우 시연: 초기 데이터 설정 -> 입고 -> 판매 -> 폐기 -> 알림 -> 대시보드
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")

from database import init_db
from incoming_service import register_ingredient, register_conversion, process_incoming
from sales_service import add_recipe, process_sale
from alert_service import print_alerts
from advanced_features import register_waste, adjust_inventory, get_dashboard_data


def seed_master_data():
    """마스터 데이터: 식재료, 단위 환산, 레시피 등록"""
    ingredients = [
        ("양파",   "g",  1000),
        ("마늘",   "g",   500),
        ("대파",   "g",   300),
        ("삼겹살", "g",  2000),
        ("두부",   "ea",    2),
    ]
    ids = {}
    for name, unit, safety in ingredients:
        r = register_ingredient(name, unit, safety)
        if r["success"]:
            ids[name] = r["ingredient_id"]
            print(f"  [등록] {name} (안전재고: {safety}{unit})")
        else:
            # 이미 등록된 경우 DB에서 ID 조회
            from database import get_connection
            with get_connection() as conn:
                row = conn.execute("SELECT id FROM ingredients WHERE name = ?", (name,)).fetchone()
                ids[name] = row["id"]

    conversions = [
        ("양파",   "망",  5000),
        ("마늘",   "통",  1000),
        ("대파",   "단",   200),
        ("삼겹살", "근",   600),
        ("두부",   "모",     1),
    ]
    for ing_name, unit, factor in conversions:
        register_conversion(ids[ing_name], unit, factor)

    recipes_data = [
        ("양파볶음",  "양파",   200.0),
        ("삼겹살구이","삼겹살", 150.0),
        ("삼겹살구이","대파",    50.0),
        ("순두부찌개","두부",     1.0),
        ("순두부찌개","마늘",    20.0),
    ]
    for menu, ing_name, amount in recipes_data:
        add_recipe(menu, ids[ing_name], amount)

    return ids


def run_demo():
    print("=" * 55)
    print("  스마트 재고 관리 AI 시스템  |  F&B 소상공인용")
    print("=" * 55)

    init_db()
    print("\n[0] 마스터 데이터 초기화")
    print("-" * 40)
    ids = seed_master_data()

    # 1. 입고 처리
    print("\n[1] 입고 처리 (OCR 자동 매칭)")
    print("-" * 40)
    incoming_data = [
        ("양파 1망",   2, "망",  4000),
        ("깐마늘",     3, "통",  9000),
        ("대파 3단",   3, "단",  3000),
        ("삼겹살",     4, "근", 20000),
        ("두부 2모",   2, "모",  2400),
        ("감자",       1, "kg",  None),  # 미등록 재료 - 에러 처리 확인
    ]
    for scanned, qty, unit, price in incoming_data:
        r = process_incoming(scanned, qty, unit, price)
        if r["success"]:
            print(
                f"  [OK] '{scanned}' -> {r['ingredient_name']} "
                f"{r['converted_quantity']}{r['unit']} 입고 "
                f"(현재고: {r['new_stock']}{r['unit']})"
            )
        else:
            print(f"  [ERR] {r['error']}")

    # 2. 판매 소진
    print("\n[2] 판매 처리 (BOM 자동 소진)")
    print("-" * 40)
    sales = [
        ("양파볶음",   5),
        ("삼겹살구이", 8),
        ("순두부찌개", 3),
        ("비빔밥",     2),  # 미등록 메뉴 - 에러 처리 확인
    ]
    for menu, count in sales:
        r = process_sale(menu, count)
        if r["success"]:
            print(f"  [OK] {menu} {count}개 판매")
            for d in r["deductions"]:
                print(f"       - {d['name']}: {d['used']}{d['unit']} 차감")
        else:
            print(f"  [ERR] {r['error']}")

    # 3. 폐기(로스) 등록
    print("\n[3] 폐기(Loss) 등록")
    print("-" * 40)
    wastes = [
        (ids["양파"],   200, "유통기한 경과"),
        (ids["마늘"],    50, "변질"),
    ]
    for ing_id, qty, reason in wastes:
        r = register_waste(ing_id, qty, reason)
        if r["success"]:
            print(f"  [OK] {r['ingredient_name']} {r['quantity']}{r['unit']} 폐기 ({reason})")
        else:
            print(f"  [ERR] {r['error']}")

    # 4. 실사 보정
    print("\n[4] 재고 실사 보정")
    print("-" * 40)
    r = adjust_inventory(ids["대파"], 450, "월말 실사")
    if r["success"]:
        print(
            f"  [OK] {r['ingredient_name']}: "
            f"{r['old_stock']}{r['unit']} -> {r['new_stock']}{r['unit']} "
            f"(차이: {r['diff']:+.0f}{r['unit']})"
        )

    # 5. 재고 부족 알림
    print("\n[5] 재고 부족 알림 / 발주 추천")
    print("-" * 40)
    print_alerts()

    # 6. 대시보드
    print("\n[6] 대시보드 종합 현황")
    print("-" * 40)
    data = get_dashboard_data()

    print("  [재고 현황]")
    for s in data["stock"]:
        status = "WARN" if s["current_stock"] <= s["safety_stock"] else "OK  "
        print(
            f"  [{status}] {s['name']:<6} "
            f"{s['current_stock']:>8.0f}{s['base_unit']} "
            f"(안전재고: {s['safety_stock']}{s['base_unit']})"
        )

    if data["waste"]:
        print("\n  [폐기 누계]")
        for w in data["waste"]:
            print(f"        {w['name']:<6} 총 {w['total_waste']:.0f}{w['base_unit']} 폐기")

    if data["incoming"]:
        print("\n  [입고 누계]")
        for inc in data["incoming"]:
            print(f"        {inc['name']:<6} 총 {inc['total_incoming']:.0f}{inc['base_unit']} 입고")

    print("\n" + "=" * 55)
    print("  시연 완료")
    print("=" * 55)


if __name__ == "__main__":
    run_demo()
