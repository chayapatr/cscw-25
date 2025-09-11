import pandas as pd
import networkx as nx
import json
import ast
import functions.triplets as ft
import importlib

importlib.reload(ft)

def load_data():
    """Load all required data files"""
    ref = pd.read_csv('data/findings/ref.csv')
    abstract = pd.read_csv('data/abstract/abstract.csv')
    findings = pd.read_csv('data/findings/findings.csv')
    merged_keys = pd.read_csv('data/graph/merged_keys.csv')
    clustered_keys = pd.read_csv('data/graph/clustered_keys.csv')
    triplets = pd.read_csv('data/triplets/triplets.csv')
    
    # Load cluster labels if available
    try:
        cluster_labels = pd.read_csv('data/graph/cluster_labels.csv')
    except FileNotFoundError:
        print("Warning: cluster_labels.csv not found. Run 7.cluster_labels.py first.")
        cluster_labels = pd.DataFrame(columns=['cluster_id', 'cluster_name', 'cluster_description'])
    
    return ref, abstract, findings, merged_keys, clustered_keys, triplets, cluster_labels

def prepare_data(findings, triplets, ref, abstract):
    """Prepare data for graph creation"""
    # Add keys to findings
    for i, row in findings.iterrows():
        findings.at[i, 'key'] = f"{i}:{row['paper-id']}"
    
    # Process triplets
    triplets['cause'] = triplets['cause'].apply(lambda x: json.loads(x))
    triplets['effect'] = triplets['effect'].apply(lambda x: json.loads(x))
    
    for t in ['cause', 'effect']:
        triplets[f"{t}_full"] = triplets[t].apply(lambda x: ft.parse_key(x, full=True))
        triplets[f"{t}_short"] = triplets[t].apply(lambda x: ft.parse_key(x))
    
    # Add paper information
    triplets['ref-id'] = triplets['paper-id'].apply(lambda x: ref[ref['ref_id'] == x.split(":")[1]].iloc[0]['id'])
    triplets['paper'] = triplets['ref-id'].apply(lambda x: abstract[abstract['paperId'] == x].iloc[0]['title'])
    triplets['finding'] = triplets['paper-id'].apply(lambda x: findings[findings['key'] == x].iloc[0]['finding'])
    
    return findings, triplets

def create_merged_map(merged_keys):
    """Create mapping from merged keys to representatives"""
    merged_map = {}
    for i, row in merged_keys.iterrows():
        for k in ast.literal_eval(row['members']):
            merged_map[k] = row['representative']
    return merged_map

def create_graph_with_labels(clustered_keys, merged_keys, triplets, cluster_labels):
    """Create NetworkX graph with cluster labels"""
    G = nx.MultiDiGraph()
    reps = merged_keys['representative'].to_list()
    merged_map = create_merged_map(merged_keys)
    
    # Create cluster label mapping
    cluster_label_map = {}
    for _, row in cluster_labels.iterrows():
        cluster_label_map[row['cluster_id']] = {
            'name': row['cluster_name'],
            'description': row['cluster_description']
        }
    
    # Add key nodes
    for i, k in clustered_keys.iterrows():
        members = ast.literal_eval(merged_keys.loc[merged_keys['representative'] == k['key']].iloc[0]['members']) if k['key'] in reps else [k['key']]
        G.add_node(
            k['key'],
            cluster=k['cluster'],
            kind='key',
            members=members
        )
    
    # Add edges from triplets
    for i, f in triplets.iterrows():
        source = merged_map[f['cause_short']] if f['cause_short'] in merged_map else f['cause_short']
        target = merged_map[f['effect_short']] if f['effect_short'] in merged_map else f['effect_short']
        G.add_edge(
            source, target,
            kind="relation",
            source_full=f['cause_full'],
            effect_full=f['effect_full'],
            type=f['relation'],
            paper=f['paper'],
            finding=f['finding']
        )
    
    # Add cluster nodes with enhanced labels
    for cluster in [*clustered_keys['cluster'].unique().tolist(), 'human', 'ai', 'co']:
        # Get cluster info from labels
        if cluster in cluster_label_map:
            cluster_info = cluster_label_map[cluster]
            name = cluster_info['name']
            description = cluster_info['description']
        else:
            # Fallback for generic clusters
            name = cluster
            description = f"Generic {cluster} cluster"
        
        G.add_node(
            cluster,
            kind='cluster',
            name=name,
            description=description
        )
        
        # Add edges from cluster to its members
        for i, k in clustered_keys[clustered_keys['cluster'] == cluster].iterrows():
            G.add_edge(
                cluster, k['key'],
                kind='cluster'
            )
    
    return G

def main():
    """Main function to create labeled graph"""
    print("Loading data...")
    ref, abstract, findings, merged_keys, clustered_keys, triplets, cluster_labels = load_data()
    
    print("Preparing data...")
    findings, triplets = prepare_data(findings, triplets, ref, abstract)
    
    print("Creating graph with cluster labels...")
    G = create_graph_with_labels(clustered_keys, merged_keys, triplets, cluster_labels)
    
    print("Saving graph...")
    graph_data = nx.node_link_data(G, edges="edges")
    with open('data/graph/graph_labeled.json', 'w') as f:
        json.dump(graph_data, f, indent=2)
    
    print(f"Graph created with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
    print("Saved to: data/graph/graph_labeled.json")
    
    # Print cluster information
    cluster_nodes = [n for n in G.nodes(data=True) if n[1].get('kind') == 'cluster']
    labeled_clusters = [n for n in cluster_nodes if n[0] in cluster_labels['cluster_id'].values]
    
    print(f"\nCluster summary:")
    print(f"- Total clusters: {len(cluster_nodes)}")
    print(f"- Labeled clusters: {len(labeled_clusters)}")
    print(f"- Generic clusters: {len(cluster_nodes) - len(labeled_clusters)}")
    
    return G

if __name__ == "__main__":
    main()