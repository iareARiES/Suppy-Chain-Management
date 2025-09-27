"""
Natural Language Processing utilities for sentiment analysis and event classification.
"""
import logging
from typing import List, Dict, Optional, Tuple
import re
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to import transformers, fallback to VADER
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("Transformers not available, will use VADER for sentiment analysis")

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False
    logger.warning("VADER not available, sentiment analysis will be limited")

try:
    from langdetect import detect, DetectorFactory
    DetectorFactory.seed = 0  # For consistent results
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False
    logger.warning("langdetect not available, language detection will be skipped")


class SentimentAnalyzer:
    """Sentiment analysis using transformers with VADER fallback."""
    
    def __init__(self, model_name: str = "distilbert-base-uncased-finetuned-sst-2-english"):
        self.model_name = model_name
        self.transformer_pipeline = None
        self.vader_analyzer = None
        
        # Initialize transformers pipeline
        if TRANSFORMERS_AVAILABLE:
            try:
                self.transformer_pipeline = pipeline(
                    "sentiment-analysis",
                    model=model_name,
                    return_all_scores=True
                )
                logger.info(f"Initialized transformers sentiment pipeline with {model_name}")
            except Exception as e:
                logger.warning(f"Failed to initialize transformers pipeline: {e}")
                self.transformer_pipeline = None
        
        # Initialize VADER fallback
        if VADER_AVAILABLE:
            self.vader_analyzer = SentimentIntensityAnalyzer()
            logger.info("Initialized VADER sentiment analyzer")
    
    def analyze_sentiment(self, text: str) -> float:
        """
        Analyze sentiment of text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Sentiment score between -1 (negative) and 1 (positive)
        """
        if not text or len(text.strip()) < 10:
            return 0.0
        
        # Try transformers first
        if self.transformer_pipeline:
            try:
                results = self.transformer_pipeline(text[:512])  # Limit length
                if results and len(results) > 0:
                    # Get the first result (highest confidence)
                    result = results[0]
                    if result['label'] == 'POSITIVE':
                        return result['score']
                    else:  # NEGATIVE
                        return -result['score']
            except Exception as e:
                logger.warning(f"Transformers sentiment analysis failed: {e}")
        
        # Fallback to VADER
        if self.vader_analyzer:
            try:
                scores = self.vader_analyzer.polarity_scores(text)
                # Convert compound score (-1 to 1) to our scale
                return scores['compound']
            except Exception as e:
                logger.warning(f"VADER sentiment analysis failed: {e}")
        
        return 0.0
    
    def analyze_batch(self, texts: List[str]) -> List[float]:
        """Analyze sentiment for a batch of texts."""
        return [self.analyze_sentiment(text) for text in texts]


