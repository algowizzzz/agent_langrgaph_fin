#!/usr/bin/env python3
"""
Individual Tool Testing Suite
Tests each tool component separately with detailed validation
"""

import asyncio
import tempfile
import os

# Import tools to test
from tools.document_tools import upload_document, search_uploaded_docs
from tools.code_execution_tools import execute_python_code, process_table_data, calculate_statistics
from tools.visualization_tools import create_chart, create_wordcloud, create_statistical_plot, create_comparison_chart
from tools.text_analytics_tools import analyze_text_metrics, extract_key_phrases, analyze_sentiment, extract_entities

async def test_tools():
    """Test individual tools"""
    print("🔧 INDIVIDUAL TOOL TESTING")
    print("=" * 40)
    
    # Test Python execution
    print("\n🐍 Testing Python Code Execution")
    code = """
import numpy as np
numbers = [1, 2, 3, 4, 5]
result = {
    'sum': sum(numbers),
    'mean': np.mean(numbers),
    'count': len(numbers)
}
print(f"Sum: {result['sum']}, Mean: {result['mean']}")
"""
    
    try:
        exec_result = await execute_python_code(code)
        if exec_result.get('status') == 'success':
            print("✅ Python execution: SUCCESS")
            print(f"   Output: {exec_result.get('output', '')}")
        else:
            print("❌ Python execution: FAILED")
            print(f"   Error: {exec_result.get('error', '')}")
    except Exception as e:
        print(f"❌ Python execution: ERROR - {e}")
    
    # Test visualization
    print("\n📊 Testing Chart Creation")
    chart_data = {
        'x': ['A', 'B', 'C', 'D'],
        'y': [10, 20, 15, 25]
    }
    
    try:
        chart_result = await create_chart(chart_data, 'bar', 'Test Chart')
        if chart_result.get('status') == 'success':
            print("✅ Chart creation: SUCCESS")
            print(f"   Image size: {len(chart_result.get('image_base64', ''))} chars")
        else:
            print("❌ Chart creation: FAILED")
            print(f"   Error: {chart_result.get('error', '')}")
    except Exception as e:
        print(f"❌ Chart creation: ERROR - {e}")
    
    # Test word cloud
    print("\n☁️ Testing Word Cloud")
    text = "finance risk management banking regulatory compliance capital audit governance"
    
    try:
        wc_result = await create_wordcloud(text, max_words=10)
        if wc_result.get('status') == 'success':
            print("✅ Word cloud: SUCCESS")
            print(f"   Words: {wc_result.get('word_count', 0)}")
        else:
            print("❌ Word cloud: FAILED")
            print(f"   Error: {wc_result.get('error', '')}")
    except Exception as e:
        print(f"❌ Word cloud: ERROR - {e}")
    
    # Test text analytics
    print("\n📝 Testing Text Analytics")
    sample_text = "This is a financial report with positive outcomes and great results."
    
    try:
        metrics_result = await analyze_text_metrics(sample_text)
        if metrics_result.get('status') == 'success':
            print("✅ Text metrics: SUCCESS")
            print(f"   Word count: {metrics_result.get('basic_metrics', {}).get('word_count', 0)}")
        else:
            print("❌ Text metrics: FAILED")
    except Exception as e:
        print(f"❌ Text metrics: ERROR - {e}")
    
    try:
        sentiment_result = await analyze_sentiment(sample_text)
        if sentiment_result.get('status') == 'success':
            print("✅ Sentiment analysis: SUCCESS")
            print(f"   Sentiment: {sentiment_result.get('sentiment_label', 'unknown')}")
        else:
            print("❌ Sentiment analysis: FAILED")
    except Exception as e:
        print(f"❌ Sentiment analysis: ERROR - {e}")

if __name__ == "__main__":
    asyncio.run(test_tools())