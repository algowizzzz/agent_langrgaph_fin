"""
Fixed synthesis tools with proper error handling instead of mock LLM
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Import configuration with error handling
try:
    from config import config
    config_available = True
except ImportError as e:
    logger.error(f"Config not available: {e}")
    config_available = False

# Initialize LLM with proper error handling
llm = None
llm_error = None

if config_available:
    try:
        # Try OpenAI first (since Anthropic is over quota)
        if config.ai.llm_provider == "openai" and config.ai.openai_api_key:
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(
                model=config.ai.openai_model,
                temperature=0,
                api_key=config.ai.openai_api_key
            )
            logger.info(f"Synthesis LLM initialized successfully with OpenAI model: {config.ai.openai_model}")
        # Fallback to Anthropic if OpenAI not configured
        elif config.ai.anthropic_api_key:
            from langchain_anthropic import ChatAnthropic
            llm = ChatAnthropic(
                model=config.ai.anthropic_model,
                temperature=0,
                api_key=config.ai.anthropic_api_key
            )
            logger.info(f"Synthesis LLM initialized successfully with Anthropic model: {config.ai.anthropic_model}")
        else:
            llm_error = "No valid API key found for OpenAI or Anthropic"
            logger.error(llm_error)
    except Exception as e:
        llm_error = f"Failed to initialize LLM for synthesis: {e}"
        logger.error(llm_error)
else:
    llm_error = "Configuration not available for LLM initialization"

# Connection limiting to prevent rate limit errors
CONNECTION_SEMAPHORE = asyncio.Semaphore(3)  # Max 3 concurrent API calls
MAX_RETRIES = 3
BASE_DELAY = 1  # Base delay for exponential backoff

class SynthesisError:
    """Structured error response for synthesis failures"""
    
    @staticmethod
    def create_error(error_type: str, message: str, suggested_action: str = None, retryable: bool = True) -> Dict:
        return {
            "error_type": error_type,
            "success": False,
            "message": message,
            "suggested_action": suggested_action,
            "retryable": retryable,
            "replanning_hints": {
                "synthesis_failed": True,
                "reason": message
            }
        }

async def llm_with_retry(prompt: str, max_retries: int = MAX_RETRIES) -> str:
    """LLM call with connection limiting and retry logic, proper error handling."""
    
    # Check if LLM is available
    if llm is None:
        error_msg = llm_error or "LLM not initialized"
        logger.error(f"LLM not available: {error_msg}")
        raise ValueError(f"LLM not available: {error_msg}")
    
    async with CONNECTION_SEMAPHORE:
        for attempt in range(max_retries):
            try:
                response = await llm.ainvoke(prompt)
                if hasattr(response, 'content'):
                    return response.content
                return str(response)
            except Exception as e:
                wait_time = BASE_DELAY * (2 ** attempt)
                logger.warning(f"LLM call attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"LLM call failed after {max_retries} attempts: {e}")
                    raise

async def refine_synthesis(documents: List[Dict], query: str, synthesis_type: str = "summary") -> Dict[str, Any]:
    """
    Refine approach for large document sets: process 10 chunks at a time, building cumulative analysis.
    """
    logger.info(f"🔄 Starting refine synthesis for {len(documents)} documents")
    
    try:
        # Initialize running analysis
        running_analysis = ""
        total_processed = 0
        batch_size = 10
        
        # Process documents in batches of 10
        for batch_start in range(0, len(documents), batch_size):
            batch_end = min(batch_start + batch_size, len(documents))
            batch = documents[batch_start:batch_end]
            batch_num = (batch_start // batch_size) + 1
            
            logger.info(f"🔄 Processing batch {batch_num}: documents {batch_start+1}-{batch_end}")
            
            # Extract content from current batch
            batch_content = []
            for i, doc in enumerate(batch):
                if isinstance(doc, dict):
                    if 'content' in doc:
                        content = doc['content']
                    elif 'page_content' in doc:
                        content = doc['page_content']
                    elif 'text' in doc:
                        content = doc['text']
                    else:
                        content = str(doc)
                else:
                    content = str(doc)
                
                # For Excel sheets, extract sheet name from content
                sheet_name = f"Sheet {batch_start + i + 1}"
                if "## Sheet:" in content:
                    lines = content.split('\n')
                    for line in lines:
                        if line.startswith('## Sheet:'):
                            sheet_name = line.replace('## Sheet:', '').strip()
                            break
                
                batch_content.append(f"=== {sheet_name} ===\n{content}")
            
            # Create refine prompt
            if batch_num == 1:
                # First batch - initial analysis
                refine_prompt = f"""Please analyze the following data to address this query: "{query}"

