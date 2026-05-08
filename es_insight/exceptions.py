"""自定义异常类"""


class ESInsightException(Exception):
    """基础异常类"""
    pass


class ParseError(ESInsightException):
    """解析错误"""
    def __init__(self, message: str, file_name: str = None):
        self.file_name = file_name
        super().__init__(f"[{file_name}] {message}" if file_name else message)


class AnalysisError(ESInsightException):
    """分析错误"""
    pass


class ReportGenerationError(ESInsightException):
    """报告生成错误"""
    pass


class ConfigurationError(ESInsightException):
    """配置错误"""
    pass
