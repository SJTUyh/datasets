"""
tau2_mini 数据处理模块

该模块负责处理两种任务：
1. 将原始评估结果转换为标准的 metadata 格式
2. 将压缩后的 metadata 转换为最终的数据集内容
"""

import os
import sys
from pathlib import Path

# 添加 tools 目录到路径，以便导入相关工具
tools_dir = Path(__file__).parent / 'tools'
sys.path.insert(0, str(tools_dir))

# 导入所需的工具函数
from convert_tau2_results import generate_metadata
from extract_tau2_subsets import extract_subsets


def process_eval_results(input_dir: str, output_dir: str) -> None:
    """
    处理原始评估结果，生成标准的 metadata 格式

    Args:
        input_dir: 原始评估结果目录路径
        output_dir: 输出的 metadata 文件夹路径
    """
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 调用 convert_tau2_results 中的 generate_metadata 函数
    print(f"处理评估结果: {input_dir}")
    generate_metadata(input_dir, output_dir)
    print(f"Metadata 已保存到: {output_dir}")


def process_compressed_metadata(input_dir: str, output_dir: str, source_dir: str = None) -> None:
    """
    处理压缩后的 metadata，生成最终的数据集内容

    Args:
        input_dir: kmeans压缩后的metadata路径（tau2_output 目录）
        output_dir: 基于压缩的metadata文件夹生成的压缩后的数据集内容路径
        source_dir: 原始数据集目录路径（tau2 不需要此参数，仅为统一接口保留）
    """
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 调用 extract_tau2_subsets 中的 extract_subsets 函数
    print("=" * 60)
    print("处理压缩后的 metadata")
    print("=" * 60)
    extract_subsets(input_dir, output_dir)

    print("\n" + "=" * 60)
    print("处理完成！")
    print(f"输出目录: {output_dir}")
