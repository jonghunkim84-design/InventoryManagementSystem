# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding="utf-8")

from flask import Flask, render_template, request, redirect, url_for, flash
from database import init_db, get_connection
from incoming_service import process_incoming
from sales_service import process_sale
from alert_service import check_inventory_alerts, get_stock_summary
from advanced_features import register_waste, adjust_inventory, get_dashboard_data

app = Flask(__name__)
app.secret_key = "inventory-secret-key"


@app.route("/")
def dashboard():
    data = get_dashboard_data()
    alerts = check_inventory_alerts()

    with get_connection() as conn:
        recent_incoming = conn.execute(
            """
            SELECT i.name, l.quantity, l.scanned_at, i.base_unit
            FROM incoming_logs l
            JOIN ingredients i ON l.ingredient_id = i.id
            ORDER BY l.scanned_at DESC LIMIT 10
            """
        ).fetchall()
        total_waste_count = conn.execute("SELECT COUNT(*) FROM waste_logs").fetchone()[0]

    return render_template(
        "dashboard.html",
        active="dashboard",
        stock=data["stock"],
        waste=data["waste"],
        recent_incoming=[dict(r) for r in recent_incoming],
        alert_count=len(alerts),
        total_waste_count=total_waste_count,
    )


@app.route("/incoming", methods=["GET", "POST"])
def incoming():
    if request.method == "POST":
        scanned_name = request.form["scanned_name"].strip()
        quantity = float(request.form["quantity"])
        unit_name = request.form["unit_name"]
        total_price = request.form.get("total_price")
        total_price = int(total_price) if total_price else None

        result = process_incoming(scanned_name, quantity, unit_name, total_price)
        if result["success"]:
            flash(
                f"입고 완료: {result['ingredient_name']} {result['converted_quantity']:.0f}{result['unit']} "
                f"(현재고: {result['new_stock']:.0f}{result['unit']})",
                "success",
            )
        else:
            flash(result["error"], "error")
        return redirect(url_for("incoming"))

    with get_connection() as conn:
        logs = conn.execute(
            """
            SELECT i.name, l.quantity, l.total_price, l.scanned_at, i.base_unit
            FROM incoming_logs l
            JOIN ingredients i ON l.ingredient_id = i.id
            ORDER BY l.scanned_at DESC LIMIT 20
            """
        ).fetchall()
        units = conn.execute(
            "SELECT DISTINCT unit_name FROM ingredient_conversions ORDER BY unit_name"
        ).fetchall()

    return render_template(
        "incoming.html",
        active="incoming",
        logs=[dict(r) for r in logs],
        units=[r["unit_name"] for r in units],
    )


@app.route("/sales", methods=["GET", "POST"])
def sales():
    if request.method == "POST":
        menu_name = request.form["menu_name"]
        order_count = int(request.form["order_count"])

        result = process_sale(menu_name, order_count)
        if result["success"]:
            deductions = ", ".join(
                f"{d['name']} {d['used']:.0f}{d['unit']}" for d in result["deductions"]
            )
            flash(f"{menu_name} {order_count}개 판매 완료 | 차감: {deductions}", "success")
        else:
            flash(result["error"], "error")
        return redirect(url_for("sales"))

    with get_connection() as conn:
        menus = conn.execute(
            "SELECT DISTINCT menu_name FROM recipes ORDER BY menu_name"
        ).fetchall()
        recipes = conn.execute(
            """
            SELECT r.menu_name, i.name, r.usage_amount, i.base_unit
            FROM recipes r
            JOIN ingredients i ON r.ingredient_id = i.id
            ORDER BY r.menu_name, i.name
            """
        ).fetchall()

    return render_template(
        "sales.html",
        active="sales",
        menus=[r["menu_name"] for r in menus],
        recipes=[dict(r) for r in recipes],
    )


@app.route("/waste", methods=["GET", "POST"])
def waste():
    if request.method == "POST":
        ingredient_id = request.form["ingredient_id"]
        quantity = float(request.form["quantity"])
        reason = request.form["reason"]

        result = register_waste(ingredient_id, quantity, reason)
        if result["success"]:
            flash(
                f"폐기 등록 완료: {result['ingredient_name']} {result['quantity']:.0f}{result['unit']} ({reason})",
                "success",
            )
        else:
            flash(result["error"], "error")
        return redirect(url_for("waste"))

    with get_connection() as conn:
        ingredients = conn.execute(
            "SELECT id, name, current_stock, base_unit FROM ingredients ORDER BY name"
        ).fetchall()
        logs = conn.execute(
            """
            SELECT i.name, w.quantity, w.reason, w.created_at, i.base_unit
            FROM waste_logs w
            JOIN ingredients i ON w.ingredient_id = i.id
            ORDER BY w.created_at DESC LIMIT 20
            """
        ).fetchall()

    return render_template(
        "waste.html",
        active="waste",
        ingredients=[dict(r) for r in ingredients],
        logs=[dict(r) for r in logs],
    )


@app.route("/adjust", methods=["GET", "POST"])
def adjust():
    if request.method == "POST":
        ingredient_id = request.form["ingredient_id"]
        new_amount = float(request.form["new_amount"])
        reason = request.form["reason"].strip()

        result = adjust_inventory(ingredient_id, new_amount, reason)
        if result["success"]:
            flash(
                f"재고 보정 완료: {result['ingredient_name']} "
                f"{result['old_stock']:.0f} → {result['new_stock']:.0f}{result['unit']} "
                f"(차이: {result['diff']:+.0f}{result['unit']})",
                "success",
            )
        else:
            flash(result["error"], "error")
        return redirect(url_for("adjust"))

    with get_connection() as conn:
        ingredients = conn.execute(
            "SELECT id, name, current_stock, base_unit FROM ingredients ORDER BY name"
        ).fetchall()
        logs = conn.execute(
            """
            SELECT i.name, a.adjustment_amount, a.reason, a.created_at, i.base_unit
            FROM inventory_adjustments a
            JOIN ingredients i ON a.ingredient_id = i.id
            ORDER BY a.created_at DESC LIMIT 20
            """
        ).fetchall()

    return render_template(
        "adjust.html",
        active="adjust",
        ingredients=[dict(r) for r in ingredients],
        logs=[dict(r) for r in logs],
    )


@app.route("/alerts")
def alerts():
    return render_template(
        "alerts.html",
        active="alerts",
        alerts=check_inventory_alerts(),
        stock=get_stock_summary(),
    )


if __name__ == "__main__":
    init_db()
    print("서버 시작: http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
