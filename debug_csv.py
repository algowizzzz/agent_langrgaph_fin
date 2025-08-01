#!/usr/bin/env python3
import requests
import time

# Test CSV functionality specifically
session_id = f'test_csv_debug_{int(time.time())}'
print(f'Testing CSV with session: {session_id}')

# Upload CSV
files = {'file': ('sample_data.csv', open('test_documents/sample_data.csv', 'rb'), 'text/csv')}
upload_response = requests.post(f'http://localhost:8000/upload?session_id={session_id}', files=files)
upload_result = upload_response.json()
print(f'CSV Upload result: {upload_result}')

if upload_result.get('status') == 'success':
    stored_filename = upload_result.get('filename')
    print(f'CSV stored as: {stored_filename}')
    
    # Test summarization
    chat_response = requests.post('http://localhost:8000/chat', json={
        'query': 'Summarize this CSV data',
        'session_id': session_id,
        'active_document': stored_filename
    })
    chat_result = chat_response.json()
    print(f'CSV Summarization status: {chat_result.get("status")}')
    if chat_result.get('status') != 'success':
        print(f'Error details: {chat_result}')
    else:
        print(f'CSV Summary: {chat_result.get("final_answer", "")[:200]}...')
    
    # Test specific CSV query
    csv_query_response = requests.post('http://localhost:8000/chat', json={
        'query': 'How many employees are in the Finance department?',
        'session_id': session_id,
        'active_document': stored_filename
    })
    csv_query_result = csv_query_response.json()
    print(f'CSV Query status: {csv_query_result.get("status")}')
    if csv_query_result.get('status') == 'success':
        print(f'CSV Query answer: {csv_query_result.get("final_answer", "")[:200]}...')
    else:
        print(f'CSV Query error: {csv_query_result}')