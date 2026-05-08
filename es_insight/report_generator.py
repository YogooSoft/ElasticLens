"""报告生成模块 - 生成 HTML/Markdown/PDF/JSON 格式的巡检报告"""

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from jinja2 import Environment, FileSystemLoader, select_autoescape
import json
from loguru import logger

from es_insight.models.health import (
    HealthAssessmentResult, 
    ClusterHealthData
)
from es_insight.models.common import Issue, Severity as IssueSeverity
from es_insight.models.nodes import ResourceAnalysisResult, NodeInfo
from es_insight.models.rule import RuleExecutionResult, RuleViolation, RuleSeverity
from es_insight.config import Config


class ReportGenerator:
    """报告生成器类"""
    
    def __init__(self, output_dir: str = "./reports"):
        """
        初始化报告生成器
        
        Args:
            output_dir: 输出目录
        """
        self.output_dir = output_dir
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 初始化 Jinja2 环境
        self.jinja_env = Environment(
            loader=FileSystemLoader(self._get_template_dir()),
            autoescape=select_autoescape(['html', 'xml'])
        )
        
        logger.info(f"报告生成器初始化完成，输出目录：{output_dir}")
    
    def _get_template_dir(self) -> str:
        """获取模板目录"""
        # 尝试多个可能的模板目录位置
        possible_paths = [
            Path(__file__).parent.parent / "templates",
            Path(__file__).parent / "templates",
            Path.cwd() / "templates"
        ]
        
        for path in possible_paths:
            if path.exists():
                return str(path)
        
        # 如果模板目录不存在，返回默认路径（后续需要创建）
        return str(Path(__file__).parent.parent / "templates")
    
    def generate_all(
        self,
        health_result: HealthAssessmentResult,
        resource_result: ResourceAnalysisResult,
        rule_result: RuleExecutionResult,
        cluster_data: Any,
        formats: List[str] = None,
        alerts: List[Dict[str, Any]] = None  # 新增参数：规则引擎的详细告警
    ) -> Dict[str, str]:
        """
        生成所有格式的报告
        
        Args:
            health_result: 健康度评估结果
            resource_result: 资源分析结果
            rule_result: 规则执行结果
            cluster_data: 集群原始数据
            formats: 输出格式列表
            alerts: 规则引擎生成的详细告警列表
            
        Returns:
            生成的文件路径字典 {format: filepath}
        """
        if formats is None:
            formats = ['html', 'markdown', 'json']
        
        generated_files = {}
        
        # 准备报告数据
        report_data = self._prepare_report_data(
            health_result, resource_result, rule_result, cluster_data, alerts
        )
        
        # 生成各格式报告
        if 'html' in formats:
            html_path = self.generate_html(report_data)
            generated_files['html'] = html_path
        
        if 'markdown' in formats:
            md_path = self.generate_markdown(report_data)
            generated_files['markdown'] = md_path
        
        if 'json' in formats:
            json_path = self.generate_json(report_data)
            generated_files['json'] = json_path
        
        if 'pdf' in formats:
            # PDF 生成需要额外的依赖（如 weasyprint 或 pdfkit）
            try:
                pdf_path = self.generate_pdf(report_data)
                generated_files['pdf'] = pdf_path
            except ImportError as e:
                logger.warning(f"PDF 生成失败，缺少依赖：{e}")
        
        logger.info(f"成功生成 {len(generated_files)} 个报告文件")
        return generated_files
    
    def _prepare_report_data(
        self,
        health_result: HealthAssessmentResult,
        resource_result: ResourceAnalysisResult,
        rule_result: RuleExecutionResult,
        cluster_data: Any,
        alerts: List[Dict[str, Any]] = None  # 新增参数：规则引擎的详细告警
    ) -> Dict[str, Any]:
        """准备报告数据"""
        # 类别名称映射
        category_names = {
            'cluster_health': '集群健康',
            'node_resources': '节点资源',
            'index_health': '索引健康',
            'thread_pool': '线程池',
            'shard': '分片检查',
            'ilm': 'ILM 管理',
            'snapshot': '快照备份',
            'security': '安全配置'
        }
        
        return {
            'title': f'ES 集群巡检报告 - {cluster_data.health.cluster_name}',
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'timestamp': self.timestamp,
            
            # 集群基本信息
            'cluster': {
                'name': cluster_data.health.cluster_name,
                'status': cluster_data.health.status.value,
                'nodes_count': cluster_data.health.number_of_nodes,
                'indices_count': len(cluster_data.indices),
                'active_shards_percent': cluster_data.health.active_shards_percent
            },
            
            # 健康度评估
            'health': {
                'score': health_result.total_score,
                'level': health_result.health_level,
                'issues': health_result.issues,
                'recommendations': health_result.recommendations,
                'detailed_alerts': alerts or []  # 新增：详细告警列表
            },
            
            # 资源分析
            'resource': {
                'warning_nodes': resource_result.warning_nodes,
                'critical_nodes': resource_result.critical_nodes,
                'imbalance_score': resource_result.imbalance_score,
                'disk_trend': resource_result.cluster_disk_trend
            },
            
            # 规则检查
            'rules': {
                'triggered_count': len(rule_result.triggered_rules),
                'critical_count': rule_result.critical_count,
                'warning_count': rule_result.warning_count,
                'info_count': rule_result.info_count,
                'violations': rule_result.triggered_rules
            },
            
            # 类别名称映射（用于模板显示）
            'category_names': category_names
        }
    
    def generate_html(self, report_data: Dict[str, Any]) -> str:
        """生成 HTML 报告"""
        try:
            template = self.jinja_env.get_template('report.html.j2')
        except:
            # 如果模板不存在，使用内置的简单 HTML 模板
            template_content = self._get_simple_html_template()
            template = self.jinja_env.from_string(template_content)
        
        html_content = template.render(**report_data)
        
        output_path = os.path.join(
            self.output_dir, 
            f"inspection_report_{self.timestamp}.html"
        )
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"HTML 报告已生成：{output_path}")
        return output_path
    
    def generate_markdown(self, report_data: Dict[str, Any]) -> str:
        """生成 Markdown 报告"""
        md_content = self._generate_markdown_content(report_data)
        
        output_path = os.path.join(
            self.output_dir,
            f"inspection_report_{self.timestamp}.md"
        )
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        logger.info(f"Markdown 报告已生成：{output_path}")
        return output_path
    
    def generate_json(self, report_data: Dict[str, Any]) -> str:
        """生成 JSON 报告"""
        # 转换数据为 JSON 序列化格式
        json_data = self._serialize_for_json(report_data)
        
        output_path = os.path.join(
            self.output_dir,
            f"inspection_report_{self.timestamp}.json"
        )
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"JSON 报告已生成：{output_path}")
        return output_path
    
    def generate_pdf(self, report_data: Dict[str, Any]) -> str:
        """生成 PDF 报告（需要额外安装依赖）"""
        # 这个功能需要安装 weasyprint 或 pdfkit
        # pip install weasyprint
        try:
            from weasyprint import HTML
            
            # 先生成 HTML
            html_path = self.generate_html(report_data)
            
            output_path = os.path.join(
                self.output_dir,
                f"inspection_report_{self.timestamp}.pdf"
            )
            
            HTML(filename=html_path).write_pdf(output_path)
            logger.info(f"PDF 报告已生成：{output_path}")
            return output_path
            
        except ImportError:
            raise ImportError(
                "PDF 生成需要安装 weasyprint: pip install weasyprint"
            )
    
    def _generate_markdown_content(self, report_data: Dict[str, Any]) -> str:
        """生成 Markdown 内容"""
        lines = []
        
        # 标题
        lines.append(f"# {report_data['title']}")
        lines.append("")
        lines.append(f"**生成时间**: {report_data['generated_at']}")
        lines.append("")
        
        # 集群概览
        lines.append("## 📊 集群概览")
        lines.append("")
        cluster = report_data['cluster']
        lines.append(f"- **集群名称**: {cluster['name']}")
        lines.append(f"- **状态**: {self._get_status_emoji(cluster['status'])} {cluster['status']}")
        lines.append(f"- **节点数**: {cluster['nodes_count']}")
        lines.append(f"- **索引数**: {cluster['indices_count']}")
        lines.append(f"- **活跃分片比例**: {cluster['active_shards_percent']:.1f}%")
        lines.append("")
        
        # 健康度评估
        lines.append("## 🏥 健康度评估")
        lines.append("")
        health = report_data['health']
        lines.append(f"**综合评分**: {health['score']:.1f} / 100")
        lines.append(f"**健康等级**: {self._get_health_level_emoji(health['level'])} {health['level']}")
        lines.append("")
        
        # 发现的问题
        if health['issues']:
            lines.append("### 发现的问题")
            lines.append("")
            for i, issue in enumerate(health['issues'], 1):
                severity_emoji = self._get_severity_emoji(issue.severity)
                lines.append(f"{i}. {severity_emoji} **{issue.title}**")
                lines.append(f"   - 描述：{issue.description}")
                lines.append(f"   - 建议：{issue.suggestion}")
                lines.append("")
        
        # 优化建议
        if health['recommendations']:
            lines.append("### 💡 优化建议")
            lines.append("")
            for i, rec in enumerate(health['recommendations'], 1):
                lines.append(f"{i}. {rec}")
            lines.append("")
        
        # 资源分析
        lines.append("## 💻 资源分析")
        lines.append("")
        resource = report_data['resource']
        lines.append(f"**不均衡度**: {resource['imbalance_score']:.2f}")
        lines.append("")
        
        if resource['warning_nodes']:
            lines.append("⚠️ **警告节点**:")
            for node in resource['warning_nodes']:
                lines.append(f"- {node.name}: {node.cpu_percent}% CPU, {node.heap_used_percent}% 内存")
            lines.append("")
        
        if resource['critical_nodes']:
            lines.append("🔴 **严重节点**:")
            for node in resource['critical_nodes']:
                lines.append(f"- {node.name}: {node.cpu_percent}% CPU, {node.heap_used_percent}% 内存")
            lines.append("")
        
        # 规则检查
        lines.append("## ✅ 规则检查")
        lines.append("")
        rules = report_data['rules']
        lines.append(f"**触发规则数**: {rules['triggered_count']}")
        lines.append(f"- 🔴 严重：{rules['critical_count']}")
        lines.append(f"- ⚠️ 警告：{rules['warning_count']}")
        lines.append(f"- ℹ️ 提示：{rules['info_count']}")
        lines.append("")
        
        if rules['violations']:
            lines.append("### 违反的规则")
            lines.append("")
            for violation in rules['violations']:
                lines.append(f"- **{violation.rule_id}**: {violation.message}")
            lines.append("")
        
        # 详细检查项（新增）
        if health.get('detailed_alerts'):
            lines.append("## 🔍 详细检查项")
            lines.append("")
            
            # 按类别分组
            alerts_by_category = {}
            for alert in health['detailed_alerts']:
                category = alert.get('category', 'other')
                if category not in alerts_by_category:
                    alerts_by_category[category] = []
                alerts_by_category[category].append(alert)
            
            # 显示每个类别的检查项
            category_names = {
                'cluster_health': '集群健康',
                'node_resources': '节点资源',
                'index_health': '索引健康',
                'thread_pool': '线程池',
                'shard': '分片检查',
                'ilm': 'ILM 管理',
                'snapshot': '快照备份',
                'security': '安全配置'
            }
            
            for category, alerts in sorted(alerts_by_category.items()):
                category_name = category_names.get(category, category)
                lines.append(f"### {category_name} ({len(alerts)} 项)")
                lines.append("")
                
                for i, alert in enumerate(alerts, 1):
                    severity_emoji = self._get_severity_emoji(alert.get('severity', 'info'))
                    check_item = alert.get('check_item', 'unknown')
                    message = alert.get('message', '')
                    current_value = alert.get('current_value', 'N/A')
                    threshold = alert.get('threshold', 'N/A')
                    recommendation = alert.get('recommendation', '')
                    location = alert.get('location', '')
                    
                    lines.append(f"{i}. {severity_emoji} **{check_item}**")
                    lines.append(f"   - 详情：{message}")
                    if location:
                        lines.append(f"   - 位置：{location}")
                    lines.append(f"   - 当前值：{current_value}")
                    lines.append(f"   - 阈值：{threshold}")
                    if recommendation:
                        lines.append(f"   - 建议：{recommendation}")
                    lines.append("")
        
        return "\n".join(lines)
    
    def _serialize_for_json(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """序列化数据为 JSON 格式"""
        # 处理不能直接序列化的对象
        serialized = {}
        
        for key, value in data.items():
            if isinstance(value, dict):
                serialized[key] = self._serialize_for_json(value)
            elif isinstance(value, list):
                serialized[key] = [
                    self._serialize_object(item) for item in value
                ]
            else:
                serialized[key] = value
        
        return serialized
    
    def _serialize_object(self, obj: Any) -> Any:
        """序列化单个对象"""
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        elif isinstance(obj, dict):
            return {k: self._serialize_object(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_object(item) for item in obj]
        else:
            return obj
    
    def _get_status_emoji(self, status: str) -> str:
        """获取状态对应的 Emoji"""
        emojis = {
            'green': '✅',
            'yellow': '⚠️',
            'red': '🔴'
        }
        return emojis.get(status, '❓')
    
    def _get_health_level_emoji(self, level: str) -> str:
        """获取健康等级对应的 Emoji"""
        emojis = {
            'excellent': '🌟',
            'good': '👍',
            'warning': '⚠️',
            'critical': '🔴'
        }
        return emojis.get(level, '❓')
    
    def _get_severity_emoji(self, severity: IssueSeverity) -> str:
        """获取严重程度对应的 Emoji"""
        emojis = {
            IssueSeverity.CRITICAL: '🔴',
            IssueSeverity.WARNING: '⚠️',
            IssueSeverity.INFO: 'ℹ️'
        }
        return emojis.get(severity, '❓')
    
    def _get_simple_html_template(self) -> str:
        """简单的 HTML 模板（当外部模板不存在时使用）"""
        return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { color: #333; border-bottom: 3px solid #4CAF50; padding-bottom: 10px; }
        h2 { color: #555; margin-top: 30px; }
        .score { font-size: 48px; font-weight: bold; color: #4CAF50; }
        .good { color: #4CAF50; }
        .warning { color: #FF9800; }
        .critical { color: #F44336; }
        .issue { background: #fff3cd; padding: 15px; margin: 10px 0; border-left: 4px solid #FF9800; }
        .recommendation { background: #d4edda; padding: 15px; margin: 10px 0; border-left: 4px solid #4CAF50; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 12px; text-align: left; border: 1px solid #ddd; }
        th { background: #f5f5f5; font-weight: bold; }
        .footer { margin-top: 50px; color: #888; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>{{ title }}</h1>
        <p><strong>生成时间</strong>: {{ generated_at }}</p>
        
        <h2>📊 集群概览</h2>
        <table>
            <tr><th>集群名称</th><td>{{ cluster.name }}</td></tr>
            <tr><th>状态</th><td>{{ cluster.status }}</td></tr>
            <tr><th>节点数</th><td>{{ cluster.nodes_count }}</td></tr>
            <tr><th>索引数</th><td>{{ cluster.indices_count }}</td></tr>
        </table>
        
        <h2>🏥 健康度评估</h2>
        <div class="score {% if health.score >= 75 %}good{% elif health.score >= 60 %}warning{% else %}critical{% endif %}">
            {{ "%.1f"|format(health.score) }} / 100
        </div>
        <p><strong>健康等级</strong>: {{ health.level }}</p>
        
        {% if health.issues %}
        <h2>⚠️ 发现的问题</h2>
        {% for issue in health.issues %}
        <div class="issue">
            <strong>{{ loop.index }}. {{ issue.title }}</strong><br>
            <small>{{ issue.description }}</small><br>
            <strong>建议</strong>: {{ issue.suggestion }}
        </div>
        {% endfor %}
        {% endif %}
        
        {% if health.recommendations %}
        <h2>💡 优化建议</h2>
        <ul>
        {% for rec in health.recommendations %}
        <li class="recommendation">{{ rec }}</li>
        {% endfor %}
        </ul>
        {% endif %}
        
        {% if health.detailed_alerts and health.detailed_alerts|length > 0 %}
        <h2>🔍 详细检查项</h2>
        
        {% set categories = namespace(list=[]) %}
        {% for alert in health.detailed_alerts %}
            {% if alert.category not in categories.list %}
                {% set categories.list = categories.list + [alert.category] %}
            {% endif %}
        {% endfor %}
        
        {% for category in categories.list %}
        <h3 style="color: #666; margin-top: 25px;">{{ category_names.get(category, category) }}</h3>
        <table>
            <thead>
                <tr>
                    <th>检查项</th>
                    <th>详情</th>
                    <th>位置</th>
                    <th>当前值</th>
                    <th>阈值</th>
                    <th>建议</th>
                </tr>
            </thead>
            <tbody>
            {% for alert in health.detailed_alerts %}
                {% if alert.category == category %}
                <tr>
                    <td>
                        {% if alert.severity == 'critical' %}🔴
                        {% elif alert.severity == 'warning' %}⚠️
                        {% else %}ℹ️
                        {% endif %}
                        <strong>{{ alert.check_item }}</strong>
                    </td>
                    <td>{{ alert.message }}</td>
                    <td>{{ alert.location or 'N/A' }}</td>
                    <td>{{ alert.current_value }}</td>
                    <td>{{ alert.threshold }}</td>
                    <td>{{ alert.recommendation or 'N/A' }}</td>
                </tr>
                {% endif %}
            {% endfor %}
            </tbody>
        </table>
        {% endfor %}
        {% endif %}
        
        <div class="footer">
            <p>Generated by ES Insight Tool | {{ timestamp }}</p>
        </div>
    </div>
</body>
</html>
"""
