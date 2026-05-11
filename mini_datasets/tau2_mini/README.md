# tau2_mini

## 简介

tau2_mini 是基于 TAU2 评估结果进行采样的小规模数据集，使用 K-Means 聚类算法从原始评估结果中选择具有代表性的子集。

## 使用方法

### 第一步：将评估结果转换为 metadata

```bash
cd d:\for_developing\syh_datasets\datasets\mini_datasets
python eval_results_to_metadata.py tau2_mini -i <评估结果目录> -o <输出metadata目录>
```

例如：
```bash
python eval_results_to_metadata.py tau2_mini -i D:\BRIDGE\TAU2_ORG_EVAL_RESULTS\GLM-5-ENABLED -o d:\for_developing\syh_datasets\datasets\mini_datasets\tau2_mini\tau2_metadata_output
```

### 第二步：使用 K-Means 压缩 metadata

```bash
python select_metadata_by_kmeans.py --input <metadata目录> --work-dir <输出目录> --compression-ratio 0.1
```

例如：
```bash
python select_metadata_by_kmeans.py --input d:\for_developing\syh_datasets\datasets\mini_datasets\tau2_mini\tau2_metadata_output --work-dir d:\for_developing\syh_datasets\datasets\mini_datasets\tau2_mini\compressed_output --compression-ratio 0.1
```

### 第三步：将压缩后的 metadata 转换为最终数据集

```bash
python compressed_metadata_to_mini_datasets.py tau2_mini --input <压缩后的metadata目录> --output <最终输出目录>
```

例如：
```bash
python compressed_metadata_to_mini_datasets.py tau2_mini --input d:\for_developing\syh_datasets\datasets\mini_datasets\tau2_mini\compressed_output\tau2_metadata_output_compressed_0.1 --output d:\for_developing\syh_datasets\datasets\mini_datasets\tau2_mini\final_output
```

## 输入数据格式

评估结果目录应包含多个 JSON 文件，每个文件对应一个子集，文件名格式为：`{模型名称}_{子集名称}_trajectories.json`

例如：
- `GLM-5-Enabled_airline_trajectories.json`
- `GLM-5-Enabled_retail_trajectories.json`
- `GLM-5-Enabled_telecom_trajectories.json`

每个 JSON 文件的格式如下：
```json
{
  "timestamp": "2026-02-24T10:30:49.625131",
  "simulations": [
    {
      "id": "a505d6c3-f7c7-4207-a449-16e70bea175f",
      "task_id": "46",
      "reward_info": {
        "reward": 1
      }
    },
    ...
  ]
}
```

## 输出格式

### metadata 目录结构

```
metadata_output/
├── info.json
├── airline_metadata.csv
├── retail_metadata.csv
└── telecom_metadata.csv
```

### info.json 格式

```json
[
  {
    "name": "airline_metadata",
    "count": 100,
    "avg_scores": [0.65],
    "difficulty_map": {
      "level0": 0
    }
  },
  ...
]
```

### CSV 文件格式

CSV 文件的特征列使用模型名称命名（连字符 `-` 会被替换为下划线 `_`）：

```csv
id,GLM_5_Enabled,difficulty
46,0.75,level0
2,0.5,level0
```
