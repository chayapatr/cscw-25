from anthropic import Anthropic
from pydantic import BaseModel
import functions.prompts as prompts
import functions.claude as claude
import functions.fetch as fetch
import pandas as pd
import json
import os
import dotenv

dotenv.load_dotenv()

import importlib
importlib.reload(claude)
importlib.reload(prompts)
importlib.reload(fetch)

client = Anthropic()

class Note(BaseModel):
    type: str
    description: str

class AbstractSummary(BaseModel):
    keywords: list[str]
    summaries: list[str]
    note: Note

def main():
    # Load abstracts
    df = pd.read_csv("./data/abstract/abstract.csv")
    df_ref = pd.DataFrame(columns=["id", "ref_id"])

    # Create batch requests
    requests = []
    ref = []
    
    for i, row in df.iterrows():
        # Create Claude request with structured output
        request_params = {
            "model": "claude-opus-4-1-20250805",
            "max_tokens": 8192,
            "system": prompts.findings + "\n\nRespond with valid JSON matching this schema:\n" + 
                     '{"keywords": ["string"], "summaries": ["string"], "note": {"type": "string", "description": "string"}}',
            "messages": [{
                "role": "user",
                "content": row.title + "\n" + row.abstract
            }]
        }
        
        requests.append(claude.create_request(f"paper-{i}", request_params))
        df_ref.loc[len(df_ref)] = [row.paperId, f"paper-{i}"]

    # Save reference mapping
    df_ref.to_csv('data/findings/ref.csv', index=False)
    
    # Create and submit batch
    batch = claude.gen_batch(client, requests)
    
    print(f"Batch ID: {batch['batch_object']}")
    fetch.save(f"Batch ID: {batch['batch_object']}", "data/findings/claude_batch_id.txt")
    
    return batch

def get_results(batch_id=None):
    """Get results from completed batch"""
    if batch_id is None:
        # Read batch ID from file
        with open("data/findings/claude_batch_id.txt", "r") as f:
            batch_id = f.read().strip().replace("Batch ID: ", "")
    
    # Check batch status
    batch_status = claude.get_batch_status(client, batch_id)
    print(f"Batch status: {batch_status.processing_status}")
    
    if batch_status.processing_status != "ended":
        print("Batch not completed yet")
        return batch_status
    
    # Get results
    res_path = "data/findings/res.jsonl"
    
    # Clear existing results file
    if os.path.exists(res_path):
        os.remove(res_path)
    
    claude.get_batch_results(client, batch_id, res_path)
    
    # Process results
    df = pd.DataFrame(columns=["paper-id", "keywords", "summaries", "notes"])
    df_findings = pd.DataFrame(columns=["paper-id", "finding"])
    
    with open(res_path, "r") as f:
        for line in f:
            if line.strip():
                result = json.loads(line)
                if result["result"]["type"] == "succeeded":
                    custom_id = result["custom_id"]
                    content_text = result["result"]["message"]["content"][0]["text"]
                    
                    try:
                        # Parse the JSON response
                        content = claude.extract_json_from_response(content_text)
                        
                        # Handle None response
                        if content is None:
                            print(f"Null response for {custom_id}")
                            print(f"Content was: {content_text[:200]}...")
                            continue
                        
                        # Convert to match original format
                        note_data = content.get("note") or {}
                        summary_data = AbstractSummary(
                            keywords=content.get("keywords", []),
                            summaries=content.get("summaries", []),
                            note=Note(
                                type=note_data.get("type", ""),
                                description=note_data.get("description", "")
                            )
                        )
                        
                        df.loc[len(df)] = [custom_id, str(summary_data.keywords), str(summary_data.summaries), str(summary_data.note)]
                        
                        for finding in summary_data.summaries:
                            df_findings.loc[len(df_findings)] = [custom_id, finding]
                            
                    except Exception as e:
                        print(f"Error processing {custom_id}: {e}")
                        print(f"Content was: {content_text[:200]}...")
                        # Add error entry
                        df.loc[len(df)] = [custom_id, "[]", "[]", "Note(type='error', description='Failed to parse response')"]
    
    # Save results in same format as original
    df.to_csv('data/findings/res.csv', index=False)
    df_findings.to_csv('data/findings/findings.csv', index=False)
    
    print(f"Processed {len(df)} papers")
    print(f"Extracted {len(df_findings)} findings")
    
    return df, df_findings

if __name__ == "__main__":
    # Uncomment to create batch
    # batch = main()
    
    # Uncomment to get results (after batch completes)
    results = get_results()