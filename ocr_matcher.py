import difflib
from database import get_connection


def find_best_match(scanned_name: str, threshold: float = 0.3, conn=None) -> str | None:
    """
    스캔된 식재료명을 DB 등록 식재료와 매칭하여 ingredient_id 반환.
    1순위: 부분 문자열 포함 여부 (예: '깐마늘' -> '마늘', '양파 1망' -> '양파')
    2순위: difflib 유사도 기반 퍼지 매칭
    """
    if conn is not None:
        return _match(scanned_name, threshold, conn)

    with get_connection() as fresh_conn:
        return _match(scanned_name, threshold, fresh_conn)


def _match(scanned_name: str, threshold: float, conn) -> str | None:
    rows = conn.execute("SELECT id, name FROM ingredients").fetchall()
    if not rows:
        return None

    ingredients = [{"id": row["id"], "name": row["name"]} for row in rows]

    # 1순위: 등록명이 스캔명의 부분 문자열인 경우 (예: '마늘' in '깐마늘')
    for ing in ingredients:
        if ing["name"] in scanned_name:
            return ing["id"]

    # 2순위: difflib 유사도 매칭
    names = [i["name"] for i in ingredients]
    matches = difflib.get_close_matches(scanned_name, names, n=1, cutoff=threshold)
    if matches:
        matched_name = matches[0]
        return next(i["id"] for i in ingredients if i["name"] == matched_name)

    return None
