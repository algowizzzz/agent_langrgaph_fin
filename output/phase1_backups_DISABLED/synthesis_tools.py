import logging
import asyncio
import time
from typing import List, Dict

# Use the actual config to get API keys
from config import config
from langchain_anthropic import ChatAnthropic

logger = logging.getLogger(__name__)

# Initialize the live LLM
try:
    if not config.ai.anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY is not set in the environment or .env file.")
    llm = ChatAnthropic(
        model=config.ai.anthropic_model,
        temperature=0.3,
        max_tokens=4096,
        api_key=config.ai.anthropic_api_key
    )
    logger.info(f"Synthesis LLM initialized successfully with model: {config.ai.anthropic_model}")
except Exception as e:
    logger.error(f"Failed to initialize ChatAnthropic for synthesis: {e}")
    class FallbackMockLLM:
        async def ainvoke(self, prompt: str):
            return f"ERROR: LLM not initialized. Could not process prompt: '{prompt[:100]}...'"
    llm = FallbackMockLLM()

# Connection limiting to prevent rate limit errors
CONNECTION_SEMAPHORE = asyncio.Semaphore(3)  # Max 3 concurrent API calls
MAX_RETRIES = 3
BASE_DELAY = 1  # Base delay for exponential backoff

async def llm_with_retry(prompt: str, max_retries: int = MAX_RETRIES) -> str:
    """LLM call with connection limiting and retry logic for rate limit errors."""
    async with CONNECTION_SEMAPHORE:
        for attempt in range(max_retries):
            try:
                response = await llm.ainvoke(prompt)
                return response.content if hasattr(response, 'content') else str(response)
            except Exception as e:
                error_str = str(e)
                if "rate_limit_error" in error_str or "429" in error_str:
                    if attempt < max_retries - 1:
                        delay = BASE_DELAY * (2 ** attempt)  # Exponential backoff
                        logger.warning(f"Rate limit hit, retrying in {delay}s (attempt {attempt + 1}/{max_retries})")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        logger.error(f"Rate limit exceeded after {max_retries} attempts")
                        raise e
                else:
                    # Non-rate-limit error, don't retry
                    logger.error(f"LLM call failed with non-rate-limit error: {e}")
                    raise e
        return f"Error: Failed to get response after {max_retries} attempts"


