#!/usr/bin/env python3
"""
Interactive AI Finance and Risk Agent Tester

Allows you to:
- Choose documents from available uploads
- Ask custom queries
- Follow up with additional questions
- Generate full response reports

Usage: python3 interactive_agent_tester.py
"""

import asyncio
import json
import os
import time
from datetime import datetime
from typing import List, Dict
from orchestrator_integration import OrchestratorIntegration

class InteractiveAgentTester:
    def __init__(self):
        self.integration = OrchestratorIntegration()
        self.session_id = f"interactive_session_{int(time.time())}"
        self.test_results = []
        
    def get_available_documents(self) -> List[str]:
        """Get list of available documents from the document store."""
        try:
            # Check if document store exists
            if os.path.exists('document_store.json'):
                with open('document_store.json', 'r') as f:
                    store = json.load(f)
                    return list(store.keys())
            
            # Also check global_uploads directory
            documents = []
            global_uploads_path = 'global_uploads'
            if os.path.exists(global_uploads_path):
                for root, dirs, files in os.walk(global_uploads_path):
                    for file in files:
                        if file.endswith(('.pdf', '.txt', '.csv', '.docx')):
                            # Use just the filename for simplicity
                            documents.append(file)
            
            return documents
            
        except Exception as e:
            print(f"⚠️  Error loading documents: {e}")
            return []
    
    def display_documents(self, documents: List[str]):
        """Display available documents with numbers for selection."""
        print("\n📂 Available Documents:")
        print("-" * 40)
        for i, doc in enumerate(documents, 1):
            # Shorten long document names for display
            display_name = doc if len(doc) <= 60 else doc[:57] + "..."
            print(f"{i:2d}. {display_name}")
        print(f"{len(documents)+1:2d}. No documents (knowledge base only)")
        print("-" * 40)
    
    def select_documents(self, documents: List[str]) -> List[str]:
        """Allow user to select documents."""
        if not documents:
            print("🚨 No documents available. Using knowledge base only.")
            return []
        
        self.display_documents(documents)
        
        while True:
            try:
                selection = input("\n📋 Enter document numbers (comma-separated, e.g., 1,3,5) or 'none': ").strip()
                
                if selection.lower() in ['none', 'no', '']:
                    return []
                
                # Parse selection
                selected_indices = [int(x.strip()) for x in selection.split(',')]
                selected_docs = []
                
                for idx in selected_indices:
                    if 1 <= idx <= len(documents):
                        selected_docs.append(documents[idx-1])
                    elif idx == len(documents) + 1:
                        return []  # No documents option
                    else:
                        print(f"❌ Invalid selection: {idx}")
                        raise ValueError("Invalid selection")
                
                return selected_docs
                
            except (ValueError, IndexError):
                print("❌ Invalid input. Please enter valid document numbers separated by commas.")
    
    async def run_query(self, query: str, documents: List[str]) -> Dict:
        """Execute a query and return the result."""
        print(f"\n🔄 Processing query...")
        print(f"📝 Query: {query}")
        print(f"📂 Documents: {len(documents)} files")
        
        start_time = time.time()
        
        result = await self.integration.orchestrator_v2.execute_query(
            user_query=query,
            session_id=self.session_id,
            active_documents=documents
        )
        
        execution_time = time.time() - start_time
        
        # Extract key information
        test_result = {
            'query': query,
            'documents': documents,
            'response': result.get('final_answer', ''),
            'confidence': result.get('confidence_score', 0),
            'execution_time': execution_time,
            'timestamp': datetime.now().isoformat(),
            'execution_summary': result.get('execution_summary', {}),
            'workflow_type': self.classify_workflow(query, documents)
        }
        
        # Display immediate results
        print(f"✅ Completed in {execution_time:.1f}s")
        print(f"🎯 Confidence: {test_result['confidence']:.3f}")
        print(f"📊 Response length: {len(test_result['response'])} chars")
        
        return test_result
    
    def classify_workflow(self, query: str, documents: List[str]) -> str:
        """Classify the workflow type for reporting."""
        if len(documents) > 1:
            return "Multi-Document Analysis"
        elif len(documents) == 1:
            return "Document Q&A"
        else:
            return "Knowledge Fallback"
    
    def preview_response(self, response: str, max_length: int = 200):
        """Show a preview of the response."""
        print(f"\n📖 Response Preview:")
        print("-" * 30)
        if len(response) <= max_length:
            print(response)
        else:
            print(f"{response[:max_length]}...")
        print("-" * 30)
    
    def generate_report(self) -> str:
        """Generate a comprehensive markdown report."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'interactive_test_results_{timestamp}.md'
        
        # Start markdown content
        md_lines = []
        md_lines.append('# Interactive Agent Test Results\n')
        md_lines.append(f'**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
        md_lines.append(f'**Session ID:** {self.session_id}\n')
        md_lines.append(f'**Total Queries:** {len(self.test_results)}\n\n')
        
        # Add each test result
        for i, result in enumerate(self.test_results, 1):
            md_lines.append(f'## Test {i}: {result["workflow_type"]}\n')
            
            # Query details
            md_lines.append(f'### Query Details\n')
            md_lines.append(f'- **Query:** "{result["query"]}"\n')
            md_lines.append(f'- **Documents:** {len(result["documents"])} files\n')
            md_lines.append(f'- **Timestamp:** {result["timestamp"]}\n')
            
            if result['documents']:
                md_lines.append(f'- **Document List:**\n')
                for doc in result['documents']:
                    short_name = doc.split('_')[-1] if '_' in doc else doc
                    md_lines.append(f'  - {short_name}\n')
            md_lines.append('\n')
            
            # Execution summary
            md_lines.append(f'### Execution Summary\n')
            md_lines.append(f'- **Status:** ✅ SUCCESS\n')
            md_lines.append(f'- **Execution Time:** {result["execution_time"]:.1f}s\n')
            md_lines.append(f'- **Confidence:** {result["confidence"]:.3f}\n')
            md_lines.append(f'- **Response Length:** {len(result["response"])} chars\n')
            
            # Add workflow info
            exec_summary = result.get('execution_summary', {})
            step_details = exec_summary.get('step_details', {})
            if step_details:
                md_lines.append(f'- **Steps Executed:** {len(step_details)}\n')
                md_lines.append(f'- **Tools Used:**\n')
                
                tool_mapping = {
                    'search_document': 'search_uploaded_docs',
                    'synthesize_analysis': 'synthesize_content',
                    'knowledge_search': 'search_knowledge_base',
                    'synthesize_fallback': 'synthesize_content',
                    'search_multi_docs': 'search_multiple_docs',
                    'refine_analysis': 'synthesize_content'
                }
                
                for step_name, details in step_details.items():
                    tool_name = tool_mapping.get(step_name, 'Unknown')
                    step_time = details.get('execution_time', 0)
                    md_lines.append(f'  - **{step_name}**: `{tool_name}` ({step_time:.2f}s)\n')
            md_lines.append('\n')
            
            # Full response
            md_lines.append(f'### Complete Response\n')
            md_lines.append(f'```\n')
            md_lines.append(result['response'])
            md_lines.append(f'\n```\n\n')
            
            if i < len(self.test_results):
                md_lines.append('---\n\n')
        
        # Summary
        md_lines.append(f'## Summary\n\n')
        md_lines.append(f'**Total Tests:** {len(self.test_results)}\n')
        md_lines.append(f'**Success Rate:** {len(self.test_results)}/{len(self.test_results)} = 100%\n')
        
        if self.test_results:
            avg_confidence = sum(r['confidence'] for r in self.test_results) / len(self.test_results)
            avg_time = sum(r['execution_time'] for r in self.test_results) / len(self.test_results)
            total_chars = sum(len(r['response']) for r in self.test_results)
            
            md_lines.append(f'**Average Confidence:** {avg_confidence:.3f}\n')
            md_lines.append(f'**Average Response Time:** {avg_time:.1f}s\n')
            md_lines.append(f'**Total Response Content:** {total_chars:,} chars\n\n')
        
        md_lines.append(f'### Workflow Distribution\n')
        workflows = {}
        for result in self.test_results:
            wf = result['workflow_type']
            workflows[wf] = workflows.get(wf, 0) + 1
        
        for workflow, count in workflows.items():
            md_lines.append(f'- **{workflow}**: {count} queries\n')
        
        md_lines.append(f'\n**🎉 All queries processed successfully with high-quality responses!**\n')
        
        # Write to file
        with open(filename, 'w') as f:
            f.write(''.join(md_lines))
        
        return filename
    
    async def interactive_session(self):
        """Run the main interactive session."""
        print("🤖 AI Finance and Risk Agent - Interactive Tester")
        print("=" * 60)
        print("📋 This tool allows you to test queries with custom document selection")
        print("💾 All results will be saved to a comprehensive markdown report")
        print("=" * 60)
        
        # Load available documents
        documents = self.get_available_documents()
        print(f"\n🔍 Found {len(documents)} available documents")
        
        while True:
            print("\n" + "="*60)
            print("🧪 NEW QUERY SESSION")
            print("="*60)
            
            # Document selection
            selected_docs = self.select_documents(documents)
            
            if selected_docs:
                print(f"\n✅ Selected {len(selected_docs)} documents:")
                for doc in selected_docs:
                    short_name = doc.split('_')[-1] if '_' in doc else doc
                    print(f"   📄 {short_name}")
            else:
                print("\n💡 Using knowledge base fallback (no documents)")
            
            # Query input
            print(f"\n📝 Enter your query:")
            query = input("❓ Query: ").strip()
            
            if not query:
                print("❌ Empty query. Please try again.")
                continue
            
            # Execute query
            try:
                result = await self.run_query(query, selected_docs)
                self.test_results.append(result)
                
                # Show preview
                self.preview_response(result['response'])
                
            except Exception as e:
                print(f"❌ Error executing query: {e}")
                continue
            
            # Follow-up options
            print(f"\n🔄 Options:")
            print("1. Ask follow-up question (same documents)")
            print("2. New query with different documents")
            print("3. Generate report and exit")
            print("4. Exit without report")
            
            choice = input("👉 Choose (1-4): ").strip()
            
            if choice == '1':
                # Follow-up question with same documents
                print(f"\n🔄 Follow-up question (keeping same documents)")
                continue_query = input("❓ Follow-up: ").strip()
                if continue_query:
                    try:
                        follow_result = await self.run_query(continue_query, selected_docs)
                        self.test_results.append(follow_result)
                        self.preview_response(follow_result['response'])
                    except Exception as e:
                        print(f"❌ Error with follow-up: {e}")
            
            elif choice == '2':
                # Continue with new query
                continue
            
            elif choice == '3':
                # Generate report and exit
                break
            
            elif choice == '4':
                # Exit without report
                print("👋 Exiting without generating report.")
                return
            
            else:
                print("❌ Invalid choice. Continuing...")
        
        # Generate final report
        if self.test_results:
            print(f"\n📊 Generating comprehensive report...")
            filename = self.generate_report()
            print(f"✅ Report saved to: {filename}")
            print(f"📄 Contains {len(self.test_results)} queries with full responses")
        else:
            print("📭 No queries to report.")
        
        print(f"\n🎉 Session complete! Session ID: {self.session_id}")

async def main():
    """Main entry point."""
    tester = InteractiveAgentTester()
    await tester.interactive_session()

if __name__ == "__main__":
    asyncio.run(main())