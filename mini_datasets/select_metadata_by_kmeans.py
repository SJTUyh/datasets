from pathlib import Path
import json
import argparse
import pandas as pd
import numpy as np
import warnings
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.utils import resample
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA


def truncate_label(name: str, max_length: int = None) -> str:
    if max_length is None or len(name) <= max_length:
        return name
    keep = max(1, (max_length - 3) // 2)
    return name[:keep] + "..." + name[-keep:]


def prepare_data(data: pd.DataFrame, difficulty_map: dict = None) -> pd.DataFrame:
    """
    Prepare data by mapping difficulty and creating numeric version.

    Parameters:
    - data: Raw DataFrame with original columns
    - difficulty_map: Custom mapping from difficulty strings to numeric values

    Returns:
    - Processed numeric DataFrame
    """
    if difficulty_map is None:
        difficulty_map = {
            'level0': 0,
            'level1': 1,
            'level2': 2
        }
    data = data.copy()
    data["difficulty"] = data["difficulty"].map(difficulty_map)

    # Create numeric version for clustering - drop id column
    data_numeric = data.drop(columns=["id"])
    data_numeric = data_numeric.fillna(0)

    return data_numeric


def compute_kmeans(data: pd.DataFrame, n_clusters: int, random_state: int = 42) -> tuple:
    """
    Compute k-means clustering on the given data.

    Parameters:
    - data: DataFrame containing the data to cluster
    - n_clusters: Number of clusters to form

    Returns:
    - Cluster labels and centers
    """
    kmeans = KMeans(n_clusters=n_clusters, random_state=random_state)
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', message='Number of distinct clusters.*found smaller than n_clusters.*')
        kmeans.fit(data)
    return kmeans.labels_, kmeans.cluster_centers_


def visualize_clustering(data: pd.DataFrame, labels: np.ndarray, centers: np.ndarray,
                        save_path: Path, dataset_name: str,
                        max_name_length: int = None,
                        max_elements_per_chart: int = 24) -> None:
    """
    Visualize clustering results using multiple complementary methods.

    Parameters:
    - data: Original numeric DataFrame
    - labels: Cluster labels for each data point
    - centers: Cluster centers
    - save_path: Directory to save figures
    - dataset_name: Name of the dataset for figure naming
    - max_name_length: Max length of feature names in charts (None = no truncation)
    - max_elements_per_chart: Max number of elements per chart (default 24)
    """
    save_path.mkdir(exist_ok=True, parents=True)

    # Standardize data for PCA
    scaler = StandardScaler()
    data_scaled = scaler.fit_transform(data)

    # 1. PCA 2D visualization
    fig = plt.figure(figsize=(18, 12))
    gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.25)

    # Plot 1: PCA scatter plot
    ax1 = fig.add_subplot(gs[0, 0])
    pca = PCA(n_components=2, random_state=42)
    data_pca = pca.fit_transform(data_scaled)
    centers_pca = pca.transform(scaler.transform(centers))

    scatter = ax1.scatter(data_pca[:, 0], data_pca[:, 1], c=labels, cmap='viridis',
                         alpha=0.6, s=50, edgecolors='k', linewidths=0.5)
    ax1.scatter(centers_pca[:, 0], centers_pca[:, 1], c='red', marker='X', s=200,
               linewidths=2, label='Centroids')
    ax1.set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]:.2%} variance)')
    ax1.set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]:.2%} variance)')
    ax1.set_title('PCA Visualization of Clusters', fontweight='bold')
    ax1.legend()
    plt.colorbar(scatter, ax=ax1, label='Cluster')
    ax1.grid(True, alpha=0.3)

    # Plot 2: Box plots of features by cluster
    ax2 = fig.add_subplot(gs[0, 1])
    data_with_labels = data.copy()
    data_with_labels['Cluster'] = labels

    feature_names = data.columns.tolist()
    n_features = len(feature_names)
    n_clusters = len(np.unique(labels))

    # Plot box plots for first few features (or all if small)
    max_features = min(4, n_features)
    box_width = 0.8 / max_features

    for feat_idx in range(max_features):
        feat_name = feature_names[feat_idx]
        box_data = []
        for cluster in range(n_clusters):
            cluster_data = data_with_labels[data_with_labels['Cluster'] == cluster][feat_name]
            box_data.append(cluster_data.values)

        positions = np.arange(n_clusters) + feat_idx * box_width - (max_features - 1) * box_width / 2
        bp = ax2.boxplot(box_data, positions=positions, widths=box_width * 0.8,
                        patch_artist=True, labels=[f'C{i}' for i in range(n_clusters)])

        # Color each feature differently
        for patch in bp['boxes']:
            patch.set_alpha(0.7)

    ax2.set_xticks(np.arange(n_clusters))
    ax2.set_xticklabels([f'Cluster {i}' for i in range(n_clusters)])
    ax2.set_ylabel('Feature Value')
    ax2.set_title(f'Feature Distributions by Cluster (Top {max_features})', fontweight='bold')
    ax2.legend([plt.Rectangle((0, 0), 1, 1, fc=f'C{i}') for i in range(max_features)],
              feature_names[:max_features], loc='upper right')
    ax2.grid(True, alpha=0.3, axis='y')

    display_feature_names = [truncate_label(fn, max_name_length) for fn in feature_names]

    # Plot 3: Radar chart of cluster centers (handle splitting if too many features)
    centers_scaled = scaler.transform(centers)

    radar_chunks = []
    for start in range(0, n_features, max_elements_per_chart):
        end = min(start + max_elements_per_chart, n_features)
        radar_chunks.append((start, end))

    for chunk_idx, (chunk_start, chunk_end) in enumerate(radar_chunks):
        chunk_n = chunk_end - chunk_start
        chunk_angles = np.linspace(0, 2 * np.pi, chunk_n, endpoint=False).tolist()
        chunk_angles += chunk_angles[:1]

        if chunk_idx == 0:
            ax3 = fig.add_subplot(gs[1, :], projection='polar')
        else:
            radar_fig = plt.figure(figsize=(10, 8))
            ax3 = radar_fig.add_subplot(111, projection='polar')

        for i in range(n_clusters):
            values = centers_scaled[i][chunk_start:chunk_end].tolist()
            values += values[:1]
            ax3.plot(chunk_angles, values, 'o-', linewidth=2, label=f'Cluster {i}')
            ax3.fill(chunk_angles, values, alpha=0.25)

        ax3.set_xticks(chunk_angles[:-1])
        ax3.set_xticklabels(display_feature_names[chunk_start:chunk_end], fontsize=8)
        title_suffix = f' (Part {chunk_idx + 1}/{len(radar_chunks)})' if len(radar_chunks) > 1 else ''
        ax3.set_title(f'Cluster Centers (Scaled){title_suffix}', fontweight='bold', y=1.1)
        ax3.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
        ax3.grid(True)

        if chunk_idx > 0:
            radar_fig.savefig(
                save_path / f'{dataset_name}_clustering_radar_part{chunk_idx + 1}.png',
                dpi=300, bbox_inches='tight')
            plt.close(radar_fig)

    plt.savefig(save_path / f'{dataset_name}_clustering_visualization.png',
               dpi=300, bbox_inches='tight')
    plt.close()


