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
        for i, doc in enumerate(documents):
            # Handle different document formats
            if isinstance(doc, dict):
                if 'content' in doc:
                    content_pieces.append(f"Document {i+1}: {doc['content']}")
                elif 'page_content' in doc:
                    content_pieces.append(f"Document {i+1}: {doc['page_content']}")
                elif 'text' in doc:
                    content_pieces.append(f"Document {i+1}: {doc['text']}")
                else:
                    # Try to extract any text content
                    text_content = str(doc)
                    content_pieces.append(f"Document {i+1}: {text_content}")
            else:
                content_pieces.append(f"Document {i+1}: {str(doc)}")
        
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
        
        return {
            "success": True,
            "synthesis_type": synthesis_type,
            "query": query,
            "result": synthesis_result.strip(),
            "documents_processed": len(documents),
            "content_length": len(synthesis_result),
            "processing_details": {
                "model_used": config.ai.anthropic_model if config_available else "unknown",
                "prompt_length": len(prompt),
                "documents_count": len(documents)
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