Data to analyze:
{chr(10).join(batch_content)}

Please provide a comprehensive analysis addressing the query. This is the first batch of data, so provide initial insights and findings.

Analysis:"""
            else:
                # Subsequent batches - refine previous analysis
                refine_prompt = f"""Please update and refine the previous analysis with new data.

Original Query: "{query}"

Previous Analysis:
{running_analysis}

New Data (Batch {batch_num}):
{chr(10).join(batch_content)}

Please provide an updated analysis that:
1. Integrates findings from the new data
2. Updates previous conclusions if needed
3. Maintains cumulative insights
4. Addresses the original query comprehensively

Updated Analysis:"""
            
            # Get LLM response for this batch
            try:
                batch_result = await llm_with_retry(refine_prompt)
                running_analysis = batch_result.strip()
                total_processed += len(batch)
                
                logger.info(f"✅ Completed batch {batch_num}, total processed: {total_processed}/{len(documents)}")
                
            except Exception as e:
                return SynthesisError.create_error(
                    error_type="refine_batch_failed",
                    message=f"Refine synthesis failed at batch {batch_num}: {str(e)}",
                    suggested_action="retry_or_reduce_batch_size",
                    retryable=True
                )
        
        # Final validation
        if not running_analysis or len(running_analysis.strip()) < 50:
            return SynthesisError.create_error(
                error_type="insufficient_refine_result",
                message="Refine synthesis produced insufficient content",
                suggested_action="retry_with_modified_approach",
                retryable=True
            )
        
        logger.info(f"🎉 Refine synthesis completed successfully for {len(documents)} documents")
        
        return {
            "success": True,
            "synthesis_type": synthesis_type,
            "query": query,
            "result": running_analysis,
            "documents_processed": len(documents),
            "content_length": len(running_analysis),
            "processing_details": {
                "approach": "refine",
                "batch_size": batch_size,
                "total_batches": (len(documents) + batch_size - 1) // batch_size,
                "model_used": config.ai.anthropic_model if config_available else "unknown",
                "documents_count": len(documents),
                "source": "documents"
            }
        }
        
    except Exception as e:
        return SynthesisError.create_error(
            error_type="refine_synthesis_failed",
            message=f"Refine synthesis failed: {str(e)}",
            suggested_action="fallback_to_single_pass_or_retry",
            retryable=True
        )

async def synthesize_content(documents: List[Dict], query: str, synthesis_type: str = "summary") -> Dict[str, Any]:
    """
    Synthesize content from multiple documents with proper error handling.
    Uses refine approach for >10 chunks, processing 10 at a time.
    """
    logger.info(f"Synthesizing {synthesis_type} for query: '{query}' from {len(documents)} documents")
    
    # 🔧 NEW: Check if we need refine approach (>10 chunks)
    if len(documents) > 10:
        logger.info(f"🔄 Using REFINE approach for {len(documents)} chunks (>10), processing 10 at a time")
        return await refine_synthesis(documents, query, synthesis_type)
    
    # Input validation
    if not documents:
        return SynthesisError.create_error(
            error_type="no_documents_provided",
            message="No documents provided for synthesis",
            suggested_action="provide_document_content_or_search_results",
            retryable=False
        )
    
    if not query:
        return SynthesisError.create_error(
            error_type="no_query_provided",
            message="No query provided for synthesis",
            suggested_action="provide_specific_synthesis_query",
            retryable=False
        )
    
    # Check for LLM availability
    if llm is None:
        return SynthesisError.create_error(
            error_type="llm_not_available",
            message=f"LLM not available for synthesis: {llm_error}",
            suggested_action="check_anthropic_api_configuration",
            retryable=False
        )
    
    try:
        # Process documents and extract content
        content_pieces = []
        llm_fallback_needed = False
        
        # Group chunks by source document for better multi-document handling
        source_groups = {}
        
        for i, doc in enumerate(documents):
            # Handle different document formats
            if isinstance(doc, dict):
                # Check if this is an error response that suggests using LLM knowledge
                if doc.get('error_type') == 'use_llm_knowledge':
                    llm_fallback_needed = True
                    continue
                
                # Get source document name for grouping
                source_doc = doc.get('source_document', f'Document_{i+1}')
                if source_doc not in source_groups:
                    source_groups[source_doc] = []
                
                # Extract content
                if 'content' in doc:
                    content = doc['content']
                elif 'page_content' in doc:
                    content = doc['page_content']
                elif 'text' in doc:
                    content = doc['text']
                else:
                    content = str(doc)
                
                source_groups[source_doc].append(content)
            else:
                # Handle non-dict documents
                source_doc = f'Document_{i+1}'
                if source_doc not in source_groups:
                    source_groups[source_doc] = []
                source_groups[source_doc].append(str(doc))
        
        # Format content with clear source document identification
        for source_name, chunks in source_groups.items():
            # Create a readable source name
            if 'car24_chpt1' in source_name.lower():
                display_name = "CAR Guidelines Chapter 1"
            elif 'car24_chpt7' in source_name.lower():
                display_name = "CAR Guidelines Chapter 7"
            elif 'riskandfinace' in source_name.lower():
                display_name = "Risk and Finance Guide"
            else:
                # Use a shortened version of the filename
                display_name = source_name.split('_')[-1] if '_' in source_name else source_name
            
            # Combine all chunks from this source
            combined_content = "\n\n".join(chunks)
            content_pieces.append(f"=== {display_name} ===\n{combined_content}")
        
        # If we have multiple sources, add a clear header for comparison
        if len(source_groups) > 1:
            comparison_header = f"\n\nYou are comparing {len(source_groups)} separate documents:\n"
            for i, source_name in enumerate(source_groups.keys(), 1):
                if 'car24_chpt1' in source_name.lower():
                    comparison_header += f"{i}. CAR Guidelines Chapter 1\n"
                elif 'car24_chpt7' in source_name.lower():
                    comparison_header += f"{i}. CAR Guidelines Chapter 7\n"
                else:
                    short_name = source_name.split('_')[-1] if '_' in source_name else source_name
                    comparison_header += f"{i}. {short_name}\n"
            content_pieces.insert(0, comparison_header)
        
        # Handle LLM fallback for knowledge base queries
        if not content_pieces and llm_fallback_needed:
            logger.info(f"No documents found, using LLM knowledge for query: {query}")
            
            # Create a prompt that uses LLM's built-in knowledge
            llm_prompt = f"""Please answer this query using your built-in knowledge:

