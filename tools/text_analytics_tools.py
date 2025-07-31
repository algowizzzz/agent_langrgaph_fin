"""
Text analytics and natural language processing tools for document intelligence.
Provides sentiment analysis, readability scoring, keyword extraction, and text metrics.
"""

import re
import string
from collections import Counter
from typing import Dict, List, Any, Optional
import math

# Try to import optional advanced libraries
try:
    import textstat
    TEXTSTAT_AVAILABLE = True
except ImportError:
    TEXTSTAT_AVAILABLE = False

try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False

async def analyze_text_metrics(text: str) -> Dict[str, Any]:
    """
    Analyzes basic text metrics and readability scores.
    
    Args:
        text: Input text to analyze
        
    Returns:
        Dictionary with comprehensive text metrics
    """
    try:
        # Basic metrics
        word_count = len(text.split())
        char_count = len(text)
        char_count_no_spaces = len(text.replace(' ', ''))
        sentence_count = len(re.split(r'[.!?]+', text))
        paragraph_count = len([p for p in text.split('\n\n') if p.strip()])
        
        # Calculate averages
        avg_words_per_sentence = word_count / max(sentence_count, 1)
        avg_chars_per_word = char_count_no_spaces / max(word_count, 1)
        
        # Word length analysis
        words = re.findall(r'\b\w+\b', text.lower())
        word_lengths = [len(word) for word in words]
        
        result = {
            "status": "success",
            "basic_metrics": {
                "word_count": word_count,
                "character_count": char_count,
                "character_count_no_spaces": char_count_no_spaces,
                "sentence_count": sentence_count,
                "paragraph_count": paragraph_count,
                "avg_words_per_sentence": round(avg_words_per_sentence, 2),
                "avg_chars_per_word": round(avg_chars_per_word, 2)
            },
            "word_analysis": {
                "unique_words": len(set(words)),
                "lexical_diversity": round(len(set(words)) / max(word_count, 1), 3),
                "avg_word_length": round(sum(word_lengths) / max(len(word_lengths), 1), 2),
                "max_word_length": max(word_lengths) if word_lengths else 0,
                "min_word_length": min(word_lengths) if word_lengths else 0
            }
        }
        
        # Add readability scores if textstat is available
        if TEXTSTAT_AVAILABLE:
            result["readability_scores"] = {
                "flesch_reading_ease": textstat.flesch_reading_ease(text),
                "flesch_kincaid_grade": textstat.flesch_kincaid_grade(text),
                "gunning_fog": textstat.gunning_fog(text),
                "automated_readability_index": textstat.automated_readability_index(text),
                "coleman_liau_index": textstat.coleman_liau_index(text),
                "reading_time_minutes": round(textstat.reading_time(text, ms_per_char=14.69), 1)
            }
        else:
            # Basic readability calculation
            syllable_count = _count_syllables(text)
            if sentence_count > 0 and word_count > 0:
                flesch_score = 206.835 - (1.015 * avg_words_per_sentence) - (84.6 * (syllable_count / word_count))
                result["readability_scores"] = {
                    "flesch_reading_ease_basic": round(flesch_score, 1),
                    "note": "Install textstat package for advanced readability metrics"
                }
        
        return result
        
    except Exception as e:
        return {"status": "error", "error": str(e)}

async def extract_key_phrases(text: str, top_n: int = 10, min_length: int = 2) -> Dict[str, Any]:
    """
    Extracts key phrases and important terms from text.
    
    Args:
        text: Input text
        top_n: Number of top phrases to return
        min_length: Minimum word length to consider
        
    Returns:
        Dictionary with key phrases and word frequencies
    """
    try:
        # Clean and tokenize text
        text_clean = re.sub(r'[^\w\s]', ' ', text.lower())
        words = [word for word in text_clean.split() if len(word) >= min_length]
        
        # Remove common stop words (basic list)
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before', 'after',
            'above', 'below', 'between', 'among', 'this', 'that', 'these', 'those', 'i', 'me',
            'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours', 'yourself',
            'he', 'him', 'his', 'himself', 'she', 'her', 'hers', 'herself', 'it', 'its', 'itself',
            'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom',
            'this', 'that', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have',
            'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'can', 'shall'
        }
        
        filtered_words = [word for word in words if word not in stop_words]
        
        # Count word frequencies
        word_freq = Counter(filtered_words)
        
        # Extract bigrams (two-word phrases)
        bigrams = []
        for i in range(len(filtered_words) - 1):
            bigram = f"{filtered_words[i]} {filtered_words[i+1]}"
            bigrams.append(bigram)
        
        bigram_freq = Counter(bigrams)
        
        # Extract trigrams (three-word phrases)
        trigrams = []
        for i in range(len(filtered_words) - 2):
            trigram = f"{filtered_words[i]} {filtered_words[i+1]} {filtered_words[i+2]}"
            trigrams.append(trigram)
        
        trigram_freq = Counter(trigrams)
        
        return {
            "status": "success",
            "top_words": dict(word_freq.most_common(top_n)),
            "top_bigrams": dict(bigram_freq.most_common(top_n)),
            "top_trigrams": dict(trigram_freq.most_common(top_n)),
            "total_unique_words": len(word_freq),
            "total_unique_bigrams": len(bigram_freq),
            "total_unique_trigrams": len(trigram_freq)
        }
        
    except Exception as e:
        return {"status": "error", "error": str(e)}

