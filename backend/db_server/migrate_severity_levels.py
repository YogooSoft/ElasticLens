"""数据库迁移脚本：增加告警级别计数字段"""
import sqlite3
from pathlib import Path

def migrate():
    """执行迁移"""
    db_path = Path(__file__).parent.parent / 'es_insight.db'
    
    if not db_path.exists():
        print(f"❌ 数据库文件不存在: {db_path}")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(reports)")
        columns = [row[1] for row in cursor.fetchall()]
        
        fields_to_add = {
            'level_1_count': 'INTEGER DEFAULT 0',
            'level_2_count': 'INTEGER DEFAULT 0',
            'level_3_count': 'INTEGER DEFAULT 0'
        }
        
        for field, definition in fields_to_add.items():
            if field not in columns:
                print(f"➕ 正在添加字段: {field}")
                cursor.execute(f"ALTER TABLE reports ADD COLUMN {field} {definition}")
            else:
                print(f"✅ 字段已存在: {field}")
        
        conn.commit()
        print("🎉 数据库迁移完成！")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ 迁移失败: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
