#!/usr/bin/env python3
"""
压缩 Metadata 转 Mini Datasets 工具

该脚本将压缩后的 metadata 转换为最终的数据集内容。
"""

import sys
import argparse
import importlib.util
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description='将压缩后的 metadata 转换为最终的数据集内容'
    )

    # 第一个位置参数：数据集名称（如 vbench_1.0_mini）
    parser.add_argument(
        'dataset_name',
        type=str,
        help='数据集名称（如 vbench_1.0_mini）'
    )

    # 输入目录
    parser.add_argument(
        '--input', '-i',
        type=str,
        required=True,
        help='kmeans压缩后的metadata路径'
    )

    # 输出目录
    parser.add_argument(
        '--output', '-o',
        type=str,
        required=True,
        help='基于压缩的metadata文件夹生成的压缩后的数据集内容路径'
    )

    # 原始数据集路径（部分数据集需要，如 terminal_bench_2.0 需传入 terminal-bench-2 目录）
    parser.add_argument(
        '--source-dir', '-s',
        type=str,
        default=None,
        help='原始数据集目录路径（如 terminal-bench-2），不传则由 processor 自动检测'
    )

    args = parser.parse_args()

    # 动态导入对应的处理模块
    try:
        # 添加当前目录到 Python 路径
        current_dir = Path(__file__).parent

        # 构建 processor.py 的路径
        processor_path = current_dir / args.dataset_name / 'processor.py'

        if not processor_path.exists():
            raise FileNotFoundError(f"找不到处理文件: {processor_path}")

        # 使用 importlib 动态加载模块
        spec = importlib.util.spec_from_file_location('processor', processor_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"无法加载模块: {processor_path}")

        processor_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(processor_module)

        print(f"使用数据集处理模块: {args.dataset_name}/processor.py")

        # 调用处理函数
        if args.source_dir:
            processor_module.process_compressed_metadata(args.input, args.output, args.source_dir)
        else:
            processor_module.process_compressed_metadata(args.input, args.output)

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
