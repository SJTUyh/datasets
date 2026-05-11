# TAU2-mini
## 简介
TAU2-mini 是基于[TAU2评估结果](https://github.com/THUDM/TAU2)进行约1/10规模的采样得到的一个小规模数据集，它在测试得分上与原始数据集大致相同。
## 数据集获取方式
[🔗TAU2-mini 数据集](https://modelers.cn/datasets/AISBench/TAU2-mini)

## 复现数据提取过程
先安装kmeans采样脚本依赖：
```bash
pip3 install -r ../requirements.txt
```
执行采样过程：
```bash
# 步骤1: 使用 K-Means 压缩 metadata，自动为每个子集取最优簇
python ../select_metadata_by_kmeans.py --input ./tau2_metadata --work-dir ./compressed_output --compression-ratio 0.1 -a

# 步骤2: 将压缩后的 metadata 转换为最终数据集
python ../compressed_metadata_to_mini_datasets.py tau2_mini --input ./compressed_output/tau2_metadata_output_compressed_0.10 --output ./final_mini_dataset
```

例如：
```bash
# 步骤1: 使用 K-Means 压缩 metadata，自动为每个子集取最优簇
python ../select_metadata_by_kmeans.py --input ./tau2_metadata --work-dir ./compressed_output --compression-ratio 0.1 -a

# 步骤2: 将压缩后的 metadata 转换为最终数据集
python ../compressed_metadata_to_mini_datasets.py tau2_mini --input ./compressed_output/tau2_metadata_compressed_0.10 --output ./final_mini_dataset
```

采样效果图结构如下：
```bash
compressed_output/
├── tau2_metadata_compressed_0.10
│   ├── clustering_visualizations # 每个子集的kmeans聚类效果可视化图
│   ├── random
│   └── representative
└── tau2_metadata_figures_0.10 # 采样得分效果图
    ├── comparison_summary.json
    ├── airline_metadata_means_comparison.png
    ├── retail_metadata_means_comparison.png
    └── telecom_metadata_means_comparison.png
```

最终生成的采样数据集如下：
```bash
final_mini_dataset/
├── airline
│   └── split_tasks.json # 在其中添加了一个mini split
├── retail
│   └── split_tasks.json # 在其中添加了一个mini split
└── telecom
    └── split_tasks.json # 在其中添加了一个mini split
```

