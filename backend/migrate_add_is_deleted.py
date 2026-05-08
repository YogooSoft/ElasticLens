"""数据库迁移脚本：为 tasks 和 reports 表添加 is_deleted 字段"""
import sqlite3
from pathlib import Path
from loguru import logger


def migrate_add_is_deleted_field():
    """
    为现有的 tasks 和 reports 表添加 is_deleted 字段
    如果字段已存在则跳过
    """
    # 数据库文件路径
    db_path = Path(__file__).parent / "es_insight.db"
    
    if not db_path.exists():
        logger.warning(f"数据库文件不存在：{db_path}")
        return False
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # 检查 tasks 表是否有 is_deleted 字段
        cursor.execute("PRAGMA table_info(tasks)")
        tasks_columns = [col[1] for col in cursor.fetchall()]
        
        if 'is_deleted' not in tasks_columns:
            logger.info("为 tasks 表添加 is_deleted 字段...")
            cursor.execute('ALTER TABLE tasks ADD COLUMN is_deleted INTEGER DEFAULT 0')
            logger.info("✅ tasks 表 is_deleted 字段添加成功")
        else:
            logger.info("tasks 表已存在 is_deleted 字段，跳过")
        
        # 检查 reports 表是否有 is_deleted 字段
        cursor.execute("PRAGMA table_info(reports)")
        reports_columns = [col[1] for col in cursor.fetchall()]
        
        if 'is_deleted' not in reports_columns:
            logger.info("为 reports 表添加 is_deleted 字段...")
            cursor.execute('ALTER TABLE reports ADD COLUMN is_deleted INTEGER DEFAULT 0')
            logger.info("✅ reports 表 is_deleted 字段添加成功")
        else:
            logger.info("reports 表已存在 is_deleted 字段，跳过")
        
        conn.commit()
        conn.close()
        
        logger.info("数据库迁移完成！")
        return True
        
    except Exception as e:
        logger.error(f"数据库迁移失败：{str(e)}")
        return False


if __name__ == '__main__':
    logger.info("开始执行数据库迁移...")
    success = migrate_add_is_deleted_field()
    if success:
        logger.info("迁移成功！")
    else:
        logger.error("迁移失败！")
