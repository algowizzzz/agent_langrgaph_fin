import unittest
import asyncio
import os
import json
import sys
from unittest.mock import patch, MagicMock, AsyncMock

# Add the project root for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from orchestrator import Orchestrator

class TestFixedWorkflows(unittest.TestCase):

    def setUp(self):
        self.orchestrator = Orchestrator()
        self.session_id = "test-session-fixed-workflows"
        self.test_doc_name = "integration_test_doc.txt"
        self.doc_content = """# Comprehensive Financial Report
## Section 1: Overview
This document provides a summary of the fiscal year.
## Section 2: Market Analysis
### Subsection 2.3: Risk Factors
A key risk is wrong-way risk. The primary regulatory framework is Basel III.
## Section 3: Compliance
Our firm adheres to all financial regulations. The regulatory environment is complex.
"""
        with open(self.test_doc_name, "w") as f:
            f.write(self.doc_content)
        asyncio.run(self.orchestrator.tools['upload_document']['function'](self.test_doc_name))

    def tearDown(self):
        if os.path.exists(self.test_doc_name):
            os.remove(self.test_doc_name)
        from tools.document_tools import document_chunk_store
        document_chunk_store.clear()

    @patch('orchestrator.ChatAnthropic')
    def test_query_summarize_entire_document(self, MockChatAnthropic):
        # This plan should succeed
        mock_instance = MockChatAnthropic.return_value
        mock_instance.ainvoke = AsyncMock(return_value=MagicMock(content=json.dumps({
            "plan": [
                {"thought": "Get all content.", "tool_call": {"name": "search_uploaded_docs", "params": {"doc_name": self.test_doc_name, "retrieve_full_doc": True}}},
                {"thought": "Summarize it.", "tool_call": {"name": "synthesize_content", "params": {"chunks": "PREVIOUS_STEP_OUTPUT", "method": "map_reduce", "length": "one-paragraph summary"}}}
            ]
        })))
        
        orchestrator = Orchestrator()
        result = asyncio.run(orchestrator.run("Summarize the document", self.session_id))
        self.assertEqual(result['status'], 'success')
        self.assertIn("fiscal year", result['final_answer'].lower())
        mock_instance.ainvoke.assert_called_once()

    @patch('orchestrator.ChatAnthropic')
    def test_query_search_and_summarize_section(self, MockChatAnthropic):
        # This plan should also succeed now
        mock_instance = MockChatAnthropic.return_value
        mock_instance.ainvoke = AsyncMock(return_value=MagicMock(content=json.dumps({
            "plan": [
                {"thought": "Find section 2.3.", "tool_call": {"name": "search_uploaded_docs", "params": {"doc_name": self.test_doc_name, "filter_by_metadata": {"Header 3": "Subsection 2.3: Risk Factors"}}}},
                {"thought": "Summarize risk factors.", "tool_call": {"name": "synthesize_content", "params": {"chunks": "PREVIOUS_STEP_OUTPUT", "method": "simple_llm_call", "length": "a short summary"}}}
            ]
        })))

        orchestrator = Orchestrator()
        result = asyncio.run(orchestrator.run("Summarize section 2.3", self.session_id))

        self.assertEqual(result['status'], 'success')
        self.assertIn("wrong-way risk", result['final_answer'].lower())
        mock_instance.ainvoke.assert_called_once()

    @patch('orchestrator.ChatAnthropic')
    def test_query_keyword_search(self, MockChatAnthropic):
        # This plan should succeed
        mock_instance = MockChatAnthropic.return_value
        mock_instance.ainvoke = AsyncMock(return_value=MagicMock(content=json.dumps({
            "plan": [
                {"thought": "Search for 'regulatory'.", "tool_call": {"name": "search_uploaded_docs", "params": {"doc_name": self.test_doc_name, "query": "regulatory"}}},
                {"thought": "List the results.", "tool_call": {"name": "synthesize_content", "params": {"chunks": "PREVIOUS_STEP_OUTPUT", "method": "simple_llm_call", "length": "a list of excerpts"}}}
            ]
        })))

        orchestrator = Orchestrator()
        result = asyncio.run(orchestrator.run("Find all mentions of 'regulatory'", self.session_id))
        
        self.assertEqual(result['status'], 'success')
        self.assertIn("regulatory framework", result['final_answer'].lower())
        mock_instance.ainvoke.assert_called_once()

    @patch('orchestrator.ChatAnthropic')
    def test_failed_plan_returns_error_object(self, MockChatAnthropic):
        # This plan is designed to fail to test the new error handling
        mock_instance = MockChatAnthropic.return_value
        mock_instance.ainvoke = AsyncMock(return_value=MagicMock(content=json.dumps({
            "plan": [
                {"thought": "This is a bad plan.", "tool_call": {"name": "non_existent_tool", "params": {}}}
            ]
        })))

        orchestrator = Orchestrator()
        result = asyncio.run(orchestrator.run("Execute a failing plan", self.session_id))
        
        self.assertEqual(result['status'], 'error')
        self.assertIn("Tool 'non_existent_tool' not found", result['final_answer'])
        mock_instance.ainvoke.assert_called_once()


if __name__ == '__main__':
    unittest.main()
