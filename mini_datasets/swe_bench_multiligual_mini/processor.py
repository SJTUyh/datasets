"""
swe_bench_multilingual_mini 数据处理模块

该模块负责将原始评估结果转换为标准的 metadata 格式
"""

import os
import sys
from pathlib import Path

tools_dir = Path(__file__).parent / "tools"
sys.path.insert(0, str(tools_dir))

from convert_evaluate_to_metadata import generate_metadata


def process_eval_results(input_dir: str, output_dir: str) -> None:
    """
    处理原始评估结果，生成标准的 metadata 格式

    Args:
        input_dir: 原始评估结果目录路径
        output_dir: 输出的 metadata 文件夹路径
    """
    os.makedirs(output_dir, exist_ok=True)

    print(f"处理评估结果: {input_dir}")
    generate_metadata(input_dir, output_dir)
    print(f"Metadata 已保存到: {output_dir}")


def process_compressed_metadata(input_dir: str, output_dir: str, source_dir: str = None) -> None:
    """
    处理压缩后的 metadata，生成最终的数据集内容

    Args:
        input_dir: kmeans压缩后的metadata路径
        output_dir: 基于压缩的metadata文件夹生成的压缩后的数据集内容路径
        source_dir: 原始数据集目录路径（统一接口保留）
    """
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 60)
    print("处理压缩后的 metadata")
    print("=" * 60)

    print("\n" + "=" * 60)
    print("处理完成！")
    print(f"输出目录: {output_dir}")