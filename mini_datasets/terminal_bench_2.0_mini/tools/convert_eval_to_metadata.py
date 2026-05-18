import argparse
import csv
import json
import os


def read_csv_scores(csv_paths):
    model_scores = {}
    for filepath in csv_paths:
        filename = os.path.basename(filepath)
        model_name = os.path.splitext(filename)[0]
        case_scores = {}
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                task = row.get("Task", "").strip()
                resolution_rate_str = row.get("Resolution Rate", "0%").strip()
                resolution_rate_str = resolution_rate_str.rstrip("%")
                try:
                    score = float(resolution_rate_str) / 100.0
                except ValueError:
                    score = 0.0
                if task:
                    case_scores[task] = score
        model_scores[model_name] = case_scores
    return model_scores


def generate_metadata(csv_paths: list, output_dir: str) -> None:
    output_dir = os.path.abspath(output_dir)

    model_scores = read_csv_scores(csv_paths)
    if not model_scores:
        print("No valid CSV data found")
        return

    print(f"Found {len(model_scores)} CSV file(s)")
    for model_name, scores in model_scores.items():
        print(f"  {model_name}: {len(scores)} cases")

    all_case_ids = set()
    for scores in model_scores.values():
        all_case_ids.update(scores.keys())
    all_case_ids = sorted(all_case_ids)

    csv_name = "terminal_bench_metadata"
    csv_path = os.path.join(output_dir, f"{csv_name}.csv")
    info_path = os.path.join(output_dir, "info.json")

    os.makedirs(output_dir, exist_ok=True)

    model_score_cols = {
        model_name: f"{model_name.replace('-', '_')}/reward"
        for model_name in model_scores
    }

    if os.path.exists(csv_path):
        existing_rows = []
        with open(csv_path, "r", newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            existing_fieldnames = reader.fieldnames.copy()
            for row in reader:
                existing_rows.append(row)

        existing_ids = {row["id"] for row in existing_rows}

        for model_name, score_col_name in model_score_cols.items():
            if score_col_name not in existing_fieldnames:
                if "difficulty" in existing_fieldnames:
                    diff_idx = existing_fieldnames.index("difficulty")
                    existing_fieldnames.insert(diff_idx, score_col_name)
                else:
                    existing_fieldnames.append(score_col_name)

            scores = model_scores[model_name]
            for row in existing_rows:
                data_id = row["id"]
                row[score_col_name] = scores.get(data_id, 0)

        for case_id in all_case_ids:
            if case_id not in existing_ids:
                new_row = {"id": case_id, "difficulty": "level0"}
                for fn in existing_fieldnames:
                    if fn not in new_row:
                        new_row[fn] = 0
                for model_name, score_col_name in model_score_cols.items():
                    new_row[score_col_name] = model_scores[model_name].get(case_id, 0)
                existing_rows.append(new_row)

        with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=existing_fieldnames)
            writer.writeheader()
            for row in existing_rows:
                writer.writerow(row)

    else:
        fieldnames = ["id"]
        for score_col_name in model_score_cols.values():
            fieldnames.append(score_col_name)
        fieldnames.append("difficulty")

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for case_id in all_case_ids:
                row = {"id": case_id, "difficulty": "level0"}
                for model_name, score_col_name in model_score_cols.items():
                    row[score_col_name] = model_scores[model_name].get(case_id, 0)
                writer.writerow(row)

    avg_scores = []
    for model_name, scores in model_scores.items():
        if len(scores) > 0:
            avg = sum(scores.values()) / len(scores)
        else:
            avg = 0.0
        avg_scores.append(avg)
        print(f"  {model_name}: avg_score = {avg:.4f}")

    overall_avg = sum(avg_scores) / len(avg_scores) if avg_scores else 0.0
    print(f"Overall average score: {overall_avg:.4f}")

    if abs(overall_avg) < 1e-6:
        print()
        print("=" * 60)
        print(f"  ⚠ WARNING: overall avg_score is extremely close to 0!")
        print(f"  avg_score = {overall_avg}")
        print("=" * 60)
        print()

    if os.path.exists(info_path):
        with open(info_path, "r", encoding="utf-8") as f:
            info_data = json.load(f)
    else:
        info_data = []

    info_dict = {item["name"]: item for item in info_data}

    if csv_name in info_dict:
        info_dict[csv_name]["avg_scores"] = avg_scores
        info_dict[csv_name]["count"] = len(all_case_ids)
    else:
        info_dict[csv_name] = {
            "name": csv_name,
            "count": len(all_case_ids),
            "avg_scores": avg_scores,
            "difficulty_map": {"level0": 0},
        }

    info_data = list(info_dict.values())
    with open(info_path, "w", encoding="utf-8") as f:
        json.dump(info_data, f, ensure_ascii=False, indent=4)

    print(f"Metadata saved to {output_dir}")
    print(f"  CSV: {csv_name}.csv")
    print(f"  info: info.json")


def main():
    parser = argparse.ArgumentParser(
        description="Convert terminus2 eval CSV results to metadata"
    )
    parser.add_argument(
        "csv_files",
        nargs="+",
        help="Path(s) to eval CSV file(s)",
    )
    parser.add_argument(
        "--output_dir",
        required=True,
        help="Path to the output metadata folder",
    )
    args = parser.parse_args()

    generate_metadata(args.csv_files, args.output_dir)


if __name__ == "__main__":
    main()