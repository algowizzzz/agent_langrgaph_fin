import asyncio
import json
import logging
from typing import Dict, List, Any

from langchain_anthropic import ChatAnthropic
from tools.document_tools import upload_document, discover_document_structure, search_uploaded_docs, document_chunk_store
from tools.synthesis_tools import synthesize_content
from tools.search_tools import search_knowledge_base, search_conversation_history
from tools.code_execution_tools import execute_python_code, process_table_data, calculate_statistics
from tools.visualization_tools import create_chart, create_wordcloud, create_statistical_plot, create_comparison_chart
from tools.text_analytics_tools import analyze_text_metrics, extract_key_phrases, analyze_sentiment, extract_entities

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Orchestrator:
    def __init__(self):
        try:
            self.llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", temperature=0)
            logger.info(f"Orchestrator LLM initialized successfully: {self.llm.model}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            self.llm = None
        
        self.tools = self._load_tools()
        self.system_prompt = self._build_system_prompt()
        self.state = {"loaded_documents": {}, "conversation_history": []}
        self.reasoning_log = []

    def _load_tools(self) -> Dict[str, Any]:
        """Loads all available tools with their signatures and descriptions."""
        return {
            "upload_document": {
                "function": upload_document,
                "signature": "upload_document(file_path: str) -> dict",
                "description": "Processes a single document (PDF, DOCX, TXT, CSV) from a local file path, chunks it, and stores it in the in-memory store for the current session. Returns a confirmation message with the document name."
            },
            "discover_document_structure": {
                "function": discover_document_structure,
                "signature": "discover_document_structure(doc_name: str) -> dict",
                "description": "Scans a previously uploaded document to identify its structure, such as headers, sections, and page numbers. Returns a dictionary containing lists of headers and other metadata keys."
            },
            "search_uploaded_docs": {
                "function": search_uploaded_docs,
                "signature": "search_uploaded_docs(doc_name: str, query: str = None, filter_by_page: list[int] = None, filter_by_metadata: dict = None, retrieve_full_doc: bool = False) -> list",
                "description": "Performs a direct keyword search on the content of a specific uploaded document. Can filter results by page number or metadata (e.g., {'Header 1': 'Introduction'}). Setting retrieve_full_doc=True returns all chunks. Returns a list of matching text chunks."
            },
            "synthesize_content": {
                "function": synthesize_content,
                "signature": "synthesize_content(chunks: list, method: str, length: str, tone: str = 'professional') -> str",
                "description": "Generates a cohesive text based on a list of input chunks. The method determines the synthesis strategy ('simple_llm_call', 'refine', 'map_reduce'). Length specifies the desired output size (e.g., 'summary', 'one paragraph', 'bullet points'). Returns the synthesized text."
            },
            "search_knowledge_base": {
                "function": search_knowledge_base,
                "signature": "search_knowledge_base(query: str) -> list",
                "description": "Performs a semantic search over the long-term knowledge base. Use for general questions or to find information not present in the recently uploaded documents."
            },
            "search_conversation_history": {
                "function": search_conversation_history,
                "signature": "search_conversation_history(query: str) -> list",
                "description": "Searches the history of the current conversation to recall previous statements or results."
            },
            
            # Code Execution Tools
            "execute_python_code": {
                "function": execute_python_code,
                "signature": "execute_python_code(code: str, context: dict = None) -> dict",
                "description": "Executes Python code safely for data analysis, calculations, and processing. Supports pandas, numpy, matplotlib, and basic statistics. Returns execution results, output, and any errors."
            },
            "process_table_data": {
                "function": process_table_data,
                "signature": "process_table_data(table_data: list, operation: str, **kwargs) -> dict",
                "description": "Processes table/CSV data using pandas operations. Supports summary, aggregate, filter, and pivot operations. Input should be list of dictionaries (table rows)."
            },
            "calculate_statistics": {
                "function": calculate_statistics,
                "signature": "calculate_statistics(data: list, metrics: list = None) -> dict",
                "description": "Calculates statistical metrics (mean, median, std, min, max, quantiles) for numerical data. Useful for analyzing extracted numbers from documents."
            },
            
            # Visualization Tools
            "create_chart": {
                "function": create_chart,
                "signature": "create_chart(data: dict, chart_type: str, title: str = '', save_path: str = None, **kwargs) -> dict",
                "description": "Creates charts and graphs from data. Supports bar, line, pie, scatter, histogram charts. Data should have 'x' and 'y' keys. Returns base64 encoded image and saves to file if path provided."
            },
            "create_wordcloud": {
                "function": create_wordcloud,
                "signature": "create_wordcloud(text: str, max_words: int = 100, save_path: str = None, **kwargs) -> dict",
                "description": "Generates word clouds from text content. Great for visualizing key terms and themes in documents. Returns base64 encoded image and top words list."
            },
            "create_statistical_plot": {
                "function": create_statistical_plot,
                "signature": "create_statistical_plot(data: list, plot_type: str = 'box', title: str = '', save_path: str = None) -> dict",
                "description": "Creates statistical plots (box, distribution, violin) for numerical data analysis. Useful for visualizing data distributions from extracted tables."
            },
            "create_comparison_chart": {
                "function": create_comparison_chart,
                "signature": "create_comparison_chart(datasets: dict, chart_type: str = 'bar', title: str = '', save_path: str = None) -> dict",
                "description": "Creates comparison charts with multiple datasets. Input datasets as {name: [values]} dictionary. Supports bar and line comparison charts."
            },
            
            # Text Analytics Tools
            "analyze_text_metrics": {
                "function": analyze_text_metrics,
                "signature": "analyze_text_metrics(text: str) -> dict",
                "description": "Analyzes comprehensive text metrics including readability scores, word counts, sentence structure, and lexical diversity. Includes Flesch reading ease and other standard metrics."
            },
            "extract_key_phrases": {
                "function": extract_key_phrases,
                "signature": "extract_key_phrases(text: str, top_n: int = 10, min_length: int = 2) -> dict",
                "description": "Extracts key words, phrases, and important terms from text. Returns top words, bigrams, and trigrams with frequency counts. Useful for theme analysis."
            },
            "analyze_sentiment": {
                "function": analyze_sentiment,
                "signature": "analyze_sentiment(text: str) -> dict",
                "description": "Performs sentiment analysis on text content. Returns sentiment score (-1 to 1), classification (positive/negative/neutral), and confidence measures."
            },
            "extract_entities": {
                "function": extract_entities,
                "signature": "extract_entities(text: str) -> dict",
                "description": "Extracts named entities from text including emails, phone numbers, URLs, dates, money amounts, percentages, and potential proper nouns."
            },
        }

    def _build_system_prompt(self) -> str:
        """Builds the system prompt with tool descriptions."""
        prompt = """You are a world-class AI assistant. Your goal is to create a step-by-step plan to answer the user's query. 

You have access to the following tools. Respond with a JSON object containing a 'plan' which is a list of steps. Each step should have:
- "thought": Your reasoning for this step
- "tool": The tool name (only use tools from the list below)
- "params": Object with the tool parameters (use the exact parameter names from signatures)

Available tools:

"""
        for name, details in self.tools.items():
            prompt += f"- Tool: {name}\n  Signature: {details['signature']}\n  Description: {details['description']}\n\n"
        
        prompt += """
STRATEGY GUIDANCE:

For COMPREHENSIVE ANALYSIS queries (e.g., "give me all X", "list all Y", "summarize entire document"):
1. Use search_uploaded_docs with retrieve_full_doc=True to get ALL chunks  
2. Use synthesize_content with method="refine" for systematic analysis
3. DO NOT use search queries - process the entire document

For TARGETED SEARCH queries (e.g., "find mentions of X", "search for Y"):
1. Use search_uploaded_docs with specific query terms
2. Use synthesize_content with method="map_reduce" for search results

For SECTION-SPECIFIC queries (e.g., "summarize section X"):  
1. First discover_document_structure to see available sections
2. Use search_uploaded_docs with filter_by_metadata for the specific section
3. If no section found, suggest searching entire document

Example - COMPREHENSIVE ANALYSIS:
{
  "plan": [
    {
      "thought": "User wants ALL regulations from the document, so I need to analyze the entire document systematically",
      "tool": "search_uploaded_docs",
      "params": {"doc_name": "document.txt", "retrieve_full_doc": true}
    },
    {
      "thought": "Now I'll use refine method to systematically extract all regulations from all chunks",
      "tool": "synthesize_content", 
      "params": {"chunks": "PREVIOUS_STEP_OUTPUT", "method": "refine", "length": "bullet points"}
    }
  ]
}

Example - TARGETED SEARCH:
{
  "plan": [
    {
      "thought": "User wants to find specific mentions, so I'll search for relevant terms",
      "tool": "search_uploaded_docs",
      "params": {"doc_name": "document.txt", "query": "search term"}
    }
  ]
}

"""
        return prompt

    def _parse_llm_response(self, response_text: str) -> Dict:
        """Parses the LLM's JSON response."""
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            logger.error("Failed to decode LLM response into JSON.")
            return {"error": "Invalid JSON response from LLM."}
    
    def _is_placeholder(self, value: str) -> bool:
        """Detects if a string value is a placeholder for previous step output."""
        if not isinstance(value, str):
            return False
        
        value_lower = value.lower()
        placeholder_indicators = [
            "previous", "placeholder", "result", "output", "step", 
            "<", ">", "$prev", "last_response", "previous_step"
        ]
        
        # Check if it contains multiple placeholder indicators (more likely to be a placeholder)
        indicator_count = sum(1 for indicator in placeholder_indicators if indicator in value_lower)
        
        # Or if it's wrapped in brackets/symbols commonly used for placeholders
        is_wrapped = (value.startswith('<') and value.endswith('>')) or \
                    (value.startswith('[') and value.endswith(']')) or \
                    value.startswith('$') or \
                    'PLACEHOLDER' in value.upper()
        
        return indicator_count >= 2 or is_wrapped
    
    def _select_best_final_answer(self, user_query: str, step_results: dict, last_result) -> str:
        """Select the most appropriate final answer based on query type and available results."""
        query_lower = user_query.lower()
        
        # For summarization queries, prefer synthesis output over analysis metrics
        if any(word in query_lower for word in ['summarize', 'summarise', 'summary', 'overview']):
            if 'synthesize_content' in step_results:
                return step_results['synthesize_content']
        
        # For search queries, prefer search results
        elif any(word in query_lower for word in ['find', 'search', 'mention', 'look for']):
            if 'search_uploaded_docs' in step_results:
                return step_results['search_uploaded_docs']
        
        # For analysis queries, use the last analytical result  
        elif any(word in query_lower for word in ['analyze', 'analyse', 'metrics', 'statistics']):
            return last_result
            
        # For general queries, prefer synthesis if available, otherwise use last result
        if 'synthesize_content' in step_results:
            return step_results['synthesize_content']
        
        return last_result

    async def run(self, user_query: str, session_id: str, uploaded_files: Dict = None):
        """Main execution loop (OODA)."""
        print(f"\n--- 🚀 Orchestrator Starting for Session {session_id} ---")
        self.reasoning_log = [] # Reset for each run
        
        # 1. Orient - Build the prompt
        current_state_prompt = f"Current State:\n- Loaded Docs: {list(document_chunk_store.keys())}\n- User Query: '{user_query}'"
        prompt = f"{self.system_prompt}{current_state_prompt}"
        
        print("\n--- 🤔 Asking LLM for a plan ---")
        try:
            response = await self.llm.ainvoke(prompt)
            response_text = response.content
            
            print("\n--- ⚡ Acting: Parsing and Executing the plan ---")
            parsed_response = self._parse_llm_response(response_text)
            
            if "plan" in parsed_response:
                plan = parsed_response["plan"]
                step_results = {}  # Store results by step type for smart reference
                step_result = None  # Keep for backward compatibility
                
                for i, step in enumerate(plan):
                    # Handle multiple possible formats
                    if "tool_call" in step:
                        tool_name = step["tool_call"]["name"]
                        tool_params = step["tool_call"]["params"]
                    elif "tool" in step and step["tool"] is not None:
                        tool_name = step["tool"]
                        # Handle different parameter formats
                        if "params" in step:
                            tool_params = step["params"]
                        elif "tool_input" in step:
                            tool_params = step["tool_input"]
                        else:
                            tool_params = {}
                    else:
                        continue  # Skip steps without tool calls (e.g., "thought" only)
                    
                    # Smart placeholder replacement
                    if isinstance(tool_params, dict):
                        for key, value in tool_params.items():
                            if isinstance(value, str) and self._is_placeholder(value):
                                # Smart reference based on placeholder content
                                if "search" in value.lower() and "search_uploaded_docs" in step_results:
                                    tool_params[key] = step_results["search_uploaded_docs"]
                                elif "synthesis" in value.lower() and "synthesize_content" in step_results:
                                    tool_params[key] = step_results["synthesize_content"]
                                else:
                                    # Fallback to previous step result
                                    tool_params[key] = step_result
                    elif isinstance(tool_params, list):
                        # Handle list parameters with placeholders
                        for idx, value in enumerate(tool_params):
                            if isinstance(value, str) and self._is_placeholder(value):
                                if "search" in value.lower() and "search_uploaded_docs" in step_results:
                                    tool_params[idx] = step_results["search_uploaded_docs"]
                                elif "synthesis" in value.lower() and "synthesize_content" in step_results:
                                    tool_params[idx] = step_results["synthesize_content"]
                                else:
                                    tool_params[idx] = step_result
                    
                    print(f"  Executing Step {i+1}: {tool_name}({tool_params})")
                    
                    if tool_name not in self.tools:
                        raise ValueError(f"Tool '{tool_name}' not found in available tools.")

                    tool_function = self.tools[tool_name]["function"]
                    if tool_name == "synthesize_content":
                        tool_params["user_query"] = user_query
                        
                    step_result = await tool_function(**tool_params)
                    
                    # Store results by tool name for smart reference
                    step_results[tool_name] = step_result
                    
                    # Store string representation for logging, but keep actual result for next step
                    self.reasoning_log.append({"tool_name": tool_name, "tool_params": tool_params, "tool_output": str(step_result)})

                # Smart final answer selection based on the query type and available results
                final_answer = self._select_best_final_answer(user_query, step_results, step_result)
                return {"status": "success", "final_answer": final_answer, "reasoning_log": self.reasoning_log}
            else:
                return {"status": "error", "final_answer": "Could not generate a valid plan.", "reasoning_log": self.reasoning_log}

        except Exception as e:
            logger.error(f"Error during plan execution: {e}")
            self.reasoning_log.append({"error": str(e)})
            return {"status": "error", "final_answer": f"An error occurred: {e}", "reasoning_log": self.reasoning_log}
