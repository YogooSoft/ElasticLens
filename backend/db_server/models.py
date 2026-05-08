"""数据模型操作封装"""
import json
from datetime import datetime
from typing import List, Dict, Optional
from .database import db_manager


class TaskModel:
    """任务数据模型"""
    
    @staticmethod
    def create_task(task_id: str, filename: str, file_size: int) -> dict:
        """
        创建任务记录
        
        Args:
            task_id: 任务ID
            filename: 原始文件名
            file_size: 文件大小（字节）
            
        Returns:
            dict: 创建的任务信息
        """
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO tasks (id, filename, file_size, status, progress, created_at, updated_at)
                VALUES (?, ?, ?, 'pending', 0, ?, ?)
            ''', (task_id, filename, file_size, 
                  datetime.now().isoformat(), 
                  datetime.now().isoformat()))
            return {
                'id': task_id,
                'filename': filename,
                'file_size': file_size,
                'status': 'pending',
                'progress': 0
            }
    
    @staticmethod
    def update_task_status(task_id: str, status: str, progress: int = None, 
                          error_message: str = None) -> bool:
        """
        更新任务状态
        
        Args:
            task_id: 任务ID
            status: 新状态 (pending/processing/completed/failed)
            progress: 进度 0-100
            error_message: 错误信息（失败时）
            
        Returns:
            bool: 是否更新成功
        """
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            updates = ['status = ?', 'updated_at = ?']
            params = [status, datetime.now().isoformat()]
            
            if progress is not None:
                updates.append('progress = ?')
                params.append(progress)
            
            if error_message is not None:
                updates.append('error_message = ?')
                params.append(error_message)
            
            if status == 'completed':
                updates.append('completed_at = ?')
                params.append(datetime.now().isoformat())
            
            params.append(task_id)
            sql = f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(sql, params)
            return cursor.rowcount > 0
    
    @staticmethod
    def get_task(task_id: str) -> Optional[dict]:
        """
        获取单个任务（排除已删除的任务）
        
        Args:
            task_id: 任务ID
            
        Returns:
            dict or None: 任务信息，不存在或已删除返回 None
        """
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM tasks WHERE id = ? AND is_deleted = 0', (task_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    @staticmethod
    def get_all_tasks(limit: int = 100, offset: int = 0) -> List[dict]:
        """
        获取任务列表（分页，排除已删除的任务）
        
        Args:
            limit: 每页数量
            offset: 偏移量
            
        Returns:
            List[dict]: 任务列表
        """
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM tasks 
                WHERE is_deleted = 0
                ORDER BY created_at DESC 
                LIMIT ? OFFSET ?
            ''', (limit, offset))
            return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def delete_task(task_id: str) -> bool:
        """
        软删除任务（同时软删除关联的报告）
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否删除成功
        """
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            # 软删除任务
            cursor.execute('UPDATE tasks SET is_deleted = 1, updated_at = ? WHERE id = ?', 
                          (datetime.now().isoformat(), task_id))
            task_deleted = cursor.rowcount > 0
            
            # 软删除关联的报告
            cursor.execute('UPDATE reports SET is_deleted = 1 WHERE task_id = ?', (task_id,))
            
            return task_deleted


