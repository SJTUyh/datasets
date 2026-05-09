"""
vbench_1.0_mini 数据处理模块

该模块负责处理两种任务：
1. 将原始评估结果转换为标准的 metadata 格式
2. 将压缩后的 metadata 转换为最终的数据集内容
"""

import os
import sys
from pathlib import Path

# 添加 tools 目录到路径，以便导入相关工具
tools_dir = Path(__file__).parent / 'tools'
sys.path.insert(0, str(tools_dir))

# 导入所需的工具函数
from convert_vbench_results import generate_metadata
from extract_vbench_subsets import extract_subsets


def process_eval_results(input_dir: str, output_dir: str) -> None:
    """
    处理原始评估结果，生成标准的 metadata 格式

    Args:
        input_dir: 原始评估结果目录路径
        output_dir: 输出的 metadata 文件夹路径
    """
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 调用 convert_vbench_results 中的 generate_metadata 函数
    print(f"处理评估结果: {input_dir}")
    generate_metadata(input_dir, output_dir)
    print(f"Metadata 已保存到: {output_dir}")


def process_compressed_metadata(input_dir: str, output_dir: str) -> None:
    """
    处理压缩后的 metadata，生成最终的数据集内容

    Args:
        input_dir: kmeans压缩后的metadata路径
        output_dir: 基于压缩的metadata文件夹生成的压缩后的数据集内容路径
    """
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 第一步：调用 extract_vbench_subsets 生成 kmeans 和随机方式采样的新 prompts
    print("=" * 60)
    print("第一步：提取子集 prompts")
    print("=" * 60)

    # 为了方便，我们先创建一个临时目录用于存放提取的 prompts
    prompts_temp_dir = os.path.join(output_dir, "temp_prompts")
    extract_subsets(input_dir, prompts_temp_dir)

    # 第二步：调用 filter_vbench_sub_info_json 基于 prompts 生成对应的 json 文件
    print("\n" + "=" * 60)
    print("第二步：生成筛选后的 JSON 文件")
    print("=" * 60)

    # 分别处理 kmeans 和 random 两个子集
    for subset_type in ["kmeans", "random"]:
        subset_prompts_dir = os.path.join(prompts_temp_dir, subset_type)
        if os.path.exists(subset_prompts_dir):
            output_json_path = os.path.join(output_dir, f"VBench_{subset_type}_info.json")

            print(f"\n处理 {subset_type} 子集...")
            print(f"Prompts 目录: {subset_prompts_dir}")
            print(f"输出 JSON: {output_json_path}")

            # 我们需要直接调用 filter_vbench_sub_info_json 中的逻辑
            # 或者通过命令行方式调用，因为该脚本是设计为命令行运行的
            # 为了方便，我们直接复制该脚本的核心逻辑来调用

            # 获取当前 tools 目录
            current_tools_dir = str(tools_dir)
            original_json_path = os.path.join(current_tools_dir, "VBench_full_info.json")

            if not os.path.exists(original_json_path):
                print(f"警告: 找不到原始 JSON 文件 {original_json_path}")
                continue

            # 收集 case 名称
            case_names = set()
            for filename in os.listdir(subset_prompts_dir):
                if filename.endswith('.txt'):
                    file_path = os.path.join(subset_prompts_dir, filename)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            case_name = line.strip()
                            if case_name:
                                case_names.add(case_name)

            # 读取并筛选 JSON 数据
            import json
            with open(original_json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            filtered_data = [item for item in data if item.get('prompt_en') in case_names]

            # 保存筛选后的数据
            with open(output_json_path, 'w', encoding='utf-8') as f:
                json.dump(filtered_data, f, ensure_ascii=False, indent=2)

            print(f"筛选完成: {len(filtered_data)} 个元素，共 {len(data)} 个")
            print(f"输出保存到: {output_json_path}")

    # 同时也把 prompts 文件保留在输出目录中，方便使用
    print("\n" + "=" * 60)
    print("整理输出文件")
    print("=" * 60)

    # 将 prompts 移动到输出目录的合适位置
    final_prompts_dir = os.path.join(output_dir, "prompts")
    if os.path.exists(final_prompts_dir):
        import shutil
        shutil.rmtree(final_prompts_dir)

    if os.path.exists(prompts_temp_dir):
        import shutil
        shutil.move(prompts_temp_dir, final_prompts_dir)

    print(f"\n处理完成！")
    print(f"输出目录: {output_dir}")
    print(f"Prompts 已保存到: {final_prompts_dir}")
    print(f"JSON 文件已生成:")
    for subset_type in ["kmeans", "random"]:
        json_path = os.path.join(output_dir, f"VBench_{subset_type}_info.json")
        if os.path.exists(json_path):
            print(f"  - {os.path.basename(json_path)}")
