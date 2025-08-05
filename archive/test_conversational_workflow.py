#!/usr/bin/env python3
"""
Test Conversational CSV Workflow
Tests the complete workflow as follow-up questions in a conversation:
1. Upload CSV and summarize data
2. Do calculations (follow-up)
3. Create visualization (follow-up)
4. Identify insights (follow-up)
"""

import asyncio
import tempfile
import os
import time

from orchestrator_integration import OrchestratorIntegration
from tools.document_tools import upload_document

class ConversationalWorkflowTester:
    def __init__(self):
        self.integration = OrchestratorIntegration(enable_v2=True, fallback_to_v1=True)
        self.session_id = f"conversational_workflow_{int(time.time())}"
        self.conversation_log = []
        
    def log_interaction(self, step: int, question: str, response: dict):
        """Log each conversation step"""
        interaction = {
            "step": step,
            "question": question,
            "status": response.get('status'),
            "version": response.get('orchestrator_version', 'unknown'),
            "confidence": response.get('confidence_score', 0),
            "answer_preview": response.get('final_answer', '')[:200] + '...',
            "timestamp": time.time()
        }
        self.conversation_log.append(interaction)
        
        status_emoji = "✅" if response.get('status') == 'success' else "❌"
        print(f"{status_emoji} Step {step}: {response.get('status', 'unknown').upper()}")
        print(f"   🤖 Version: {response.get('orchestrator_version', 'unknown')}")
        print(f"   🎯 Confidence: {response.get('confidence_score', 0):.2f}")
        print(f"   📝 Response: {response.get('final_answer', '')[:150]}...")
        print()
    
    async def create_test_data(self):
        """Create realistic employee salary CSV"""
        csv_content = """employee_id,name,department,salary,experience_years,performance_rating,join_date
001,John Smith,Sales,52000,3,4.2,2021-03-15
002,Jane Doe,Sales,48000,2,4.5,2022-01-10
003,Bob Wilson,Marketing,55000,4,4.0,2020-06-20
004,Alice Brown,Marketing,60000,5,4.3,2019-11-05
005,Charlie Davis,IT,75000,6,4.8,2018-08-12
006,Diana Miller,IT,70000,4,4.6,2020-02-28
007,Eve Johnson,IT,78000,7,4.9,2017-05-14
008,Frank Wilson,Finance,62000,4,4.1,2020-09-30
009,Grace Taylor,Finance,58000,3,4.4,2021-07-18
010,Henry Clark,HR,50000,3,3.9,2021-12-01
011,Ivy Martinez,Sales,51000,3,4.3,2021-04-22
012,Jack Anderson,Marketing,57000,4,4.2,2020-10-15
013,Kate Thompson,IT,72000,5,4.7,2019-03-08
014,Leo Garcia,Finance,65000,5,4.5,2019-01-20
015,Mia Rodriguez,HR,52000,4,4.1,2020-07-25"""

        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        temp_file.write(csv_content)
        temp_file.close()
        
        print(f"📄 Created employee salary dataset: {os.path.basename(temp_file.name)}")
        print("📊 Dataset contains: 15 employees across 5 departments")
        print("💰 Salary range: $48K - $78K")
        print()
        
        return temp_file.name

    async def run_conversational_test(self):
        """Run the conversational workflow test"""
        print("🗣️ CONVERSATIONAL CSV WORKFLOW TEST")
        print("=" * 60)
        print("Testing: Upload → Summarize → Calculate → Visualize → Insights")
        print("=" * 60)
        
        # Create and upload test data
        csv_file = await self.create_test_data()
        
        try:
            # Upload the CSV file
            print("📤 Uploading CSV file...")
            upload_result = await upload_document(csv_file, self.session_id)
            
            if upload_result.get('status') != 'success':
                print(f"❌ Upload failed: {upload_result}")
                return
                
            doc_name = upload_result.get('doc_name')
            print(f"✅ File uploaded as: {doc_name}")
            print()
            
            # Define the conversational flow
            conversation_steps = [
                {
                    "step": 1,
                    "question": f"I've uploaded employee salary data in {doc_name}. Please summarize what data we have - how many employees, what departments, salary ranges, etc.",
                    "description": "Initial data summary",
                    "expected": "Data overview and basic statistics"
                },
                {
                    "step": 2,
                    "question": "Now calculate the average salary by department and also show me the overall statistics like mean, median, and standard deviation for all salaries.",
                    "description": "Follow-up calculation request",
                    "expected": "Department averages and statistical calculations"
                },
                {
                    "step": 3,  
                    "question": "Great! Now create a bar chart showing the average salary by department, and also make a box plot showing the salary distribution.",
                    "description": "Follow-up visualization request",
                    "expected": "Charts and visual representations"
                },
                {
                    "step": 4,
                    "question": "Based on all this analysis, what insights can you identify? Which department pays the most? Are there any patterns with experience and performance ratings?",
                    "description": "Follow-up insights request", 
                    "expected": "Business insights and patterns"
                }
            ]
            
            # Execute conversational flow
            for step_info in conversation_steps:
                step_num = step_info["step"]
                question = step_info["question"]
                description = step_info["description"]
                
                print(f"🔄 STEP {step_num}: {description}")
                print(f"❓ User: {question}")
                print("⏳ Processing...")
                
                try:
                    # Send question to orchestrator (same session for continuity)
                    result = await self.integration.run(
                        user_query=question,
                        session_id=self.session_id,  # Same session for memory
                        active_documents=[doc_name]
                    )
                    
                    self.log_interaction(step_num, question, result)
                    
                except Exception as e:
                    print(f"❌ STEP {step_num} ERROR: {str(e)}")
                    self.log_interaction(step_num, question, {
                        "status": "error", 
                        "error": str(e),
                        "final_answer": f"Error: {str(e)}"
                    })
                
                # Brief pause between questions (simulate natural conversation)
                print("⏸️  Pausing before next question...")
                await asyncio.sleep(3)
                print()
            
            self.print_conversation_summary()
            
        finally:
            # Cleanup
            try:
                os.unlink(csv_file)
            except:
                pass
    
    def print_conversation_summary(self):
        """Print summary of the conversational test"""
        print("=" * 60)
        print("📋 CONVERSATIONAL WORKFLOW SUMMARY")
        print("=" * 60)
        
        total_steps = len(self.conversation_log)
        successful_steps = len([log for log in self.conversation_log if log['status'] == 'success'])
        
        print(f"🎯 Total Conversation Steps: {total_steps}")
        print(f"✅ Successful Steps: {successful_steps}/{total_steps}")
        print(f"📊 Success Rate: {successful_steps/total_steps*100:.1f}%")
        
        # Calculate response times
        if len(self.conversation_log) > 1:
            response_times = []
            for i in range(1, len(self.conversation_log)):
                time_diff = self.conversation_log[i]['timestamp'] - self.conversation_log[i-1]['timestamp']
                response_times.append(time_diff)
            
            avg_response_time = sum(response_times) / len(response_times)
            print(f"⏱️  Average Response Time: {avg_response_time:.1f} seconds")
        
        # Version usage
        v2_usage = len([log for log in self.conversation_log if log['version'] == '2.0'])
        v1_usage = len([log for log in self.conversation_log if log['version'] == '1.0'])
        
        print(f"🆕 Orchestrator 2.0 Usage: {v2_usage}/{total_steps} ({v2_usage/total_steps*100:.1f}%)")
        print(f"🔄 Orchestrator 1.0 Fallback: {v1_usage}/{total_steps} ({v1_usage/total_steps*100:.1f}%)")
        
        # Average confidence
        confidences = [log['confidence'] for log in self.conversation_log if log['confidence'] > 0]
        if confidences:
            avg_confidence = sum(confidences) / len(confidences)
            print(f"🎯 Average Confidence: {avg_confidence:.2f}")
        
        print("\n📝 Step-by-Step Results:")
        for log in self.conversation_log:
            status_icon = "✅" if log['status'] == 'success' else "❌"
            print(f"{status_icon} Step {log['step']}: {log['status'].upper()} (v{log['version']}, {log['confidence']:.2f})")
        
        if successful_steps == total_steps:
            print("\n🎉 COMPLETE SUCCESS! All conversational steps worked perfectly.")
            print("✨ The system maintained context across the entire conversation.")
        elif successful_steps >= total_steps * 0.75:
            print(f"\n🟡 MOSTLY SUCCESSFUL! {successful_steps}/{total_steps} steps worked.")
            print("💡 System demonstrates good conversational capabilities.")
        else:
            print(f"\n🔴 NEEDS WORK! Only {successful_steps}/{total_steps} steps succeeded.")
            print("⚠️  Conversational flow needs improvement.")
        
        print("\n🎯 KEY WORKFLOW CAPABILITIES TESTED:")
        print("  📊 Data summarization from uploaded CSV")
        print("  🧮 Statistical calculations and analysis") 
        print("  📈 Chart and visualization generation")
        print("  🔍 Business insight identification")
        print("  🧠 Conversational memory and context")

async def main():
    """Run the conversational workflow test"""
    tester = ConversationalWorkflowTester()
    await tester.run_conversational_test()

if __name__ == "__main__":
    asyncio.run(main())