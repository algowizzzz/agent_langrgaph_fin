import logging
from typing import Dict, List, Any, Optional
import asyncio
import json
from pathlib import Path

from langchain_core.messages import HumanMessage
from langchain_core.documents import Document
from langchain.chains.summarize import load_summarize_chain
from langchain_core.prompts import PromptTemplate
from langgraph.graph import StateGraph, END

from document_processor import document_processor
from config import config

logger = logging.getLogger(__name__)

from typing_extensions import TypedDict

class DocumentAnalysisState(TypedDict):
    """State for Document Analysis Pod workflow."""
    user_query: str
    template_instructions: str
    uploaded_files: Dict[str, Dict]  # filename -> {id, role}
    session_id: str
    doc_chunks: List[Document]
    planner_prompts: Dict[str, str]  # {initial_prompt, refine_prompt}
    final_result: str
    error: Optional[str]
    processing_status: str
    # New reasoning fields
    reasoning_steps: List[Dict[str, Any]]  # Step-by-step reasoning
    current_step: str
    thoughts: str

class RetryableAnalysisError(Exception):
    """Exception for errors that should trigger retry logic."""
    pass

class DocumentAnalysisPod:
    """Document Analysis Pod using dynamic Planner/Executor model."""
    
    def __init__(self):
        self.llm = None
        self.graph = None
        self._setup_llm()
        self._build_graph()
    
    def _add_reasoning_step(self, state: dict, step_name: str, thought: str, details: Dict[str, Any] = None) -> dict:
        """Add a reasoning step to track agent's thought process."""
        if "reasoning_steps" not in state:
            state["reasoning_steps"] = []
        
        reasoning_step = {
            "step": step_name,
            "thought": thought,
            "timestamp": __import__('datetime').datetime.now().isoformat(),
            "details": details or {}
        }
        
        state["reasoning_steps"].append(reasoning_step)
        state["current_step"] = step_name
        state["thoughts"] = thought
        
        # Log for debugging
        logger.info(f"🤔 Agent Reasoning - {step_name}: {thought}")
        
        return state
    
    def _setup_llm(self):
        """Initialize LLM with error handling."""
        try:
            # Check if we have API keys and should use real LLM
            # Prioritize Anthropic (Claude) for this test
            if config.ai.anthropic_api_key and not config.ai.enable_mock_mode:
                from langchain_anthropic import ChatAnthropic
                self.llm = ChatAnthropic(
                    api_key=config.ai.anthropic_api_key,
                    model=config.ai.anthropic_model,
                    temperature=0.3  # Lower temperature for analysis
                )
                logger.info(f"Using Anthropic LLM for Document Analysis: {config.ai.anthropic_model}")
            elif config.ai.openai_api_key and not config.ai.enable_mock_mode:
                from langchain_openai import ChatOpenAI
                self.llm = ChatOpenAI(
                    api_key=config.ai.openai_api_key,
                    model=config.ai.openai_model,
                    temperature=0.3  # Lower temperature for analysis
                )
                logger.info(f"Using OpenAI LLM for Document Analysis: {config.ai.openai_model}")
            else:
                logger.info("Using mock LLM for Document Analysis (no API keys or mock mode enabled)")
                self.llm = MockAnalysisLLM()
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {str(e)}")
            logger.info("Falling back to mock LLM for Document Analysis")
            self.llm = MockAnalysisLLM()  # Fallback to mock
    
    def _build_graph(self):
        """Build the LangGraph workflow."""
        workflow = StateGraph(DocumentAnalysisState)
        
        # Add nodes
        workflow.add_node("load_documents", self._load_documents)
        workflow.add_node("planner_node", self._planner_node)
        workflow.add_node("executor_node", self._executor_node)
        workflow.add_node("synthesizer_node", self._synthesizer_node)
        
        # Add edges
        workflow.set_entry_point("load_documents")
        workflow.add_edge("load_documents", "planner_node")
        workflow.add_edge("planner_node", "executor_node")
        workflow.add_edge("executor_node", "synthesizer_node")
        workflow.add_edge("synthesizer_node", END)
        
        self.graph = workflow.compile()
        logger.info("Document Analysis Pod graph compiled successfully")
    
    async def _load_documents(self, state: dict) -> dict:
        """Load and process uploaded documents."""
        try:
            logger.info("Loading documents for analysis")
            state["processing_status"] = "loading_documents"
            
            uploaded_files = state.get("uploaded_files", {})
            file_count = len(uploaded_files)
            file_names = list(uploaded_files.keys())
            
            # Add reasoning step
            self._add_reasoning_step(
                state, 
                "Loading Documents", 
                f"Found {file_count} file(s) to analyze: {', '.join(file_names)}. I will now load, parse, and split them into manageable chunks.",
                {"file_count": file_count, "files": file_names}
            )
            all_chunks = []
            
            # Process Content files
            content_files = {name: info for name, info in uploaded_files.items() 
                           if info.role == "Content"}
            
            if not content_files:
                state["error"] = "No Content files provided for analysis"
                return state
            
            for filename, file_info in content_files.items():
                try:
                    file_id = file_info.id
                    if not file_id:
                        logger.error(f"File ID is missing for {filename}. Skipping file.")
                        continue
                    
                    session_id = state.get("session_id", "unknown")
                    
                    # Construct file path using the correct file_id
                    file_path = Path(f"./uploads/{session_id}/{file_id}_{filename}")
                    
                    logger.info(f"Processing document: {filename} at path: {file_path}")
                    
                    # Check if file exists
                    if not file_path.exists():
                        logger.error(f"File does not exist: {file_path}")
                        upload_dir = Path(f"./uploads/{session_id}")
                        
                        # Add detailed logging to debug
                        if upload_dir.exists():
                            logger.info(f"Contents of upload directory '{upload_dir}':")
                            for item in upload_dir.iterdir():
                                logger.info(f"- {item.name}")
                        else:
                            logger.error(f"Upload directory does not exist: {upload_dir}")
                            continue

                        # Try to find the file with different naming
                        matching_files = list(upload_dir.glob(f"{file_id}_*"))
                        if matching_files:
                            file_path = matching_files[0]
                            logger.info(f"Found file at: {file_path}")
                        else:
                            logger.error(f"No files found with ID {file_id} in {upload_dir}")
                            continue
                    
                    # Process document
                    result = await document_processor.process_document(str(file_path))
                    
                    if result.success:
                        all_chunks.extend(result.documents)
                        logger.info(f"Successfully processed {filename}: {len(result.documents)} chunks")
                    else:
                        logger.error(f"Failed to process {filename}: {result.error}")
                        # Continue with other files instead of failing completely
                        
                except Exception as e:
                    logger.error(f"Error processing file {filename}: {str(e)}")
                    continue
            
            if not all_chunks:
                state["error"] = "No text content could be extracted from any uploaded files"
                return state
            
            state["doc_chunks"] = all_chunks
            state["processing_status"] = "documents_loaded"
            
            logger.info(f"Successfully loaded {len(all_chunks)} document chunks from {len(content_files)} files")
            return state
            
        except Exception as e:
            logger.error(f"Error loading documents: {str(e)}")
            state["error"] = f"Document loading failed: {str(e)}"
            return state
    
    async def _planner_node(self, state: dict) -> dict:
        """Generate analysis prompts based on user query and template instructions."""
        try:
            logger.info("Planning document analysis approach")
            state["processing_status"] = "planning"
            
            user_query = state.get("user_query", "")
            template_instructions = state.get("template_instructions", "")
            doc_chunks = state.get("doc_chunks", [])
            total_chars = sum(len(chunk.page_content) for chunk in doc_chunks)
            
            # Add reasoning step
            self._add_reasoning_step(
                state, 
                "Planning Analysis", 
                f"The user's request is: '{user_query}'. I have processed the document(s) into {len(doc_chunks)} chunk(s), totaling {total_chars} characters.",
                {"user_query": user_query, "chunk_count": len(doc_chunks), "total_chars": total_chars, "has_templates": bool(template_instructions)}
            )
            
            # Stage 1: Extract core task and instructions
            stage1_prompt = f"""Analyze this user request for document analysis and break it down into components:

User Request: "{user_query}"

Template Instructions (if provided): "{template_instructions}"

Please identify:
1. CORE_TASK: The main analysis task (e.g., summarize, extract key points, analyze data, etc.)
2. INSTRUCTIONS: Specific requirements, format preferences, or focus areas

Respond in this exact format:
CORE_TASK: [main task]
INSTRUCTIONS: [specific requirements]"""

            stage1_response = await self._call_llm_with_retry(stage1_prompt)
            
            # Parse stage 1 response
            core_task, instructions = self._parse_stage1_response(stage1_response)
            
            # Combine with template instructions if provided
            combined_instructions = self._combine_instructions(instructions, template_instructions)
            
            # Stage 2: Generate persona-based prompts
            stage2_prompt = f"""You are an expert document analysis assistant. Your primary task is to create two prompts for a downstream AI model. These prompts will be used in a "refine" chain to analyze text provided by a user.

The user wants to accomplish this CORE TASK: "{core_task}"
They have provided these specific REQUIREMENTS: "{combined_instructions}"

CRITICAL INSTRUCTION: The downstream model will be given text content from a document. Your generated prompts MUST explicitly reference this text content as the primary source for the analysis.

Create two prompts:
1.  **INITIAL_PROMPT**: This prompt will be used on the very first chunk of text. It must instruct the AI to perform the user's request on the provided text.
2.  **REFINE_PROMPT**: This prompt will be used on all subsequent chunks of text. It must instruct the AI to refine its previous analysis using the new text provided.

IMPORTANT: Respond with ONLY the raw JSON object, without any markdown, comments, or other text.
Your response must be in this exact format:
{{
    "initial_prompt": "Your initial analysis prompt here. It MUST mention that the AI should use the following text content: {{text}}",
    "refine_prompt": "Your refinement prompt here. It MUST mention that the AI should refine its existing answer: {{existing_answer}} using the following new text content: {{text}}"
}}"""

            stage2_response = await self._call_llm_with_retry(stage2_prompt)
            
            # Clean and parse JSON response
            cleaned_response = self._clean_llm_json_response(stage2_response)
            try:
                prompts_dict = json.loads(cleaned_response)
                state["planner_prompts"] = {
                    "initial_prompt": prompts_dict.get("initial_prompt", "Analyze this document content."),
                    "refine_prompt": prompts_dict.get("refine_prompt", "Refine the analysis with this additional content.")
                }
            except json.JSONDecodeError:
                logger.warning("Failed to parse JSON from planner response even after cleaning, using fallback prompts")
                state["planner_prompts"] = self._get_fallback_prompts_with_context(user_query, template_instructions)
            
            state["processing_status"] = "planning_complete"
            logger.info("Document analysis planning completed successfully")
            return state
            
        except Exception as e:
            logger.error(f"Error in planner node: {str(e)}")
            # Use fallback prompts instead of failing
            state["planner_prompts"] = self._get_fallback_prompts_with_context("analyze documents", "")
            state["processing_status"] = "planning_fallback"
            return state
    
    def _clean_llm_json_response(self, response: str) -> str:
        """Clean up LLM response to extract a valid JSON object."""
        # Find the start and end of the JSON object
        start_index = response.find('{')
        end_index = response.rfind('}')
        
        if start_index != -1 and end_index != -1:
            # Extract the JSON part
            json_str = response[start_index:end_index+1]
            return json_str.strip()
        else:
            # If no JSON object is found, return the original response
            return response
    
    def _parse_stage1_response(self, response: str) -> tuple[str, str]:
        """Parse the stage 1 response to extract core task and instructions."""
        try:
            lines = response.strip().split('\n')
            core_task = "analyze"
            instructions = ""
            
            for line in lines:
                if line.startswith("CORE_TASK:"):
                    core_task = line.replace("CORE_TASK:", "").strip()
                elif line.startswith("INSTRUCTIONS:"):
                    instructions = line.replace("INSTRUCTIONS:", "").strip()
            
            return core_task, instructions
            
        except Exception as e:
            logger.warning(f"Error parsing stage 1 response: {str(e)}")
            return "analyze", ""
    
    def _combine_instructions(self, user_instructions: str, template_instructions: str) -> str:
        """Combine user instructions with template instructions."""
        combined = []
        
        if user_instructions:
            combined.append(f"User Requirements: {user_instructions}")
        
        if template_instructions:
            combined.append(f"Template Guidelines: {template_instructions}")
        
        return " | ".join(combined) if combined else "Provide a comprehensive analysis"
    
    def _get_fallback_prompts(self, core_task: str) -> Dict[str, str]:
        """Generate fallback prompts based on core task."""
        task_lower = core_task.lower()
        
        if "summarize" in task_lower or "summary" in task_lower:
            return {
                "initial_prompt": "Provide a comprehensive summary of the key points, main ideas, and important details from this document content.",
                "refine_prompt": "Expand and refine the summary by incorporating the key points and important details from this additional document content."
            }
        elif "extract" in task_lower or "key points" in task_lower:
            return {
                "initial_prompt": "Extract and list the key points, important information, and main findings from this document content.",
                "refine_prompt": "Add to the list of key points and important information by analyzing this additional document content."
            }
        elif "analyze" in task_lower or "analysis" in task_lower:
            return {
                "initial_prompt": "Conduct a thorough analysis of this document content, identifying main themes, patterns, and significant information.",
                "refine_prompt": "Enhance the analysis by incorporating insights, themes, and significant information from this additional document content."
            }
        else:
            return {
                "initial_prompt": "Analyze this document content and provide comprehensive insights based on the request.",
                "refine_prompt": "Refine and expand the analysis by incorporating information from this additional document content."
            }
    
    def _get_fallback_prompts_with_context(self, user_query: str, template_instructions: str) -> Dict[str, str]:
        """Generate fallback prompts that include the user's actual request."""
        task_lower = user_query.lower()
        
        # Include the user's actual request in the prompts
        base_instruction = f"The user asked: '{user_query}'"
        if template_instructions:
            base_instruction += f" with these additional instructions: {template_instructions}"
        
        if "summary" in task_lower or "summarize" in task_lower:
            return {
                "initial_prompt": f"{base_instruction}\n\nBased on this request, summarize the main points and key information from this document content:\n\n{{text}}",
                "refine_prompt": f"{base_instruction}\n\nHere's the current summary:\n{{existing_answer}}\n\nEnhance it by incorporating additional information from this document content:\n\n{{text}}"
            }
        elif "extract" in task_lower or "key points" in task_lower:
            return {
                "initial_prompt": f"{base_instruction}\n\nBased on this request, extract and list the key points, important information, and main findings from this document content:\n\n{{text}}",
                "refine_prompt": f"{base_instruction}\n\nHere are the current key points:\n{{existing_answer}}\n\nAdd more key points by analyzing this additional document content:\n\n{{text}}"
            }
        elif "analyze" in task_lower or "analysis" in task_lower:
            return {
                "initial_prompt": f"{base_instruction}\n\nBased on this request, conduct a thorough analysis of this document content:\n\n{{text}}",
                "refine_prompt": f"{base_instruction}\n\nHere's the current analysis:\n{{existing_answer}}\n\nEnhance the analysis with insights from this additional document content:\n\n{{text}}"
            }
        elif "same" in task_lower or "compare" in task_lower or "different" in task_lower:
            return {
                "initial_prompt": f"{base_instruction}\n\nBased on this request, analyze this document content and prepare for comparison:\n\n{{text}}",
                "refine_prompt": f"{base_instruction}\n\nHere's the analysis of the first document:\n{{existing_answer}}\n\nNow compare it with this additional document content and answer the user's question:\n\n{{text}}"
            }
        else:
            return {
                "initial_prompt": f"{base_instruction}\n\nBased on this request, analyze this document content and provide the information requested:\n\n{{text}}",
                "refine_prompt": f"{base_instruction}\n\nHere's the current analysis:\n{{existing_answer}}\n\nRefine and expand the analysis with information from this additional document content:\n\n{{text}}"
            }
    
    async def _executor_node(self, state: dict) -> dict:
        """Execute the analysis using the planned prompts."""
        try:
            logger.info("Executing document analysis")
            state["processing_status"] = "executing"
            
            doc_chunks = state.get("doc_chunks", [])
            planner_prompts = state.get("planner_prompts", {})
            
            # Add reasoning step with batch processing info
            total_chunks = len(doc_chunks)
            use_batch_processing = (
                config.ai.enable_batch_processing and 
                total_chunks > config.ai.batch_size
            )
            
            if use_batch_processing:
                num_batches = (total_chunks + config.ai.batch_size - 1) // config.ai.batch_size
                reasoning_msg = f"I will now analyse the {total_chunks} text chunk(s) using batch processing ({num_batches} batches of ~{config.ai.batch_size} chunks each) for optimal performance."
            else:
                reasoning_msg = f"I will now analyse the {total_chunks} text chunk(s) in a single optimized batch call."
            
            self._add_reasoning_step(
                state, 
                "Analyzing Documents", 
                reasoning_msg,
                {"chunk_count": total_chunks, "total_chars": sum(len(chunk.page_content) for chunk in doc_chunks), "batch_processing": use_batch_processing}
            )
            
            if not doc_chunks:
                state["error"] = "No document chunks available for analysis"
                return state
            
            # Create custom prompts for the refine chain
            initial_prompt_template = PromptTemplate.from_template(
                planner_prompts.get("initial_prompt", "Analyze this document content: {text}")
            )
            
            refine_prompt_template = PromptTemplate.from_template(
                planner_prompts.get("refine_prompt", 
                    "Given the existing analysis:\n{existing_answer}\n\n"
                    "Refine it with this additional content:\n{text}")
            )
            
            # Use real LLM if available, otherwise mock
            if hasattr(self.llm, 'ainvoke') and not isinstance(self.llm, MockAnalysisLLM):
                result = await self._run_real_refine_chain(
                    doc_chunks, 
                    initial_prompt_template, 
                    refine_prompt_template
                )
            else:
                result = await self._run_mock_refine_chain(
                    doc_chunks, 
                    initial_prompt_template, 
                    refine_prompt_template
                )
            
            state["final_result"] = result
            state["processing_status"] = "execution_complete"
            
            logger.info("Document analysis execution completed successfully")
            return state
            
        except Exception as e:
            logger.error(f"Error in executor node: {str(e)}")
            state["error"] = f"Analysis execution failed: {str(e)}"
            return state
    
    async def _run_real_refine_chain(self, docs: List[Document], initial_prompt: PromptTemplate, refine_prompt: PromptTemplate) -> str:
        """Real implementation of refine chain using actual LLM with batch processing optimization."""
        try:
            if not docs:
                return "No documents provided for analysis."
            
            # Determine processing strategy based on chunk count and configuration
            total_chunks = len(docs)
            use_batch_processing = (
                config.ai.enable_batch_processing and 
                total_chunks > config.ai.batch_size
            )
            
            if use_batch_processing:
                logger.info(f"Using batch processing for {total_chunks} chunks (batch_size: {config.ai.batch_size})")
                return await self._run_batch_refine_chain(docs, initial_prompt, refine_prompt)
            else:
                logger.info(f"Using single batch processing for {total_chunks} chunks")
                return await self._run_single_batch_refine_chain(docs, initial_prompt, refine_prompt)
            
        except Exception as e:
            logger.error(f"Error in real refine chain: {str(e)}")
            return f"Analysis completed with {len(docs)} document chunks. Error occurred during processing: {str(e)}"
    
    async def _run_single_batch_refine_chain(self, docs: List[Document], initial_prompt: PromptTemplate, refine_prompt: PromptTemplate) -> str:
        """Process all chunks in a single LLM call (≤25 chunks)."""
        try:
            # Combine all chunks into one call
            combined_text = "\n\n---CHUNK SEPARATOR---\n\n".join(
                doc.page_content for doc in docs
            )
            
            # Single LLM call with all content
            result = await self._call_llm_with_retry(
                initial_prompt.format(text=combined_text)
            )
            
            logger.info(f"Single batch processing completed: {len(docs)} chunks in 1 LLM call")
            return result
            
        except Exception as e:
            logger.error(f"Error in single batch refine chain: {str(e)}")
            return f"Analysis completed with {len(docs)} document chunks. Error occurred during processing: {str(e)}"
    
    async def _run_batch_refine_chain(self, docs: List[Document], initial_prompt: PromptTemplate, refine_prompt: PromptTemplate) -> str:
        """Optimized batch processing refine chain for large documents (>25 chunks)."""
        try:
            batch_size = config.ai.batch_size
            
            # Create batches
            batches = [docs[i:i + batch_size] for i in range(0, len(docs), batch_size)]
            logger.info(f"Created {len(batches)} batches of ~{batch_size} chunks each")
            
            # Process first batch
            first_batch_text = "\n\n---CHUNK SEPARATOR---\n\n".join(
                doc.page_content for doc in batches[0]
            )
            current_analysis = await self._call_llm_with_retry(
                initial_prompt.format(text=first_batch_text)
            )
            logger.info(f"Processed batch 1/{len(batches)} ({len(batches[0])} chunks)")
            
            # Process remaining batches with refinement
            for batch_idx, batch in enumerate(batches[1:], 2):
                # Add rate-limiting delay
                await asyncio.sleep(config.ai.rate_limit_delay_seconds)
                
                batch_text = "\n\n---CHUNK SEPARATOR---\n\n".join(
                    doc.page_content for doc in batch
                )
                current_analysis = await self._call_llm_with_retry(
                    refine_prompt.format(
                        existing_answer=current_analysis,
                        text=batch_text
                    )
                )
                logger.info(f"Processed batch {batch_idx}/{len(batches)} ({len(batch)} chunks)")
            
            logger.info(f"Batch processing completed: {len(docs)} chunks in {len(batches)} LLM calls")
            return current_analysis
            
        except Exception as e:
            logger.error(f"Error in batch refine chain: {str(e)}")
            return f"Analysis completed with {len(docs)} document chunks. Error occurred during processing: {str(e)}"
    
    async def _run_mock_refine_chain(self, docs: List[Document], initial_prompt: PromptTemplate, refine_prompt: PromptTemplate) -> str:
        """Mock implementation of refine chain for testing."""
        try:
            # Simulate refine chain behavior
            results = []
            
            # Process first document
            first_doc = docs[0] if docs else None
            if first_doc:
                initial_analysis = f"Analysis of {first_doc.metadata.get('file_name', 'document')}: "
                initial_analysis += f"This document contains {len(first_doc.page_content)} characters of content. "
                initial_analysis += "Key elements have been identified and analyzed according to the specified requirements."
                results.append(initial_analysis)
            
            # Process remaining documents
            for i, doc in enumerate(docs[1:], 1):
                refined_analysis = f"Additional analysis from {doc.metadata.get('file_name', f'document_{i}')}: "
                refined_analysis += f"This content adds {len(doc.page_content)} characters of information. "
                refined_analysis += "The analysis has been refined and expanded with these new insights."
                results.append(refined_analysis)
            
            # Combine results
            final_result = "COMPREHENSIVE DOCUMENT ANALYSIS\n\n"
            final_result += f"Analyzed {len(docs)} document chunks from uploaded files.\n\n"
            final_result += "ANALYSIS SUMMARY:\n"
            final_result += "\n".join(f"{i+1}. {result}" for i, result in enumerate(results))
            final_result += f"\n\nTotal content processed: {sum(len(doc.page_content) for doc in docs)} characters"
            final_result += f"\nFiles analyzed: {len(set(doc.metadata.get('file_name', 'unknown') for doc in docs))}"
            
            return final_result
            
        except Exception as e:
            logger.error(f"Error in mock refine chain: {str(e)}")
            return f"Analysis completed with {len(docs)} document chunks. Mock analysis generated due to processing constraints."
    
    async def _synthesizer_node(self, state: dict) -> dict:
        """Synthesize final results (for multi-document scenarios)."""
        try:
            logger.info("Synthesizing final results")
            state["processing_status"] = "synthesizing"
            
            final_result = state.get("final_result", "")
            
            # Add reasoning step
            self._add_reasoning_step(
                state, 
                "Finalizing Results", 
                f"The core analysis is complete. I will now format this into a clean, structured report for the user.",
                {"has_results": bool(final_result), "result_length": len(final_result)}
            )
            
            if not final_result:
                state["error"] = "No analysis results to synthesize"
                return state
            
            # For single analysis, just format the result nicely
            synthesized_result = f"""📊 DOCUMENT ANALYSIS RESULTS

{final_result}

---
Analysis completed using BMO Document Analysis Pod
Generated with comprehensive document processing and AI-powered insights."""
            
            state["final_result"] = synthesized_result
            state["processing_status"] = "complete"
            
            logger.info("Document analysis synthesis completed")
            return state
            
        except Exception as e:
            logger.error(f"Error in synthesizer node: {str(e)}")
            # Don't fail here, just return the original result
            state["processing_status"] = "synthesis_error"
            return state
    
    async def _call_llm_with_retry(self, prompt: str) -> str:
        """Call LLM with retry logic and error handling."""
        max_retries = config.ai.max_retries
        
        for attempt in range(max_retries):
            try:
                # Add timeout handling
                response = await asyncio.wait_for(
                    self.llm.ainvoke([HumanMessage(content=prompt)]),
                    timeout=config.ai.timeout_seconds
                )
                
                if hasattr(response, 'content'):
                    return response.content
                else:
                    return str(response)
                    
            except asyncio.TimeoutError:
                logger.warning(f"LLM call timed out (attempt {attempt + 1}/{max_retries})")
                if attempt == max_retries - 1:
                    raise RetryableAnalysisError("LLM call timed out after retries")
                
            except Exception as e:
                logger.warning(f"LLM call failed (attempt {attempt + 1}/{max_retries}): {str(e)}")
                if attempt == max_retries - 1:
                    raise RetryableAnalysisError(f"LLM call failed after retries: {str(e)}")
                
                # Exponential backoff
                await asyncio.sleep(2 ** attempt)
        
        raise RetryableAnalysisError("All retry attempts exhausted")
    
    async def analyze_documents(self, user_query: str, uploaded_files: Dict[str, Dict], 
                              template_instructions: str = "", session_id: str = "", reasoning_log: List = None) -> Dict[str, Any]:
        """Analyze documents through the complete workflow."""
        try:
            logger.info(f"Starting document analysis for {len(uploaded_files)} files")
            
            initial_state = {
                "user_query": user_query,
                "template_instructions": template_instructions,
                "uploaded_files": uploaded_files,
                "session_id": session_id,
                "doc_chunks": [],
                "planner_prompts": {},
                "final_result": "",
                "error": None,
                "processing_status": "started",
                "reasoning_steps": reasoning_log if reasoning_log is not None else []  # Use the passed-in log
            }
            
            # Run the graph
            result = await self.graph.ainvoke(initial_state)
            
            return {
                "result": result.get("final_result", "Analysis could not be completed"),
                "status": result.get("processing_status", "unknown"),
                "error": result.get("error"),
                "chunks_processed": len(result.get("doc_chunks", [])),
                "files_processed": len(uploaded_files),
                "reasoning_steps": result.get("reasoning_steps", []),
                "thoughts": result.get("thoughts", "")
            }
            
        except Exception as e:
            logger.error(f"Error in document analysis: {str(e)}")
            return {
                "result": "I apologize, but I encountered an error while analyzing your documents. Please try again or contact support.",
                "status": "error",
                "error": str(e),
                "chunks_processed": 0,
                "files_processed": 0
            }