class EventClassifier:
    """Classify events from text using keyword matching and heuristics."""
    
    def __init__(self):
        # Event type keywords
        self.event_keywords = {
            'fire': [
                'fire', 'blaze', 'burning', 'burned', 'burned down', 'flames', 'smoke',
                'arson', 'ignition', 'combustion', 'inferno', 'conflagration'
            ],
            'flood': [
                'flood', 'flooding', 'flooded', 'water damage', 'inundation', 'deluge',
                'torrential rain', 'heavy rain', 'storm surge', 'overflow', 'submerged'
            ],
            'strike': [
                'strike', 'striking', 'strikers', 'labor strike', 'work stoppage',
                'walkout', 'protest', 'demonstration', 'union action', 'industrial action',
                'work stoppage', 'picketing', 'labor dispute'
            ],
            'inspection': [
                'inspection', 'inspected', 'audit', 'audited', 'compliance check',
                'regulatory review', 'safety inspection', 'quality inspection',
                'government inspection', 'authorities visit'
            ],
            'shutdown': [
                'shutdown', 'shut down', 'closed', 'closure', 'suspended', 'halted',
                'stopped production', 'ceased operations', 'temporary closure',
                'production halt', 'facility closed'
            ],
            'outage': [
                'outage', 'power outage', 'blackout', 'electrical failure',
                'equipment failure', 'system down', 'technical issue', 'malfunction',
                'breakdown', 'service interruption'
            ],
            'policy': [
                'policy change', 'new regulation', 'government policy', 'regulatory change',
                'compliance requirement', 'new law', 'legislation', 'rule change',
                'administrative change', 'bureaucratic change'
            ],
            'M&A': [
                'merger', 'acquisition', 'takeover', 'buyout', 'purchase', 'sold',
                'acquired', 'merged', 'consolidation', 'partnership', 'joint venture',
                'investment', 'funding', 'capital injection'
            ]
        }
        
        # Severity indicators
        self.severity_keywords = {
            'high': [
                'major', 'severe', 'critical', 'serious', 'significant', 'extensive',
                'massive', 'devastating', 'catastrophic', 'emergency', 'urgent',
                'complete', 'total', 'entire', 'all', 'widespread'
            ],
            'medium': [
                'moderate', 'partial', 'some', 'several', 'multiple', 'various',
                'considerable', 'substantial', 'notable', 'important'
            ],
            'low': [
                'minor', 'small', 'limited', 'slight', 'minimal', 'brief',
                'temporary', 'short-term', 'localized', 'isolated'
            ]
        }
    
    def classify_event(self, text: str) -> Tuple[str, str, float]:
        """
        Classify event type and severity from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Tuple of (event_type, severity, confidence)
        """
        text_lower = text.lower()
        
        # Find event type
        event_scores = {}
        for event_type, keywords in self.event_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                event_scores[event_type] = score
        
        if not event_scores:
            return 'other', 'low', 0.0
        
        # Get the event type with highest score
        event_type = max(event_scores, key=event_scores.get)
        event_confidence = min(event_scores[event_type] / 3.0, 1.0)  # Normalize to 0-1
        
        # Find severity
        severity_scores = {}
        for severity, keywords in self.severity_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                severity_scores[severity] = score
        
        if severity_scores:
            severity = max(severity_scores, key=severity_scores.get)
        else:
            severity = 'medium'  # Default
        
        return event_type, severity, event_confidence
    
    def extract_duration(self, text: str) -> Optional[float]:
        """
        Extract duration in hours from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Duration in hours or None if not found
        """
        # Duration patterns
        patterns = [
            r'(\d+)\s*hours?',
            r'(\d+)\s*hrs?',
            r'(\d+)\s*days?\s*\((\d+)\s*hours?\)',
            r'(\d+)\s*weeks?\s*\((\d+)\s*days?\)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                groups = match.groups()
                if len(groups) == 1:
                    return float(groups[0])
                elif len(groups) == 2:
                    # Convert days to hours
                    if 'day' in pattern:
                        return float(groups[0]) * 24
                    else:
                        return float(groups[1])
        
        return None


class LanguageDetector:
    """Language detection utility."""
    
    def __init__(self):
        self.available = LANGDETECT_AVAILABLE
    
    def detect_language(self, text: str) -> Optional[str]:
        """
        Detect language of text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Language code or None if detection fails
        """
        if not self.available or not text or len(text.strip()) < 10:
            return None
        
        try:
            return detect(text)
        except Exception as e:
            logger.warning(f"Language detection failed: {e}")
            return None


# Global instances
_sentiment_analyzer = None
_event_classifier = None
_language_detector = None

def get_sentiment_analyzer() -> SentimentAnalyzer:
    """Get global sentiment analyzer instance."""
    global _sentiment_analyzer
    if _sentiment_analyzer is None:
        _sentiment_analyzer = SentimentAnalyzer()
    return _sentiment_analyzer

def get_event_classifier() -> EventClassifier:
    """Get global event classifier instance."""
    global _event_classifier
    if _event_classifier is None:
        _event_classifier = EventClassifier()
    return _event_classifier

def get_language_detector() -> LanguageDetector:
    """Get global language detector instance."""
    global _language_detector
    if _language_detector is None:
        _language_detector = LanguageDetector()
    return _language_detector