async def synthesize_content(chunks: List[Dict], method: str, length: str, tone: str = 'professional', user_query: str = None) -> str:
    """
    Processes a list of text chunks to generate a coherent output using a specified method with a live LLM.
    The user_query is now passed to provide context to the synthesis process.
    """
    # Input validation - handle common data type issues
    if isinstance(chunks, str):
        logger.warning(f"Received string instead of chunks list: {chunks}")
        return f"Error: Expected document chunks, but received placeholder text '{chunks}'. This indicates a data flow issue in the processing pipeline."
    
    if not isinstance(chunks, list):
        logger.error(f"Invalid input type for synthesize_content: expected list, got {type(chunks)}")
        return f"Error: synthesize_content requires a list of document chunks, but received {type(chunks).__name__}."
    
    if not chunks:
        logger.warning("Received empty chunks list for synthesis")
        return "No content available to synthesize. Please ensure document chunks are provided."
    
    # Filter out error objects and keep only valid chunks
    valid_chunks = []
    error_messages = []
    
    for chunk in chunks:
        if isinstance(chunk, dict):
            if "error" in chunk:
                # This is an error object from search_multiple_docs
                error_msg = chunk.get("error", "Unknown error")
                source_doc = chunk.get("source_document", "Unknown document")
                error_messages.append(f"Document '{source_doc}': {error_msg}")
                logger.warning(f"Skipping error chunk: {error_msg} for {source_doc}")
            elif "page_content" in chunk:
                # This is a valid document chunk
                valid_chunks.append(chunk)
            else:
                logger.warning(f"Skipping invalid chunk structure: {list(chunk.keys())}")
        else:
            logger.warning(f"Skipping non-dict chunk: {type(chunk)}")
    
    # Check if we have any valid chunks to process
    if not valid_chunks:
        if error_messages:
            error_summary = "; ".join(error_messages)
            return f"Unable to synthesize content due to errors: {error_summary}"
        else:
            return "No valid document chunks found for synthesis."
    
    # Log what we're working with
    if error_messages:
        logger.warning(f"Proceeding with {len(valid_chunks)} valid chunks, skipping {len(error_messages)} error chunks")
    
    logger.info(f"Synthesizing {len(valid_chunks)} chunks using method '{method}' for query: '{user_query}'.")

    # --- Method 1: Simple LLM Call ---
    if method == 'simple_llm_call':
        full_text = "\n\n---\n\n".join([chunk["page_content"] for chunk in valid_chunks])
        prompt = f"User Query: {user_query}\n\nBased on the following content, please generate a {length} response in a {tone} tone:\n\n<document_content>\n{full_text}\n</document_content>"
        return await llm_with_retry(prompt)

    # --- Method 2: Refine ---
    elif method == 'refine':
        if not valid_chunks:
            return "Cannot perform refine synthesis: No valid chunks provided."
        
        # Optimized batching: Process multiple chunks per LLM call
        BATCH_SIZE = 15  # Process 15 chunks at once - optimal for context window efficiency
        
        # Start with the first chunk as the base
        initial_chunk = valid_chunks[0]["page_content"]
        initial_prompt = f"User Query: {user_query}\n\nPlease provide an initial {length} analysis of the following text in a {tone} tone:\n\n{initial_chunk}"
        existing_answer = await llm_with_retry(initial_prompt)
        
        # Process remaining chunks in batches
        remaining_chunks = valid_chunks[1:]
        
        for batch_start in range(0, len(remaining_chunks), BATCH_SIZE):
            batch_end = min(batch_start + BATCH_SIZE, len(remaining_chunks))
            batch_chunks = remaining_chunks[batch_start:batch_end]
            
            # Combine multiple chunks into one batch
            batch_content = "\n\n--- Document Section ---\n".join([chunk["page_content"] for chunk in batch_chunks])
            
            batch_num = (batch_start // BATCH_SIZE) + 1
            total_batches = (len(remaining_chunks) + BATCH_SIZE - 1) // BATCH_SIZE
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch_chunks)} chunks)")
            
            refine_prompt = f"""User Query: {user_query}

You have an existing analysis:
<existing_analysis>
{existing_answer}
</existing_analysis>

Please refine this analysis with the new information below. Process ALL the document sections provided and create a cohesive {length} response in a {tone} tone:

<new_information>
{batch_content}
</new_information>

Instructions:
- Integrate insights from ALL document sections above
- Maintain consistency with the existing analysis
- Ensure comprehensive coverage of the new information
- Create a unified, well-structured response"""

            existing_answer = await llm_with_retry(refine_prompt)
            
        return existing_answer

    # --- Method 3: Map-Reduce (Rate-Limited) ---
    elif method == 'map_reduce':
        # The map prompt now includes the user's original query for better context.
        map_prompt_template = "User Query: {user_query}\n\nBased on the user's query, extract the key information from this piece of text: {text}"
        
        # Process chunks with connection limiting to prevent rate limit errors
        map_results = []
        total_chunks = len(valid_chunks)
        logger.info(f"Processing {total_chunks} chunks with rate limiting (max 3 concurrent)")
        
        # Create tasks but let the semaphore control concurrency
        async def process_chunk(chunk):
            prompt = map_prompt_template.format(user_query=user_query, text=chunk["page_content"])
            return await llm_with_retry(prompt)
        
        # Process all chunks with automatic rate limiting via semaphore
        map_tasks = [process_chunk(chunk) for chunk in valid_chunks]
        map_results = await asyncio.gather(*map_tasks)
        
        combined_map_results = "\n\n".join(map_results)
        
        # The reduce prompt also includes the user's query.
        reduce_prompt = f"User Query: {user_query}\n\nCombine the following key points into a single, {length} document in a {tone} tone. Ensure the final output directly addresses the user's query and is well-structured:\n\n<key_points>\n{combined_map_results}\n</key_points>"
        
        response = await llm_with_retry(reduce_prompt)
        return response

    else:
        return f"Error: Unknown synthesis method '{method}'. Available methods are 'simple_llm_call', 'refine', 'map_reduce'."
