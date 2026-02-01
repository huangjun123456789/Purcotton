# -*- coding: utf-8 -*-
"""
数据库迁移脚本：为 shelves 表添加 layers 字段（货架层数）

运行方式：
    cd backend
    python migrate_add_layers.py
"""
import sqlite3
import os

# 数据库文件路径
DB_PATH = os.path.join(os.path.dirname(__file__), "warehouse_heatmap.db")


def migrate():
    """执行迁移"""
    if not os.path.exists(DB_PATH):
        print(f"数据库文件不存在: {DB_PATH}")
        print("如果是首次运行，启动后端服务会自动创建数据库表。")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 检查列是否已存在
        cursor.execute("PRAGMA table_info(shelves)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if "layers" in columns:
            print("layers 列已存在，无需迁移。")
            return
        
        # 添加新列，默认值为 1（单层货架）
        print("正在添加 layers 列...")
        cursor.execute("""
            ALTER TABLE shelves 
            ADD COLUMN layers INTEGER DEFAULT 1
        """)
        
        # 为现有数据设置默认值
        cursor.execute("""
            UPDATE shelves SET layers = 1 WHERE layers IS NULL
        """)
        
        conn.commit()
        print("迁移成功！layers 列已添加到 shelves 表。")
        print("现有货架已设置为默认 1 层。")
        
    except Exception as e:
        print(f"迁移失败: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
