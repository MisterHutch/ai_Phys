import nltk
from textblob import TextBlob
from typing import Dict, List, Optional
import re


class AnalysisService:
    def __init__(self):
        nltk_resources = [
            ('tokenizers', 'punkt_tab'),
            ('taggers', 'averaged_perceptron_tagger_eng'),
        ]
        for resource_type, resource_name in nltk_resources:
            try:
                nltk.data.find(f'{resource_type}/{resource_name}')
            except LookupError:
                try:
                    nltk.download(resource_name, quiet=True)
                except Exception:
                    pass

    def analyze_email(self, body_text: str, subject: str = '') -> Dict:
        """Analyze email content and return sentiment, keywords, and communication style"""
        combined_text = f"{subject} {body_text}".strip()

        if not combined_text:
            return {
                'sentiment_score': 0.0,
                'sentiment_label': 'neutral',
                'keywords': '',
                'communication_style': 'unknown',
                'urgency_level': 0,
            }

        blob = TextBlob(combined_text)

        sentiment_score = blob.sentiment.polarity
        sentiment_label = self._classify_sentiment(sentiment_score)
        keywords = self._extract_keywords(blob)
        communication_style = self._classify_communication_style(body_text)
        urgency_level = self._assess_urgency(combined_text)

        return {
            'sentiment_score': round(sentiment_score, 4),
            'sentiment_label': sentiment_label,
            'keywords': ','.join(keywords),
            'communication_style': communication_style,
            'urgency_level': urgency_level,
        }

    def _classify_sentiment(self, score: float) -> str:
        """Classify polarity score as positive, neutral, or negative"""
        if score > 0.1:
            return 'positive'
        elif score < -0.1:
            return 'negative'
        return 'neutral'

    def _extract_keywords(self, blob: TextBlob) -> List[str]:
        """Extract meaningful noun phrases from the text"""
        try:
            seen = set()
            keywords = []
            for phrase in blob.noun_phrases:
                cleaned = phrase.strip().lower()
                if cleaned and cleaned not in seen:
                    seen.add(cleaned)
                    keywords.append(cleaned)
            return keywords[:10]
        except LookupError:
            return []

    def _classify_communication_style(self, body_text: str) -> str:
        """Classify communication style based on message length and structure"""
        if not body_text:
            return 'unknown'
        word_count = len(body_text.split())
        if word_count < 20:
            return 'concise'
        elif word_count > 150:
            return 'detailed'
        return 'moderate'

    def _assess_urgency(self, text: str) -> int:
        """Return urgency level 0-3 based on keyword presence"""
        urgent_patterns = [
            r'\burgent\b', r'\basap\b', r'\bimmediately\b',
            r'\bcritical\b', r'\bemergency\b', r'\bdeadline\b',
            r'\btime.sensitive\b', r'\bpriority\b',
        ]
        lower = text.lower()
        matches = sum(1 for p in urgent_patterns if re.search(p, lower))
        if matches == 0:
            return 0
        elif matches == 1:
            return 1
        elif matches == 2:
            return 2
        return 3

    def summarize_analyses(self, analyses: List[Dict]) -> Optional[Dict]:
        """Summarize a list of analysis results for insights"""
        if not analyses:
            return None

        total = len(analyses)
        sentiment_counts = {'positive': 0, 'neutral': 0, 'negative': 0}
        style_counts: Dict[str, int] = {}
        avg_sentiment = 0.0
        avg_urgency = 0.0

        for a in analyses:
            label = a.get('sentiment_label', 'neutral')
            sentiment_counts[label] = sentiment_counts.get(label, 0) + 1
            style = a.get('communication_style', 'unknown')
            style_counts[style] = style_counts.get(style, 0) + 1
            avg_sentiment += a.get('sentiment_score', 0.0)
            avg_urgency += a.get('urgency_level', 0)

        dominant_style = max(style_counts, key=style_counts.get) if style_counts else 'unknown'

        return {
            'total_analyzed': total,
            'average_sentiment_score': round(avg_sentiment / total, 4),
            'sentiment_distribution': sentiment_counts,
            'dominant_communication_style': dominant_style,
            'communication_style_distribution': style_counts,
            'average_urgency_level': round(avg_urgency / total, 2),
        }


analysis_service = AnalysisService()
