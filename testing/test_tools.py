# This file will contain unit tests for each individual tool.
# This ensures that each component of our agent works correctly in isolation.
import unittest
import asyncio
import os

from tools.document_tools import upload_document, discover_document_structure, search_uploaded_docs
from tools.synthesis_tools import synthesize_content

class TestAgentTools(unittest.TestCase):

    def setUp(self):
        """Set up a test document for each test case."""
        self.test_doc_name = "unit_test_doc.txt"
        with open(self.test_doc_name, "w") as f:
            f.write("# Title\n\n## Section 1\nContent for section 1.\n\n## Section 2\nContent about regulatory compliance.")

    def tearDown(self):
        """Clean up the test document."""
        if os.path.exists(self.test_doc_name):
            os.remove(self.test_doc_name)

    def test_upload_document(self):
        """Tests the upload_document tool."""
        result = asyncio.run(upload_document(self.test_doc_name))
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['doc_name'], self.test_doc_name)
        self.assertGreater(result['chunks_created'], 0)

    def test_discover_document_structure(self):
        """Tests the discover_document_structure tool."""
        asyncio.run(upload_document(self.test_doc_name))
        result = asyncio.run(discover_document_structure(self.test_doc_name))
        self.assertEqual(result['status'], 'success')
        self.assertIn('Title', result['headers'])
        self.assertIn('Section 2', result['headers'])

    def test_search_uploaded_docs(self):
        """Tests the search_uploaded_docs tool."""
        asyncio.run(upload_document(self.test_doc_name))
        # Test metadata search
        result = asyncio.run(search_uploaded_docs(self.test_doc_name, filter_by_metadata={'Header 2': 'Section 2'}))
        self.assertEqual(len(result), 1)
        self.assertIn('regulatory compliance', result[0]['page_content'])
        # Test keyword search
        result_keyword = asyncio.run(search_uploaded_docs(self.test_doc_name, query='regulatory', filter_by_metadata=None))
        self.assertEqual(len(result_keyword), 1)
        self.assertIn('compliance', result_keyword[0]['page_content'])

    def test_synthesize_content(self):
        """Tests the synthesize_content tool."""
        chunks = [{"page_content": "This is a test chunk about financial regulations.", "metadata": {}}]
        result = asyncio.run(synthesize_content(chunks, method='simple_llm_call', length='summary'))
        # Check for a more realistic response from the live LLM
        self.assertIn("financial", result.lower())

if __name__ == '__main__':
    unittest.main()