def draw_representative_sample(data: pd.DataFrame, labels: np.ndarray, n: int, random_state: int = 1, difficulty_map: dict = None) -> pd.DataFrame:
    """
    Draw N representative datapoints based on k-means clustering labels.
    First selects the point closest to each cluster centroid,
    then distributes remaining samples proportionally.

    Parameters:
    - data: DataFrame containing the data to sample from
    - labels: Cluster labels for each data point
    - n: Number of representative datapoints to draw
    - random_state: Random seed for reproducibility
    - difficulty_map: Custom mapping from difficulty strings to numeric values

    Returns:
    - DataFrame containing the representative sample
    """
    unique_labels = np.unique(labels)
    n_clusters = len(unique_labels)

    # Ensure n is not larger than data size
    n = min(n, len(data))

    # If n is less than number of clusters, adjust n_clusters
    if n < n_clusters:
        n_clusters = n

    # First, get the point closest to centroid for each cluster
    data_numeric = prepare_data(data, difficulty_map)
    # Create a copy of data with difficulty converted to numeric
    data_with_numeric_difficulty = data.copy()
    if difficulty_map is not None and 'difficulty' in data.columns:
        data_with_numeric_difficulty['difficulty'] = data_with_numeric_difficulty['difficulty'].map(difficulty_map)
    centroid_samples = pd.DataFrame()
    remaining_data = data_with_numeric_difficulty.copy()
    remaining_indices = np.ones(len(data), dtype=bool)

    # Use existing labels to calculate centroids instead of re-running K-means
    centroids = []
    for label in unique_labels[:n_clusters]:
        cluster_data = data_numeric[labels == label]
        if len(cluster_data) > 0:
            centroid = cluster_data.mean().values
            centroids.append(centroid)
        else:
            # If cluster is empty, use a random point
            random_idx = np.random.choice(len(data_numeric))
            centroids.append(data_numeric.iloc[random_idx].values)
    centroids = np.array(centroids)

    # Select points closest to centroids
    for label, centroid in zip(unique_labels[:n_clusters], centroids):
        cluster_mask = labels == label
        cluster_data_numeric = data_numeric[cluster_mask]

        # Calculate distances to centroid
        distances = np.linalg.norm(cluster_data_numeric - centroid, axis=1)
        closest_idx = np.argmin(distances)

        # Get the original index in the full dataset
        original_idx = np.where(cluster_mask)[0][closest_idx]

        # Add to centroid samples and mark for removal from remaining data
        centroid_samples = pd.concat([centroid_samples, data_with_numeric_difficulty.iloc[[original_idx]]])
        remaining_indices[original_idx] = False

    # Update remaining data
    remaining_data = data_with_numeric_difficulty[remaining_indices]
    remaining_labels = labels[remaining_indices]

    # Calculate proportional distribution for remaining samples
    remaining_n = n - n_clusters
    if remaining_n > 0 and len(remaining_data) > 0:
        # Count remaining points per cluster
        unique_remaining_labels, counts = np.unique(remaining_labels, return_counts=True)
        proportions = counts / counts.sum()

        # Calculate samples per cluster
        exact_samples = proportions * remaining_n
        sample_counts = exact_samples.astype(int)
        fractions = exact_samples - sample_counts

        # Distribute remaining samples based on largest fractional parts
        remaining = remaining_n - sample_counts.sum()
        if remaining > 0:
            fraction_indices = np.argsort(fractions)[-remaining:]
            for idx in fraction_indices:
                sample_counts[idx] += 1

        # Sample from remaining points
        additional_samples = pd.DataFrame()
        for label, count in zip(unique_remaining_labels, sample_counts):
            if count > 0:
                cluster_data = remaining_data[remaining_labels == label]
                count = min(count, len(cluster_data))
                if count > 0:
                    cluster_sample = resample(cluster_data,
                                           n_samples=count,
                                           random_state=random_state,
                                           replace=False)
                    additional_samples = pd.concat([additional_samples, cluster_sample])

        # Combine centroid samples with additional samples
        representative_sample = pd.concat([centroid_samples, additional_samples])
    else:
        representative_sample = centroid_samples

    return representative_sample


