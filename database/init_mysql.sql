-- 仓库热力图系统数据库初始化脚本 (MySQL)
-- 创建数据库
CREATE DATABASE IF NOT EXISTS warehouse_heatmap 
    CHARACTER SET utf8mb4 
    COLLATE utf8mb4_unicode_ci;

USE warehouse_heatmap;

-- 仓库表
CREATE TABLE IF NOT EXISTS warehouses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE COMMENT '仓库编码',
    name VARCHAR(100) NOT NULL COMMENT '仓库名称',
    address VARCHAR(255) COMMENT '仓库地址',
    description TEXT COMMENT '描述',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='仓库表';

-- 库区表
CREATE TABLE IF NOT EXISTS zones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    warehouse_id INT NOT NULL,
    code VARCHAR(50) NOT NULL COMMENT '库区编码',
    name VARCHAR(100) NOT NULL COMMENT '库区名称',
    description TEXT COMMENT '描述',
    sort_order INT DEFAULT 0 COMMENT '排序顺序',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (warehouse_id) REFERENCES warehouses(id) ON DELETE CASCADE,
    INDEX idx_zone_warehouse (warehouse_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='库区表';

-- 通道/巷道表
CREATE TABLE IF NOT EXISTS aisles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    zone_id INT NOT NULL,
    code VARCHAR(50) NOT NULL COMMENT '通道编码',
    name VARCHAR(100) NOT NULL COMMENT '通道名称',
    y_coordinate INT NOT NULL COMMENT 'Y轴坐标',
    sort_order INT DEFAULT 0 COMMENT '排序顺序',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (zone_id) REFERENCES zones(id) ON DELETE CASCADE,
    INDEX idx_aisle_zone (zone_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='通道表';

-- 货架表
CREATE TABLE IF NOT EXISTS shelves (
    id INT AUTO_INCREMENT PRIMARY KEY,
    aisle_id INT NOT NULL,
    code VARCHAR(50) NOT NULL COMMENT '货架编码',
    name VARCHAR(100) NOT NULL COMMENT '货架名称',
    shelf_type ENUM('normal', 'high_rack', 'ground_stack', 'mezzanine', 'cantilever') DEFAULT 'normal' COMMENT '货架类型',
    `rows` INT DEFAULT 4 COMMENT '行数',
    `columns` INT DEFAULT 5 COMMENT '列数',
    x_coordinate INT NOT NULL COMMENT 'X轴坐标',
    sort_order INT DEFAULT 0 COMMENT '排序顺序',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (aisle_id) REFERENCES aisles(id) ON DELETE CASCADE,
    INDEX idx_shelf_aisle (aisle_id),
    INDEX idx_shelf_type (shelf_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='货架表';

-- 库位表
CREATE TABLE IF NOT EXISTS locations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    shelf_id INT NOT NULL,
    code VARCHAR(50) NOT NULL COMMENT '库位编码',
    full_code VARCHAR(100) NOT NULL UNIQUE COMMENT '完整库位编码',
    row_label VARCHAR(10) NOT NULL COMMENT '行标签',
    column_number INT NOT NULL COMMENT '列号',
    row_index INT NOT NULL COMMENT '行索引',
    column_index INT NOT NULL COMMENT '列索引',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (shelf_id) REFERENCES shelves(id) ON DELETE CASCADE,
    INDEX idx_location_shelf (shelf_id),
    INDEX idx_location_code (code),
    INDEX idx_location_full_code (full_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='库位表';

-- 库位热度数据表
CREATE TABLE IF NOT EXISTS location_heat_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    location_id INT NOT NULL,
    date DATETIME NOT NULL COMMENT '统计日期',
    pick_frequency INT DEFAULT 0 COMMENT '拣货频率',
    turnover_rate FLOAT DEFAULT 0 COMMENT '周转率',
    heat_value FLOAT DEFAULT 0 COMMENT '热度值',
    inventory_qty INT DEFAULT 0 COMMENT '库存数量',
    inbound_qty INT DEFAULT 0 COMMENT '入库数量',
    outbound_qty INT DEFAULT 0 COMMENT '出库数量',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (location_id) REFERENCES locations(id) ON DELETE CASCADE,
    INDEX idx_heat_location (location_id),
    INDEX idx_heat_date (date),
    INDEX idx_heat_location_date (location_id, date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='库位热度数据表';

-- 插入示例数据
INSERT INTO warehouses (code, name, address, description) VALUES
('WH001', '主仓库', '上海市浦东新区', '主仓库示例数据');

INSERT INTO zones (warehouse_id, code, name, sort_order) VALUES
(1, '默认库区', '默认库区', 0);

-- 插入巷道数据
INSERT INTO aisles (zone_id, code, name, y_coordinate, sort_order) VALUES
(1, '01巷', '01巷', 0, 0),
(1, '02巷', '02巷', 1, 1);

-- 插入货架数据 (01巷)
INSERT INTO shelves (aisle_id, code, name, shelf_type, `rows`, `columns`, x_coordinate, sort_order) VALUES
(1, '货架01', '货架01', 'normal', 4, 5, 0, 0),
(1, '货架02', '货架02', 'normal', 4, 5, 1, 1),
(1, '货架03', '货架03', 'normal', 4, 5, 2, 2),
(1, '地堆01', '地堆01', 'ground_stack', 4, 5, 3, 3),
(1, '货架04', '货架04', 'normal', 4, 5, 4, 4);

-- 插入货架数据 (02巷)
INSERT INTO shelves (aisle_id, code, name, shelf_type, `rows`, `columns`, x_coordinate, sort_order) VALUES
(2, '货架01', '货架01', 'normal', 4, 5, 0, 0),
(2, '货架02', '货架02', 'normal', 4, 5, 1, 1),
(2, '货架03', '货架03', 'normal', 4, 6, 2, 2),
(2, '货架04', '货架04', 'normal', 4, 5, 3, 3);

-- 创建存储过程：为货架生成库位
DELIMITER //
CREATE PROCEDURE generate_locations_for_shelf(IN p_shelf_id INT)
BEGIN
    DECLARE v_rows INT;
    DECLARE v_columns INT;
    DECLARE v_shelf_code VARCHAR(50);
    DECLARE v_aisle_code VARCHAR(50);
    DECLARE v_zone_code VARCHAR(50);
    DECLARE v_row_idx INT DEFAULT 0;
    DECLARE v_col_idx INT DEFAULT 0;
    DECLARE v_row_labels VARCHAR(26) DEFAULT 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
    DECLARE v_row_label VARCHAR(1);
    DECLARE v_code VARCHAR(50);
    DECLARE v_full_code VARCHAR(100);
    
    -- 获取货架信息
    SELECT s.`rows`, s.`columns`, s.code, a.code, z.code
    INTO v_rows, v_columns, v_shelf_code, v_aisle_code, v_zone_code
    FROM shelves s
    JOIN aisles a ON s.aisle_id = a.id
    JOIN zones z ON a.zone_id = z.id
    WHERE s.id = p_shelf_id;
    
    -- 生成库位
    SET v_row_idx = 0;
    WHILE v_row_idx < v_rows DO
        SET v_row_label = SUBSTRING(v_row_labels, v_row_idx + 1, 1);
        SET v_col_idx = 0;
        WHILE v_col_idx < v_columns DO
            SET v_code = CONCAT(v_row_label, v_col_idx + 1);
            SET v_full_code = CONCAT(v_zone_code, '-', v_aisle_code, '-', v_shelf_code, '-', v_code);
            
            INSERT INTO locations (shelf_id, code, full_code, row_label, column_number, row_index, column_index)
            VALUES (p_shelf_id, v_code, v_full_code, v_row_label, v_col_idx + 1, v_row_idx, v_col_idx);
            
            SET v_col_idx = v_col_idx + 1;
        END WHILE;
        SET v_row_idx = v_row_idx + 1;
    END WHILE;
END //
DELIMITER ;

-- 为所有货架生成库位
CALL generate_locations_for_shelf(1);
CALL generate_locations_for_shelf(2);
CALL generate_locations_for_shelf(3);
CALL generate_locations_for_shelf(4);
CALL generate_locations_for_shelf(5);
CALL generate_locations_for_shelf(6);
CALL generate_locations_for_shelf(7);
CALL generate_locations_for_shelf(8);
CALL generate_locations_for_shelf(9);

-- 创建存储过程：生成示例热度数据
DELIMITER //
CREATE PROCEDURE generate_sample_heat_data()
BEGIN
    DECLARE v_location_id INT;
    DECLARE v_done INT DEFAULT FALSE;
    DECLARE v_pick_freq INT;
    DECLARE v_turnover FLOAT;
    DECLARE v_heat FLOAT;
    
    DECLARE cur CURSOR FOR SELECT id FROM locations;
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_done = TRUE;
    
    OPEN cur;
    
    read_loop: LOOP
        FETCH cur INTO v_location_id;
        IF v_done THEN
            LEAVE read_loop;
        END IF;
        
        -- 生成随机热度数据
        SET v_pick_freq = FLOOR(RAND() * 500);
        SET v_turnover = RAND() * 2;
        SET v_heat = 0.6 * v_pick_freq + 0.4 * v_turnover * 100;
        
        INSERT INTO location_heat_data (location_id, date, pick_frequency, turnover_rate, heat_value, inventory_qty)
        VALUES (v_location_id, NOW(), v_pick_freq, v_turnover, v_heat, FLOOR(RAND() * 1000));
    END LOOP;
    
    CLOSE cur;
END //
DELIMITER ;

-- 生成示例热度数据
CALL generate_sample_heat_data();

SELECT '数据库初始化完成！' AS message;
