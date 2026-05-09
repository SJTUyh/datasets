# K-Means 数据集子集选择工具

这个工具使用 K-Means 聚类算法从原始数据集中生成具有代表性的子集，并提供详细的比较分析和可视化效果。

## 目录

- [项目简介](#项目简介)
- [依赖安装](#依赖安装)
- [完整工作流](#完整工作流)
- [压缩原理](#压缩原理)
- [使用方法](#使用方法)
- [输出目录结构](#输出目录结构)
- [呈现效果含义](#呈现效果含义)
- [参数说明](#参数说明)

## 项目简介

该工具链包含三个主要脚本，提供完整的数据集处理流程：
1. **eval_results_to_metadata.py**：将原始评估结果转换为标准的 metadata 格式
2. **select_metadata_by_kmeans.py**：使用 K-Means 聚类算法从 metadata 中生成具有代表性的子集
3. **compressed_metadata_to_mini_datasets.py**：将压缩后的 metadata 转换为最终的数据集内容

主要功能特性：
- 使用 K-Means 聚类算法生成具有代表性的数据子集
- 同时生成随机样本作为对照
- 对比分析原始数据、代表性样本和随机样本的统计特性
- 提供丰富的可视化效果
- 支持灵活的数据集处理器，可自定义前后处理逻辑

## 依赖安装

```bash
pip install -r requirements.txt
```

## 完整工作流

本工具包含三个主要脚本，构成完整的数据集处理工作流：

### 1. eval_results_to_metadata.py - 评估结果转 Metadata
将原始评估结果转换为标准的 metadata 格式，为 K-Means 压缩做准备。

#### 使用示例：
```bash
python eval_results_to_metadata.py <dataset_name> --input <原始评估结果路径> --output <metadata输出路径>
```

#### 参数说明：
- `dataset_name`: 数据集名称（如 vbench_1.0_mini），用于指定对应的处理模块
- `--input/-i`: 原始评估结果路径
- `--output/-o`: 生成的 metadata 文件夹路径

#### 要求：
- 需要在 `<dataset_name>` 目录下存在 `processor.py` 文件，该文件需实现 `process_eval_results(input_dir, output_dir)` 函数

---

### 2. select_metadata_by_kmeans.py - K-Means 压缩
使用 K-Means 聚类算法从 metadata 中生成具有代表性的子集。

#### 使用示例：
```bash
python select_metadata_by_kmeans.py --input ./multi_data_sample --work-dir ./output --compression-ratio 0.1
```

---

### 3. compressed_metadata_to_mini_datasets.py - 压缩 Metadata 转 Mini Datasets
将压缩后的 metadata 转换为最终的数据集内容。

#### 使用示例：
```bash
python compressed_metadata_to_mini_datasets.py <dataset_name> --input <压缩后的metadata路径> --output <最终数据集输出路径>
```

#### 参数说明：
- `dataset_name`: 数据集名称（如 vbench_1.0_mini），用于指定对应的处理模块
- `--input/-i`: kmeans压缩后的metadata路径
- `--output/-o`: 基于压缩的metadata文件夹生成的压缩后的数据集内容路径

#### 要求：
- 需要在 `<dataset_name>` 目录下存在 `processor.py` 文件，该文件需实现 `process_compressed_metadata(input_dir, output_dir)` 函数

---

### 完整工作流示例（以 vbench_1.0_mini 为例）：

```bash
# 步骤1: 将评估结果转换为 metadata
python eval_results_to_metadata.py vbench_1.0_mini --input ./raw_eval_results --output ./vbench_metadata

# 步骤2: 使用 K-Means 压缩 metadata
python select_metadata_by_kmeans.py --input ./vbench_metadata --work-dir ./compressed_output --compression-ratio 0.1

# 步骤3: 将压缩后的 metadata 转换为最终数据集
python compressed_metadata_to_mini_datasets.py vbench_1.0_mini --input ./compressed_output/vbench_metadata_compressed_0.10/representative --output ./final_mini_dataset
```

## 压缩原理

### 1. K-Means 聚类
- 将数据点根据特征相似度聚类成指定数量的簇
- 每个簇代表一个数据特征组
- 簇中心是该组数据的特征平均值

### 2. 代表性样本抽取
- 首先从每个簇中选择距离中心最近的数据点（保证代表性）
- 剩余样本根据簇大小按比例随机分配
- 确保保留数据的整体分布特征

### 3. 最优簇数计算
- 默认使用 `n_clusters = min(sqrt(n_samples), n_samples)`
- 同时考虑唯一数据组合数，避免无效聚类
- 可选自动优化模式，根据平均分数相似度寻找最佳簇数

## 使用方法

### 准备数据

确保元数据目录包含以下内容（以 `multi_data_sample` 为例）：

```
multi_data_sample/
├── info.json
├── random_metadata0.csv
├── random_metadata1.csv
└── random_metadata2.csv
```

#### `info.json` 格式：

```json
[
    {
        "name": "random_metadata0",
        "count": 160,
        "avg_scores": [0.05, 0.44, 0.35],
        "difficulty_map": {
            "level0": 0,
            "level1": 1,
            "level2": 2
        },
        "n_cluster": 5  // 可选，指定簇数
    }
]
```

#### CSV 格式：

```csv
id,score0,score1,score2,difficulty
eyoqdm,0.13,0.65,0.37,level0
glzgurmuplzu,0.0,0.45,0.51,level0
...
```

### 运行脚本

```bash
python select_metadata_by_kmeans.py --input ./multi_data_sample --work-dir ./output --compression-ratio 0.1
```

## 输出目录结构

运行后会在工作目录下生成两个子目录：

```
output/
├── multi_data_sample_compressed_0.10/
│   ├── clustering_visualizations/
│   │   ├── random_metadata0_clustering_visualization.png
│   │   ├── random_metadata1_clustering_visualization.png
│   │   └── random_metadata2_clustering_visualization.png
│   ├── representative/
│   │   ├── random_metadata0.csv
│   │   ├── random_metadata0_ids.json
│   │   ├── random_metadata1.csv
│   │   ├── random_metadata1_ids.json
│   │   ├── random_metadata2.csv
│   │   ├── random_metadata2_ids.json
│   │   └── info.json
│   └── random/
│       ├── random_metadata0.csv
│       ├── random_metadata0_ids.json
│       ├── random_metadata1.csv
│       ├── random_metadata1_ids.json
│       ├── random_metadata2.csv
│       ├── random_metadata2_ids.json
│       └── info.json
└── multi_data_sample_figures_0.10/
    ├── random_metadata0_means_comparison.png
    ├── random_metadata1_means_comparison.png
    ├── random_metadata2_means_comparison.png
    └── comparison_summary.json
```

## 呈现效果含义

### 1. 聚类可视化 (`clustering_visualization.png`)

包含三个子图：

- **PCA 散点图**：将高维数据降维到2D展示，不同颜色代表不同簇，红色X是簇中心
  - 作用：直观展示聚类效果和数据分布
  - 评价：簇间分离度好，簇内聚集度高为最佳

- **特征箱线图**：展示前4个特征在各簇中的分布
  - 作用：分析不同簇的特征差异
  - 评价：各簇在特征分布上有明显区别说明聚类有效

- **雷达图**：展示各簇中心的标准化特征值
  - 作用：对比不同簇的特征构成
  - 评价：各簇形状差异大说明聚类有意义

### 2. 均值对比图 (`means_comparison.png`)

展示三个指标：
- **Full Dataset**：原始完整数据集的特征均值
- **K-means Representative**：代表性样本的特征均值
- **Random**：随机样本的特征均值

**含义**：
- 柱子高度越接近，说明样本保留原始数据特征越好
- 通常代表性样本会比随机样本更接近完整数据
- 可以直观比较两种抽样方法的优劣

### 3. 比较摘要 (`comparison_summary.json`)

包含详细的比较数据：
```json
[
    {
        "dataset_name": "random_metadata0",
        "sizes": {
            "full": 160,
            "representative": 16,
            "random": 16
        },
        "means": {...},
        "correlations": {
            "representative": {"full": 0.85, "sample": 0.82},
            "random": {"full": 0.65, "sample": 0.68}
        }
    }
]
```

**相关性系数含义**：
- 值接近1表示保留原始数据的相关性结构好
- 通常代表性样本的相关性保留优于随机样本

## 参数说明

| 参数 | 简称 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--input` | `-i` | 是 | - | 包含 info.json 和 CSV 的元数据目录 |
| `--work-dir` | `-w` | 是 | - | 保存所有输出的工作目录 |
| `--compression-ratio` | `-r` | 否 | 0.1 | 目标压缩比 (0-1)，如 0.1 表示保留 10% 数据 |
| `--auto-optimize` | `-a` | 否 | False | 启用自动寻找最优簇数（基于平均分数相似度） |
| `--random-state` | `-s` | 否 | 42 | 随机种子，保证结果可复现 |
| `--no-visualize` | `-n` | 否 | False | 禁用聚类可视化 |

## 示例使用场景

### 场景1：基础使用（10%压缩）
```bash
python select_metadata_by_kmeans.py --input ./multi_data_sample --work-dir ./output
```

### 场景2：较高压缩率（20%）
```bash
python select_metadata_by_kmeans.py --input ./multi_data_sample --work-dir ./output --compression-ratio 0.2
```

### 场景3：自动优化簇数
```bash
python select_metadata_by_kmeans.py --input ./multi_data_sample --work-dir ./output --auto-optimize
```

### 场景4：禁用可视化（加快处理速度）
```bash
python select_metadata_by_kmeans.py --input ./multi_data_sample --work-dir ./output --no-visualize
```

## 性能优化建议

1. **大数据集**：考虑禁用可视化 (`--no-visualize`)
2. **自动优化**：对大数据集会增加计算时间，但能找到更好的簇数
3. **压缩率选择**：
   - 0.05-0.1：适合快速验证
   - 0.1-0.2：平衡速度和质量
   - 0.2-0.3：高质量子集

## 常见问题

**Q: 为什么需要同时生成随机样本？**

A: 作为对照组，验证 K-Means 代表性样本的优越性，确保压缩方法的有效性。

**Q: 如何判断压缩质量？**

A: 主要看均值对比图和相关性系数。代表性样本越接近完整数据，说明压缩质量越好。

**Q: 压缩率设置多少合适？**

A: 根据数据集大小和需求调整。一般 5%-20% 都能获得较好效果。数据集越大，可以用更低的压缩率。
