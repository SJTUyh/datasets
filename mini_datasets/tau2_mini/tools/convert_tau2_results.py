"""
tau2 评估结果转换工具

该模块负责处理 tau2 评估结果的转换：
1. 将原始评估结果转换为标准的 metadata 格式
2. 将压缩后的 metadata 转换为最终的数据集内容
"""

import os
import json
import csv
from pathlib import Path
from collections import defaultdict


def generate_metadata(input_dir: str, output_dir: str) -> None:
    """
    处理原始评估结果，生成标准的 metadata 格式

    Args:
        input_dir: 原始评估结果目录路径
        output_dir: 输出的 metadata 文件夹路径
    """
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 查找输入目录下的所有 JSON 文件
    input_path = Path(input_dir)
    json_files = list(input_path.glob('*.json'))

    if not json_files:
        raise FileNotFoundError(f"在目录 {input_dir} 中找不到任何 JSON 文件")

    print(f"找到 {len(json_files)} 个 JSON 文件")

    # 获取输入目录的名称，用于特征命名
    input_dir_name = os.path.basename(os.path.normpath(input_dir))

    # 读取现有的 info.json（如果存在）
    info_path = os.path.join(output_dir, "info.json")
    if os.path.exists(info_path):
        with open(info_path, 'r', encoding='utf-8') as f:
            info_data = json.load(f)
    else:
        info_data = []

    # 创建 info_data 的字典版本，方便查找
    info_dict = {item['name']: item for item in info_data}

    for json_file in json_files:
        print(f"\n处理文件: {json_file.name}")

        # 从文件名中提取模型名称和子集名称
        filename = json_file.stem
        # 解析文件名格式：{模型名称}_{子集名称}_trajectories
        parts = filename.split('_')
        if len(parts) >= 3 and parts[-1] == 'trajectories':
            # 例如 "GLM-5-Enabled_airline_trajectories" -> model_name="GLM-5-Enabled", subset_name="airline"
            subset_name = parts[-2]
            model_name = '_'.join(parts[:-2])
        else:
            # 备用解析方式
            subset_name = filename.split('_', 1)[1] if '_' in filename else filename
            model_name = filename.split('_', 1)[0] if '_' in filename else filename

        csv_name = f"{subset_name}_metadata"
        csv_path = os.path.join(output_dir, f"{csv_name}.csv")

        # 读取 JSON 文件
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 收集所有 simulations 数据
        simulations = data.get('simulations', [])

        # 按 task_id 聚合 reward
        task_rewards = defaultdict(list)
        for sim in simulations:
            task_id = str(sim.get('task_id', ''))
            reward = sim.get('reward_info', {}).get('reward', 0)
            task_rewards[task_id].append(reward)

        # 计算每个 task_id 的平均 reward
        task_avg_scores = {}
        all_scores = []
        for task_id, rewards in task_rewards.items():
            avg_reward = sum(rewards) / len(rewards)
            task_avg_scores[task_id] = avg_reward
            all_scores.append(avg_reward)

        # 计算整体统计信息
        count = len(task_avg_scores)
        avg_score = sum(all_scores) / count if count > 0 else 0

        # 使用模型名称作为分数列名（包含输入目录名，如 "GLM-5-ENABLED/GLM_5_Enabled"）
        score_col_name = f"{input_dir_name}/{model_name.replace('-', '_')}"

        # 检查 CSV 文件是否存在
        if os.path.exists(csv_path):
            # 读取现有 CSV 文件
            existing_rows = []
            with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                existing_fieldnames = reader.fieldnames.copy()
                for row in reader:
                    existing_rows.append(row)

            # 检查新特征是否已存在
            if score_col_name not in existing_fieldnames:
                existing_fieldnames.insert(-1, score_col_name)  # 在 difficulty 列之前插入

            # 更新现有行
            for row in existing_rows:
                data_id = row['id']
                if data_id in task_avg_scores:
                    row[score_col_name] = task_avg_scores[data_id]
                else:
                    row[score_col_name] = 0

            # 写入更新后的 CSV 文件
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=existing_fieldnames)
                writer.writeheader()
                for row in existing_rows:
                    writer.writerow(row)

            # 更新 info.json - 只添加新的平均分数
            if csv_name in info_dict:
                info_dict[csv_name]['avg_scores'].append(avg_score)
            else:
                # 新条目
                info_dict[csv_name] = {
                    "name": csv_name,
                    "count": len(existing_rows),
                    "avg_scores": [avg_score],
                    "difficulty_map": {
                        "level0": 0
                    }
                }
        else:
            # 生成新的 CSV 文件
            fieldnames = ['id', score_col_name, 'difficulty']
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for task_id, avg_score in task_avg_scores.items():
                    writer.writerow({
                        'id': task_id,
                        score_col_name: avg_score,
                        'difficulty': 'level0'
                    })

            # 更新 info.json - 新条目
            info_dict[csv_name] = {
                "name": csv_name,
                "count": count,
                "avg_scores": [avg_score],
                "difficulty_map": {
                    "level0": 0
                }
            }

        print(f"  处理了 {len(simulations)} 个 simulations")
        print(f"  聚合了 {count} 个唯一 task_id")
        print(f"  平均得分: {avg_score:.4f}")
        print(f"  CSV 已保存: {csv_name}.csv")

    # 生成 info.json
    info_data = list(info_dict.values())
    with open(info_path, 'w', encoding='utf-8') as f:
        json.dump(info_data, f, ensure_ascii=False, indent=4)

    print(f"\n处理完成！")
    print(f"Metadata 已保存到: {output_dir}")
    print(f"info.json 已生成")


