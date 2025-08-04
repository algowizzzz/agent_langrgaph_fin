#!/usr/bin/env python3
"""
Orchestrator V2 Coverage Test - No Fallback
Test all untested tools with V2 orchestrator exclusively
"""

import asyncio
import logging
import time
import json
from datetime import datetime
from pathlib import Path
from orchestrator_v2.orchestrator_v2 import OrchestratorV2, OrchestratorConfig

# Configure logging to capture detailed execution
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class V2CoverageTestLogger:
    """Custom logger to capture all test results and logs"""
    
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.test_start = datetime.now()
        self.logs = []
        self.results = []
        
        # Setup file handlers
        timestamp = self.test_start.strftime("%Y%m%d_%H%M%S")
        self.log_file = self.output_dir / f"v2_coverage_test_log_{timestamp}.txt"
        self.results_file = self.output_dir / f"v2_coverage_results_{timestamp}.md"
        
    def log(self, message: str, level: str = "INFO"):
        """Log a message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        self.logs.append(log_entry)
        print(log_entry)
        
        # Write to file immediately
        with open(self.log_file, 'a') as f:
            f.write(log_entry + "\n")
    
    def log_test_result(self, test_name: str, query: str, result: dict, execution_time: float):
        """Log a test result"""
        test_result = {
            "test_name": test_name,
            "query": query,
            "status": result.get('status', 'unknown'),
            "confidence": result.get('confidence_score', 0.0),
            "execution_time": execution_time,
            "tools_used": [],
            "success": result.get('status') == 'success',
            "response_preview": str(result.get('final_answer', ''))[:200] + "..."
        }
        
        # Extract tools used from traceability log
        if result.get('traceability_log') and result['traceability_log'].get('steps'):
            test_result['tools_used'] = [
                step.get('tool_used', 'unknown') 
                for step in result['traceability_log']['steps']
                if step.get('tool_used')
            ]
        
        self.results.append(test_result)
        return test_result
    
    def generate_final_report(self):
        """Generate final markdown report"""
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r['success'])
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Count unique tools tested
        all_tools_used = set()
        for result in self.results:
            all_tools_used.update(result['tools_used'])
        
        report = f"""# Orchestrator V2 Coverage Test Results

**Test Date:** {self.test_start.strftime("%Y-%m-%d %H:%M:%S")}
**Test Duration:** {(datetime.now() - self.test_start).total_seconds():.2f} seconds

## 📊 Summary

- **Total Tests:** {total_tests}
- **Successful:** {successful_tests}
- **Failed:** {total_tests - successful_tests}
- **Success Rate:** {success_rate:.1f}%
- **Unique Tools Tested:** {len(all_tools_used)}

### Tools Used in Testing:
{chr(10).join(f"- {tool}" for tool in sorted(all_tools_used))}

## 📋 Detailed Results

"""
        
        for i, result in enumerate(self.results, 1):
            report += f"""### Test {i}: {result['test_name']}

**Query:** `{result['query']}`

- **Status:** {result['status']}
- **Success:** {'✅' if result['success'] else '❌'}
- **Confidence:** {result['confidence']:.2f}
- **Execution Time:** {result['execution_time']:.2f}s
- **Tools Used:** {', '.join(result['tools_used']) if result['tools_used'] else 'None detected'}

**Response Preview:**
```
{result['response_preview']}
```

---

"""
        
        # Tool coverage analysis
        target_tools = [
            'extract_key_phrases', 'extract_entities', 'analyze_sentiment', 'analyze_text_metrics',
            'create_wordcloud', 'create_chart', 'create_statistical_plot', 'create_comparison_chart',
            'execute_python_code', 'process_table_data', 'calculate_statistics',
            'search_conversation_history', 'search_knowledge_base', 'search_multiple_docs'
        ]
        
        tested_target_tools = all_tools_used.intersection(set(target_tools))
        untested_target_tools = set(target_tools) - all_tools_used
        
        report += f"""## 🎯 Tool Coverage Analysis

**Target Tools for Testing:** {len(target_tools)}
**Successfully Tested:** {len(tested_target_tools)}
**Still Untested:** {len(untested_target_tools)}

### ✅ Successfully Tested Tools:
{chr(10).join(f"- {tool}" for tool in sorted(tested_target_tools))}

### ❌ Still Untested Tools:
{chr(10).join(f"- {tool}" for tool in sorted(untested_target_tools))}

## 📈 Recommendations

{'✅ **EXCELLENT:** All target tools have been tested!' if len(untested_target_tools) == 0 else f'⚠️ **NEEDS IMPROVEMENT:** {len(untested_target_tools)} tools still need testing.'}

