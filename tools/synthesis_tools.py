import logging
import asyncio
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


async def synthesize_content(chunks: List[Dict], method: str, length: str, tone: str = 'professional', user_query: str = None) -> str:
    """
    Processes a list of text chunks to generate a coherent output using a specified method with a live LLM.
    The user_query is now passed to provide context to the synthesis process.
    """
    logger.info(f"Synthesizing {len(chunks)} chunks using method '{method}' for query: '{user_query}'.")

    if not chunks:
        # Provide helpful response based on the query type
        if user_query and 'section' in user_query.lower():
            # Extract section name more robustly
            query_lower = user_query.lower()
            if "'" in user_query:
                section_name = user_query.split("'")[1]
            elif '"' in user_query:
                section_name = user_query.split('"')[1] 
            else:
                # Extract section name from patterns like "Risk Factors section"
                import re
                # Try different patterns to extract section name
                patterns = [
                    r'summarize\s+the\s+([^\'\"]+?)\s+section',  # "Summarize the Risk Factors section"
                    r'(?:the\s+)?([A-Za-z\s]+?)\s+section',      # "Risk Factors section"
                ]
                section_name = "requested section"
                for pattern in patterns:
                    match = re.search(pattern, query_lower)
                    if match:
                        section_name = match.group(1).strip().title()
                        break
            return f"I couldn't find a '{section_name}' section in this document. Would you like me to search the entire document for related content instead?"
        elif user_query and any(word in user_query.lower() for word in ['search', 'find', 'mention']):
            return "I didn't find any matches for your search terms in this document. The content may not contain the specific terms you're looking for, or they might be phrased differently."
        else:
            return "I couldn't find relevant content to synthesize. This might mean the requested information isn't present in the document or needs different search terms."

    # --- Method 1: Simple LLM Call ---
    if method == 'simple_llm_call':
        full_text = "\n\n---\n\n".join([chunk["page_content"] for chunk in chunks])
        prompt = f"User Query: {user_query}\n\nBased on the following content, please generate a {length} response in a {tone} tone:\n\n<document_content>\n{full_text}\n</document_content>"
        response = await llm.ainvoke(prompt)
        return response.content if hasattr(response, 'content') else str(response)

    # --- Method 2: Refine ---
    elif method == 'refine':
        if not chunks:
            return "Cannot perform refine synthesis: No chunks provided."
        
        # Optimized batching: Process multiple chunks per LLM call
        BATCH_SIZE = 15  # Process 15 chunks at once - optimal for context window efficiency
        
        # Start with the first chunk as the base
        initial_chunk = chunks[0]["page_content"]
        initial_prompt = f"User Query: {user_query}\n\nPlease provide an initial {length} analysis of the following text in a {tone} tone:\n\n{initial_chunk}"
        response = await llm.ainvoke(initial_prompt)
        existing_answer = response.content if hasattr(response, 'content') else str(response)
        
        # Process remaining chunks in batches
        remaining_chunks = chunks[1:]
        
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

            response = await llm.ainvoke(refine_prompt)
            existing_answer = response.content if hasattr(response, 'content') else str(response)
            
        return existing_answer

    # --- Method 3: Map-Reduce (Improved) ---
    elif method == 'map_reduce':
        # The map prompt now includes the user's original query for better context.
        map_prompt_template = "User Query: {user_query}\n\nBased on the user's query, extract the key information from this piece of text: {text}"
        
        map_tasks = []
        for chunk in chunks:
            prompt = map_prompt_template.format(user_query=user_query, text=chunk["page_content"])
            map_tasks.append(llm.ainvoke(prompt))
            
        map_results_responses = await asyncio.gather(*map_tasks)
        map_results = [res.content if hasattr(res, 'content') else str(res) for res in map_results_responses]
        
        combined_map_results = "\n\n".join(map_results)
        
        # The reduce prompt also includes the user's query.
        reduce_prompt = f"User Query: {user_query}\n\nCombine the following key points into a single, {length} document in a {tone} tone. Ensure the final output directly addresses the user's query and is well-structured:\n\n<key_points>\n{combined_map_results}\n</key_points>"
        
        response = await llm.ainvoke(reduce_prompt)
        return response.content if hasattr(response, 'content') else str(response)

    else:
        return f"Error: Unknown synthesis method '{method}'. Available methods are 'simple_llm_call', 'refine', 'map_reduce'."
