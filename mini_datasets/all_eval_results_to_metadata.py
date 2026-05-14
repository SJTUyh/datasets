#!/usr/bin/env python3
"""
批量评估结果转 Metadata 工具

遍历输入目录下的所有子文件夹，对每个子文件夹调用 eval_results_to_metadata.py 中的 process_dataset。
"""

import argparse
import sys
from pathlib import Path

from eval_results_to_metadata import process_dataset


def main():
    parser = argparse.ArgumentParser(
        description='批量将评估结果转换为 metadata 格式'
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
        help='原始评估结果根目录（其下的每个子文件夹将被分别处理）'
    )

    parser.add_argument(
        '--output', '-o',
        type=str,
        required=True,
        help='生成的 metadata 根目录'
    )

    args = parser.parse_args()

    input_root = Path(args.input)
    output_root = Path(args.output)

    if not input_root.exists():
        print(f"错误：输入目录不存在: {input_root}")
        sys.exit(1)

    if not input_root.is_dir():
        print(f"错误：输入路径不是目录: {input_root}")
        sys.exit(1)

    subdirs = sorted([
        d for d in input_root.iterdir()
        if d.is_dir()
    ])

    if not subdirs:
        print(f"警告：输入目录下没有子文件夹: {input_root}")
        sys.exit(0)

    success_count = 0
    fail_count = 0

    for subdir in subdirs:
        subdir_name = subdir.name

        print(f"\n{'=' * 60}")
        print(f"处理: {subdir_name}")
        print(f"  输入: {subdir}")
        print(f"  输出: {output_root}")
        print(f"{'=' * 60}")

        try:
            process_dataset(args.dataset_name, str(subdir), args.output)
            print(f"✓ {subdir_name} 处理成功")
            success_count += 1
        except Exception as e:
            print(f"✗ {subdir_name} 处理失败: {e}")
            fail_count += 1

    print(f"\n{'=' * 60}")
    print(f"批量处理完成: 成功 {success_count}, 失败 {fail_count}")
    print(f"{'=' * 60}")

    if fail_count > 0:
        sys.exit(1)


if __name__ == '__main__':
    main()