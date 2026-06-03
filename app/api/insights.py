from fastapi import APIRouter, HTTPException
from ..services.gmail_service import gmail_service
from ..services.analysis_service import analysis_service
from ..models.database import db

router = APIRouter()

@router.get("/")
async def get_insights():
    """Get email insights including sentiment and communication style analysis"""
    try:
        if not gmail_service.is_authenticated():
            raise HTTPException(status_code=401, detail="Not authenticated with Gmail")

        profile = gmail_service.get_user_profile()
        if not profile:
            raise HTTPException(status_code=400, detail="Could not get user profile")

        user = db.get_user_by_email(profile['email'])
        if not user:
            raise HTTPException(status_code=400, detail="User not found in database")

        emails = db.get_user_emails(user['id'], limit=1000)
        analyses = db.get_email_analysis(user['id'], limit=1000)

        total_emails = len(emails)
        if total_emails == 0:
            return {"message": "No emails found. Try syncing first."}

        sent_count = len([e for e in emails if e['message_type'] == 'sent'])
        received_count = total_emails - sent_count

        analysis_summary = analysis_service.summarize_analyses(analyses)

        ratio = round(sent_count / received_count, 2) if received_count > 0 else 0
        personality_insights = [
            f"You have {total_emails} emails in your recent history",
            f"You send about {ratio} emails for every one you receive"
            if received_count > 0 else "You primarily send emails",
            "Communication style analysis requires more data" if total_emails < 50
            else "You have sufficient data for personality analysis",
        ]

        if analysis_summary:
            style = analysis_summary['dominant_communication_style']
            avg_score = analysis_summary['average_sentiment_score']
            personality_insights.append(
                f"Your dominant communication style is '{style}'"
            )
            personality_insights.append(
                f"Your average email sentiment is "
                f"{'positive' if avg_score > 0.1 else 'negative' if avg_score < -0.1 else 'neutral'}"
                f" (score: {avg_score})"
            )

        insights = {
            "total_emails_analyzed": total_emails,
            "communication_breakdown": {
                "sent": sent_count,
                "received": received_count,
                "sent_percentage": round((sent_count / total_emails) * 100, 2) if total_emails > 0 else 0,
            },
            "personality_insights": personality_insights,
            "sentiment_analysis": analysis_summary,
            "recommendations": [
                "Sync more emails for better insights",
                "Email patterns suggest regular communication habits",
                "Consider analyzing email timing patterns for productivity insights",
            ],
        }

        return insights

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