Query: {query}

Please provide a comprehensive, professional response that:
1. Directly answers the question
2. Includes relevant details and context
3. Uses a helpful, informative tone
4. Is structured clearly and logically

If this is about finance, risk, or business topics, provide expert-level insights appropriate for a professional context.

Response:"""
            
            try:
                response = await llm_with_retry(llm_prompt)
                return {
                    "success": True,
                    "synthesis_type": synthesis_type,
                    "query": query,
                    "result": response,
                    "source": "llm_knowledge_base",
                    "confidence": 0.85  # High confidence for LLM built-in knowledge
                }
            except Exception as e:
                logger.error(f"LLM fallback failed: {e}")
                return SynthesisError.create_error(
                    error_type="llm_synthesis_failed",
                    message=f"Failed to generate response using LLM knowledge: {str(e)}",
                    suggested_action="check_llm_configuration_and_connectivity",
                    retryable=True
                )
        
        if not content_pieces:
            return SynthesisError.create_error(
                error_type="no_content_extracted",
                message="No text content could be extracted from provided documents",
                suggested_action="check_document_format_and_content",
                retryable=False
            )
        
        # Prepare synthesis prompt based on type
        if synthesis_type == "summary":
            prompt = f"""Please provide a comprehensive summary based on the following documents and query.

Query: {query}

Documents:
{chr(10).join(content_pieces)}

Please synthesize the information to answer the query with:
1. A clear, direct answer to the query
2. Supporting evidence from the documents
3. Key insights and patterns
4. Any limitations or gaps in the information

Synthesis:"""
        
        elif synthesis_type == "analysis":
            prompt = f"""Please provide a detailed analysis based on the following documents and query.

Query: {query}

Documents:
{chr(10).join(content_pieces)}

Please provide:
1. Detailed analysis addressing the query
2. Key findings and insights
3. Supporting evidence and examples
4. Implications and conclusions
5. Any recommendations or next steps

Analysis:"""
        
        elif synthesis_type == "comparison":
            prompt = f"""Please compare and contrast the information in the following documents related to the query.

Query: {query}

Documents:
{chr(10).join(content_pieces)}

Please provide:
1. Key similarities across documents
2. Important differences and contrasts
3. Unique insights from each document
4. Overall synthesis addressing the query

