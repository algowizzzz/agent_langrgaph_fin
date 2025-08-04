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
        from langchain_anthropic import ChatAnthropic
        llm = ChatAnthropic(
            model=config.ai.anthropic_model,
            temperature=0,
            api_key=config.ai.anthropic_api_key
        )
        logger.info(f"Synthesis LLM initialized successfully with model: {config.ai.anthropic_model}")
    except Exception as e:
        llm_error = f"Failed to initialize ChatAnthropic for synthesis: {e}"
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

async def synthesize_content(documents: List[Dict], query: str, synthesis_type: str = "summary") -> Dict[str, Any]:
    """
    Synthesize content from multiple documents with proper error handling.
    """
    logger.info(f"Synthesizing {synthesis_type} for query: '{query}' from {len(documents)} documents")
    
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