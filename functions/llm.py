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
        
def gen_batch(client, batch_jsonl, metadata=""):
    batch_input_file = client.files.create(
        file=open(batch_jsonl, "rb"),
        purpose="batch"
    )

    print(f"File ID: {batch_input_file.id}")

    batch_object = client.batches.create(
        input_file_id=batch_input_file.id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
        metadata={
            "description": metadata
        })
        
    return {
        "batch_file": batch_input_file.id,
        "batch_object": batch_object.id
    }
    
def get_batch_result(client, batch_id, path):
    retrieve = client.batches.retrieve(batch_id)
    if(not retrieve.output_file_id):
        return None

    content = client.files.content(retrieve.output_file_id)
    with open(path, "w") as f:
        f.write(content.text)
    return retrieve.output_file_id
    
# def gen_body(messages, model="o3-mini"):
#     return { "model": model, "messages": messages }