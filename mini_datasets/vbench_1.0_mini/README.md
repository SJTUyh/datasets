# VBench-1.0-mini
## 简介
VBench-1.0-mini 是基于[VBench-1.0的数据集](https://github.com/Vchitect/VBench/tree/master/prompts/prompts_per_dimension)进行约1/10规模的采样得到的一个小规模数据集，它在测试得分上与原始数据集大致相同。
## 数据集获取方式
[🔗VBench-1.0-mini 数据集](https://modelers.cn/datasets/AISBench/VBench-1.0-mini)

## 复现数据提取过程
先安装kmeans采样脚本依赖：
```bash
pip3 install -r ../requirements.txt
```
执行采样过程：
```bash
# 步骤1: 使用 K-Means 压缩 metadata，自动为每个子集取最优簇
python ../select_metadata_by_kmeans.py --input ./vbench_metadata --work-dir ./compressed_output --compression-ratio 0.1 -a

# 步骤2: 将压缩后的 metadata 转换为最终数据集
python ../compressed_metadata_to_mini_datasets.py vbench_1.0_mini --input ./compressed_output/vbench_metadata_compressed_0.10 --output ./final_mini_dataset
```

采样效果图结构如下：
```bash
compressed_output/
├── vbench_metadata_compressed_0.10
│   ├── clustering_visualizations # 每个子集的kmeans聚类效果可视化图
│   ├── random
│   └── representative
└── vbench_metadata_figures_0.10 # 采样得分效果图
    ├── comparison_summary.json
    ├── metadata_appearance_style_means_comparison.png
    ├── metadata_color_means_comparison.png
    ├── metadata_human_action_means_comparison.png
    ├── metadata_multiple_objects_means_comparison.png
    ├── metadata_object_class_means_comparison.png
    ├── metadata_overall_consistency_means_comparison.png
    ├── metadata_scene_means_comparison.png
    ├── metadata_spatial_relationship_means_comparison.png
    ├── metadata_subject_consistency_means_comparison.png
    ├── metadata_temporal_flickering_means_comparison.png
    └── metadata_temporal_style_means_comparison.png
```

最终生成的采样数据集如下：
```bash
final_mini_dataset/
├── prompts
│   ├── kmeans # 基于 kmeans 1/10 采样的提示词，对应魔乐社区prompts_per_dimension_kmeans/
│   │   ├── appearance_style.txt
│   │   ├── color.txt
│   │   ├── human_action.txt
│   │   ├── multiple_objects.txt
│   │   ├── object_class.txt
│   │   ├── overall_consistency.txt
│   │   ├── scene.txt
│   │   ├── spatial_relationship.txt
│   │   ├── subject_consistency.txt
│   │   ├── temporal_flickering.txt
│   │   └── temporal_style.txt
│   └── random # 随机1/10 采样的提示词
│       ├── appearance_style.txt
│       ├── color.txt
│       ├── human_action.txt
│       ├── multiple_objects.txt
│       ├── object_class.txt
│       ├── overall_consistency.txt
│       ├── scene.txt
│       ├── spatial_relationship.txt
│       ├── subject_consistency.txt
│       ├── temporal_flickering.txt
│       └── temporal_style.txt
├── VBench_kmeans_info.json
└── VBench_random_info.json

```