def get_random_sample(data: pd.DataFrame, sample_size: int, random_state: int = 1, difficulty_map: dict = None) -> pd.DataFrame:
    """
    Get a random sample from the dataset.

    Parameters:
    - data: DataFrame to sample from
    - sample_size: Number of samples to draw
    - random_state: Random seed for reproducibility
    - difficulty_map: Custom mapping from difficulty strings to numeric values

    Returns:
    - Random sample DataFrame
    """
    sample_size = min(sample_size, len(data))
    sample = data.sample(n=sample_size, random_state=random_state)
    # Convert difficulty to numeric if needed
    if difficulty_map is not None and 'difficulty' in sample.columns:
        sample['difficulty'] = sample['difficulty'].map(difficulty_map)
    return sample


def save_sample_and_ids(sample: pd.DataFrame, name: str, data_dir: Path) -> None:
    """
    Save a sample DataFrame and its IDs to files.

    Parameters:
    - sample: DataFrame to save
    - name: Name prefix for the files
    - data_dir: Directory to save the files
    """
    # Save full sample
    sample.to_csv(data_dir / f"{name}.csv", index=False)

    # Save IDs
    with open(data_dir / f"{name}_ids.json", 'w') as f:
        json.dump(sample["id"].tolist(), f)


def evaluate_n_cluster(data: pd.DataFrame, n_clusters: int, n_samples: int,
                      original_avg_scores: np.ndarray, score_cols: list,
                      difficulty_map: dict, random_state: int) -> float:
    """
    Evaluate a specific n_clusters value by generating a sample and calculating score deviation.

    Parameters:
    - data: Full dataset
    - n_clusters: Number of clusters to use
    - n_samples: Target number of samples
    - original_avg_scores: Original average scores
    - score_cols: List of score column names
    - difficulty_map: Difficulty mapping
    - random_state: Random seed

    Returns:
    - Sum of absolute differences between sample scores and original scores
    """
    if not score_cols:
        # No score columns, return infinite deviation to avoid optimization
        return float('inf')

    data_numeric = prepare_data(data, difficulty_map)
    labels, _ = compute_kmeans(data_numeric, n_clusters, random_state)
    sample = draw_representative_sample(data, labels, n_samples, random_state, difficulty_map)
    if len(sample) == 0:
        return float('inf')
    sample_avg_scores = sample[score_cols].mean().tolist()
    deviation = np.sum(np.abs(np.array(sample_avg_scores) - original_avg_scores))
    return deviation