class ReportModel:
    """报告数据模型"""
    
    @staticmethod
    def create_report(report_id: str, task_id: str, report_data: dict) -> dict:
        """
        创建报告记录
        
        Args:
            report_id: 报告ID
            task_id: 关联任务ID
            report_data: 完整报告数据（包含 basic_info, alerts, health_score_report 等）
            
        Returns:
            dict: 创建的报告记录
        """
        # 提取关键信息
        basic_info = report_data.get('basic_info', {})
        alerts = report_data.get('alerts', {})
        alert_summary = alerts.get('summary', {})
        health_score_report = report_data.get('health_score_report', {})
        
        # 使用健康评分报告中的数据（与HTML/Word报告保持一致）
        if health_score_report:
            summary_info = health_score_report.get('summary', {})
            total_issues = summary_info.get('total_issues_count', 0)
            critical_issues = summary_info.get('critical_issues_count', 0)
            warning_issues = summary_info.get('warning_issues_count', 0)
            health_score = health_score_report.get('total_score', 0)
            level_1_count = summary_info.get('level_1_count', 0)
            level_2_count = summary_info.get('level_2_count', 0)
            level_3_count = summary_info.get('level_3_count', 0)
        else:
            # 如果没有健康评分报告，回退到旧的数据
            total_issues = alert_summary.get('critical', 0) + alert_summary.get('warning', 0)
            critical_issues = alert_summary.get('critical', 0)
            warning_issues = alert_summary.get('warning', 0)
            health_score = alert_summary.get('health_score', 0)
            level_1_count = 0
            level_2_count = 0
            level_3_count = 0
        
        report_record = {
            'id': report_id,
            'task_id': task_id,
            'cluster_name': basic_info.get('cluster_info', {}).get('cluster_name'),
            'health_score': health_score,
            'alert_count': total_issues,
            'critical_count': critical_issues,
            'warning_count': warning_issues,
            'level_1_count': level_1_count,
            'level_2_count': level_2_count,
            'level_3_count': level_3_count,
            'json_path': f"reports/{report_id}.json",
            'html_path': f"reports/{report_id}.html",
            'metadata': json.dumps({
                'nodes_count': basic_info.get('cluster_info', {}).get('nodes_total'),
                'indices_count': basic_info.get('index_summary', {}).get('total'),
            }, ensure_ascii=False)
        }
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO reports 
                (id, task_id, cluster_name, health_score, alert_count, 
                 critical_count, warning_count, level_1_count, level_2_count, level_3_count, json_path, html_path, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                report_record['id'],
                report_record['task_id'],
                report_record['cluster_name'],
                report_record['health_score'],
                report_record['alert_count'],
                report_record['critical_count'],
                report_record['warning_count'],
                report_record['level_1_count'],
                report_record['level_2_count'],
                report_record['level_3_count'],
                report_record['json_path'],
                report_record['html_path'],
                report_record['metadata'],
                datetime.now().isoformat()
            ))
        
        return report_record
    
    @staticmethod
    def get_report(report_id: str) -> Optional[dict]:
        """
        获取报告基本信息（排除已删除的报告）
        
        Args:
            report_id: 报告ID
            
        Returns:
            dict or None: 报告信息，不存在或已删除返回 None
        """
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM reports WHERE id = ? AND is_deleted = 0', (report_id,))
            row = cursor.fetchone()
            if row:
                result = dict(row)
                # 解析metadata
                if result.get('metadata'):
                    result['metadata'] = json.loads(result['metadata'])
                return result
            return None
    
    @staticmethod
    def get_all_reports(limit: int = 50, offset: int = 0, 
                       cluster_name: str = None, 
                       min_health_score: float = None) -> List[dict]:
        """
        获取报告列表（支持筛选和分页）
        
        Args:
            limit: 每页数量
            offset: 偏移量
            cluster_name: 集群名称筛选（模糊匹配）
            min_health_score: 最低健康评分筛选
            
        Returns:
            List[dict]: 报告列表
        """
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            query = 'SELECT * FROM reports WHERE is_deleted = 0'
            params = []
            
            if cluster_name:
                query += ' AND cluster_name LIKE ?'
                params.append(f'%{cluster_name}%')
            
            if min_health_score is not None:
                query += ' AND health_score >= ?'
                params.append(min_health_score)
            
            query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                if result.get('metadata'):
                    result['metadata'] = json.loads(result['metadata'])
                results.append(result)
            
            return results
    
    @staticmethod
    def delete_report(report_id: str) -> bool:
        """
        软删除报告记录
        
        Args:
            report_id: 报告ID
            
        Returns:
            bool: 是否删除成功
        """
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE reports SET is_deleted = 1 WHERE id = ?', (report_id,))
            return cursor.rowcount > 0
