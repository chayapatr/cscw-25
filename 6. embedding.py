from openai import OpenAI
import json
import functions.fetch as fetch
import pandas as pd
import os
import dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

dotenv.load_dotenv()

import importlib
importlib.reload(fetch)

# Create DeepInfra client
client = OpenAI(
    api_key=os.getenv("DEEPINFRA_API_KEY"),
    base_url="https://api.deepinfra.com/v1/openai",
)

model = "Qwen/Qwen3-Embedding-8B"

def get_embedding(text, retry_count=3):
    """Get embedding for a single text with retry logic"""
    for attempt in range(retry_count):
        try:
            response = client.embeddings.create(
                model=model,
                input=text,
                encoding_format="float"
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Attempt {attempt + 1} failed for text: {text[:50]}... Error: {e}")
            if attempt < retry_count - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                print(f"Failed to get embedding after {retry_count} attempts")
                return None

def process_embedding_batch(items, max_workers=100):
    """Process embeddings using ThreadPoolExecutor"""
    results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_item = {
            executor.submit(get_embedding, item): item 
            for item in items
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_item):
            item = future_to_item[future]
            try:
                embedding = future.result()
                if embedding is not None:
                    results.append({"id": item, "embedding": embedding})
                else:
                    print(f"Failed to get embedding for: {item}")
            except Exception as e:
                print(f"Error processing {item}: {e}")
    
    return results

def main():
    """Main function to create embeddings from keys.txt"""
    # Check if keys.txt exists
    keys_path = "data/embeddings/keys.txt"
    if not os.path.exists(keys_path):
        print(f"Error: {keys_path} does not exist. Run triplet processing first to generate keys.")
        return
    
    # Read keys from file
    with open(keys_path, "r") as f:
        keys = [line.strip() for line in f if line.strip()]
    
    if not keys:
        print("No keys found in keys.txt")
        return
    
    print(f"Processing {len(keys)} keys for embeddings...")
    
    # Process embeddings in batches
    batch_size = 50  # Adjust based on API limits
    all_results = []
    
    for i in range(0, len(keys), batch_size):
        batch = keys[i:i + batch_size]
        print(f"Processing batch {i//batch_size + 1}/{(len(keys) + batch_size - 1)//batch_size}")
        
        batch_results = process_embedding_batch(batch)
        all_results.extend(batch_results)
        
        # Add delay between batches to respect rate limits
        if i + batch_size < len(keys):
            time.sleep(1)
    
    # Create DataFrame and save results
    df = pd.DataFrame(all_results)
    
    # Save to CSV in same format as original
    output_path = "data/embeddings/embeddings.csv"
    df.to_csv(output_path, index=False)
    
    print(f"Processed {len(df)} embeddings")
    print(f"Saved embeddings to {output_path}")
    
    return df

def process_existing_jsonl():
    """Process existing embeddings.jsonl file if it exists (for compatibility)"""
    jsonl_path = "embeddings.jsonl"
    if not os.path.exists(jsonl_path):
        print(f"No existing {jsonl_path} found")
        return None
    
    df = pd.DataFrame(columns=["id", "embedding"])
    
    with open(jsonl_path, "r") as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                df.loc[len(df)] = [data['custom_id'], data['response']['body']['data'][0]['embedding']]
    
    df.to_csv("data/embeddings/embeddings.csv", index=False)
    print(f"Processed {len(df)} embeddings from existing JSONL")
    return df

if __name__ == "__main__":
    # Try to process existing JSONL first, otherwise create new embeddings
    df = process_existing_jsonl()
    if df is None or len(df) == 0:
        df = main()