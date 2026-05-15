# SWE-bench-Multilingual-mini
## 简介
SWE-bench-Multilingual-mini 是基于 SWE-bench Multilingual 评估结果进行约1/10规模的采样得到的一个小规模数据集，它在多模型测试得分上与原始数据集大致相同。

评估得分涵盖以下 13 个模型：Claude-4.5-Sonnet、DeepSeek-V3.2、GPT-5.2-Codex、GLM-5、Claude-4.5-Opus、Kimi-K2.5、Gemini-3-Flash、GPT-5-mini、Claude-4.5-Haiku、Gemini-3-Pro、Minimax-2.5、GPT-5.2-high_reasoning、Claude-4.6-Opus。

## 数据集获取方式
[🔗SWE-Bench_Multilingual_mini 数据集](https://modelers.cn/datasets/AISBench/SWE-Bench_Multilingual_mini)

## 复现数据提取过程
先安装kmeans采样脚本依赖：
```bash
pip3 install -r ../requirements.txt
```

执行采样过程：
```bash
# 步骤1: 使用 K-Means 压缩 metadata，自动为每个子集取最优簇
python ../select_metadata_by_kmeans.py --input ./swe_multilingual_metadata --work-dir ./compressed_output --compression-ratio 0.05 -a

python ../select_metadata_by_kmeans.py --input ./swe_multilingual_metadata --work-dir ./compressed_output --compression-ratio 0.1 -a

python ../select_metadata_by_kmeans.py --input ./swe_multilingual_metadata --work-dir ./compressed_output --compression-ratio 0.2 -a

# 步骤2: 将压缩后的 metadata 转换为最终数据集（需指定原始数据集路径）
python ../compressed_metadata_to_mini_datasets.py swe_bench_multiligual_mini --input ./compressed_output/swe_multilingual_metadata_compressed_0.05 --output ./SWE-Bench_Multilingual_select_0.05/data --source-dir <原始SWE-bench-Multilingual数据集路径>

python ../compressed_metadata_to_mini_datasets.py swe_bench_multiligual_mini --input ./compressed_output/swe_multilingual_metadata_compressed_0.10 --output ./SWE-Bench_Multilingual_select_0.10/data --source-dir <原始SWE-bench-Multilingual数据集路径>

python ../compressed_metadata_to_mini_datasets.py swe_bench_multiligual_mini --input ./compressed_output/swe_multilingual_metadata_compressed_0.20 --output ./SWE-Bench_Multilingual_select_0.20/data --source-dir <原始SWE-bench-Multilingual数据集路径>
```

例如：
```bash
# 步骤1: 使用 K-Means 压缩 metadata，自动为每个子集取最优簇
python ../select_metadata_by_kmeans.py --input ./swe_multilingual_metadata --work-dir ./compressed_output --compression-ratio 0.1 -a

# 步骤2: 将压缩后的 metadata 转换为最终数据集
python ../compressed_metadata_to_mini_datasets.py swe_bench_multiligual_mini --input ./compressed_output/swe_multilingual_metadata_compressed_0.10 --output ./final_mini_dataset --source-dir /path/to/SWE-bench_Multilingual
```

采样效果图结构如下：
```bash
compressed_output/
├── swe_multilingual_metadata_compressed_0.10
│   ├── clustering_visualizations # kmeans聚类效果可视化图
│   ├── random
│   └── representative
└── swe_multilingual_metadata_figures_0.10 # 采样得分效果图
    ├── comparison_summary.json
    └── swe_bench_multilingual_metadata_means_comparison.png
```

最终生成的采样数据集如下（从原始 parquet 文件中筛选对应 instance_id 的数据）：
```bash
SWE-Bench_Multilingual_select_0.10/data
└── <原始parquet文件名>.parquet
```