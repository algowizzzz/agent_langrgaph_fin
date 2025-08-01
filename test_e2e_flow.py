import requests
import json
import os

# Configuration
BASE_URL = "http://localhost:8000"
FILE_PATH = "/Users/saadahmed/Desktop/Apps/AWS_Extra/Agent/test_business_data.csv"
SESSION_ID = "e2e_test_session"
QUERY = "data insights"

def run_test():
    """
    Runs an end-to-end test of the document upload and chat query flow.
    """
    if not os.path.exists(FILE_PATH):
        print(f"Error: Test file not found at {FILE_PATH}")
        return

    # 1. Upload the document
    print(f"--- Step 1: Uploading Document ---")
    print(f"File: {FILE_PATH}")
    
    upload_url = f"{BASE_URL}/upload?session_id={SESSION_ID}"
    files = {'file': (os.path.basename(FILE_PATH), open(FILE_PATH, 'rb'), 'text/csv')}
    
    try:
        upload_response = requests.post(upload_url, files=files, timeout=30)
        upload_response.raise_for_status()
        upload_data = upload_response.json()
        print("Upload successful:")
        print(json.dumps(upload_data, indent=2))
        
        if upload_data.get("status") != "success" or upload_data.get("chunks_created", 0) == 0:
            print("\nError: Upload did not result in created chunks.")
            return

    except requests.exceptions.RequestException as e:
        print(f"\nError during file upload: {e}")
        return

    # 2. Send a query about the document
    print(f"\n--- Step 2: Sending Query ---")
    print(f"Query: '{QUERY}'")

    chat_url = f"{BASE_URL}/chat"
    chat_payload = {
        "session_id": SESSION_ID,
        "query": QUERY,
        "active_document": os.path.basename(FILE_PATH)
    }
    
    try:
        chat_response = requests.post(chat_url, json=chat_payload, timeout=120)
        chat_response.raise_for_status()
        chat_data = chat_response.json()
        
        print("\n--- Step 3: Chat Response ---")
        print("Final Answer:")
        print(chat_data.get("final_answer", "No final answer received."))
        
        print("\nFull response:")
        print(json.dumps(chat_data, indent=2))

    except requests.exceptions.RequestException as e:
        print(f"\nError during chat request: {e}")

if __name__ == "__main__":
    run_test()
