import pytest
import tempfile
import os
from app.models.database import DatabaseManager


@pytest.fixture
def db():
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    manager = DatabaseManager(db_path=db_path)
    yield manager
    os.unlink(db_path)


def test_store_and_retrieve_analysis(db):
    user_id = db.create_user(email='test@example.com', name='Test User')

    email_data = {
        'id': 'msg001',
        'user_id': user_id,
        'thread_id': 'thread001',
        'subject': 'Hello',
        'sender_email': 'sender@example.com',
        'sender_name': 'Sender',
        'recipient_emails': 'test@example.com',
        'body_text': 'Hello there',
        'body_html': '',
        'date_sent': None,
        'date_received': None,
        'labels': '',
        'message_type': 'received',
    }
    db.store_email(email_data)

    analysis_data = {
        'sentiment_score': 0.5,
        'sentiment_label': 'positive',
        'keywords': 'hello',
        'communication_style': 'concise',
        'urgency_level': 0,
    }
    result = db.store_analysis('msg001', analysis_data)
    assert result is True

    analyses = db.get_email_analysis(user_id)
    assert len(analyses) == 1
    assert analyses[0]['email_id'] == 'msg001'
    assert analyses[0]['sentiment_label'] == 'positive'
    assert analyses[0]['communication_style'] == 'concise'
    assert analyses[0]['urgency_level'] == 0


def test_get_email_analysis_empty(db):
    user_id = db.create_user(email='empty@example.com')
    analyses = db.get_email_analysis(user_id)
    assert analyses == []


def test_store_analysis_replace(db):
    user_id = db.create_user(email='replace@example.com')

    email_data = {
        'id': 'msg002',
        'user_id': user_id,
        'thread_id': 'thread002',
        'subject': 'Test',
        'sender_email': 'a@example.com',
        'sender_name': 'A',
        'recipient_emails': 'replace@example.com',
        'body_text': 'Test body',
        'body_html': '',
        'date_sent': None,
        'date_received': None,
        'labels': '',
        'message_type': 'received',
    }
    db.store_email(email_data)

    db.store_analysis('msg002', {
        'sentiment_score': 0.1, 'sentiment_label': 'neutral',
        'keywords': '', 'communication_style': 'concise', 'urgency_level': 0,
    })
    db.store_analysis('msg002', {
        'sentiment_score': 0.8, 'sentiment_label': 'positive',
        'keywords': 'update', 'communication_style': 'detailed', 'urgency_level': 1,
    })

    analyses = db.get_email_analysis(user_id)
    assert len(analyses) == 1
    assert analyses[0]['sentiment_label'] == 'positive'
