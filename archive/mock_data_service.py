import json
import re
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import logging
from config import config

logger = logging.getLogger(__name__)

class MockDataService:
    """Service for retrieving mock BMO knowledge base data using keyword matching."""
    
    def __init__(self, data_file_path: str = None):
        self.data_file_path = data_file_path or config.mock_data.file_path
        self.qa_data = {}
        self.load_data()
    
    def load_data(self) -> None:
        """Load mock data from JSON file."""
        try:
            data_path = Path(self.data_file_path)
            if not data_path.exists():
                logger.error(f"Mock data file not found: {self.data_file_path}")
                return
                
            with open(data_path, 'r') as f:
                self.qa_data = json.load(f)
            
            logger.info(f"Loaded {len(self.qa_data.get('bmo_qa_pairs', []))} mock Q&A pairs")
            
        except Exception as e:
            logger.error(f"Error loading mock data: {str(e)}")
            self.qa_data = {"bmo_qa_pairs": [], "general_responses": []}
    
    def _calculate_keyword_score(self, query: str, keywords: List[str]) -> float:
        """Calculate keyword match score between query and keyword list."""
        query_lower = query.lower()
        query_words = set(re.findall(r'\b\w+\b', query_lower))
        
        # Direct keyword matches
        keyword_matches = 0
        for keyword in keywords:
            if keyword.lower() in query_lower:
                keyword_matches += 1
        
        # Word-level matches
        word_matches = 0
        for keyword in keywords:
            keyword_words = set(re.findall(r'\b\w+\b', keyword.lower()))
            word_matches += len(query_words.intersection(keyword_words))
        
        # Calculate score (0.0 to 1.0)
        total_possible_matches = len(keywords) + sum(len(re.findall(r'\b\w+\b', kw)) for kw in keywords)
        if total_possible_matches == 0:
            return 0.0
            
        raw_score = (keyword_matches * 2 + word_matches) / max(total_possible_matches, 1)
        return min(raw_score, 1.0)
    
    def retrieve_from_mock(self, question: str) -> List[Dict]:
        """Retrieve relevant mock context based on keyword matching."""
        try:
            if not question or not question.strip():
                return []
            
            qa_pairs = self.qa_data.get('bmo_qa_pairs', [])
            if not qa_pairs:
                logger.warning("No mock data available")
                return []
            
            # Score all Q&A pairs
            scored_pairs = []
            for pair in qa_pairs:
                keywords = pair.get('keywords', [])
                score = self._calculate_keyword_score(question, keywords)
                
                if score > 0:  # Only include pairs with some relevance
                    scored_pairs.append({
                        'content': pair.get('answer', ''),
                        'question': pair.get('question', ''),
                        'category': pair.get('category', 'General'),
                        'score': score,
                        'confidence': pair.get('confidence', 0.5),
                        'id': pair.get('id', 'unknown')
                    })
            
            # Sort by score (descending) and return top results
            scored_pairs.sort(key=lambda x: x['score'], reverse=True)
            
            # Filter by minimum threshold
            threshold = config.mock_data.keyword_match_threshold
            relevant_pairs = [pair for pair in scored_pairs if pair['score'] >= threshold]
            
            logger.info(f"Found {len(relevant_pairs)} relevant pairs for query: '{question[:50]}...'")
            return relevant_pairs[:5]  # Return top 5 matches
            
        except Exception as e:
            logger.error(f"Error retrieving mock data: {str(e)}")
            return []
    
    def get_general_response(self, query: str) -> Optional[str]:
        """Get a general response for common queries."""
        try:
            general_responses = self.qa_data.get('general_responses', [])
            
            for response_data in general_responses:
                keywords = response_data.get('keywords', [])
                score = self._calculate_keyword_score(query, keywords)
                
                if score >= 0.3:  # Lower threshold for general responses
                    return response_data.get('response', '')
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting general response: {str(e)}")
            return None
    
    def get_stats(self) -> Dict:
        """Get statistics about the mock data."""
        return {
            'total_qa_pairs': len(self.qa_data.get('bmo_qa_pairs', [])),
            'categories': list(set(pair.get('category', 'Unknown') 
                                 for pair in self.qa_data.get('bmo_qa_pairs', []))),
            'last_updated': self.qa_data.get('metadata', {}).get('last_updated', 'Unknown'),
            'version': self.qa_data.get('metadata', {}).get('version', '1.0')
        }

# Global instance
mock_data_service = MockDataService()