class MockAnalysisLLM:
    """Mock LLM for document analysis testing."""
    
    async def ainvoke(self, messages):
        """Mock async invoke method for analysis."""
        # Simulate processing time
        await asyncio.sleep(0.2)
        
        content = messages[0].content if messages else ""
        
        # Pattern matching for different analysis prompts
        if "CORE_TASK" in content and "INSTRUCTIONS" in content:
            return MockAnalysisResponse("""CORE_TASK: Comprehensive document analysis
INSTRUCTIONS: Provide detailed analysis with key insights and findings""")
        
        elif "initial_prompt" in content and "refine_prompt" in content:
            return MockAnalysisResponse('''{
    "initial_prompt": "Analyze this document content thoroughly, identifying key themes, important information, and main insights. Provide a structured analysis that captures the essential elements.",
    "refine_prompt": "Building on the existing analysis: {existing_answer}\\n\\nRefine and expand this analysis by incorporating the key themes, important information, and insights from this additional content: {text}\\n\\nEnsure the refined analysis is comprehensive and well-integrated."
}''')
        
        else:
            return MockAnalysisResponse("Document analysis completed with comprehensive insights and detailed findings based on the provided requirements.")

class MockAnalysisResponse:
    """Mock response object for analysis."""
    def __init__(self, content: str):
        self.content = content

# Global Document Analysis Pod instance
document_analysis_pod = DocumentAnalysisPod()