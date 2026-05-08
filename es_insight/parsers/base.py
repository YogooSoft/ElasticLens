"""基础解析器类"""

import json
import zipfile
import tempfile
import shutil
import os
from pathlib import Path
from typing import Union
import pandas as pd
from loguru import logger

from es_insight.exceptions import ParseError


class DiagnosticFileParser:
    """诊断文件解析器基类"""
    
    def __init__(self, zip_path: str):
        """
        初始化解析器
        
        Args:
            zip_path: ZIP 诊断包路径
        """
        self.zip_path = zip_path
        self.extract_dir = None
        logger.info(f"初始化解析器，诊断包：{zip_path}")
        
    def extract(self) -> str:
        """
        解压 ZIP 文件
        
        Returns:
            解压后的目录路径
        """
        try:
            # 创建临时目录
            self.extract_dir = tempfile.mkdtemp(prefix="es_insight_")
            logger.debug(f"解压到临时目录：{self.extract_dir}")
            
            # 解压 ZIP 文件
            with zipfile.ZipFile(self.zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.extract_dir)
                
            logger.info(f"成功解压诊断包到：{self.extract_dir}")
            return self.extract_dir
            
        except zipfile.BadZipFile as e:
            raise ParseError(f"无效的 ZIP 文件：{str(e)}", self.zip_path)
        except Exception as e:
            raise ParseError(f"解压失败：{str(e)}", self.zip_path)
    
    def parse_json(self, file_name: str) -> dict:
        """
        解析 JSON 文件
        
        Args:
            file_name: 文件名（相对于解压后的目录）
            
        Returns:
            解析后的字典数据
        """
        if not self.extract_dir:
            raise ParseError("请先调用 extract() 方法解压文件")
            
        file_path = os.path.join(self.extract_dir, file_name)
        
        # 尝试在子目录中查找
        if not os.path.exists(file_path):
            # 搜索所有子目录
            for root, dirs, files in os.walk(self.extract_dir):
                if file_name in files:
                    file_path = os.path.join(root, file_name)
                    break
                    
        if not os.path.exists(file_path):
            raise ParseError(f"文件不存在：{file_name}", file_name)
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.debug(f"成功解析 JSON 文件：{file_name}")
            return data
            
        except json.JSONDecodeError as e:
            raise ParseError(f"JSON 解析失败：{str(e)}", file_name)
        except Exception as e:
            raise ParseError(f"读取文件失败：{str(e)}", file_name)
    
    def parse_txt_table(self, file_name: str) -> pd.DataFrame:
        """
        解析 TXT 表格文件（以分隔符格式）
        
        Args:
            file_name: 文件名
            
        Returns:
            DataFrame 对象
        """
        if not self.extract_dir:
            raise ParseError("请先调用 extract() 方法解压文件")
            
        file_path = os.path.join(self.extract_dir, file_name)
        
        # 尝试在子目录中查找
        if not os.path.exists(file_path):
            for root, dirs, files in os.walk(self.extract_dir):
                if file_name in files:
                    file_path = os.path.join(root, file_name)
                    break
                    
        if not os.path.exists(file_path):
            raise ParseError(f"文件不存在：{file_name}", file_name)
            
        try:
            # 尝试自动检测分隔符
            df = pd.read_csv(file_path, sep=r'\s+', engine='python')
            logger.debug(f"成功解析 TXT 表格：{file_name}")
            return df
            
        except Exception as e:
            raise ParseError(f"TXT 解析失败：{str(e)}", file_name)
    
    def cleanup(self):
        """清理临时文件"""
        if self.extract_dir and os.path.exists(self.extract_dir):
            try:
                shutil.rmtree(self.extract_dir)
                logger.info(f"已清理临时目录：{self.extract_dir}")
            except Exception as e:
                logger.warning(f"清理临时文件失败：{e}")
