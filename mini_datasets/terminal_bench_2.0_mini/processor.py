"""
terminal_bench_2.0_mini 数据处理模块

该模块负责将原始评估结果转换为标准的 metadata 格式
"""

import os
import sys
from pathlib import Path

tools_dir = Path(__file__).parent / "tools"
sys.path.insert(0, str(tools_dir))

from convert_eval_to_metadata import generate_metadata


def process_eval_results(input_dir: str, output_dir: str) -> None:
    """
    处理原始评估结果，生成标准的 metadata 格式

    Args:
        input_dir: 原始评估结果目录路径（模型文件夹，如 .../Forge__Gemini-3.1-Pro-Preview）
        output_dir: 输出的 metadata 文件夹路径
    """
    os.makedirs(output_dir, exist_ok=True)

    print(f"处理评估结果: {input_dir}")
    generate_metadata(input_dir, output_dir)
    print(f"Metadata 已保存到: {output_dir}")