Comparison:"""
        
        elif synthesis_type == "system_awareness":
            # Special handling for system awareness queries to list actual tools
            prompt = f"""The user is asking about system capabilities. Please provide a detailed response using the provided system information.

Query: {query}

System Information:
{chr(10).join(content_pieces)}

Requirements:
- If the query asks about "tools", list ALL individual tool names with descriptions
- If there's an "available_tools" section with "all_tools", enumerate each tool specifically
- Include the total number of tools available
- Be specific and comprehensive, not just categorical
- Use the exact tool names and descriptions from the data
- If there are 23 tools, list all 23 tools individually

Response:"""
        
        else:
            prompt = f"""Please synthesize the following documents to address the query.

Query: {query}
Synthesis Type: {synthesis_type}

Documents:
{chr(10).join(content_pieces)}

Please provide a comprehensive response addressing the query based on the document content.

Response:"""
        
        # Perform synthesis with retry logic
        try:
            synthesis_result = await llm_with_retry(prompt)
        except Exception as e:
            return SynthesisError.create_error(
                error_type="llm_call_failed",
                message=f"LLM synthesis failed: {str(e)}",
                suggested_action="check_api_key_and_retry",
                retryable=True
            )
        
        # Validate result
        if not synthesis_result or len(synthesis_result.strip()) < 50:
            return SynthesisError.create_error(
                error_type="insufficient_synthesis_result",
                message="LLM returned insufficient synthesis content",
                suggested_action="retry_with_modified_prompt",
                retryable=True
            )
        
        logger.info(f"Successfully synthesized {synthesis_type} for query '{query}'")
        
        # Add source indication for Q&A responses using LLM knowledge
        final_result = synthesis_result.strip()
        if llm_fallback_needed and synthesis_type in ["qa_response", "summary"]:
            final_result += "\n\n*Source: LLM Built-in Knowledge (no relevant documents found in internal knowledge base)*"
        
        return {
            "success": True,
            "synthesis_type": synthesis_type,
            "query": query,
            "result": final_result,
            "documents_processed": len(documents),
            "content_length": len(synthesis_result),
            "processing_details": {
                "model_used": config.ai.anthropic_model if config_available else "unknown",
                "prompt_length": len(prompt),
                "documents_count": len(documents),
                "source": "llm_knowledge" if llm_fallback_needed else "documents"
            }
        }
        
    except Exception as e:
        logger.error(f"Error during content synthesis: {e}")
        return SynthesisError.create_error(
            error_type="synthesis_processing_error",
            message=f"Error during synthesis processing: {str(e)}",
            suggested_action="check_input_data_and_retry",
            retryable=True
        )

async def generate_summary(text: str, max_length: int = 500) -> Dict[str, Any]:
    """
    Generate a summary of the provided text with proper error handling.
    """
    logger.info(f"Generating summary of {len(text)} characters (max length: {max_length})")
    
    if not text or not text.strip():
        return SynthesisError.create_error(
            error_type="no_text_provided",
            message="No text provided for summary generation",
            suggested_action="provide_text_content",
            retryable=False
        )
    
    if llm is None:
        return SynthesisError.create_error(
            error_type="llm_not_available",
            message=f"LLM not available for summary generation: {llm_error}",
            suggested_action="check_anthropic_api_configuration",
            retryable=False
        )
    
    try:
        prompt = f"""Please provide a concise summary of the following text in approximately {max_length} characters or less.

Text to summarize:
{text}

Summary:"""
        
        summary_result = await llm_with_retry(prompt)
        
        if not summary_result or len(summary_result.strip()) < 20:
            return SynthesisError.create_error(
                error_type="insufficient_summary_result",
                message="LLM returned insufficient summary content",
                suggested_action="retry_with_modified_prompt",
                retryable=True
            )
        
        # Trim if necessary
        if len(summary_result) > max_length:
            summary_result = summary_result[:max_length-3] + "..."
        
        logger.info(f"Successfully generated summary of {len(summary_result)} characters")
        
        return {
            "success": True,
            "original_length": len(text),
            "summary_length": len(summary_result),
            "summary": summary_result.strip(),
            "compression_ratio": len(summary_result) / len(text),
            "processing_details": {
                "model_used": config.ai.anthropic_model if config_available else "unknown",
                "max_length_requested": max_length
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        return SynthesisError.create_error(
            error_type="summary_generation_error",
            message=f"Error generating summary: {str(e)}",
            suggested_action="check_text_format_and_retry",
            retryable=True
        )