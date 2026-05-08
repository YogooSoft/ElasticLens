"""数据库初始化和连接管理"""
import sqlite3
from pathlib import Path
from contextlib import contextmanager
from loguru import logger


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, db_path: str = None):
        """
        初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径,默认为 backend/es_insight.db
        """
        if db_path is None:
            # 数据库文件存放在 backend 目录下
            db_path = Path(__file__).parent.parent / "es_insight.db"
        self.db_path = Path(db_path)
        self.init_database()
    
    def init_database(self):
        """初始化数据库表结构"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # 启用外键约束
        cursor.execute('PRAGMA foreign_keys = ON')
        
        # 创建任务表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                file_size INTEGER,
                status TEXT NOT NULL DEFAULT 'pending',
                progress INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                error_message TEXT,
                is_deleted INTEGER DEFAULT 0
            )
        ''')
        
        # 创建报告表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                report_name TEXT,
                cluster_name TEXT,
                health_score REAL,
                alert_count INTEGER DEFAULT 0,
                critical_count INTEGER DEFAULT 0,
                warning_count INTEGER DEFAULT 0,
                json_path TEXT,
                html_path TEXT,
                word_path TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_deleted INTEGER DEFAULT 0,
                FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
            )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_created ON tasks(created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_reports_task ON reports(task_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_reports_cluster ON reports(cluster_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_reports_health ON reports(health_score)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_reports_created ON reports(created_at)')
        
        conn.commit()
        conn.close()
        logger.info(f"数据库初始化完成：{self.db_path}")
    
    @contextmanager
    def get_connection(self):
        """
        获取数据库连接（上下文管理器）
        
        Yields:
            sqlite3.Connection: 数据库连接对象
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # 使结果可通过列名访问
        
        # 启用外键约束
        conn.execute('PRAGMA foreign_keys = ON')
        
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"数据库操作失败：{e}")
            raise
        finally:
            conn.close()


# 全局数据库管理器实例
db_manager = DatabaseManager()
