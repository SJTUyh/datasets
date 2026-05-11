# datasets
这个仓库用于承载特殊处理的测评数据集。

## mini_datasets
### 简介
[K-Means聚类算法采样的 数据集子集](./mini_datasets/README.md) - 使用 K-Means 聚类算法从原始数据集中生成具有代表性的子集，并提供详细的比较分析和可视化效果。其中包含三个主要脚本：
- `eval_results_to_metadata.py`：将原始评估结果转换为标准的 metadata 格式
- `select_metadata_by_kmeans.py`：使用 K-Means 聚类算法从 metadata 中生成具有代表性的子集
- `compressed_metadata_to_mini_datasets.py`：将压缩后的 metadata 转换为最终的数据集内容

### 支持数据集
|数据集|简介|
| ---- | ---- |
|[VBench-1.0-mini](./mini_datasets/vbench_1.0_mini/)|基于VBench 1.0 采样1/10的子集|
|[TAU2-mini](./mini_datasets/tau2_mini/)|基于TAU2 采样1/10的子集|