def find_optimal_n_cluster(data: pd.DataFrame, n_samples: int,
                          original_avg_scores: np.ndarray, score_cols: list,
                          difficulty_map: dict, random_state: int,
                          n_unique: int) -> int:
    """
    Find optimal n_cluster by evaluating multiple values and choosing the one with closest average scores.

    Parameters:
    - data: Full dataset
    - n_samples: Target number of samples
    - original_avg_scores: Original average scores
    - score_cols: List of score column names
    - difficulty_map: Difficulty mapping
    - random_state: Random seed
    - n_unique: Number of unique data combinations

    Returns:
    - Optimal n_clusters
    """
    # Define search space for n_clusters
    min_clusters = max(2, min(2, n_samples))  # 从2开始寻找最优簇数
    max_clusters = min(min(100, n_unique), n_samples)

    # Generate candidate values
    if max_clusters - min_clusters <= 10:
        candidates = list(range(min_clusters, max_clusters + 1))
    else:
        # Use linear steps to cover the range
        step = max(1, (max_clusters - min_clusters) // 10)
        candidates = list(range(min_clusters, max_clusters + 1, step))
        # Ensure unique and sorted
        candidates = sorted(list(set(candidates)))

    # Evaluate all candidates
    best_score = float('inf')
    best_n_clusters = min_clusters

    print(f"  Searching optimal n_cluster in range [{min_clusters}, {max_clusters}] (candidates: {candidates})")

    for n_clusters in candidates:
        deviation = evaluate_n_cluster(data, n_clusters, n_samples, original_avg_scores,
                                     score_cols, difficulty_map, random_state)
        print(f"    n_cluster={n_clusters}, deviation={deviation:.6f}")

        if deviation < best_score:
            best_score = deviation
            best_n_clusters = n_clusters

    print(f"  Best n_cluster={best_n_clusters} with deviation={best_score:.6f}")
    return best_n_clusters


def calculate_optimal_parameters(data: pd.DataFrame, data_size: int, compression_ratio: float = 0.1,
                                 n_cluster: int = None, auto_optimize: bool = False,
                                 original_avg_scores: np.ndarray = None, score_cols: list = None,
                                 difficulty_map: dict = None, random_state: int = 42) -> tuple:
    """
    Calculate optimal n_clusters and n_samples based on data size and compression ratio.
    Also ensures n_clusters doesn't exceed the number of unique data combinations.
    If n_cluster is provided, use that value (with validation).
    If auto_optimize is True, search for optimal n_cluster by evaluating average score similarity.

    Parameters:
    - data: DataFrame to check for unique data combinations
    - data_size: Total number of samples in dataset
    - compression_ratio: Target compression ratio (0-1)
    - n_cluster: Optional predefined number of clusters
    - auto_optimize: Whether to automatically find optimal n_cluster
    - original_avg_scores: Original average scores (for auto-optimization)
    - score_cols: List of score column names (for auto-optimization)
    - difficulty_map: Difficulty mapping (for auto-optimization)
    - random_state: Random seed (for auto-optimization)

    Returns:
    - Tuple of (n_clusters, n_samples)
    """
    # 计算压缩后的样本数，不设置最小限制，让压缩率能够正确反映
    n_samples = max(int(data_size * compression_ratio), 1)
    n_samples = min(n_samples, data_size)

    # Calculate number of unique data combinations (excluding id column)
    if 'id' in data.columns:
        unique_data = data.drop(columns=['id']).drop_duplicates()
    else:
        unique_data = data.drop_duplicates()
    n_unique = len(unique_data)

    # Handle n_cluster if provided
    if n_cluster is not None:
        n_clusters = n_cluster
        print(f"  Using n_cluster={n_clusters} from info.json")
    elif auto_optimize and original_avg_scores is not None and score_cols is not None and len(score_cols) > 0 and difficulty_map is not None:
        n_clusters = find_optimal_n_cluster(data, n_samples, original_avg_scores, score_cols,
                                          difficulty_map, random_state, n_unique)
    else:
        # Calculate initial n_clusters
        initial_n_clusters = min(int(np.sqrt(n_samples)), n_samples)
        # Ensure n_clusters doesn't exceed the number of unique data combinations
        n_clusters = min(initial_n_clusters, n_unique)
        n_clusters = max(n_clusters, 2)

        # Print warning if clusters were adjusted
        if initial_n_clusters > n_unique:
            print(f"  Warning: Only {n_unique} unique data combinations found, adjusted n_clusters from {initial_n_clusters} to {n_clusters}")
        if auto_optimize and (score_cols is None or len(score_cols) == 0):
            print(f"  Warning: No score columns found, auto-optimization disabled")

    # Validate n_clusters
    original_n_clusters = n_clusters
    # 确保簇数不超过压缩后的样本数，同时不超过唯一数据组合数
    n_clusters = min(n_clusters, n_unique, n_samples)
    # 确保至少有2个簇以保证聚类有意义
    n_clusters = max(n_clusters, 2)
    if original_n_clusters != n_clusters:
        print(f"  Warning: Adjusted n_clusters from {original_n_clusters} to {n_clusters} to ensure validity")

    return n_clusters, n_samples


def process_single_dataset_for_generation(info_item: dict, input_dir: Path, repr_dir: Path, random_dir: Path, compression_ratio: float, auto_optimize: bool = False, random_state: int = 42, visualize: bool = True, max_name_length: int = None, max_elements_per_chart: int = 24) -> tuple:
    """
    Process a single dataset from the info.json for generation.

    Parameters:
    - info_item: Dictionary with dataset information from info.json
    - input_dir: Directory containing input metadata files
    - repr_dir: Directory to save representative samples
    - random_dir: Directory to save random samples
    - compression_ratio: Target compression ratio (default, used if not specified in info_item)
    - auto_optimize: Whether to automatically find optimal n_cluster
    - random_state: Random seed

    Returns:
    - Tuple of (repr_info, rand_info)
    """
    dataset_name = info_item["name"]
    difficulty_map = info_item["difficulty_map"]
    # Get n_cluster from info_item if present
    n_cluster = info_item.get("n_cluster")
    # Get compression_ratio from info_item if present, use default otherwise
    dataset_compression_ratio = info_item.get("compression_ratio", compression_ratio)
    if dataset_compression_ratio != compression_ratio:
        print(f"  Using compression_ratio={dataset_compression_ratio} from info.json (overrides default {compression_ratio})")

    # Load data
    csv_path = input_dir / f"{dataset_name}.csv"
    data = pd.read_csv(csv_path)
    data_size = len(data)
    print(f"  Loaded {dataset_name} with {data_size} samples")

    # Calculate original average scores
    score_cols = [col for col in data.columns if col != "id"]
    # Create a copy of data with difficulty converted to numeric for calculating original average scores
    data_with_numeric_difficulty = data.copy()
    if difficulty_map is not None and 'difficulty' in data.columns:
        data_with_numeric_difficulty['difficulty'] = data_with_numeric_difficulty['difficulty'].map(difficulty_map)
    original_avg_scores = np.array(data_with_numeric_difficulty[score_cols].mean().tolist())
    print(f"  Original average scores: {original_avg_scores}")

    # Calculate optimal parameters
    n_clusters, n_samples = calculate_optimal_parameters(
        data, data_size, dataset_compression_ratio, n_cluster,
        auto_optimize=auto_optimize, original_avg_scores=original_avg_scores,
        score_cols=score_cols, difficulty_map=difficulty_map, random_state=random_state
    )
    print(f"  Optimal parameters: n_clusters={n_clusters}, n_samples={n_samples}")

    # Prepare data
    data_numeric = prepare_data(data, difficulty_map)

    # Generate clusters
    labels, centers = compute_kmeans(data_numeric, n_clusters, random_state)

    # Visualize clustering
    if visualize:
        visualize_dir = repr_dir.parent / "clustering_visualizations"
        visualize_clustering(data_numeric, labels, centers, visualize_dir, dataset_name, max_name_length, max_elements_per_chart)
        print(f"  Clustering visualization saved to: {visualize_dir}")

    # Generate samples
    representative_sample = draw_representative_sample(data, labels, n_samples, random_state, difficulty_map)
    random_sample = get_random_sample(data, n_samples, random_state, difficulty_map)

    # Create directories
    repr_dir.mkdir(exist_ok=True, parents=True)
    random_dir.mkdir(exist_ok=True, parents=True)

    # Save representative sample
    save_sample_and_ids(representative_sample, dataset_name, repr_dir)

    # Save random sample
    save_sample_and_ids(random_sample, dataset_name, random_dir)

    # Create updated info items
    repr_info = {
        "name": dataset_name,
        "count": len(representative_sample),
        "avg_scores": representative_sample[score_cols].mean().tolist(),
        "difficulty_map": difficulty_map,
        "n_cluster": n_clusters
    }

    rand_info = {
        "name": dataset_name,
        "count": len(random_sample),
        "avg_scores": random_sample[score_cols].mean().tolist(),
        "difficulty_map": difficulty_map
    }

    return repr_info, rand_info


def prepare_numeric_data(data: pd.DataFrame, replace_difficulty_with_number: bool = False,
                        difficulty_map: dict = None) -> pd.DataFrame:
    """Prepare numeric data for analysis by removing non-numeric columns and filling NaNs."""
    data = data.copy()
    if replace_difficulty_with_number:
        if 'difficulty' in data.columns:
            if difficulty_map is None:
                difficulty_map = {
                    'level0': 0,
                    'level1': 1,
                    'level2': 2
                }
            # 确保difficulty值是字符串类型
            data["difficulty"] = data["difficulty"].astype(str)
            # 打印转换前的困难度值
            print(f"Difficulty values before mapping: {data['difficulty'].unique()}")
            # 映射困难度值
            data["difficulty"] = data["difficulty"].map(difficulty_map)
            # 打印转换后的困难度值
            print(f"Difficulty values after mapping: {data['difficulty'].unique()}")
        else:
            print("Warning: No difficulty column found for mapping")

    # Drop id column if exists, keep others
    drop_cols = []
    if 'id' in data.columns:
        drop_cols.append('id')
    if 'environment' in data.columns:
        drop_cols.append('environment')
    if 'size_in_gb' in data.columns:
        drop_cols.append('size_in_gb')

    return data.drop(columns=drop_cols, errors='ignore').fillna(0)


def compare_means_single(dataset_name: str, full_data: pd.DataFrame, representative: pd.DataFrame,
                         random: pd.DataFrame, figures_path: Path,
                         max_name_length: int = None,
                         max_elements_per_chart: int = 24) -> pd.DataFrame:
    """
    Compare means of different samples against full dataset for a single dataset.
    """
    full_cols = full_data.columns.tolist()
    id_idx = full_cols.index('id')
    difficulty_idx = full_cols.index('difficulty')
    score_cols = full_cols[id_idx + 1:difficulty_idx]

    display_score_cols = [truncate_label(c, max_name_length) for c in score_cols]

    means_df = pd.DataFrame({
        "Full Dataset": full_data.mean(numeric_only=True),
        "K-means Representative": representative.mean(numeric_only=True),
        "Random": random.mean(numeric_only=True)
    })

    n_elements = len(score_cols)
    n_charts = (n_elements + max_elements_per_chart - 1) // max_elements_per_chart
    markers = ['o', 's', '^']
    line_styles = ['-', '--', ':']

    for chart_idx in range(n_charts):
        start = chart_idx * max_elements_per_chart
        end = min(start + max_elements_per_chart, n_elements)
        chunk_cols = score_cols[start:end]
        chunk_display = display_score_cols[start:end]

        fig, ax = plt.subplots(figsize=(12, 6))
        ax.grid(True, axis='y', linestyle='--', alpha=0.7, zorder=0)

        for idx, (sample_name, means) in enumerate(means_df.items()):
            ax.plot(chunk_display, means[chunk_cols], marker=markers[idx], linestyle=line_styles[idx],
                    linewidth=2, markersize=8, label=sample_name, zorder=3)

            for i, val in enumerate(means[chunk_cols]):
                ax.text(i, val, f'{val:.3f}', ha='center', va='bottom', fontsize=9, zorder=4)

        ax.set_ylabel('Mean Value')
        title_suffix = f' (Part {chart_idx + 1}/{n_charts})' if n_charts > 1 else ''
        ax.set_title(f'Means Comparison - {dataset_name}{title_suffix}')
        ax.set_xticks(range(len(chunk_display)))
        ax.set_xticklabels(chunk_display, rotation=45, ha='right')
        ax.legend()

        plt.tight_layout()
        suffix = f'_part{chart_idx + 1}' if n_charts > 1 else ''
        plt.savefig(figures_path / f'{dataset_name}_means_comparison{suffix}.png', dpi=300, bbox_inches='tight')
        plt.close()

    return means_df


def compare_correlation_patterns(full_data: pd.DataFrame, subset_data: pd.DataFrame) -> tuple:
    """Compare correlation patterns between full dataset and subset."""
    if len(full_data.columns) < 2 or len(subset_data.columns) < 2:
        return np.nan, np.nan

    try:
        full_corr = np.corrcoef(full_data.T)
        subset_corr = np.corrcoef(subset_data.T)

        # Get upper triangular values (excluding diagonal)
        full_corr_vals = full_corr[np.triu_indices(full_corr.shape[0], k=1)]
        subset_corr_vals = subset_corr[np.triu_indices(subset_corr.shape[0], k=1)]

        return np.nanmean(full_corr_vals), np.nanmean(subset_corr_vals)
    except:
        return np.nan, np.nan


def process_single_dataset_for_comparison(dataset_name: str, original_dir: Path, repr_dir: Path,
                                          random_dir: Path, figures_path: Path,
                                          difficulty_map: dict = None,
                                          max_name_length: int = None,
                                          max_elements_per_chart: int = 24) -> dict:
    """Process and compare a single dataset."""
    print(f"\n=== Processing {dataset_name} ===")

    try:
        # Load datasets
        full_data = pd.read_csv(original_dir / f"{dataset_name}.csv")
        representative = pd.read_csv(repr_dir / f"{dataset_name}.csv")
        random_sample = pd.read_csv(random_dir / f"{dataset_name}.csv")

        print(f"Original dataset size: {len(full_data)}")
        print(f"Representative sample size: {len(representative)}")
        print(f"Random sample size: {len(random_sample)}")

        # 确保difficulty字段存在且格式一致
        for df in [full_data, representative, random_sample]:
            if 'difficulty' in df.columns:
                # 检查difficulty字段类型
                print(f"Difficulty column type: {df['difficulty'].dtype}")
                # 确保所有值都是字符串类型
                df['difficulty'] = df['difficulty'].astype(str)
                # 打印前几个值，方便调试
                print(f"First few difficulty values: {df['difficulty'].head().tolist()}")
            else:
                print("Warning: No difficulty column found")

        # Prepare numeric versions
        full_numeric = prepare_numeric_data(full_data)
        representative_numeric = prepare_numeric_data(representative)
        random_numeric = prepare_numeric_data(random_sample)

        # Compare means - use original data to find column positions
        means_df = compare_means_single(dataset_name, full_data, representative, random_sample, figures_path, max_name_length, max_elements_per_chart)

        # Compare correlation patterns
        results = {
            "dataset_name": dataset_name,
            "sizes": {
                "full": len(full_data),
                "representative": len(representative),
                "random": len(random_sample)
            },
            "means": means_df.to_dict()
        }

        # Try correlation comparison
        full_num_with_diff = prepare_numeric_data(full_data, replace_difficulty_with_number=True, difficulty_map=difficulty_map)
        repr_num_with_diff = prepare_numeric_data(representative, replace_difficulty_with_number=True, difficulty_map=difficulty_map)
        rand_num_with_diff = prepare_numeric_data(random_sample, replace_difficulty_with_number=True, difficulty_map=difficulty_map)

        repr_corr = compare_correlation_patterns(full_num_with_diff, repr_num_with_diff)
        rand_corr = compare_correlation_patterns(full_num_with_diff, rand_num_with_diff)

        results["correlations"] = {
            "representative": {"full": repr_corr[0], "sample": repr_corr[1]},
            "random": {"full": rand_corr[0], "sample": rand_corr[1]}
        }

        return results

    except Exception as e:
        print(f"Error processing {dataset_name}: {e}")
        import traceback
        traceback.print_exc()
        return None


def generate_subsets(input_dir: str, output_dir: str, compression_ratio: float = 0.1,
                     auto_optimize: bool = False, random_state: int = 42, visualize: bool = True,
                     max_name_length: int = None, max_elements_per_chart: int = 24) -> None:
    """Generate and save different samples from multiple datasets."""
    input_path = Path(input_dir)
    output_path = Path(output_dir)

    # Create subdirectories for different sampling methods
    repr_output_dir = output_path / "representative"
    random_output_dir = output_path / "random"

    # Load info.json
    info_path = input_path / "info.json"
    with open(info_path, 'r', encoding='utf-8') as f:
        original_info = json.load(f)

    print(f"Loaded info.json with {len(original_info)} datasets")
    if auto_optimize:
        print("Auto-optimization mode enabled: searching for optimal n_cluster")

    # Process each dataset
    repr_info_list = []
    rand_info_list = []

    for info_item in original_info:
        print(f"\nProcessing {info_item['name']}...")
        repr_info, rand_info = process_single_dataset_for_generation(
            info_item, input_path, repr_output_dir, random_output_dir, compression_ratio, auto_optimize, random_state, visualize, max_name_length, max_elements_per_chart
        )
        repr_info_list.append(repr_info)
        rand_info_list.append(rand_info)

    # Save info.json for representative samples
    with open(repr_output_dir / "info.json", 'w', encoding='utf-8') as f:
        json.dump(repr_info_list, f, indent=4, ensure_ascii=False)

    # Save info.json for random samples
    with open(random_output_dir / "info.json", 'w', encoding='utf-8') as f:
        json.dump(rand_info_list, f, indent=4, ensure_ascii=False)

    print(f"\nCompression complete!")
    print(f"  - Representative samples saved to: {repr_output_dir}")
    print(f"  - Random samples saved to: {random_output_dir}")


def compare_subsets(original_dir: str, compressed_dir: str, figures_dir: str = "figures",
                    max_name_length: int = None, max_elements_per_chart: int = 24) -> None:
    """Compare original datasets with compressed samples."""
    # Filter out RuntimeWarning about invalid values in divide
    warnings.filterwarnings('ignore', category=RuntimeWarning, message='invalid value encountered in divide')

    # Create figures directory
    figures_path = Path(figures_dir)
    figures_path.mkdir(exist_ok=True, parents=True)

    original_path = Path(original_dir)
    compressed_path = Path(compressed_dir)
    repr_path = compressed_path / "representative"
    random_path = compressed_path / "random"

    # Load info.json from original directory
    with open(original_path / "info.json", 'r', encoding='utf-8') as f:
        original_info = json.load(f)

    print(f"Loaded {len(original_info)} datasets from info.json")

    # Process each dataset
    all_results = []
    for info_item in original_info:
        dataset_name = info_item["name"]
        difficulty_map = info_item.get("difficulty_map", None)

        result = process_single_dataset_for_comparison(
            dataset_name,
            original_path,
            repr_path,
            random_path,
            figures_path,
            difficulty_map,
            max_name_length,
            max_elements_per_chart
        )

        if result:
            all_results.append(result)

    # Save summary results
    summary_path = figures_path / "comparison_summary.json"
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=4)

    print(f"\n=== Summary ===")
    print(f"Processed {len(all_results)} datasets")
    print(f"All figures saved to: {figures_path}")
    print(f"Summary saved to: {summary_path}")


