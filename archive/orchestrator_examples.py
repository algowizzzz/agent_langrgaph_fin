"""
Orchestrator Example Workflows - Proven Test Cases
Based on 90% success rate testing from testing_31jul/
"""

PROVEN_WORKFLOWS = {
    "word_counting": {
        "description": "Count specific words or analyze text metrics",
        "user_queries": ["count of word risk", "how many times is X mentioned", "word frequency"],
        "proven_workflow": [
            {
                "step": 1,
                "tool": "search_uploaded_docs",
                "params": {"doc_name": "ACTIVE_DOCUMENT", "retrieve_full_doc": True},
                "output_type": "list[dict]",
                "tested": True
            },
            {
                "step": 2, 
                "tool": "analyze_text_metrics",
                "params": {"text": "EXTRACT_PAGE_CONTENT_FROM_STEP_1"},
                "data_transformation": "chunks[0]['page_content']",
                "output_type": "dict",
                "tested": True
            }
        ],
        "success_rate": "100%",
        "business_value": "Users get accurate word counts and text metrics"
    },
    
    "document_summary": {
        "description": "Generate professional document summaries",
        "user_queries": ["summarize document", "give me an overview", "what is this document about"],
        "proven_workflow": [
            {
                "step": 1,
                "tool": "search_uploaded_docs", 
                "params": {"doc_name": "ACTIVE_DOCUMENT", "retrieve_full_doc": True},
                "output_type": "list[dict]",
                "tested": True
            },
            {
                "step": 2,
                "tool": "synthesize_content",
                "params": {
                    "chunks": "CHUNKS_FROM_STEP_1", 
                    "method": "refine",
                    "length": "two paragraphs",
                    "tone": "professional",
                    "user_query": "USER_QUERY"
                },
                "output_type": "str",
                "tested": True
            }
        ],
        "success_rate": "100%",
        "business_value": "Users get comprehensive professional summaries"
    },
    
    "section_extraction": {
        "description": "Extract and explain specific document sections",
        "user_queries": ["explain the risk section", "what does X section say", "find information about Y"],
        "proven_workflow": [
            {
                "step": 1,
                "tool": "search_uploaded_docs",
                "params": {"doc_name": "ACTIVE_DOCUMENT", "query": "EXTRACT_KEY_TERMS_FROM_QUERY"},
                "output_type": "list[dict]",
                "tested": True
            },
            {
                "step": 2,
                "tool": "synthesize_content",
                "params": {
                    "chunks": "CHUNKS_FROM_STEP_1",
                    "method": "map_reduce", 
                    "length": "one paragraph",
                    "tone": "professional",
                    "user_query": "USER_QUERY"
                },
                "output_type": "str",
                "tested": True
            }
        ],
        "success_rate": "100%",
        "business_value": "Users get focused information about specific topics"
    },
    
    "key_concepts": {
        "description": "Identify key themes and concepts in documents",
        "user_queries": ["what are the main topics", "key concepts", "important themes"],
        "proven_workflow": [
            {
                "step": 1,
                "tool": "search_uploaded_docs",
                "params": {"doc_name": "ACTIVE_DOCUMENT", "retrieve_full_doc": True},
                "output_type": "list[dict]",
                "tested": True
            },
            {
                "step": 2,
                "tool": "extract_key_phrases", 
                "params": {"text": "EXTRACT_PAGE_CONTENT_FROM_STEP_1", "top_n": 10, "min_length": 3},
                "data_transformation": "chunks[0]['page_content']",
                "output_type": "dict",
                "tested": True
            }
        ],
        "success_rate": "100%",
        "business_value": "Users identify important document themes and concepts"
    },
    
    "document_sentiment": {
        "description": "Analyze document tone and sentiment",
        "user_queries": ["what is the tone", "sentiment analysis", "document perspective"],
        "proven_workflow": [
            {
                "step": 1,
                "tool": "search_uploaded_docs",
                "params": {"doc_name": "ACTIVE_DOCUMENT", "retrieve_full_doc": True},
                "output_type": "list[dict]",
                "tested": True
            },
            {
                "step": 2,
                "tool": "analyze_sentiment",
                "params": {"text": "EXTRACT_PAGE_CONTENT_FROM_STEP_1"},
                "data_transformation": "chunks[0]['page_content']", 
                "output_type": "dict",
                "tested": True
            }
        ],
        "success_rate": "100%",
        "business_value": "Users understand document tone and perspective"
    }
}

