"""
terminal_bench_2.0_mini 数据处理模块

该模块负责处理两种任务：
1. 将原始评估结果转换为标准的 metadata 格式
2. 将压缩后的 metadata 转换为最终的数据集内容
"""

import os
import sys
from pathlib import Path

tools_dir = Path(__file__).parent / "tools"
sys.path.insert(0, str(tools_dir))

from convert_eval_to_metadata import generate_metadata
from extract_terminal_bench_subsets import extract_subsets


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


def process_compressed_metadata(input_dir: str, output_dir: str, source_dir: str = None) -> None:
    """
    处理压缩后的 metadata，生成最终的数据集内容

    Args:
        input_dir: kmeans压缩后的metadata路径
        output_dir: 基于压缩的metadata文件夹生成的压缩后的数据集内容路径
        source_dir: 原始数据集目录路径（terminal-bench-2），不传则自动检测
    """
    os.makedirs(output_dir, exist_ok=True)

    input_path = Path(input_dir)

    csv_files = list(input_path.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"在 {input_dir} 中未找到 CSV 文件")
    metadata_csv = str(csv_files[0])

    if source_dir is None:
        source_dir = str(Path(__file__).parent / "terminal-bench-2")
    if not Path(source_dir).exists():
        raise FileNotFoundError(f"terminal-bench-2 目录不存在: {source_dir}")

    print("=" * 60)
    print("处理压缩后的 metadata")
    print("=" * 60)
    extract_subsets(metadata_csv, source_dir, output_dir)

    print("\n" + "=" * 60)
    print("处理完成！")
    print(f"输出目录: {output_dir}")