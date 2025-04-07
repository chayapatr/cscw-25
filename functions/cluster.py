import numpy as np
from sklearn.cluster import KMeans
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt
from kneed import KneeLocator
from sklearn.metrics.pairwise import cosine_similarity

def get_cluster_representatives(embeddings, words, cluster_labels, cluster_id, n=10):
    cluster_indices = np.where(cluster_labels == cluster_id)[0]
    cluster_embeddings = embeddings[cluster_indices]
    
    centroid = np.mean(cluster_embeddings, axis=0)
    similarities = cosine_similarity(cluster_embeddings, centroid.reshape(1, -1)).flatten()
    
    top_indices = np.argsort(similarities)[-n:][::-1]
    return [words[cluster_indices[i]] for i in top_indices]

def find_optimal_clusters(embeddings_array):
    inertias = []
    k_range = range(1, min(20, len(embeddings_array)))
    
    for k in k_range:
        kmeans = KMeans(n_clusters=k, random_state=42)
        kmeans.fit(embeddings_array)
        inertias.append(kmeans.inertia_)
    
    kneedle = KneeLocator(k_range, inertias, curve='convex', direction='decreasing', S=1.0)
    optimal_k = kneedle.elbow
    
    return optimal_k

def perform_clustering(embeddings_array, optimal_k):
    kmeans = KMeans(n_clusters=optimal_k, random_state=42)
    clusters = kmeans.fit_predict(embeddings_array)
    return clusters
    
def visualize_clusters(embeddings_array, words, clusters, optimal_k):
    tsne = TSNE(n_components=2, random_state=42)
    embeddings_2d = tsne.fit_transform(embeddings_array)
    
    plt.figure(figsize=(16, 12))
    scatter = plt.scatter(embeddings_2d[:, 0], embeddings_2d[:, 1], c=clusters, cmap='tab10', alpha=0.6)
    
    plt.legend(*scatter.legend_elements(),
                        title="Clusters",
                        loc="center left",
                        bbox_to_anchor=(1, 0.5))
    
    # Add 3 random labels for each cluster
    for cluster_id in range(optimal_k):
        cluster_mask = clusters == cluster_id
        cluster_points = embeddings_2d[cluster_mask]
        cluster_words = np.array(words)[cluster_mask]
        
        if len(cluster_points) > 0:
            n_samples = min(3, len(cluster_points))
            random_indices = np.random.choice(len(cluster_points), n_samples, replace=False)
            
            for idx in random_indices:
                plt.annotate(cluster_words[idx][:50] + '...' if len(cluster_words[idx]) > 50 else cluster_words[idx], 
                           (cluster_points[idx, 0], cluster_points[idx, 1]),
                           fontsize=8)
    
    plt.title(f'Keyword Clusters (k={optimal_k})')
    plt.show()
    
def print_cluster_representatives(embeddings_array, words, clusters, optimal_k):
    representatives = []
    print("\nTop 15 representatives for each cluster:")
    for cluster_id in range(optimal_k):
        representative = get_cluster_representatives(embeddings_array, words, clusters, cluster_id, n=15)
        print(f"\nCluster {cluster_id}:")
        print("- "+"\n- ".join(representative))
        representatives.append(representative)
    
    return representatives

def cluster_and_visualize(keyword_embeddings):
    embeddings_array = np.array(list(keyword_embeddings.values()))
    words = list(keyword_embeddings.keys())

    optimal_k = find_optimal_clusters(embeddings_array)
    clusters = perform_clustering(embeddings_array, optimal_k)

    visualize_clusters(embeddings_array, words, clusters, optimal_k)
    representatives = print_cluster_representatives(embeddings_array, words, clusters, optimal_k)

    return clusters, optimal_k, representatives
