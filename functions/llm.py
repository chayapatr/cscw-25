import json

def wrap(id, body):
    return {
        "custom_id": id,
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": body,
    }
    
def gen_batch_jsonl(path, arr):
    with open(path, 'w') as f:
        f.write(f"{"\n".join([json.dumps(i) for i in arr])}\n")
    
# def gen_body(messages, model="o3-mini"):
#     return { "model": model, "messages": messages }