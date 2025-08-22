"""
ModelAI - 智能3D建模工具
为Unity游戏制作生成高质量3D模型的AI驱动工具
"""

__version__ = "0.1.0"
__author__ = "ModelAI Team"

from .core import ModelGenerator
from .models import ModelType, ModelClassifier
from .unity_export import UnityExporter