import pytest
from app.services.analysis_service import AnalysisService


@pytest.fixture
def service():
    return AnalysisService()


def test_analyze_email_positive(service):
    result = service.analyze_email(
        body_text="Thank you so much! This is excellent and wonderful news.",
        subject="Great update"
    )
    assert result['sentiment_label'] == 'positive'
    assert result['sentiment_score'] > 0.1
    assert result['communication_style'] == 'concise'


def test_analyze_email_negative(service):
    result = service.analyze_email(
        body_text="This is terrible and awful. Very disappointing and bad.",
        subject="Problem"
    )
    assert result['sentiment_label'] == 'negative'
    assert result['sentiment_score'] < -0.1


def test_analyze_email_neutral(service):
    result = service.analyze_email(
        body_text="Please review the attached document by end of day.",
        subject="Document"
    )
    assert result['sentiment_label'] in ('neutral', 'positive', 'negative')
    assert 'sentiment_score' in result


def test_analyze_email_empty(service):
    result = service.analyze_email(body_text='', subject='')
    assert result['sentiment_score'] == 0.0
    assert result['sentiment_label'] == 'neutral'
    assert result['communication_style'] == 'unknown'
    assert result['urgency_level'] == 0


def test_communication_style_concise(service):
    result = service.analyze_email(body_text="OK sounds good.", subject="Re")
    assert result['communication_style'] == 'concise'


def test_communication_style_detailed(service):
    long_text = " ".join(["word"] * 200)
    result = service.analyze_email(body_text=long_text, subject="Long email")
    assert result['communication_style'] == 'detailed'


def test_communication_style_moderate(service):
    moderate_text = " ".join(["word"] * 80)
    result = service.analyze_email(body_text=moderate_text, subject="Moderate")
    assert result['communication_style'] == 'moderate'


def test_urgency_detection(service):
    result = service.analyze_email(
        body_text="This is urgent and critical! Please respond immediately.",
        subject="ASAP"
    )
    assert result['urgency_level'] >= 1


def test_no_urgency(service):
    result = service.analyze_email(
        body_text="Let me know when you get a chance.",
        subject="Casual email"
    )
    assert result['urgency_level'] == 0


def test_keywords_extracted(service):
    result = service.analyze_email(
        body_text="The project deadline is next week. The team meeting is on Friday.",
        subject="Project update"
    )
    assert isinstance(result['keywords'], str)


def test_summarize_analyses_empty(service):
    result = service.summarize_analyses([])
    assert result is None


def test_summarize_analyses(service):
    analyses = [
        {'sentiment_score': 0.5, 'sentiment_label': 'positive',
         'communication_style': 'concise', 'urgency_level': 0, 'keywords': ''},
        {'sentiment_score': -0.3, 'sentiment_label': 'negative',
         'communication_style': 'detailed', 'urgency_level': 2, 'keywords': ''},
        {'sentiment_score': 0.0, 'sentiment_label': 'neutral',
         'communication_style': 'concise', 'urgency_level': 0, 'keywords': ''},
    ]
    summary = service.summarize_analyses(analyses)
    assert summary is not None
    assert summary['total_analyzed'] == 3
    assert summary['sentiment_distribution']['positive'] == 1
    assert summary['sentiment_distribution']['negative'] == 1
    assert summary['sentiment_distribution']['neutral'] == 1
    assert summary['dominant_communication_style'] == 'concise'
    assert isinstance(summary['average_sentiment_score'], float)
    assert isinstance(summary['average_urgency_level'], float)
