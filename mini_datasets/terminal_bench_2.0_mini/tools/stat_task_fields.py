import argparse
import csv
import os
import sys
from collections import Counter


def parse_simple_toml(filepath):
    """Parse a simple TOML file without external dependencies.
    Handles the basic structure needed for task.toml files.
    """
    result = {}
    current_section = result

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("[") and line.endswith("]"):
                section_name = line[1:-1].strip()
                if section_name not in result:
                    result[section_name] = {}
                current_section = result[section_name]
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                current_section[key] = value

    return result


def main():
    parser = argparse.ArgumentParser(
        description="统计 terminal-bench-2.0 数据集中各 case 的 difficulty 和 category 字段分布"
    )
    parser.add_argument(
        "csv_path",
        help="metadata CSV 文件路径",
    )
    parser.add_argument(
        "dataset_dir",
        help="terminal-bench-2 数据集根目录路径",
    )
    args = parser.parse_args()

    csv_path = os.path.abspath(args.csv_path)
    dataset_dir = os.path.abspath(args.dataset_dir)

    if not os.path.isfile(csv_path):
        print(f"错误: CSV 文件不存在: {csv_path}")
        sys.exit(1)
    if not os.path.isdir(dataset_dir):
        print(f"错误: 数据集目录不存在: {dataset_dir}")
        sys.exit(1)

    case_ids = []
    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            case_ids.append(row["id"])

    print(f"从 CSV 中读取到 {len(case_ids)} 个 case")

    difficulty_counter = Counter()
    category_counter = Counter()
    missing_cases = []
    missing_fields = []

    for case_id in case_ids:
        task_toml_path = os.path.join(dataset_dir, case_id, "task.toml")
        if not os.path.isfile(task_toml_path):
            missing_cases.append(case_id)
            continue

        data = parse_simple_toml(task_toml_path)

        metadata = data.get("metadata", {})
        difficulty = metadata.get("difficulty")
        category = metadata.get("category")

        if difficulty is None:
            missing_fields.append((case_id, "difficulty"))
        else:
            difficulty_counter[difficulty] += 1

        if category is None:
            missing_fields.append((case_id, "category"))
        else:
            category_counter[category] += 1

    print()
    print("=" * 60)
    print("  difficulty 字段分布")
    print("=" * 60)
    for value, count in difficulty_counter.most_common():
        print(f"  {value:20s} : {count:4d}")

    print()
    print("=" * 60)
    print("  category 字段分布")
    print("=" * 60)
    for value, count in category_counter.most_common():
        print(f"  {value:20s} : {count:4d}")

    total_difficulty = sum(difficulty_counter.values())
    total_category = sum(category_counter.values())

    print()
    print(f"difficulty 已统计: {total_difficulty} / {len(case_ids)}")
    print(f"category   已统计: {total_category} / {len(case_ids)}")

    if missing_cases:
        print()
        print(f"缺少 task.toml 的 case ({len(missing_cases)}):")
        for case_id in missing_cases:
            print(f"  - {case_id}")

    if missing_fields:
        print()
        print(f"缺少字段的 case ({len(missing_fields)}):")
        for case_id, field in missing_fields:
            print(f"  - {case_id}: 缺少 {field}")


if __name__ == "__main__":
    main()