-- 1. 폐기 기록 테이블 추가
CREATE TABLE waste_logs (
    id TEXT PRIMARY KEY,
    ingredient_id TEXT NOT NULL,
    quantity REAL NOT NULL,
    reason TEXT, -- '유통기한 경과', '변질' 등
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ingredient_id) REFERENCES ingredients(id)
);

-- 2. 재고 보정(실사) 기록 테이블 추가
CREATE TABLE inventory_adjustments (
    id TEXT PRIMARY KEY,
    ingredient_id TEXT NOT NULL,
    adjustment_amount REAL NOT NULL, -- 변경된 수량
    reason TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ingredient_id) REFERENCES ingredients(id)
);
