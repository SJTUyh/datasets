import argparse
import csv
import json
import os
from collections import defaultdict


def find_result_files(eval_dir):
    result_files = []
    for root, dirs, files in os.walk(eval_dir):
        if "result.json" in files:
            result_files.append(os.path.join(root, "result.json"))
    return result_files


def collect_rewards_from_subdirs(result_file_dir):
    case_rewards = defaultdict(list)
    for name in os.listdir(result_file_dir):
        subdir = os.path.join(result_file_dir, name)
        if not os.path.isdir(subdir):
            continue
        if "__" not in name:
            continue
        sub_result = os.path.join(subdir, "result.json")
        if not os.path.isfile(sub_result):
            continue
        case_name = name.rsplit("__", 1)[0]
        with open(sub_result, "r", encoding="utf-8") as f:
            data = json.load(f)
        reward = data.get("verifier_result", {}).get("rewards", {}).get("reward")
        if reward is not None:
            case_rewards[case_name].append(float(reward))
    return case_rewards


def merge_reward_stats(result_files):
    case_rewards = defaultdict(list)

    for filepath in result_files:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        evals = data.get("stats", {}).get("evals", {})
        if not evals:
            continue
        eval_key = next(iter(evals))
        reward_stats = evals[eval_key].get("reward_stats", {}).get("reward", {})

        if not reward_stats:
            result_file_dir = os.path.dirname(filepath)
            fallback_rewards = collect_rewards_from_subdirs(result_file_dir)
            for case_name, rewards in fallback_rewards.items():
                case_rewards[case_name].extend(rewards)
            continue

        for reward_str, entries in reward_stats.items():
            reward_value = float(reward_str)
            for entry in entries:
                if "__" in entry:
                    case_name = entry.rsplit("__", 1)[0]
                else:
                    case_name = entry
                case_rewards[case_name].append(reward_value)

    return case_rewards


def compute_averages(case_rewards):
    return {
        case_name: sum(values) / len(values)
        for case_name, values in case_rewards.items()
    }


def generate_metadata(eval_dir: str, output_dir: str) -> None:
    eval_dir = os.path.abspath(eval_dir)
    output_dir = os.path.abspath(output_dir)
    model_name = os.path.basename(eval_dir)

    result_files = find_result_files(eval_dir)
    if not result_files:
        print(f"No result.json files found under {eval_dir}")
        return

    print(f"Found {len(result_files)} result.json file(s)")

    case_rewards = merge_reward_stats(result_files)
    case_averages = compute_averages(case_rewards)

    count = len(case_averages)
    all_scores = list(case_averages.values())
    avg_score = sum(all_scores) / count if count > 0 else 0

    print(f"Computed average rewards for {count} cases")
    print(f"Overall average score: {avg_score:.4f}")

    if abs(avg_score) < 1e-6:
        print()
        print("=" * 60)
        print(f"  ⚠ WARNING: avg_score is extremely close to 0!")
        print(f"  Model: {model_name}")
        print(f"  avg_score = {avg_score}")
        print("=" * 60)
        print()

    score_col_name = f"{model_name.replace('-', '_')}/reward"

    csv_name = "terminal_bench_metadata"
    csv_path = os.path.join(output_dir, f"{csv_name}.csv")
    info_path = os.path.join(output_dir, "info.json")

    os.makedirs(output_dir, exist_ok=True)

    if os.path.exists(info_path):
        with open(info_path, "r", encoding="utf-8") as f:
            info_data = json.load(f)
    else:
        info_data = []
    info_dict = {item["name"]: item for item in info_data}

    if os.path.exists(csv_path):
        existing_rows = []
        with open(csv_path, "r", newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            existing_fieldnames = reader.fieldnames.copy()
            for row in reader:
                existing_rows.append(row)

        if score_col_name not in existing_fieldnames:
            existing_fieldnames.insert(-1, score_col_name)

        for row in existing_rows:
            data_id = row["id"]
            row[score_col_name] = case_averages.get(data_id, 0)

        with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=existing_fieldnames)
            writer.writeheader()
            for row in existing_rows:
                writer.writerow(row)

        if csv_name in info_dict:
            info_dict[csv_name]["avg_scores"].append(avg_score)
        else:
            info_dict[csv_name] = {
                "name": csv_name,
                "count": len(existing_rows),
                "avg_scores": [avg_score],
                "difficulty_map": {"level0": 0},
            }
    else:
        fieldnames = ["id", score_col_name, "difficulty"]
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for case_name, avg_score_val in case_averages.items():
                writer.writerow({
                    "id": case_name,
                    score_col_name: avg_score_val,
                    "difficulty": "level0",
                })

        info_dict[csv_name] = {
            "name": csv_name,
            "count": count,
            "avg_scores": [avg_score],
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
        description="Convert terminal-bench-2.0 eval results to metadata"
    )
    parser.add_argument(
        "--eval_dir",
        required=True,
        help="Path to the model evaluation folder (e.g. .../Forge__Gemini-3.1-Pro-Preview)",
    )
    parser.add_argument(
        "--output_dir",
        required=True,
        help="Path to the output metadata folder",
    )
    args = parser.parse_args()

    generate_metadata(args.eval_dir, args.output_dir)


if __name__ == "__main__":
    main()