-- 스마트 재고 관리 시스템 스키마
-- 식재료 마스터
CREATE TABLE ingredients (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    current_stock REAL DEFAULT 0,
    base_unit TEXT NOT NULL, -- g, ml, ea
    safety_stock REAL DEFAULT 0
);

-- 단위 환산 테이블 (입고 단위 -> 기본 단위)
CREATE TABLE ingredient_conversions (
    id TEXT PRIMARY KEY,
    ingredient_id TEXT NOT NULL,
    unit_name TEXT NOT NULL, -- 예: "1망", "1박스"
    conversion_factor REAL NOT NULL, -- 예: 5000 (g)
    FOREIGN KEY (ingredient_id) REFERENCES ingredients(id)
);

-- 입고 기록
CREATE TABLE incoming_logs (
    id TEXT PRIMARY KEY,
    ingredient_id TEXT NOT NULL,
    quantity REAL NOT NULL,
    total_price INTEGER,
    scanned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ingredient_id) REFERENCES ingredients(id)
);

-- 레시피 (BOM)
CREATE TABLE recipes (
    id TEXT PRIMARY KEY,
    menu_name TEXT NOT NULL,
    ingredient_id TEXT NOT NULL,
    usage_amount REAL NOT NULL,
    FOREIGN KEY (ingredient_id) REFERENCES ingredients(id)
);
