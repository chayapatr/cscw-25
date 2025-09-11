from anthropic import Anthropic
import os
import dotenv

dotenv.load_dotenv()

client = Anthropic()

def cancel_batch(batch_id=None):
    """Cancel a Claude batch"""
    if batch_id is None:
        # Read batch ID from file
        try:
            with open("data/triplets/claude_batch_id.txt", "r") as f:
                batch_id = f.read().strip().replace("Batch ID: ", "")
        except FileNotFoundError:
            print("No batch ID file found. Please provide batch ID manually.")
            return
    
    try:
        # Get batch status first
        batch_status = client.beta.messages.batches.retrieve(batch_id)
        print(f"Current batch status: {batch_status.processing_status}")
        
        if batch_status.processing_status in ["ended", "canceled", "failed"]:
            print(f"Batch is already {batch_status.processing_status}. Cannot cancel.")
            return batch_status
        
        # Cancel the batch
        canceled_batch = client.beta.messages.batches.cancel(batch_id)
        print(f"Batch {batch_id} has been canceled")
        print(f"New status: {canceled_batch.processing_status}")
        
        return canceled_batch
        
    except Exception as e:
        print(f"Error canceling batch {batch_id}: {e}")
        return None

if __name__ == "__main__":
    # Cancel the current batch
    result = cancel_batch()