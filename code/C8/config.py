"""
RAG系统配置文件
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any


BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parents[1]


def _default_data_path() -> str:
    return str(PROJECT_ROOT / "data" / "C8" / "cook")


def _default_index_save_path() -> str:
    return str(BASE_DIR / "vector_index")


@dataclass
class RAGConfig:
    """RAG系统配置类"""

    # 路径配置
    data_path: str = field(default_factory=_default_data_path)
    index_save_path: str = field(default_factory=_default_index_save_path)

    # 模型配置
    embedding_model: str = "BAAI/bge-small-zh-v1.5"
    llm_model: str = field(default_factory=lambda: os.getenv("LLM", "deepseek-v4-pro"))
    deepseek_api_base: str = field(default_factory=lambda: os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com"))

    # 检索配置
    top_k: int = 3

    # 生成配置
    temperature: float = 0.1
    max_tokens: int = 20480

    def __post_init__(self):
        """初始化后的处理"""
        pass
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'RAGConfig':
        """从字典创建配置对象"""
        return cls(**config_dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'data_path': self.data_path,
            'index_save_path': self.index_save_path,
            'embedding_model': self.embedding_model,
            'llm_model': self.llm_model,
            'deepseek_api_base': self.deepseek_api_base,
            'top_k': self.top_k,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens
        }

# 默认配置实例
DEFAULT_CONFIG = RAGConfig()
