import numpy as np
from sklearn.cluster import DBSCAN
import pandas as pd

def prepare_embeddings(embeddings):
    import ast
    keywords = embeddings['key'].to_list()
    # Handle both string representations and actual arrays
    def parse_embedding(emb):
        if isinstance(emb, str):
            # Parse string representation of list
            return ast.literal_eval(emb)
        elif isinstance(emb, list) and len(emb) > 0 and isinstance(emb[0], (int, float)):
            # Already a flat list
            return emb
        elif isinstance(emb, list) and len(emb) > 0 and isinstance(emb[0], list):
            # Nested list, take first element
            return emb[0]
        else:
            # Assume it's already the correct format
            return emb
    
    embeddings_array = []
    for k in keywords:
        emb = embeddings.loc[embeddings['key'] == k].iloc[0]['embedding']
        parsed_emb = parse_embedding(emb)
        embeddings_array.append(parsed_emb)
    
    embeddings = np.array(embeddings_array)
    # print(embeddings)
    return keywords, embeddings

def cluster_embeddings(embeddings, eps=0.05):
        clustering = DBSCAN(eps=eps, min_samples=2, metric='cosine').fit(embeddings)
        print(clustering)
        return clustering.labels_

def get_cluster_representatives(clustered_df, embeddings):
    representatives = {}
    
    # Ignore noise points (cluster = -1)
    for cluster_id in clustered_df['cluster'].unique():
        if cluster_id == -1:
            continue
            
        # Get keywords and embeddings for this cluster
        cluster_mask = clustered_df['cluster'] == cluster_id
        cluster_keywords = clustered_df[cluster_mask]['keyword'].tolist()
        cluster_embeddings = embeddings[cluster_mask]
        
        # Calculate centroid
        centroid = np.mean(cluster_embeddings, axis=0)
        
        # Find closest word to centroid using cosine similarity
        similarities = np.dot(cluster_embeddings, centroid)
        similarities = similarities / (np.linalg.norm(cluster_embeddings, axis=1) * np.linalg.norm(centroid))
        representative_idx = np.argmax(similarities)
        
        representatives[int(cluster_id)] = {
            'representative': cluster_keywords[representative_idx],
            'members': cluster_keywords
        }
    
    return representatives

# Modify your original code
def process_keywords(embedding_df):
    keywords, embeddings = prepare_embeddings(embedding_df)
    labels = cluster_embeddings(embeddings)
    df = pd.DataFrame({'keyword': keywords, 'cluster': labels})
    
    representatives = get_cluster_representatives(df, embeddings)
    
    return df, representatives

# clustered, cluster_representatives = process_keywords(embedding)

# for cluster_id, info in cluster_representatives.items():
#     print(f"\nCluster {cluster_id}:")
#     print(f"Representative: {info['representative']}")
#     print(f"All members: {', '.join(info['members'])}")