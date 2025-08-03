import asyncio
import json
import logging
import time
from typing import Dict, List, Any

from langchain_anthropic import ChatAnthropic
from tools.document_tools import upload_document, discover_document_structure, search_uploaded_docs, search_multiple_docs, document_chunk_store
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
        
        # Rate limiting for API calls
        self.api_semaphore = asyncio.Semaphore(2)  # Max 2 concurrent calls for orchestrator
        self.max_retries = 3
        self.base_delay = 1

    async def _llm_with_retry(self, prompt: str) -> str:
        """LLM call with connection limiting and retry logic for rate limit errors."""
        async with self.api_semaphore:
            for attempt in range(self.max_retries):
                try:
                    response = await self.llm.ainvoke(prompt)
                    return response.content if hasattr(response, 'content') else str(response)
                except Exception as e:
                    error_str = str(e)
                    if "rate_limit_error" in error_str or "429" in error_str or "concurrent connections" in error_str:
                        if attempt < self.max_retries - 1:
                            delay = self.base_delay * (2 ** attempt)  # Exponential backoff
                            logger.warning(f"Rate limit hit in orchestrator, retrying in {delay}s (attempt {attempt + 1}/{self.max_retries})")
                            await asyncio.sleep(delay)
                            continue
                        else:
                            logger.error(f"Rate limit exceeded in orchestrator after {self.max_retries} attempts")
                            raise e
                    else:
                        # Non-rate-limit error, don't retry
                        logger.error(f"Orchestrator LLM call failed with non-rate-limit error: {e}")
                        raise e
            return f"Error: Failed to get orchestrator response after {self.max_retries} attempts"

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
            "search_multiple_docs": {
                "function": search_multiple_docs,
                "signature": "search_multiple_docs(doc_names: list[str], query: str = None, filter_by_metadata: dict = None) -> list",
                "description": "Performs keyword search across multiple uploaded documents simultaneously. Each result chunk includes 'source_document' field for identification. Use for multi-document analysis and comparison. Returns a list of matching text chunks from all specified documents."
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
        """Builds the system prompt with tool descriptions and proven workflows."""
        prompt = """You are a world-class AI assistant. Your goal is to create a step-by-step plan to answer the user's query.

🔥 CRITICAL RULE: The CONVERSATION HISTORY is automatically provided above. For follow-up questions referencing "previous", "earlier", "based on", "mentioned", etc., READ the conversation history directly - NO need to call search_conversation_history.

You have access to the following tools. Respond with a JSON object containing a 'plan' which is a list of steps. Each step should have:
- "thought": Your reasoning for this step
- "tool": The tool name (only use tools from the list below)
- "params": Object with the tool parameters (use the exact parameter names from signatures)

🎯 PROVEN WORKFLOWS (90% success rate - USE THESE PATTERNS):

1. WORD COUNTING/FREQUENCY:
   Query: "count of word risk", "how many times is X mentioned", "word frequency"
   Proven Pattern:
   Step 1: search_uploaded_docs(doc_name="ACTIVE_DOCUMENT", retrieve_full_doc=True)
   Step 2: extract_key_phrases(text="EXTRACT_PAGE_CONTENT_FROM_STEP_1", top_n=50, min_length=1)
   ⚠️ CRITICAL: Use extract_key_phrases for word counts, analyze_text_metrics for general stats!

2. DOCUMENT SUMMARY:
   Query: "summarize document", "overview"
   Proven Pattern:
   Step 1: search_uploaded_docs(doc_name="ACTIVE_DOCUMENT", retrieve_full_doc=True)
   Step 2: synthesize_content(chunks="CHUNKS_FROM_STEP_1", method="refine", length="two paragraphs")

3. SECTION EXTRACTION:
   Query: "explain X section", "find information about Y"
   Proven Pattern:
   Step 1: search_uploaded_docs(doc_name="ACTIVE_DOCUMENT", query="KEY_TERMS")
   Step 2: synthesize_content(chunks="CHUNKS_FROM_STEP_1", method="map_reduce", length="one paragraph")

4. KEY CONCEPTS:
   Query: "main topics", "key concepts", "important themes"
   Proven Pattern:
   Step 1: search_uploaded_docs(doc_name="ACTIVE_DOCUMENT", retrieve_full_doc=True)
   Step 2: extract_key_phrases(text="EXTRACT_PAGE_CONTENT_FROM_STEP_1", top_n=10)

🌟 MULTI-DOCUMENT WORKFLOWS (USE WHEN MULTIPLE ACTIVE_DOCUMENTS):

5. COMPARATIVE ANALYSIS:
   Query: "compare documents", "differences between X and Y", "analyze both reports"
   Proven Pattern:
   Step 1: search_multiple_docs(doc_names=["ACTIVE_DOCUMENTS"])
   Step 2: synthesize_content(chunks="CHUNKS_FROM_STEP_1", method="simple_llm_call", length="comparison analysis")
   ⚠️ CRITICAL: Use search_multiple_docs when multiple documents are active! No query needed for full comparison.

6. CROSS-DOCUMENT SEARCH:
   Query: "find mentions across all documents", "search all files for X"
   Proven Pattern:
   Step 1: search_multiple_docs(doc_names=["ACTIVE_DOCUMENTS"], query="SEARCH_TERMS")
   Step 2: synthesize_content(chunks="CHUNKS_FROM_STEP_1", method="refine", length="comprehensive findings")

7. COMPREHENSIVE MULTI-DOC SUMMARY:
   Query: "summarize all documents", "overview of all files"
   Proven Pattern:
   Step 1: search_multiple_docs(doc_names=["ACTIVE_DOCUMENTS"])
   Step 2: synthesize_content(chunks="CHUNKS_FROM_STEP_1", method="refine", length="executive summary")

🚨 CRITICAL DATA FLOW RULES:
- search_uploaded_docs returns: [{"page_content": "text...", "metadata": {...}}]
- search_multiple_docs returns: [{"page_content": "text...", "metadata": {...}, "source_document": "filename"}]
- Text analytics tools (analyze_text_metrics, extract_key_phrases, analyze_sentiment) need: "text string"
- Synthesis tools (synthesize_content) need: chunk arrays
- ALWAYS extract chunks[0]["page_content"] when passing to text analytics!
- Multi-document chunks include "source_document" field for identification

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
        """Parses the LLM's JSON response, handling extra text after JSON."""
        try:
            # Try parsing the full response first
            return json.loads(response_text)
        except json.JSONDecodeError:
            # If that fails, try to extract just the JSON part
            try:
                # Look for JSON object between { and }
                start = response_text.find('{')
                if start == -1:
                    raise ValueError("No JSON object found")
                
                # Find the matching closing brace
                brace_count = 0
                end = start
                for i, char in enumerate(response_text[start:], start):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end = i + 1
                            break
                
                json_part = response_text[start:end]
                return json.loads(json_part)
            except (json.JSONDecodeError, ValueError):
                logger.error("Failed to decode LLM response into JSON.")
                return {"error": "Invalid JSON response from LLM."}
    
    def _is_placeholder(self, value: str) -> bool:
        """Detects if a string value is a placeholder for previous step output."""
        if not isinstance(value, str):
            return False
        
        # Simplified and more reliable placeholder detection
        value_upper = value.upper()
        explicit_placeholders = [
            "PREVIOUS_STEP_OUTPUT", "STEP_1_OUTPUT", "STEP_2_OUTPUT", "STEP_3_OUTPUT", 
            "STEP_4_OUTPUT", "STEP_5_OUTPUT", "COMBINE_PREVIOUS_OUTPUTS",
            "EXTRACT_PAGE_CONTENT_FROM_STEP_1", "CHUNKS_FROM_STEP_1", 
            "SEARCH_RESULTS", "DOCUMENT_CHUNKS", "RESULTS_FROM_STEPS",
            "COMBINED_RESULTS", "MERGE_OUTPUTS"
        ]
        
        # Check for exact placeholder matches first
        if any(placeholder in value_upper for placeholder in explicit_placeholders):
            return True
            
        # Check for pattern-based placeholders
        if value_upper.startswith("STEP_") and "OUTPUT" in value_upper:
            return True
            
        # Check for wrapped placeholders
        is_wrapped = (value.startswith('<') and value.endswith('>')) or \
                    (value.startswith('[') and value.endswith(']')) or \
                    value.startswith('$')
        
        return is_wrapped
    
    def _replace_placeholders(self, tool_params: dict, step_results: dict, step_result) -> dict:
        """Replace placeholder values in tool parameters with actual data from previous steps."""
        final_params = tool_params.copy()
        
        if isinstance(final_params, dict):
            for key, value in final_params.items():
                if isinstance(value, str) and self._is_placeholder(value):
                    replacement_data = None
                    
                    # Tool-specific replacement rules
                    if key == "chunks" and "search_multiple_docs" in step_results:
                        replacement_data = step_results["search_multiple_docs"]
                    elif key == "chunks" and "search_uploaded_docs" in step_results:
                        replacement_data = step_results["search_uploaded_docs"]
                    elif key == "text" and "search_multiple_docs" in step_results:
                        # For text analytics, extract page_content from first chunk
                        search_results = step_results["search_multiple_docs"]
                        if isinstance(search_results, list) and len(search_results) > 0:
                            for chunk in search_results:
                                if isinstance(chunk, dict) and "page_content" in chunk:
                                    replacement_data = chunk["page_content"]
                                    break
                    
                    # Content-based replacement rules
                    if replacement_data is None:
                        value_upper = value.upper()
                        if "CHUNK" in value_upper or "SEARCH" in value_upper:
                            if "search_multiple_docs" in step_results:
                                replacement_data = step_results["search_multiple_docs"]
                            elif "search_uploaded_docs" in step_results:
                                replacement_data = step_results["search_uploaded_docs"]
                        elif "SYNTHESIS" in value_upper or "SUMMARY" in value_upper:
                            if "synthesize_content" in step_results:
                                replacement_data = step_results["synthesize_content"]
                    
                    # Fallback to most recent result
                    if replacement_data is None:
                        replacement_data = step_result
                    
                    final_params[key] = replacement_data
        
        return final_params
    
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
    
    async def _create_intelligent_final_response(self, user_query: str, step_results: dict, last_result) -> str:
        """
        Final intelligence synthesis - combines all relevant tool outputs into a comprehensive response.
        This acts as an 'exit node' that creates the most helpful response possible.
        """
        
        # If we have multiple analysis outputs, combine them intelligently
        if len(step_results) > 1:
            # Build a comprehensive response using LLM to synthesize all outputs
            synthesis_prompt = f"""
User Query: "{user_query}"

I have gathered the following information using multiple analysis tools:

"""
            
            # Include relevant outputs
            if 'synthesize_content' in step_results:
                synthesis_prompt += f"📄 DOCUMENT SUMMARY:\n{step_results['synthesize_content']}\n\n"
            
            if 'extract_key_phrases' in step_results:
                key_phrases = step_results['extract_key_phrases']
                if isinstance(key_phrases, dict) and 'top_words' in key_phrases:
                    top_words = ', '.join([f"{word} ({count})" for word, count in list(key_phrases['top_words'].items())[:8]])
                    synthesis_prompt += f"🔑 KEY TOPICS: {top_words}\n\n"
                elif isinstance(key_phrases, str):
                    synthesis_prompt += f"🔑 KEY INSIGHTS:\n{key_phrases}\n\n"
            
            if 'discover_document_structure' in step_results:
                structure = step_results['discover_document_structure']
                if isinstance(structure, dict) and 'headers' in structure:
                    headers = ', '.join(structure['headers'][:5])  # First 5 headers
                    synthesis_prompt += f"📋 DOCUMENT STRUCTURE: {headers}\n\n"
            
            if 'search_uploaded_docs' in step_results:
                search_results = step_results['search_uploaded_docs']
                if isinstance(search_results, list) and len(search_results) > 0:
                    synthesis_prompt += f"📊 DOCUMENT CONTENT ({len(search_results)} sections):\n"
                    for i, section in enumerate(search_results, 1):
                        content = section.get('page_content', '')[:500]  # First 500 chars
                        synthesis_prompt += f"Section {i}: {content}\n"
                    synthesis_prompt += "\n"
            
            # Add support for process_table_data results
            if 'process_table_data' in step_results:
                table_results = step_results['process_table_data']
                if isinstance(table_results, dict):
                    synthesis_prompt += f"📈 TABLE ANALYSIS RESULTS:\n{str(table_results)}\n\n"
            
            # Add support for other analysis tools
            if 'analyze_text_metrics' in step_results:
                metrics = step_results['analyze_text_metrics']
                synthesis_prompt += f"📊 TEXT METRICS:\n{str(metrics)}\n\n"
            
            synthesis_prompt += f"""
Please create a comprehensive, well-structured response that directly answers the user's query by intelligently combining the above information. 

Requirements:
- Start with a direct answer to their question
- Include the most relevant details from the analysis
- Be concise but thorough
- Use a professional, helpful tone
- Structure the response logically

Final Response:"""
            
            try:
                return await self._llm_with_retry(synthesis_prompt)
            except Exception as e:
                logger.error(f"Failed to create intelligent final response: {e}")
                # Fallback to smart selection
                return self._select_best_final_answer(user_query, step_results, last_result)
        
        # Fallback for single-step results
        return self._select_best_final_answer(user_query, step_results, last_result)

    async def run(self, user_query: str, session_id: str, active_document: str = None, active_documents: List[str] = None, memory_context: Dict = None):
        """Main execution loop (OODA) with memory integration."""
        print(f"\n--- 🚀 Orchestrator Starting for Session {session_id} ---")
        self.reasoning_log = [] # Reset for each run
        
        # 1. Orient - Build the prompt with memory context
        current_state_prompt = f"Current State:\n- Loaded Docs: {list(document_chunk_store.keys())}\n- User Query: '{user_query}'"
        
        # Add active document context (handle both single and multiple)
        if active_documents and len(active_documents) > 0:
            if len(active_documents) == 1:
                current_state_prompt += f"\n- ACTIVE DOCUMENT: '{active_documents[0]}' (PRIORITIZE this document for analysis)"
            else:
                docs_list = "', '".join(active_documents)
                current_state_prompt += f"\n- ACTIVE DOCUMENTS: ['{docs_list}'] (PRIORITIZE these documents for multi-document analysis)"
        elif active_document:
            # Backward compatibility for single document
            current_state_prompt += f"\n- ACTIVE DOCUMENT: '{active_document}' (PRIORITIZE this document for analysis)"
        
        # Format conversation history clearly (LAST 3 MESSAGES)
        conversation_section = ""
        if memory_context and memory_context.get('conversation_history'):
            conversation_history = memory_context['conversation_history'][-3:]  # Last 3 messages
            if conversation_history:
                conversation_section = "\n\n" + "="*60 + "\n📋 PREVIOUS CONVERSATION (Last 3 messages):\n" + "="*60 + "\n"
                for i, msg in enumerate(conversation_history, 1):
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')
                    timestamp = msg.get('timestamp', '')[:16] if msg.get('timestamp') else ''
                    
                    if role.lower() == 'user':
                        conversation_section += f"\n🔹 USER QUERY {i}: {content}\n"
                    elif role.lower() == 'assistant':
                        # Truncate assistant responses to keep manageable
                        truncated_content = content[:300] + "..." if len(content) > 300 else content
                        conversation_section += f"\n🤖 ASSISTANT RESPONSE {i}: {truncated_content}\n"
                
                conversation_section += "\n" + "="*60 + "\n"
        
        # Combine system prompt + current state + conversation history + current query
        formatted_prompt = f"""{self.system_prompt}

{current_state_prompt}{conversation_section}

🎯 CURRENT USER QUERY: "{user_query}"

Please create a plan to answer the current query, using conversation history when relevant."""
        
        print("\n--- 🤔 Asking LLM for a plan ---")
        print(f"📝 Prompt includes conversation history: {len(memory_context.get('conversation_history', [])) if memory_context else 0} messages")
        try:
            response_text = await self._llm_with_retry(formatted_prompt)
            
            parsed_response = self._parse_llm_response(response_text)
            
            print("\n--- ⚡ Acting: Parsing and Executing the plan ---")
            
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
                    
                    # Smart placeholder replacement - simplified and more reliable
                    if isinstance(tool_params, dict):
                        for key, value in tool_params.items():
                            if isinstance(value, str) and self._is_placeholder(value):
                                replacement_data = None
                                
                                # CRITICAL FIX: Handle ACTIVE_DOCUMENTS placeholder
                                if value == "ACTIVE_DOCUMENTS" and key == "doc_names":
                                    replacement_data = active_documents if active_documents else []
                                    print(f"    🔧 CRITICAL FIX: {value} → {active_documents}")
                                elif value == ["ACTIVE_DOCUMENTS"] and key == "doc_names":
                                    replacement_data = active_documents if active_documents else []
                                    print(f"    🔧 CRITICAL FIX: {value} → {active_documents}")
                                
                                # Tool-specific replacement rules (most important first)
                                elif tool_name == "synthesize_content" and key == "chunks":
                                    # synthesize_content should use the most recent relevant data
                                    if "process_table_data" in step_results:
                                        replacement_data = step_results["process_table_data"]
                                        print(f"    📎 Tool-specific fix: {value} → table processing results for synthesis")
                                    elif "search_multiple_docs" in step_results:
                                        replacement_data = step_results["search_multiple_docs"]
                                        print(f"    📎 Tool-specific fix: {value} → multi-document chunks for synthesis")
                                    elif "search_uploaded_docs" in step_results:
                                        replacement_data = step_results["search_uploaded_docs"]
                                        print(f"    📎 Tool-specific fix: {value} → document chunks for synthesis")
                                    
                                elif tool_name in ["analyze_text_metrics", "extract_key_phrases", "analyze_sentiment"] and key == "text":
                                    # Text analytics tools need plain text from first chunk
                                    if "search_multiple_docs" in step_results:
                                        search_results = step_results["search_multiple_docs"]
                                        if isinstance(search_results, list) and len(search_results) > 0:
                                            # Find first valid chunk (not error object)
                                            for chunk in search_results:
                                                if isinstance(chunk, dict) and "page_content" in chunk:
                                                    replacement_data = chunk["page_content"]
                                                    print(f"    📎 Text extraction: {value} → page content from multi-doc search")
                                                    break
                                    elif "search_uploaded_docs" in step_results:
                                        search_results = step_results["search_uploaded_docs"]
                                        if isinstance(search_results, list) and len(search_results) > 0:
                                            first_chunk = search_results[0]
                                            if isinstance(first_chunk, dict) and "page_content" in first_chunk:
                                                replacement_data = first_chunk["page_content"]
                                                print(f"    📎 Text extraction: {value} → page content for text analysis")
                                
                                # Content-based replacement rules
                                if replacement_data is None:
                                    value_upper = value.upper()
                                    if "CHUNK" in value_upper or "SEARCH" in value_upper:
                                        # For chunk/search references, prefer document search results
                                        if "search_multiple_docs" in step_results:
                                            replacement_data = step_results["search_multiple_docs"]
                                            print(f"    📎 Content-based: {value} → multi-document chunks")
                                        elif "search_uploaded_docs" in step_results:
                                            replacement_data = step_results["search_uploaded_docs"]
                                            print(f"    📎 Content-based: {value} → document chunks")
                                    elif "SYNTHESIS" in value_upper or "SUMMARY" in value_upper:
                                        # For synthesis references, use synthesis output
                                        if "synthesize_content" in step_results:
                                            replacement_data = step_results["synthesize_content"]
                                            print(f"    📎 Content-based: {value} → synthesis output")
                                
                                # Fallback to most recent result
                                if replacement_data is None:
                                    replacement_data = step_result
                                    print(f"    📎 Fallback: {value} → previous step result")
                                
                                tool_params[key] = replacement_data
                    elif isinstance(tool_params, list):
                        # Handle list parameters with placeholders
                        for idx, value in enumerate(tool_params):
                            if isinstance(value, str) and self._is_placeholder(value):
                                # CRITICAL FIX: Handle ACTIVE_DOCUMENTS in list parameters
                                if value == "ACTIVE_DOCUMENTS":
                                    tool_params[idx] = active_documents if active_documents else []
                                    print(f"    🔧 CRITICAL FIX (list): {value} → {active_documents}")
                                    continue
                                value_lower = value.lower()
                                if ("search" in value_lower or "chunk" in value_lower):
                                    if "search_multiple_docs" in step_results:
                                        tool_params[idx] = step_results["search_multiple_docs"]
                                    elif "search_uploaded_docs" in step_results:
                                        tool_params[idx] = step_results["search_uploaded_docs"]
                                    else:
                                        tool_params[idx] = step_result
                                elif ("table" in value_lower or "process" in value_lower) and "process_table_data" in step_results:
                                    tool_params[idx] = step_results["process_table_data"]
                                elif ("synthesis" in value_lower or "summary" in value_lower) and "synthesize_content" in step_results:
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

                # Final intelligence synthesis - combine all relevant outputs into a comprehensive response
                final_answer = await self._create_intelligent_final_response(user_query, step_results, step_result)
                return {"status": "success", "final_answer": final_answer, "reasoning_log": self.reasoning_log}
            else:
                return {"status": "error", "final_answer": "Could not generate a valid plan.", "reasoning_log": self.reasoning_log}

        except Exception as e:
            logger.error(f"Error during plan execution: {e}")
            self.reasoning_log.append({"error": str(e)})
            return {"status": "error", "final_answer": f"An error occurred: {e}", "reasoning_log": self.reasoning_log}

    async def run_streaming(self, user_query: str, session_id: str, active_document: str = None, active_documents: List[str] = None, memory_context: Dict = None):
        """Streaming version of the main execution loop with real-time reasoning steps."""
        print(f"\n--- 🚀 Streaming Orchestrator Starting for Session {session_id} ---")
        self.reasoning_log = []  # Reset for each run
        
        # Stream initial setup
        yield {
            'type': 'reasoning_step',
            'step': 'setup',
            'message': '🤔 Analyzing your query and preparing execution plan...',
            'timestamp': time.time()
        }
        
        # 1. Orient - Build the prompt with memory context
        current_state_prompt = f"Current State:\n- Loaded Docs: {list(document_chunk_store.keys())}\n- User Query: '{user_query}'"
        
        # Add active document context
        if active_documents and len(active_documents) > 0:
            if len(active_documents) == 1:
                current_state_prompt += f"\n- ACTIVE DOCUMENT: '{active_documents[0]}' (PRIORITIZE this document for analysis)"
                yield {
                    'type': 'reasoning_step',
                    'step': 'context',
                    'message': f'📄 Focusing analysis on: {active_documents[0]}',
                    'timestamp': time.time()
                }
            else:
                docs_list = "', '".join(active_documents)
                current_state_prompt += f"\n- ACTIVE DOCUMENTS: ['{docs_list}'] (PRIORITIZE these documents for multi-document analysis)"
                yield {
                    'type': 'reasoning_step',
                    'step': 'context',
                    'message': f'📚 Analyzing {len(active_documents)} documents: {docs_list[:50]}...',
                    'timestamp': time.time()
                }
        elif active_document:
            current_state_prompt += f"\n- ACTIVE DOCUMENT: '{active_document}' (PRIORITIZE this document for analysis)"
            yield {
                'type': 'reasoning_step',
                'step': 'context',
                'message': f'📄 Focusing analysis on: {active_document}',
                'timestamp': time.time()
            }
        
        # Format conversation history
        conversation_section = ""
        if memory_context and memory_context.get('conversation_history'):
            conversation_history = memory_context['conversation_history'][-3:]
            if conversation_history:
                yield {
                    'type': 'reasoning_step',
                    'step': 'memory',
                    'message': f'🧠 Loading conversation context ({len(conversation_history)} recent messages)',
                    'timestamp': time.time()
                }
                conversation_section = "\n\n" + "="*60 + "\n📋 PREVIOUS CONVERSATION (Last 3 messages):\n" + "="*60 + "\n"
                for i, msg in enumerate(conversation_history, 1):
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')
                    
                    if role.lower() == 'user':
                        conversation_section += f"\n🔹 USER QUERY {i}: {content}\n"
                    elif role.lower() == 'assistant':
                        truncated_content = content[:300] + "..." if len(content) > 300 else content
                        conversation_section += f"\n🤖 ASSISTANT RESPONSE {i}: {truncated_content}\n"
                
                conversation_section += "\n" + "="*60 + "\n"
        
        # Stream plan generation
        yield {
            'type': 'reasoning_step',
            'step': 'planning',
            'message': '🎯 Creating execution plan with AI reasoning...',
            'timestamp': time.time()
        }
        
        # Combine prompts
        formatted_prompt = f"""{self.system_prompt}

{current_state_prompt}{conversation_section}

🎯 CURRENT USER QUERY: "{user_query}"

Please create a plan to answer the current query, using conversation history when relevant."""
        
        try:
            # Get plan from LLM
            response_text = await self._llm_with_retry(formatted_prompt)
            parsed_response = self._parse_llm_response(response_text)
            
            yield {
                'type': 'reasoning_step',
                'step': 'plan_ready',
                'message': '📋 Execution plan created, starting analysis...',
                'timestamp': time.time()
            }
            
            if "plan" in parsed_response:
                plan = parsed_response["plan"]
                step_results = {}
                step_result = None
                
                # Stream each step execution
                for i, step in enumerate(plan):
                    # Parse step format
                    if "tool_call" in step:
                        tool_name = step["tool_call"]["name"]
                        tool_params = step["tool_call"]["params"]
                    elif "tool" in step and step["tool"] is not None:
                        tool_name = step["tool"]
                        if "params" in step:
                            tool_params = step["params"]
                        elif "tool_input" in step:
                            tool_params = step["tool_input"]
                        else:
                            tool_params = {}
                    else:
                        continue
                    
                    # Stream step start
                    step_description = step.get("description", f"Executing {tool_name}")
                    yield {
                        'type': 'reasoning_step',
                        'step': 'tool_execution',
                        'tool_name': tool_name,
                        'message': f'⚡ Step {i+1}: {step_description}',
                        'timestamp': time.time()
                    }
                    
                    # Execute the tool
                    if tool_name in self.tools:
                        try:
                            tool_function = self.tools[tool_name]["function"]
                            start_time = time.time()
                            
                            # Smart parameter replacement with ACTIVE_DOCUMENTS fix
                            final_params = tool_params.copy()
                            
                            # CRITICAL FIX for streaming: Handle ACTIVE_DOCUMENTS placeholder
                            if isinstance(final_params, dict):
                                for key, value in final_params.items():
                                    if value == "ACTIVE_DOCUMENTS" and key == "doc_names":
                                        final_params[key] = active_documents if active_documents else []
                                        print(f"    🔧 STREAMING FIX: {value} → {active_documents}")
                                    elif value == ["ACTIVE_DOCUMENTS"] and key == "doc_names":
                                        final_params[key] = active_documents if active_documents else []
                                        print(f"    🔧 STREAMING FIX: {value} → {active_documents}")
                            
                            final_params = self._replace_placeholders(final_params, step_results, step_result)
                            
                            # Execute tool
                            if asyncio.iscoroutinefunction(tool_function):
                                result = await tool_function(**final_params)
                            else:
                                result = tool_function(**final_params)
                            
                            execution_time = time.time() - start_time
                            
                            # Store result
                            step_results[tool_name] = result
                            step_result = result
                            
                            # Stream step completion
                            result_preview = str(result)[:100] + "..." if len(str(result)) > 100 else str(result)
                            yield {
                                'type': 'reasoning_step',
                                'step': 'tool_complete',
                                'tool_name': tool_name,
                                'message': f'✅ {tool_name} completed ({execution_time:.1f}s)',
                                'result_preview': result_preview,
                                'timestamp': time.time()
                            }
                            
                            # Log the step
                            self.reasoning_log.append({
                                "tool_name": tool_name,
                                "tool_params": final_params,
                                "tool_output": result
                            })
                            
                        except Exception as e:
                            error_msg = f"Error in {tool_name}: {str(e)}"
                            yield {
                                'type': 'reasoning_step',
                                'step': 'tool_error',
                                'tool_name': tool_name,
                                'message': f'❌ {error_msg}',
                                'timestamp': time.time()
                            }
                            logger.error(error_msg)
                            self.reasoning_log.append({"tool_name": tool_name, "error": str(e)})
                            step_results[tool_name] = {"error": str(e)}
                    else:
                        error_msg = f"Unknown tool: {tool_name}"
                        yield {
                            'type': 'reasoning_step',
                            'step': 'tool_error',
                            'tool_name': tool_name,
                            'message': f'❌ {error_msg}',
                            'timestamp': time.time()
                        }
                        logger.error(error_msg)
                
                # Stream final synthesis
                yield {
                    'type': 'reasoning_step',
                    'step': 'synthesis',
                    'message': '🧠 Synthesizing insights and creating final response...',
                    'timestamp': time.time()
                }
                
                # Create final response
                final_answer = await self._create_intelligent_final_response(user_query, step_results, step_result)
                
                # Stream final answer
                yield {
                    'type': 'final_answer',
                    'content': final_answer,
                    'reasoning_log': self.reasoning_log,
                    'timestamp': time.time()
                }
                
            else:
                yield {
                    'type': 'error',
                    'message': "Could not generate a valid execution plan.",
                    'timestamp': time.time()
                }
                
        except Exception as e:
            logger.error(f"Error during streaming execution: {e}")
            yield {
                'type': 'error',
                'message': f"An error occurred during analysis: {str(e)}",
                'timestamp': time.time()
            }
