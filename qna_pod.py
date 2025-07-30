import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import time
import asyncio
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END

from config import config

logger = logging.getLogger(__name__)

from typing_extensions import TypedDict

class QnAState(TypedDict):
    """State for Q&A Pod workflow."""
    question: str
    retrieved_context: List[Dict]
    answer: str
    source: str
    error: Optional[str]
    reasoning_steps: List[Dict[str, Any]]

class RetryableError(Exception):
    """Exception for errors that should trigger retry logic."""
    pass

class QnAPod:
    """Q&A Pod using mock data service with LangGraph workflow."""
    
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
        logger.info(f"🤔 Agent Reasoning - {step_name}: {thought}")
        return state

    def _setup_llm(self):
        """Initialize LLM with error handling."""
        try:
            if config.ai.anthropic_api_key and not config.ai.enable_mock_mode:
                from langchain_anthropic import ChatAnthropic
                self.llm = ChatAnthropic(
                    api_key=config.ai.anthropic_api_key,
                    model=config.ai.anthropic_model,
                    temperature=0.7
                )
                logger.info(f"Using Anthropic LLM: {config.ai.anthropic_model}")
            elif config.ai.openai_api_key and not config.ai.enable_mock_mode:
                from langchain_openai import ChatOpenAI
                self.llm = ChatOpenAI(
                    api_key=config.ai.openai_api_key,
                    model=config.ai.openai_model,
                    temperature=0.7
                )
                logger.info(f"Using OpenAI LLM: {config.ai.openai_model}")

            logger.info(f"LLM initialized: {type(self.llm).__name__}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {str(e)}. Please ensure API keys are set in your .env file.")
            raise e
    
    def _build_graph(self):
        """Build the LangGraph workflow."""
        workflow = StateGraph(QnAState)

        workflow.add_node("retrieve_from_knowledge_base", self._retrieve_from_knowledge_base)
        workflow.add_node("generate_qna_answer", self._generate_qna_answer)
        workflow.add_node("generate_general_answer", self._generate_general_answer)

        workflow.set_entry_point("retrieve_from_knowledge_base")
        workflow.add_conditional_edges(
            "retrieve_from_knowledge_base",
            self._should_use_retrieved_context,
            {
                "use_context": "generate_qna_answer",
                "use_general": "generate_general_answer"
            }
        )
        workflow.add_edge("generate_qna_answer", END)
        workflow.add_edge("generate_general_answer", END)
        
        self.graph = workflow.compile()
        logger.info("Q&A Pod graph compiled successfully")
    
    async def _retrieve_from_knowledge_base(self, state: dict) -> dict:
        """Placeholder for retrieving context."""
        self._add_reasoning_step(
            state,
            "Knowledge Base Search",
            "Searching internal knowledge base for relevant context to answer the user's question.",
            {"query": state.get("question")}
        )
        state["retrieved_context"] = []
        return state
    
    def _should_use_retrieved_context(self, state: dict) -> str:
        """Determine whether to use retrieved context or general knowledge."""
        if state.get("error"):
            return "use_general"
        
        if not state.get("retrieved_context", []):
            self._add_reasoning_step(
                state,
                "Knowledge Base Search",
                "No relevant context found in the internal knowledge base. Falling back to general LLM knowledge."
            )
            return "use_general"
        
        self._add_reasoning_step(
            state,
            "Context Analysis",
            "Found relevant context in the knowledge base. Preparing to generate a context-aware answer."
        )
        return "use_context"
    
    async def _generate_qna_answer(self, state: dict) -> dict:
        """Generate answer using retrieved context."""
        try:
            self._add_reasoning_step(
                state,
                "Contextual Answer Generation",
                "Generating a precise answer using the context retrieved from the BMO knowledge base."
            )
            retrieved_context = state.get("retrieved_context", [])
            question = state.get("question", "")
            context_text = self._format_context(retrieved_context)
            
            prompt = f"""Based on the following BMO internal documentation, please answer the user's question.

Context from BMO Documentation:
{context_text}

User Question: {question}

Please provide a helpful answer based on the BMO documentation above. If the context doesn't fully answer the question, mention what information is available and suggest contacting the appropriate department."""

            answer = await self._call_llm_with_retry(prompt)
            
            state["answer"] = answer
            state["source"] = "BMO Knowledge Base"
            return state
            
        except Exception as e:
            logger.error(f"Error generating QnA answer: {str(e)}")
            state["error"] = f"Failed to generate answer: {str(e)}"
            return await self._generate_general_answer(state)
    
    async def _generate_general_answer(self, state: dict) -> dict:
        """Generate answer using general knowledge."""
        try:
            self._add_reasoning_step(
                state,
                "General Answer Generation",
                "Using the general-purpose Large Language Model to answer the user's question."
            )
            question = state.get("question", "")
            
            prompt = f"""Please provide a helpful and professional response to this question: {question}

If this appears to be a BMO-specific question that you cannot answer with certainty, please suggest that the user contact the appropriate BMO department or check internal resources."""

            answer = await self._call_llm_with_retry(prompt)
            
            state["answer"] = answer
            state["source"] = "General LLM Knowledge"
            return state
            
        except Exception as e:
            logger.error(f"Error generating general answer: {str(e)}")
            state["answer"] = "I apologize, but I'm experiencing technical difficulties. Please try your question again or contact IT support for assistance."
            state["source"] = "Error Fallback"
            state["error"] = str(e)
            return state
    
    def _format_context(self, context_pairs: List[Dict]) -> str:
        """Format retrieved context for LLM prompt."""
        if not context_pairs:
            return "No relevant context found."
        
        formatted_context = []
        for i, pair in enumerate(context_pairs[:3], 1):
            category = pair.get('category', 'General')
            content = pair.get('content', '')
            question = pair.get('question', '')
            
            formatted_context.append(f"""
{i}. [{category}] {question}
   Answer: {content}
""")
        
        return "\n".join(formatted_context)
    
    async def _call_llm_with_retry(self, prompt: str) -> str:
        """Call LLM with retry logic and error handling."""
        max_retries = config.ai.max_retries
        
        for attempt in range(max_retries):
            try:
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
                    raise RetryableError("LLM call timed out after retries")
                
            except Exception as e:
                logger.warning(f"LLM call failed (attempt {attempt + 1}/{max_retries}): {str(e)}")
                if attempt == max_retries - 1:
                    raise RetryableError(f"LLM call failed after retries: {str(e)}")
                
                await asyncio.sleep(2 ** attempt)
        
        raise RetryableError("All retry attempts exhausted")
    
    async def process_question(self, question: str, reasoning_log: List = None) -> Dict[str, Any]:
        """Process a question through the Q&A workflow."""
        try:
            logger.info(f"Processing question: '{question[:50]}...'")
            
            initial_state = {
                "question": question,
                "retrieved_context": [],
                "answer": "",
                "source": "",
                "error": None,
                "reasoning_steps": reasoning_log if reasoning_log is not None else []
            }
            
            result = await self.graph.ainvoke(initial_state)
            
            return {
                "answer": result.get("answer", "No answer generated"),
                "source": result.get("source", "Unknown"),
                "error": result.get("error"),
                "context_used": len(result.get("retrieved_context", [])) > 0,
                "num_context_pairs": len(result.get("retrieved_context", [])),
                "reasoning_steps": result.get("reasoning_steps", [])
            }
            
        except Exception as e:
            logger.error(f"Error processing question: {str(e)}")
            return {
                "answer": "I apologize, but I encountered an error processing your question. Please try again or contact support.",
                "source": "Error Handler",
                "error": str(e),
                "context_used": False,
                "num_context_pairs": 0,
                "reasoning_steps": reasoning_log or []
            }

# Global Q&A Pod instance
qna_pod = QnAPod()
