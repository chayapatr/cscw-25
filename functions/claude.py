import json
import re
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request

def create_request(custom_id, params):
    """Create a batch request object"""
    return Request(
        custom_id=custom_id,
        params=MessageCreateParamsNonStreaming(**params)
    )
    
def gen_batch(client, requests):
    """Create a batch with the given requests"""
    batch_object = client.messages.batches.create(requests=requests)
    
    print(f"Batch ID: {batch_object.id}")
    
    return {
        "batch_object": batch_object.id,
        "batch": batch_object
    }

def get_batch_status(client, batch_id):
    """Get batch processing status"""
    return client.messages.batches.retrieve(batch_id)
    
def get_batch_results(client, batch_id, path=None):
    """Get batch results, optionally saving to file"""
    results = []
    
    for result in client.messages.batches.results(batch_id):
        results.append(result)
        
        if path:
            # Append each result to file as JSONL
            with open(path, "a") as f:
                result_dict = {
                    "custom_id": result.custom_id,
                    "result": {
                        "type": result.result.type
                    }
                }
                
                if result.result.type == "succeeded":
                    # Handle empty content array
                    content_text = ""
                    if result.result.message.content and len(result.result.message.content) > 0:
                        content_text = result.result.message.content[0].text
                    
                    result_dict["result"]["message"] = {
                        "id": result.result.message.id,
                        "content": [{"type": "text", "text": content_text}],
                        "role": result.result.message.role,
                        "model": result.result.message.model,
                        "stop_reason": result.result.message.stop_reason,
                        "usage": {
                            "input_tokens": result.result.message.usage.input_tokens,
                            "output_tokens": result.result.message.usage.output_tokens
                        }
                    }
                elif result.result.type == "errored":
                    error_dict = {"type": result.result.error.type}
                    # Handle different error response formats
                    if hasattr(result.result.error, 'message'):
                        error_dict["message"] = result.result.error.message
                    elif hasattr(result.result.error, 'error'):
                        error_dict["message"] = str(result.result.error.error)
                    else:
                        error_dict["message"] = str(result.result.error)
                    result_dict["result"]["error"] = error_dict
                    
                f.write(json.dumps(result_dict) + '\n')
    
    return results

def extract_between_tags(tag: str, string: str, strip: bool = False) -> list[str]:
    """Extract content between XML tags"""
    ext_list = re.findall(f"<{tag}>(.+?)</{tag}>", string, re.DOTALL)
    if strip:
        ext_list = [e.strip() for e in ext_list]
    return ext_list

def extract_tag_content(tag: str, string: str) -> str:
    """Extract single tag content"""
    match = re.search(f"<{tag}>(.+?)</{tag}>", string, re.DOTALL)
    return match.group(1).strip() if match else ""

def extract_json_from_response(response_text):
    """Extract JSON from Claude's response"""
    # Try to find JSON by looking for braces
    try:
        json_start = response_text.index("{")
        json_end = response_text.rfind("}") + 1
        return json.loads(response_text[json_start:json_end])
    except (ValueError, json.JSONDecodeError):
        pass
    
    # If response was prefilled with "{", add it back
    if not response_text.strip().startswith("{"):
        try:
            return json.loads("{" + response_text)
        except json.JSONDecodeError:
            pass
    
    raise ValueError(f"Could not extract valid JSON from response: {response_text}")

def extract_findings(response_text):
    """Extract findings from JSON formatted response"""
    try:
        return extract_json_from_response(response_text)
    except ValueError as e:
        print(f"Failed to parse JSON: {e}")
        return {
            "keywords": [],
            "findings": [],
            "note": {
                "type": "error",
                "description": "Failed to parse response"
            }
        }