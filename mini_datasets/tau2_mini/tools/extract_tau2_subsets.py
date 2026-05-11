#!/usr/bin/env python3
import argparse
import json
import csv
import os
from pathlib import Path


def load_csv_ids(csv_path):
    """Load ids from CSV file and convert to strings."""
    ids = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            ids.append(str(row['id']))
    return ids


def process_task(task_name, csv_path, original_json_path, output_dir):
    """Process a single task and create updated split_tasks.json."""
    # Load CSV ids
    csv_ids = load_csv_ids(csv_path)
    print(f"Loaded {len(csv_ids)} ids from {task_name} CSV")

    # Load original split tasks
    with open(original_json_path, 'r', encoding='utf-8') as f:
        split_tasks = json.load(f)

    # Get base split for filtering
    base_split = split_tasks.get('base', [])
    base_set = set(base_split)

    # Filter CSV ids to only include those present in base split
    mini_ids = [id_ for id_ in csv_ids if id_ in base_set]
    print(f"Filtered to {len(mini_ids)} ids present in base split")

    # Add mini split
    split_tasks['mini'] = mini_ids

    # Create output directory for task
    task_output_dir = output_dir / task_name
    task_output_dir.mkdir(parents=True, exist_ok=True)

    # Save updated split_tasks.json
    output_path = task_output_dir / 'split_tasks.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(split_tasks, f, ensure_ascii=False, indent=2)

    print(f"Saved updated split_tasks.json to {output_path}")
    return output_path


def extract_subsets(input_dir: str, output_dir: str) -> None:
    """
    提取 tau2 子集并生成带 mini split 的 split_tasks.json 文件。

    Args:
        input_dir: 压缩后的 metadata 路径（tau2_output 目录）
        output_dir: 输出目录，保存带有 mini split 的 split_tasks.json 文件
    """
    metadata_path = Path(input_dir)
    output_dir_path = Path(output_dir)

    # Auto-detect tools directory from script's parent
    script_dir = Path(__file__).parent
    tools_dir = script_dir

    # Define representative metadata directory
    representative_dir = metadata_path / 'tau2_metadata_compressed_0.10' / 'representative'

    if not representative_dir.exists():
        print(f"Error: Representative metadata directory not found at {representative_dir}")
        return

    # Create output directory
    output_dir_path.mkdir(parents=True, exist_ok=True)

    # Process each task
    tasks = [
        ('airline', 'airline_metadata.csv'),
        ('retail', 'retail_metadata.csv'),
        ('telecom', 'telecom_metadata.csv')
    ]

    for task_name, csv_filename in tasks:
        csv_path = representative_dir / csv_filename
        original_json_path = tools_dir / task_name / 'split_tasks.json'

        if not csv_path.exists():
            print(f"Warning: CSV not found for {task_name} at {csv_path}, skipping")
            continue

        if not original_json_path.exists():
            print(f"Warning: Original split_tasks.json not found for {task_name} at {original_json_path}, skipping")
            continue

        print(f"\nProcessing {task_name}...")
        process_task(task_name, csv_path, original_json_path, output_dir_path)

    print("\nDone!")


def main():
    parser = argparse.ArgumentParser(description='Extract tau2 subsets and create split files')
    parser.add_argument('--metadata-path', required=True, help='Path to tau2 output directory with metadata')
    parser.add_argument('--output-dir', required=True, help='Directory to save output split files')

    args = parser.parse_args()

    extract_subsets(args.metadata_path, args.output_dir)
    return 0


if __name__ == '__main__':
    exit(main())