def main(input_dir: str,
         work_dir: str,
         compression_ratio: float = 0.1,
         auto_optimize: bool = False,
         random_state: int = 42,
         visualize: bool = True,
         max_name_length: int = None,
         max_elements_per_chart: int = 24) -> None:
    """
    Generate subsets and compare them.

    Parameters:
    - input_dir: Directory containing info.json and metadata CSV files
    - work_dir: Working directory to save all outputs
    - compression_ratio: Target compression ratio (0-1)
    - auto_optimize: Whether to automatically find optimal n_cluster
    - random_state: Random seed for reproducibility
    - visualize: Whether to generate visualization
    - max_name_length: Max length of element names in charts (None = no truncation)
    - max_elements_per_chart: Max number of elements per chart (default 24)
    """
    work_path = Path(work_dir)
    work_path.mkdir(exist_ok=True, parents=True)

    # Get metadata name from input_dir
    metadata_name = Path(input_dir).name

    # Create output directory name
    output_dir_name = f"{metadata_name}_compressed_{compression_ratio:.2f}"
    output_dir = work_path / output_dir_name

    # Create figures directory name
    figures_dir_name = f"{metadata_name}_figures_{compression_ratio:.2f}"
    figures_dir = work_path / figures_dir_name

    print(f"=== Step 1: Generating subsets ===")
    generate_subsets(
        input_dir=input_dir,
        output_dir=str(output_dir),
        compression_ratio=compression_ratio,
        auto_optimize=auto_optimize,
        random_state=random_state,
        visualize=visualize,
        max_name_length=max_name_length,
        max_elements_per_chart=max_elements_per_chart
    )

    print(f"\n=== Step 2: Comparing subsets ===")
    compare_subsets(
        original_dir=input_dir,
        compressed_dir=str(output_dir),
        figures_dir=str(figures_dir),
        max_name_length=max_name_length,
        max_elements_per_chart=max_elements_per_chart
    )

    print(f"\n=== All tasks complete ===")
    print(f"Output directory: {output_dir}")
    print(f"Figures directory: {figures_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate and compare dataset subsets using k-means clustering')
    parser.add_argument('--input', '-i', type=str, required=True,
                        help='Directory containing info.json and metadata CSV files')
    parser.add_argument('--work-dir', '-w', type=str, required=True,
                        help='Working directory to save all outputs')
    parser.add_argument('--compression-ratio', '-r', type=float, default=0.1,
                        help='Target compression ratio (0-1, default: 0.1)')
    parser.add_argument('--auto-optimize', '-a', action='store_true',
                        help='Enable automatic search for optimal n_cluster based on average scores similarity')
    parser.add_argument('--random-state', '-s', type=int, default=42,
                        help='Random seed for reproducibility (default: 42)')
    parser.add_argument('--no-visualize', '-n', action='store_true',
                        help='Disable clustering visualization')
    parser.add_argument('--max-name-length', '-l', type=int, default=None,
                       help='Max length of element names in charts; longer names are truncated (default: no truncation)')
    parser.add_argument('--max-elements-per-chart', '-e', type=int, default=24,
                       help='Max number of elements per chart; if exceeded, charts are split (default: 24)')

    args = parser.parse_args()

    main(
        input_dir=args.input,
        work_dir=args.work_dir,
        compression_ratio=args.compression_ratio,
        auto_optimize=args.auto_optimize,
        random_state=args.random_state,
        visualize=not args.no_visualize,
        max_name_length=args.max_name_length,
        max_elements_per_chart=args.max_elements_per_chart
    )
