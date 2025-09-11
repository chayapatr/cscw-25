from anthropic import Anthropic
from pydantic import BaseModel
import functions.prompts as prompts
import functions.claude as claude
import functions.fetch as fetch
import functions.triplets as triplets
import pandas as pd
import json
import os
import dotenv

dotenv.load_dotenv()

import importlib
importlib.reload(claude)
importlib.reload(prompts)
importlib.reload(fetch)
importlib.reload(triplets)

client = Anthropic()

class Subject(BaseModel):
   type: str # human | ai | co ONLY
   subtype: str # generative | student
   feature: str # creativity | explaination | #trust
   
class Triplet(BaseModel):
   cause: Subject
   relationship: str
   effect: Subject
   net_outcome: str # positive | negative | neutral | undetermined
   
class SkipResult(BaseModel):
   skip: bool

def main():
    # Load findings
    df = pd.read_csv("./data/findings/findings.csv")

    # Create batch requests
    requests = []
    
    for i, row in df.iterrows():
        # Create Claude request with structured output
        request_params = {
            "model": "claude-opus-4-1-20250805",
            "max_tokens": 8192,
            "system": prompts.triplets + "\n\nRespond with valid JSON matching this schema:\n" + 
                     '{"cause": {"type": "string", "subtype": "string", "feature": "string"}, "relationship": "string", "effect": {"type": "string", "subtype": "string", "feature": "string"}, "net_outcome": "string"} OR {"skip": true}',
            "messages": [{
                "role": "user",
                "content": row['finding']
            }]
        }
        
        requests.append(claude.create_request(f"{i}-{row['paper-id']}", request_params))

    # Create and submit batch
    batch = claude.gen_batch(client, requests)
    
    print(f"Batch ID: {batch['batch_object']}")
    fetch.save(f"Batch ID: {batch['batch_object']}", "data/triplets/claude_batch_id.txt")
    
    return batch

def get_results(batch_id=None):
    """Get results from completed batch"""
    if batch_id is None:
        # Read batch ID from file
        with open("data/triplets/claude_batch_id.txt", "r") as f:
            batch_id = f.read().strip().replace("Batch ID: ", "")
    
    # Check batch status
    batch_status = claude.get_batch_status(client, batch_id)
    print(f"Batch status: {batch_status.processing_status}")
    
    if batch_status.processing_status != "ended":
        print("Batch not completed yet")
        return batch_status
    
    # Get results
    res_path = "data/triplets/res.jsonl"
    
    # Clear existing results file
    if os.path.exists(res_path):
        os.remove(res_path)
    
    claude.get_batch_results(client, batch_id, res_path)
    
    # Process results
    df = pd.DataFrame(columns=["paper-id", "cause", "relation", "effect", "net_outcome"])
    df_keys = []
    
    with open(res_path, "r") as f:
        for line in f:
            if line.strip():
                result = json.loads(line)
                if result["result"]["type"] == "succeeded":
                    custom_id = result["custom_id"]
                    # Convert back to original format (i-paper-id -> i:paper-id)
                    original_id = custom_id.replace("-", ":", 1) if "-" in custom_id else custom_id
                    content_text = result["result"]["message"]["content"][0]["text"]
                    
                    try:
                        # Parse the JSON response
                        content_json = claude.extract_json_from_response(content_text)
                        
                        # Check if it's a skip response
                        if content_json.get("skip", False):
                            print(f"Skipped {original_id}: marked as non-interaction")
                            continue
                        
                        # Convert to Triplet object
                        content = Triplet(
                            cause=Subject(**content_json["cause"]),
                            relationship=content_json["relationship"],
                            effect=Subject(**content_json["effect"]),
                            net_outcome=content_json.get("net_outcome", "undetermined")
                        )
                        
                        df.loc[len(df)] = [original_id, triplets.parse_subject(content.cause), str(content.relationship), triplets.parse_subject(content.effect), content.net_outcome]
                        
                        # Process keys
                        df_keys += triplets.parse_key_list(content.cause)
                        if("human|user" in triplets.parse_key_list(content.cause)):
                            print(content.cause)
                        df_keys += triplets.parse_key_list(content.effect)
                        if("human|user" in triplets.parse_key_list(content.effect)):
                            print(content.effect)

                    except Exception as e:
                        print(f"Error processing line ({original_id}): {e}")
    
    # Save results in same format as original
    df_keys = set(df_keys)
    fetch.save("\n".join([*df_keys]), "data/embeddings/keys.txt")
    df.to_csv("data/triplets/triplets.csv", index=False)
    
    print(f"Processed {len(df)} triplets")
    print(f"Generated {len(df_keys)} unique keys")
    
    return df, df_keys

if __name__ == "__main__":
    # Uncomment to create batch
    # batch = main()
    
    # Uncomment to get results (after batch completes)
    results = get_results()