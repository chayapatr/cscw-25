from anthropic import Anthropic
import pandas as pd
import json
import dotenv
from pydantic import BaseModel

dotenv.load_dotenv()

client = Anthropic()

class ClusterLabel(BaseModel):
    name: str
    description: str

class TypeClusters(BaseModel):
    clusters: dict  # cluster_id -> ClusterLabel

def get_cluster_members(df, cluster_id):
    """Get all members of a specific cluster"""
    cluster_members = df[df['cluster'] == cluster_id]['key'].tolist()
    return cluster_members

def generate_type_cluster_labels(entity_type, clusters_data):
    """Use Claude to generate labels for all clusters of a specific type in one call"""
    
    # Build prompt with all clusters for this type
    clusters_text = ""
    for cluster_id, members in clusters_data.items():
        members_text = ", ".join(members[:15])  # Limit members for readability
        clusters_text += f"\n**{cluster_id}**: {members_text}\n"
    
    prompt = f"""Analyze these {entity_type.upper()} clusters from human-AI interaction research. For each cluster, provide:
1. A descriptive name (3-8 words) that captures the essence of the cluster
2. A brief description (1-2 sentences) explaining what this cluster represents

Clusters to analyze:
{clusters_text}

Consider the semantic relationships between terms within each cluster and identify the common themes or concepts they represent in human-AI interaction research."""

    schema = {
        "clusters": {
            cluster_id: {"name": "string", "description": "string"} 
            for cluster_id in clusters_data.keys()
        }
    }

    try:
        response = client.messages.create(
            model="claude-opus-4-1-20250805",
            max_tokens=2000,
            system=f"You are an expert in human-AI interaction research. Analyze clusters of {entity_type} keywords to identify meaningful patterns and themes. Respond with valid JSON matching the provided schema.",
            messages=[{
                "role": "user",
                "content": prompt + f"\n\nRespond with JSON matching this exact structure: {json.dumps(schema, indent=2)}"
            }]
        )
        
        # Extract JSON from response
        response_text = response.content[0].text
        
        # Try to parse JSON (handle markdown code blocks)
        import re
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            type_data = json.loads(json_str)
            
            # Convert to ClusterLabel objects
            result = {}
            for cluster_id, data in type_data.get("clusters", {}).items():
                result[cluster_id] = ClusterLabel(
                    name=data.get("name", f"Cluster {cluster_id}"),
                    description=data.get("description", "No description available")
                )
            return result
        else:
            # Fallback if no JSON found
            return {cluster_id: ClusterLabel(
                name=f"Cluster {cluster_id}",
                description="Unable to generate description"
            ) for cluster_id in clusters_data.keys()}
            
    except Exception as e:
        print(f"Error generating labels for {entity_type} clusters: {e}")
        return {cluster_id: ClusterLabel(
            name=f"Cluster {cluster_id}",
            description="Error generating description"
        ) for cluster_id in clusters_data.keys()}

def main():
    # Load clustered data
    df = pd.read_csv("data/graph/clustered_keys.csv")
    
    # Get all unique clusters (exclude generic types and header)
    all_clusters = df['cluster'].unique()
    clusters_to_process = [c for c in all_clusters if ':' in str(c) and c != 'cluster']
    
    print(f"Processing {len(clusters_to_process)} clusters...")
    
    # Group clusters by type (human, ai, co)
    clusters_by_type = {}
    for cluster_id in clusters_to_process:
        entity_type = cluster_id.split(':')[0]
        if entity_type not in clusters_by_type:
            clusters_by_type[entity_type] = {}
        
        members = get_cluster_members(df, cluster_id)
        clusters_by_type[entity_type][cluster_id] = members
    
    # Process each type in a single API call
    all_cluster_labels = []
    
    for entity_type, type_clusters in clusters_by_type.items():
        print(f"\nProcessing {entity_type.upper()} clusters ({len(type_clusters)} total)...")
        
        # Generate labels for all clusters of this type
        type_labels = generate_type_cluster_labels(entity_type, type_clusters)
        
        # Convert to the expected format
        for cluster_id, label in type_labels.items():
            cluster_info = {
                "cluster_id": cluster_id,
                "name": label.name,
                "description": label.description,
                "member_count": len(type_clusters[cluster_id]),
                "members": type_clusters[cluster_id]
            }
            all_cluster_labels.append(cluster_info)
            print(f"  {cluster_id}: {label.name}")
    
    # Save results to JSON
    output_path = "data/graph/cluster_labels.json"
    with open(output_path, 'w') as f:
        json.dump(all_cluster_labels, f, indent=2)
    
    # Save a summary CSV for easy merging with graph data
    summary_df = pd.DataFrame([{
        "cluster_id": item["cluster_id"],
        "cluster_name": item["name"],
        "cluster_description": item["description"],
        "member_count": item["member_count"]
    } for item in all_cluster_labels])
    
    summary_csv_path = "data/graph/cluster_labels.csv"
    summary_df.to_csv(summary_csv_path, index=False)
    
    # Create an enhanced clustered_keys.csv with cluster names and descriptions
    enhanced_df = df.copy()
    
    # Merge with cluster labels
    enhanced_df = enhanced_df.merge(
        summary_df[['cluster_id', 'cluster_name', 'cluster_description']], 
        left_on='cluster', 
        right_on='cluster_id', 
        how='left'
    )
    
    # Fill missing values for generic clusters
    enhanced_df['cluster_name'] = enhanced_df['cluster_name'].fillna(enhanced_df['cluster'])
    enhanced_df['cluster_description'] = enhanced_df['cluster_description'].fillna('Generic cluster')
    
    # Drop duplicate cluster_id column
    enhanced_df = enhanced_df.drop('cluster_id', axis=1)
    
    # Save enhanced file
    enhanced_path = "data/graph/clustered_keys_labeled.csv"
    enhanced_df.to_csv(enhanced_path, index=False)
    
    print(f"\nCompleted! Results saved to:")
    print(f"- {output_path} (detailed JSON)")
    print(f"- {summary_csv_path} (summary CSV)")
    print(f"- {enhanced_path} (enhanced clustered data)")
    print(f"\nProcessed {len(all_cluster_labels)} clusters using {len(clusters_by_type)} API calls")
    
    return all_cluster_labels, summary_df, enhanced_df

if __name__ == "__main__":
    main()