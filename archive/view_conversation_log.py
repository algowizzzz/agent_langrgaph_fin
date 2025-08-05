#!/usr/bin/env python3
"""
View the actual conversation log from our testing
Shows the real user queries and system responses
"""

import asyncio
import tempfile
import os
import time

from orchestrator_integration import OrchestratorIntegration
from tools.document_tools import upload_document

async def demonstrate_actual_conversation():
    """Show the actual conversation that would happen in the UI"""
    
    print("🎬 ACTUAL USER CONVERSATION DEMONSTRATION")
    print("=" * 60)
    print("This shows the REAL queries and responses a user would see")
    print("=" * 60)
    
    # Initialize system
    integration = OrchestratorIntegration(enable_v2=True, fallback_to_v1=True)
    session_id = f"demo_conversation_{int(time.time())}"
    
    # Create realistic dataset
    csv_content = """department,employee,salary,experience,performance
Sales,John,52000,3,4.2
Sales,Jane,48000,2,4.5
Marketing,Bob,55000,4,4.0
Marketing,Alice,60000,5,4.3
IT,Charlie,75000,6,4.8
IT,Diana,70000,4,4.6
Finance,Frank,62000,4,4.1
Finance,Grace,58000,3,4.4
HR,Henry,50000,3,3.9"""

    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
    temp_file.write(csv_content)
    temp_file.close()
    
    try:
        # Upload file
        print("📤 [SYSTEM] Uploading employee_data.csv...")
        upload_result = await upload_document(temp_file.name, session_id)
        doc_name = upload_result.get('doc_name')
        print(f"✅ [SYSTEM] File uploaded successfully as: {doc_name}")
        print()
        
        # Define the conversation
        conversation = [
            {
                "user_query": f"I just uploaded employee data in {doc_name}. Can you tell me what data we have? How many employees, what departments, salary ranges?",
                "step": 1,
                "description": "Initial data exploration"
            },
            {
                "user_query": "Now calculate the average salary for each department. Also show me some basic statistics like the overall mean and median salary.",
                "step": 2, 
                "description": "Follow-up calculation request"
            },
            {
                "user_query": "Great! Can you create a bar chart showing the department salary averages? I'd like to see this visually.",
                "step": 3,
                "description": "Follow-up visualization request"
            }
        ]
        
        # Execute each conversation step
        for conv_step in conversation:
            step_num = conv_step["step"]
            user_question = conv_step["user_query"]
            description = conv_step["description"]
            
            print(f"👤 USER (Step {step_num}): {user_question}")
            print()
            print("🤖 SYSTEM: Processing your request...")
            print("⏳ [Analyzing data, running calculations, generating visualizations...]")
            print()
            
            try:
                # Get actual system response
                result = await integration.run(
                    user_query=user_question,
                    session_id=session_id,
                    active_documents=[doc_name]
                )
                
                if result.get('status') == 'success':
                    response = result.get('final_answer', '')
                    version = result.get('orchestrator_version', 'system')
                    confidence = result.get('confidence_score', 0)
                    
                    print(f"🤖 SYSTEM RESPONSE (v{version}, confidence: {confidence:.2f}):")
                    print("-" * 50)
                    print(response)
                    print("-" * 50)
                    
                    # Check if this included visualizations
                    if any(keyword in response.lower() for keyword in ['chart', 'graph', 'plot', 'visualization', 'image']):
                        print("📊 [VISUALIZATION INCLUDED: Chart would appear here in the UI]")
                    
                    print()
                else:
                    print(f"❌ SYSTEM ERROR: {result.get('error', 'Unknown error')}")
                    print()
                    
            except Exception as e:
                print(f"❌ SYSTEM ERROR: {str(e)}")
                print()
            
            # Natural pause between questions
            print("⏸️ [User reads response, thinks, then asks follow-up...]")
            print()
            await asyncio.sleep(2)  # Brief pause for demo
        
        print("=" * 60)
        print("🎬 END OF CONVERSATION DEMONSTRATION")
        print("=" * 60)
        print("This is exactly what users would see in the web interface!")
        
    finally:
        try:
            os.unlink(temp_file.name)
        except:
            pass

async def show_sample_responses():
    """Show sample responses that users typically see"""
    
    print("\n📝 SAMPLE RESPONSE PATTERNS")
    print("=" * 50)
    
    sample_responses = {
        "Data Summary": """
Based on the uploaded CSV file, here's what we have:

📊 **Dataset Overview:**
- **Total Employees:** 9 employees
- **Departments:** 5 departments (Sales, Marketing, IT, Finance, HR)
- **Salary Range:** $48,000 - $75,000
- **Experience Range:** 2-6 years
- **Performance Ratings:** 3.9 - 4.8

📈 **Department Breakdown:**
- Sales: 2 employees
- Marketing: 2 employees  
- IT: 2 employees
- Finance: 2 employees
- HR: 1 employee

💰 **Quick Stats:**
- Average Salary: ~$58,000
- Highest Paid: IT Department
- Most Experienced: IT employees (avg 5 years)
""",
        
        "Calculations": """
Here are the salary calculations by department:

📊 **Average Salary by Department:**
- IT: $72,500 (highest)
- Marketing: $57,500
- Finance: $60,000
- Sales: $50,000
- HR: $50,000

📈 **Overall Statistics:**
- Mean Salary: $58,111
- Median Salary: $58,000
- Standard Deviation: $9,234
- Range: $27,000 ($48K - $75K)

💡 **Key Insight:** IT department pays 45% more than the lowest-paying departments.
""",

        "Visualization": """
I've created a bar chart showing the average salary by department:

📊 **Department Salary Comparison Chart**
[THIS IS WHERE THE CHART IMAGE WOULD APPEAR IN THE UI]

🎨 **Chart Details:**
- Bar chart with departments on X-axis
- Average salaries on Y-axis
- Color-coded bars for easy comparison
- Shows IT leading at $72,500
- Clear visual hierarchy of compensation

The chart clearly illustrates the salary distribution across departments, with IT showing the highest compensation levels.
"""
    }
    
    for response_type, sample in sample_responses.items():
        print(f"🔶 **{response_type} Response:**")
        print(sample)
        print()

if __name__ == "__main__":
    async def main():
        await show_sample_responses()
        await demonstrate_actual_conversation()
    
    asyncio.run(main())