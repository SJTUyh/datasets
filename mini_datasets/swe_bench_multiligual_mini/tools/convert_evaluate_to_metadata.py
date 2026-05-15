"""
SWE-bench 评估结果转换工具

该模块负责处理 SWE-bench 评估结果的转换：
将原始 evaluate CSV 转换为标准的 metadata 格式
"""

import csv
import json
import os
from pathlib import Path
from collections import defaultdict


def generate_metadata(input_dir: str, output_dir: str) -> None:
    """
    处理原始评估结果，生成标准的 metadata 格式

    Args:
        input_dir: 原始评估结果目录路径（包含多个 evaluate CSV 文件）
        output_dir: 输出的 metadata 文件夹路径
    """
    os.makedirs(output_dir, exist_ok=True)

    input_path = Path(input_dir)
    csv_files = list(input_path.glob("*.csv"))

    if not csv_files:
        raise FileNotFoundError(f"在目录 {input_dir} 中找不到任何 CSV 文件")

    print(f"找到 {len(csv_files)} 个 CSV 文件")

    metadata_csv_name = "swe_bench_multilingual_metadata"
    metadata_csv_path = os.path.join(output_dir, f"{metadata_csv_name}.csv")

    info_path = os.path.join(output_dir, "info.json")
    if os.path.exists(info_path):
        with open(info_path, "r", encoding="utf-8") as f:
            info_data = json.load(f)
    else:
        info_data = []

    info_dict = {item["name"]: item for item in info_data}

    for csv_file in csv_files:
        print(f"\n处理文件: {csv_file.name}")

        csv_basename = csv_file.stem
        score_col_name = f"{csv_basename}/resolved"

        instance_scores = {}
        all_scores = []
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                instance_id = row.get("metadata.instance_id", "").strip()
                resolved_raw = row.get("metadata.scores.resolved", "").strip()

                try:
                    resolved = float(resolved_raw)
                except (ValueError, TypeError):
                    resolved = 0.0

                instance_scores[instance_id] = resolved
                all_scores.append(resolved)

        count = len(instance_scores)
        avg_score = sum(all_scores) / count if count > 0 else 0

        if os.path.exists(metadata_csv_path):
            existing_rows = []
            with open(metadata_csv_path, "r", newline="", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)
                existing_fieldnames = reader.fieldnames.copy()
                for row in reader:
                    existing_rows.append(row)

            if score_col_name not in existing_fieldnames:
                existing_fieldnames.insert(-1, score_col_name)

            for row in existing_rows:
                data_id = row["id"]
                if data_id in instance_scores:
                    row[score_col_name] = instance_scores[data_id]
                else:
                    row[score_col_name] = 0

            with open(metadata_csv_path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=existing_fieldnames)
                writer.writeheader()
                for row in existing_rows:
                    writer.writerow(row)

            if metadata_csv_name in info_dict:
                info_dict[metadata_csv_name]["avg_scores"].append(avg_score)
            else:
                info_dict[metadata_csv_name] = {
                    "name": metadata_csv_name,
                    "count": len(existing_rows),
                    "avg_scores": [avg_score],
                    "difficulty_map": {
                        "level0": 0
                    }
                }
        else:
            fieldnames = ["id", score_col_name, "difficulty"]
            with open(metadata_csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for instance_id, resolved in instance_scores.items():
                    writer.writerow({
                        "id": instance_id,
                        score_col_name: resolved,
                        "difficulty": "level0"
                    })

            info_dict[metadata_csv_name] = {
                "name": metadata_csv_name,
                "count": count,
                "avg_scores": [avg_score],
                "difficulty_map": {
                    "level0": 0
                }
            }

        print(f"  共 {count} 条记录")
        print(f"  平均得分: {avg_score:.4f}")

    info_data = list(info_dict.values())
    with open(info_path, "w", encoding="utf-8") as f:
        json.dump(info_data, f, ensure_ascii=False, indent=4)

    print(f"\n处理完成！")
    print(f"Metadata 已保存到: {output_dir}")
    print(f"已更新 info.json: {info_path}")


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="将 SWE-bench evaluate CSV 转换为 multi_data_sample 格式的 metadata CSV"
    )
    parser.add_argument(
        "input_dir",
        help="evaluate 结果 CSV 所在目录路径",
    )
    parser.add_argument(
        "output_dir",
        help="输出 metadata 文件夹路径",
    )
    args = parser.parse_args()

    if not os.path.isdir(args.input_dir):
        print(f"错误: 目录不存在: {args.input_dir}", file=sys.stderr)
        sys.exit(1)

    generate_metadata(args.input_dir, args.output_dir)