async def analyze_sentiment(text: str) -> Dict[str, Any]:
    """
    Performs sentiment analysis on text.
    
    Args:
        text: Input text for sentiment analysis
        
    Returns:
        Dictionary with sentiment scores and classification
    """
    try:
        if TEXTBLOB_AVAILABLE:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity  # -1 (negative) to 1 (positive)
            subjectivity = blob.sentiment.subjectivity  # 0 (objective) to 1 (subjective)
            
            # Classify sentiment
            if polarity > 0.1:
                sentiment_label = "positive"
            elif polarity < -0.1:
                sentiment_label = "negative"
            else:
                sentiment_label = "neutral"
            
            return {
                "status": "success",
                "sentiment_score": round(polarity, 3),
                "subjectivity_score": round(subjectivity, 3),
                "sentiment_label": sentiment_label,
                "confidence": round(abs(polarity), 3),
                "library": "TextBlob"
            }
        else:
            # Basic lexicon-based sentiment analysis
            positive_words = {
                'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'awesome',
                'positive', 'beneficial', 'effective', 'successful', 'improved', 'better',
                'love', 'like', 'enjoy', 'happy', 'pleased', 'satisfied', 'perfect'
            }
            
            negative_words = {
                'bad', 'terrible', 'awful', 'horrible', 'negative', 'poor', 'worse', 'worst',
                'failed', 'failure', 'problem', 'issue', 'error', 'wrong', 'hate', 'dislike',
                'disappointed', 'unsatisfied', 'difficult', 'hard', 'challenging'
            }
            
            words = re.findall(r'\b\w+\b', text.lower())
            positive_count = sum(1 for word in words if word in positive_words)
            negative_count = sum(1 for word in words if word in negative_words)
            
            total_sentiment_words = positive_count + negative_count
            if total_sentiment_words > 0:
                sentiment_score = (positive_count - negative_count) / total_sentiment_words
            else:
                sentiment_score = 0
            
            # Classify
            if sentiment_score > 0.1:
                sentiment_label = "positive"
            elif sentiment_score < -0.1:
                sentiment_label = "negative"
            else:
                sentiment_label = "neutral"
            
            return {
                "status": "success",
                "sentiment_score": round(sentiment_score, 3),
                "sentiment_label": sentiment_label,
                "positive_words_found": positive_count,
                "negative_words_found": negative_count,
                "library": "Basic lexicon",
                "note": "Install TextBlob for advanced sentiment analysis"
            }
            
    except Exception as e:
        return {"status": "error", "error": str(e)}

async def extract_entities(text: str) -> Dict[str, Any]:
    """
    Extracts potential named entities from text using pattern matching.
    
    Args:
        text: Input text
        
    Returns:
        Dictionary with extracted entities
    """
    try:
        # Email addresses
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        
        # Phone numbers (basic patterns)
        phones = re.findall(r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b', text)
        
        # URLs
        urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
        
        # Dates (basic patterns)
        dates = re.findall(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b', text)
        
        # Money amounts
        money = re.findall(r'\$\s*\d+(?:,\d{3})*(?:\.\d{2})?|\b\d+(?:,\d{3})*(?:\.\d{2})?\s*(?:dollars?|USD|cents?)\b', text)
        
        # Percentages
        percentages = re.findall(r'\b\d+(?:\.\d+)?%\b', text)
        
        # Potential proper nouns (capitalized words not at sentence start)
        sentences = re.split(r'[.!?]+', text)
        proper_nouns = []
        for sentence in sentences:
            words = sentence.strip().split()
            for i, word in enumerate(words[1:], 1):  # Skip first word of sentence
                if word[0].isupper() and word.lower() not in ['the', 'and', 'or', 'but', 'with']:
                    proper_nouns.append(word)
        
        return {
            "status": "success",
            "entities": {
                "emails": list(set(emails)),
                "phone_numbers": list(set(phones)),
                "urls": list(set(urls)),
                "dates": list(set(dates)),
                "money_amounts": list(set(money)),
                "percentages": list(set(percentages)),
                "potential_names": list(set(proper_nouns))[:20]  # Limit to top 20
            },
            "entity_counts": {
                "emails": len(set(emails)),
                "phone_numbers": len(set(phones)),
                "urls": len(set(urls)),
                "dates": len(set(dates)),
                "money_amounts": len(set(money)),
                "percentages": len(set(percentages)),
                "potential_names": len(set(proper_nouns))
            }
        }
        
    except Exception as e:
        return {"status": "error", "error": str(e)}

def _count_syllables(text: str) -> int:
    """Helper function to count syllables in text (basic implementation)."""
    words = re.findall(r'\b\w+\b', text.lower())
    syllable_count = 0
    
    for word in words:
        # Count vowel groups
        vowels = re.findall(r'[aeiouy]+', word)
        syllables = len(vowels)
        
        # Adjust for silent e
        if word.endswith('e') and syllables > 1:
            syllables -= 1
        
        # Ensure at least 1 syllable per word
        syllable_count += max(1, syllables)
    
    return syllable_count