def extract_subsets(input_dir: str, output_dir: str) -> None:
    """
    处理压缩后的 metadata，生成最终的数据集内容

    Args:
        input_dir: kmeans压缩后的metadata路径
        output_dir: 基于压缩的metadata文件夹生成的压缩后的数据集内容路径
    """
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 60)
    print("处理压缩后的 metadata")
    print("=" * 60)

    # 对于 tau2_mini，我们只需要将压缩后的 metadata 中的 id 提取出来
    # 生成代表性和随机两个子集的 id 列表

    # 处理 representative 子集
    rep_dir = os.path.join(input_dir, 'representative')
    if os.path.exists(rep_dir):
        rep_output_dir = os.path.join(output_dir, 'representative')
        os.makedirs(rep_output_dir, exist_ok=True)

        # 读取 info.json
        info_path = os.path.join(rep_dir, 'info.json')
        if os.path.exists(info_path):
            with open(info_path, 'r', encoding='utf-8') as f:
                info_list = json.load(f)

            # 为每个子集提取 id
            for info in info_list:
                subset_name = info['name']
                csv_path = os.path.join(rep_dir, f"{subset_name}.csv")
                ids_path = os.path.join(rep_dir, f"{subset_name}_ids.json")

                if os.path.exists(ids_path):
                    with open(ids_path, 'r', encoding='utf-8') as f:
                        ids = json.load(f)

                    # 保存 id 列表
                    output_ids_path = os.path.join(rep_output_dir, f"{subset_name}_ids.json")
                    with open(output_ids_path, 'w', encoding='utf-8') as f:
                        json.dump(ids, f, ensure_ascii=False, indent=2)

                    print(f"已保存 representative {subset_name} ids: {len(ids)} 个")

    # 处理 random 子集
    rand_dir = os.path.join(input_dir, 'random')
    if os.path.exists(rand_dir):
        rand_output_dir = os.path.join(output_dir, 'random')
        os.makedirs(rand_output_dir, exist_ok=True)

        # 读取 info.json
        info_path = os.path.join(rand_dir, 'info.json')
        if os.path.exists(info_path):
            with open(info_path, 'r', encoding='utf-8') as f:
                info_list = json.load(f)

            # 为每个子集提取 id
            for info in info_list:
                subset_name = info['name']
                csv_path = os.path.join(rand_dir, f"{subset_name}.csv")
                ids_path = os.path.join(rand_dir, f"{subset_name}_ids.json")

                if os.path.exists(ids_path):
                    with open(ids_path, 'r', encoding='utf-8') as f:
                        ids = json.load(f)

                    # 保存 id 列表
                    output_ids_path = os.path.join(rand_output_dir, f"{subset_name}_ids.json")
                    with open(output_ids_path, 'w', encoding='utf-8') as f:
                        json.dump(ids, f, ensure_ascii=False, indent=2)

                    print(f"已保存 random {subset_name} ids: {len(ids)} 个")

    print(f"\n处理完成！")
    print(f"输出目录: {output_dir}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Convert tau2 evaluate results to metadata format")
    parser.add_argument("input_dir", help="Directory containing tau2 evaluate results")
    parser.add_argument("output_dir", help="Directory to save metadata files")

    args = parser.parse_args()

    # 确保输出目录存在
    os.makedirs(args.output_dir, exist_ok=True)

    generate_metadata(args.input_dir, args.output_dir)
    print(f"Metadata generated successfully in {args.output_dir}")
