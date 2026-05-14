#!/usr/bin/env python3
"""
评估结果转 Metadata 工具

该脚本将原始评估结果转换为标准的 metadata 格式。
"""

import sys
import argparse
import importlib.util
from pathlib import Path


def process_dataset(dataset_name: str, input_dir: str, output_dir: str) -> None:
    """
    动态加载数据集对应的 processor 模块并调用其 process_eval_results。

    Args:
        dataset_name: 数据集名称（如 vbench_1.0_mini）
        input_dir: 原始评估结果路径
        output_dir: 生成的 metadata 文件夹路径
    """
    current_dir = Path(__file__).parent

    processor_path = current_dir / dataset_name / 'processor.py'

    if not processor_path.exists():
        raise FileNotFoundError(f"找不到处理文件: {processor_path}")

    spec = importlib.util.spec_from_file_location('processor', processor_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"无法加载模块: {processor_path}")

    processor_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(processor_module)

    print(f"使用数据集处理模块: {dataset_name}/processor.py")

    processor_module.process_eval_results(input_dir, output_dir)


def main():
    parser = argparse.ArgumentParser(
        description='将评估结果转换为 metadata 格式'
    )

    parser.add_argument(
        'dataset_name',
        type=str,
        help='数据集名称（如 vbench_1.0_mini）'
    )

    parser.add_argument(
        '--input', '-i',
        type=str,
        required=True,
        help='原始评估结果路径'
    )

    parser.add_argument(
        '--output', '-o',
        type=str,
        required=True,
        help='生成的 metadata 文件夹路径'
    )

    args = parser.parse_args()

    try:
        process_dataset(args.dataset_name, args.input, args.output)
    except FileNotFoundError as e:
        print(f"错误：{e}")
        print(f"\n请确保 '{args.dataset_name}' 目录存在并包含 processor.py 文件")
        sys.exit(1)
    except ImportError as e:
        print(f"错误：无法导入处理模块 '{args.dataset_name}.processor'")
        print(f"错误详情: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"处理过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
