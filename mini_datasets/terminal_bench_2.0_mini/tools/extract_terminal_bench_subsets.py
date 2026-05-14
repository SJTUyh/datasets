#!/usr/bin/env python3
import argparse
import csv
import shutil
from pathlib import Path


def load_csv_ids(csv_path):
    """Load ids from CSV file."""
    ids = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            ids.append(row['id'])
    return ids


def extract_subsets(metadata_csv: str, source_dir: str, output_dir: str) -> None:
    """
    基于压缩后的 metadata CSV，从 terminal-bench-2 筛选对应的 case 并保存到指定路径。

    Args:
        metadata_csv: 压缩后的 metadata CSV 文件路径
        source_dir: terminal-bench-2 目录路径（包含各 case 子目录）
        output_dir: 输出目录，保存筛选后的 case 文件夹
    """
    csv_path = Path(metadata_csv)
    source_path = Path(source_dir)
    output_path = Path(output_dir)

    if not csv_path.exists():
        print(f"Error: Metadata CSV not found at {csv_path}")
        return

    if not source_path.exists():
        print(f"Error: Source directory not found at {source_path}")
        return

    ids = load_csv_ids(csv_path)
    print(f"Loaded {len(ids)} ids from metadata CSV")

    output_path.mkdir(parents=True, exist_ok=True)

    copied = 0
    skipped = []

    for case_id in ids:
        case_dir = source_path / case_id
        if case_dir.exists() and case_dir.is_dir():
            dest_dir = output_path / case_id
            if dest_dir.exists():
                shutil.rmtree(dest_dir)
            shutil.copytree(case_dir, dest_dir)
            copied += 1
            print(f"  Copied: {case_id}")
        else:
            skipped.append(case_id)
            print(f"  Warning: Case directory not found: {case_id}")

    print(f"\nDone! Copied {copied} cases, skipped {len(skipped)}.")
    if skipped:
        print(f"Skipped: {skipped}")


def main():
    parser = argparse.ArgumentParser(
        description='Extract terminal-bench-2 subsets based on compressed metadata'
    )
    parser.add_argument(
        '--metadata-csv', required=True,
        help='Path to the compressed metadata CSV file'
    )
    parser.add_argument(
        '--source-dir', required=True,
        help='Path to terminal-bench-2 directory containing case folders'
    )
    parser.add_argument(
        '--output-dir', required=True,
        help='Directory to save filtered case folders'
    )

    args = parser.parse_args()

    extract_subsets(args.metadata_csv, args.source_dir, args.output_dir)
    return 0


if __name__ == '__main__':
    exit(main())