TOOL_SPECIFICATIONS = {
    "search_uploaded_docs": {
        "signature": "search_uploaded_docs(doc_name: str, query: str = None, retrieve_full_doc: bool = False) -> list[dict]",
        "description": "Search for content in uploaded documents. Use retrieve_full_doc=True for full document analysis.",
        "tested_examples": [
            {"params": {"doc_name": "riskandfinace.pdf", "query": "risk"}, "result": "1 relevant chunk found"},
            {"params": {"doc_name": "riskandfinace.pdf", "retrieve_full_doc": True}, "result": "Full document retrieved"}
        ],
        "output_format": "[{'page_content': 'text...', 'metadata': {...}}]",
        "success_rate": "100%"
    },
    
    "analyze_text_metrics": {
        "signature": "analyze_text_metrics(text: str) -> dict", 
        "description": "Analyzes comprehensive text metrics including word counts, readability scores, and structure analysis.",
        "tested_examples": [
            {"input": "Finance and risk document text", "result": "229 words, 13 risk mentions, readability scores"}
        ],
        "critical_requirement": "Input MUST be string, not list or dict",
        "data_transformation": "Extract chunks[0]['page_content'] from search results",
        "output_format": "{'basic_metrics': {'word_count': 229, ...}, 'readability_scores': {...}}",
        "success_rate": "100%"
    },
    
    "extract_key_phrases": {
        "signature": "extract_key_phrases(text: str, top_n: int = 10, min_length: int = 2) -> dict",
        "description": "Extracts key words, phrases, and important terms from text with frequency counts.",
        "tested_examples": [
            {"input": "Finance document", "result": "Top words: risk(12), financial(7), finance(6)"}
        ],
        "critical_requirement": "Input MUST be string, not list or dict", 
        "output_format": "{'top_words': {'risk': 12, ...}, 'top_bigrams': {...}, 'top_trigrams': {...}}",
        "success_rate": "100%"
    },
    
    "analyze_sentiment": {
        "signature": "analyze_sentiment(text: str) -> dict",
        "description": "Performs sentiment analysis returning sentiment score and classification.",
        "tested_examples": [
            {"input": "Financial document", "result": "Positive sentiment (score: 1.0)"}
        ],
        "critical_requirement": "Input MUST be string, not list or dict",
        "output_format": "{'sentiment_label': 'positive', 'sentiment_score': 1.0, ...}",
        "success_rate": "100%"
    },
    
    "synthesize_content": {
        "signature": "synthesize_content(chunks: list, method: str, length: str, tone: str, user_query: str) -> str",
        "description": "Generates cohesive content from document chunks using LLM synthesis.",
        "tested_examples": [
            {"method": "refine", "result": "1,271 char professional summary"},
            {"method": "map_reduce", "result": "1,030 char focused section extract"}
        ],
        "methods": ["refine", "map_reduce"],
        "input_format": "List of chunk dictionaries with page_content",
        "success_rate": "100%"
    }
}

DATA_TRANSFORMATION_PATTERNS = {
    "chunks_to_text": {
        "description": "Extract text content from search results for text analytics tools",
        "pattern": "chunks[0]['page_content']",
        "used_for": ["analyze_text_metrics", "extract_key_phrases", "analyze_sentiment", "extract_entities"],
        "critical": "Text analytics tools require string input, not chunk arrays"
    },
    
    "chunks_passthrough": {
        "description": "Pass chunk arrays directly to synthesis tools",
        "pattern": "chunks",
        "used_for": ["synthesize_content"],
        "note": "Synthesis tools expect chunk arrays with metadata"
    }
}

COMMON_FAILURES = {
    "data_type_mismatch": {
        "error": "'list' object has no attribute 'lower'",
        "cause": "Passing chunk array to text analytics tool",
        "solution": "Use DATA_TRANSFORMATION_PATTERNS['chunks_to_text']"
    },
    
    "no_chunks_found": {
        "error": "No chunks provided for synthesis", 
        "cause": "Search query too specific or boolean logic failing",
        "solution": "Use retrieve_full_doc=True or simpler search terms"
    }
}