**Coverage Rate:** {len(tested_target_tools) / len(target_tools) * 100:.1f}%
"""
        
        # Write report to file
        with open(self.results_file, 'w') as f:
            f.write(report)
        
        return report

async def run_v2_coverage_test():
    """Run comprehensive V2 coverage test"""
    
    logger = V2CoverageTestLogger("output")
    logger.log("🚀 Starting Orchestrator V2 Coverage Test (No Fallback)", "INFO")
    
    # Configure V2 with no fallback
    config = OrchestratorConfig()
    config.enable_streaming = True
    config.max_parallel_steps = 5  # Allow more parallel execution
    
    logger.log(f"📊 V2 Configuration: max_parallel={config.max_parallel_steps}", "INFO")
    
    try:
        # Initialize V2 orchestrator
        orchestrator = OrchestratorV2(config)
        logger.log("✅ Orchestrator V2 initialized successfully", "INFO")
        
        # Test cases targeting untested tools
        test_cases = [
            {
                "name": "Text Analytics - Key Phrases",
                "query": "Extract key phrases and important terms from any documents in the system. Show me the most significant terminology.",
                "target_tools": ["extract_key_phrases", "search_uploaded_docs"]
            },
            {
                "name": "Text Analytics - Entity Extraction", 
                "query": "Find and extract all named entities (people, places, dates, organizations) from available documents.",
                "target_tools": ["extract_entities", "search_uploaded_docs"]
            },
            {
                "name": "Text Analytics - Sentiment Analysis",
                "query": "Analyze the sentiment and emotional tone of the document content. Is it positive, negative, or neutral?",
                "target_tools": ["analyze_sentiment", "search_uploaded_docs"]
            },
            {
                "name": "Text Analytics - Text Metrics",
                "query": "Calculate detailed text statistics and readability metrics for the documents including word count, complexity scores.",
                "target_tools": ["analyze_text_metrics", "search_uploaded_docs"]
            },
            {
                "name": "Visualization - Word Cloud",
                "query": "Create a word cloud visualization showing the most frequent terms in the documents.",
                "target_tools": ["create_wordcloud", "search_uploaded_docs"]
            },
            {
                "name": "Visualization - Statistical Chart",
                "query": "Create statistical charts showing document metrics and analysis results.",
                "target_tools": ["create_statistical_plot", "analyze_text_metrics"]
            },
            {
                "name": "Computation - Python Code",
                "query": "Calculate the total number of pages across all uploaded documents using Python code.",
                "target_tools": ["execute_python_code", "search_uploaded_docs"]
            },
            {
                "name": "Computation - Statistics",
                "query": "Calculate statistical measures (mean, median, std dev) for document word counts and lengths.",
                "target_tools": ["calculate_statistics", "analyze_text_metrics"]
            },
            {
                "name": "Memory - Conversation History",
                "query": "Search through our conversation history to find previous document analysis discussions.",
                "target_tools": ["search_conversation_history"]
            },
            {
                "name": "Memory - Knowledge Base",
                "query": "Search the knowledge base for information about document analysis best practices and methodologies.",
                "target_tools": ["search_knowledge_base"]
            },
            {
                "name": "Multi-Document - Comparison",
                "query": "Compare content across multiple uploaded documents and identify common themes and differences.",
                "target_tools": ["search_multiple_docs", "synthesize_content"]
            },
            {
                "name": "Visualization - Comparison Chart",
                "query": "Create comparison charts showing differences between documents in terms of length, complexity, and key topics.",
                "target_tools": ["create_comparison_chart", "search_multiple_docs"]
            }
        ]
        
        logger.log(f"📋 Testing {len(test_cases)} scenarios covering 15 target tools", "INFO")
        
        # Execute test cases
        for i, test_case in enumerate(test_cases, 1):
            logger.log(f"\n{'='*60}", "INFO")
            logger.log(f"🧪 Test {i}/{len(test_cases)}: {test_case['name']}", "INFO")
            logger.log(f"🎯 Target Tools: {', '.join(test_case['target_tools'])}", "INFO")
            logger.log(f"❓ Query: {test_case['query']}", "INFO")
            
            try:
                start_time = time.time()
                
                # Execute query with V2 orchestrator
                result = await orchestrator.execute_query(
                    user_query=test_case['query'],
                    session_id=f"v2_coverage_test_{i:03d}"
                )
                
                execution_time = time.time() - start_time
                
                # Log result
                test_result = logger.log_test_result(
                    test_case['name'], 
                    test_case['query'], 
                    result, 
                    execution_time
                )
                
                status_emoji = "✅" if test_result['success'] else "❌"
                logger.log(f"{status_emoji} Result: {test_result['status']} | Confidence: {test_result['confidence']:.2f} | Time: {execution_time:.2f}s", "INFO")
                
                if test_result['tools_used']:
                    logger.log(f"🔧 Tools Used: {', '.join(test_result['tools_used'])}", "INFO")
                else:
                    logger.log("⚠️ No tools detected in execution trace", "WARN")
                
            except Exception as e:
                logger.log(f"❌ Test failed with exception: {str(e)}", "ERROR")
                # Log as failed test
                logger.log_test_result(
                    test_case['name'],
                    test_case['query'],
                    {"status": "error", "final_answer": f"Exception: {str(e)}"},
                    0.0
                )
            
            # Small delay between tests
            await asyncio.sleep(1)
        
        logger.log(f"\n{'='*60}", "INFO")
        logger.log("📈 Generating final coverage report...", "INFO")
        
        # Generate final report
        final_report = logger.generate_final_report()
        logger.log("✅ Final coverage report generated", "INFO")
        logger.log(f"📄 Report saved to: {logger.results_file}", "INFO")
        logger.log(f"📝 Logs saved to: {logger.log_file}", "INFO")
        
        print("\n" + "="*80)
        print("📊 FINAL REPORT PREVIEW")
        print("="*80)
        print(final_report[:1000] + "...")
        print("="*80)
        
    except Exception as e:
        logger.log(f"💥 CRITICAL ERROR: {str(e)}", "ERROR")
        import traceback
        logger.log(f"Traceback: {traceback.format_exc()}", "ERROR")

if __name__ == "__main__":
    asyncio.run(run_v2_coverage_test())