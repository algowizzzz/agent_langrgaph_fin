#!/usr/bin/env python3
"""
A simple, single-step test for memory-enabled follow-up questions.
"""
import requests
import json
import time
import uuid
from pathlib import Path

# --- Configuration ---
BASE_URL = "http://localhost:8000"
UPLOAD_ENDPOINT = f"{BASE_URL}/upload"
CHAT_ENDPOINT = f"{BASE_URL}/chat"
CSV_FILE_PATH = Path("test_documents/sample_data.csv")
SESSION_ID = f"single_test_session_{uuid.uuid4()}"

# --- Helper Functions ---
def print_step(title):
    print("\n" + "="*60)
    print(f"🔬 {title}")
    print("="*60)

def print_result(name, success, message=""):
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} - {name}: {message}")
    if not success:
        exit(1)

def upload_file(file_path):
    print_step(f"Uploading Test File: {file_path.name}")
    try:
        with open(file_path, "rb") as f:
            files = {"file": (file_path.name, f, "text/csv")}
            upload_url = f"{UPLOAD_ENDPOINT}?session_id={SESSION_ID}"
            response = requests.post(
                upload_url,
                files=files,
                timeout=60
            )
        response.raise_for_status()
        result = response.json()
        doc_name = result.get("filename")
        print_result("File Upload", doc_name is not None, f"Uploaded as {doc_name}")
        return doc_name
    except requests.exceptions.RequestException as e:
        print_result("File Upload", False, str(e))
        return None

def run_chat(query, doc_name):
    print_step(f"Running Chat Query: '{query}'")
    payload = {
        "query": query,
        "session_id": SESSION_ID,
        "active_document": doc_name,
    }
    try:
        response = requests.post(CHAT_ENDPOINT, json=payload, timeout=180) # Increased timeout
        response.raise_for_status()
        result = response.json()
        final_answer = result.get("final_answer", "")
        
        # Check if final_answer is a list and try to join it
        if isinstance(final_answer, list):
            print("⚠️ Warning: final_answer was a list, joining to string.")
            final_answer = " ".join(map(str, final_answer))

        success = result.get("status") == "success" and final_answer
        print_result("Chat Query", success, f"Response: {final_answer[:200]}...")
        return final_answer
    except requests.exceptions.RequestException as e:
        print_result("Chat Query", False, f"Error: {e}, Response: {response.text if 'response' in locals() else 'N/A'}")
        return None
    except json.JSONDecodeError as e:
        print_result("Chat Query", False, f"Error: {e}, Response: {response.text}")
        return None

# --- Test Execution ---
def main():
    print("🧠 Starting Single Memory-Enabled Follow-up Test")
    
    # 1. Upload CSV
    doc_name = upload_file(CSV_FILE_PATH)
    if not doc_name:
        return

    # 2. Initial Question
    initial_query = "Summarize the employee data in this CSV."
    initial_response = run_chat(initial_query, doc_name)
    if not initial_response:
        return

    # 3. Follow-up Question
    follow_up_query = "Based on your previous response, how many departments are there?"
    follow_up_response = run_chat(follow_up_query, doc_name)
    if not follow_up_response:
        return

    print("\n" + "="*60)
    print("🎉 Test Completed Successfully!")
    print("="*60)

if __name__ == "__main__":
    main()
