"""迁移现有 JSON 报告到数据库

此脚本用于将 reports/ 目录中已存在的 JSON 报告文件导入到 SQLite 数据库中。
适用于从内存存储迁移到数据库存储的场景。

使用方法:
    python migrate_existing_reports.py
"""

import json
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from db_server import TaskModel, ReportModel


def migrate_reports():
    """迁移现有报告到数据库"""
    reports_folder = Path(__file__).parent.parent / "reports"
    
    if not reports_folder.exists():
        print(f"报告目录不存在: {reports_folder}")
        return
    
    json_files = list(reports_folder.glob("*.json"))
    
    if not json_files:
        print("没有找到需要迁移的 JSON 报告文件")
        return
    
    print(f"找到 {len(json_files)} 个 JSON 报告文件，开始迁移...\n")
    
    migrated_count = 0
    failed_count = 0
    skipped_count = 0
    
    for json_file in json_files:
        try:
            report_id = json_file.stem  # 去掉 .json 后缀
            
            # 尝试从文件名提取 task_id
            if report_id.startswith("report_"):
                task_id = report_id.replace("report_", "")
            else:
                print(f"⊘ 跳过（无法提取 task_id）：{json_file.name}")
                skipped_count += 1
                continue
            
            # 检查任务是否已存在
            existing_task = TaskModel.get_task(task_id)
            if existing_task:
                print(f"⊘ 跳过（任务已存在）：{report_id}")
                skipped_count += 1
                continue
            
            # 读取 JSON 报告
            with open(json_file, 'r', encoding='utf-8') as f:
                report_data = json.load(f)
            
            # 创建任务记录
            TaskModel.create_task(
                task_id=task_id,
                filename=f"migrated_{task_id}.zip",
                file_size=json_file.stat().st_size
            )
            TaskModel.update_task_status(task_id, 'completed')
            
            # 创建报告记录
            ReportModel.create_report(report_id, task_id, report_data)
            
            migrated_count += 1
            print(f"✓ 迁移成功：{report_id}")
        
        except Exception as e:
            failed_count += 1
            print(f"✗ 迁移失败：{json_file.name} - {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*60}")
    print(f"迁移完成！")
    print(f"  成功：{migrated_count}")
    print(f"  失败：{failed_count}")
    print(f"  跳过：{skipped_count}")
    print(f"{'='*60}")


if __name__ == '__main__':
    migrate_reports()
