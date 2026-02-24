from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, List, Optional
from ..services.gmail_service import gmail_service
from ..services.analysis_service import analysis_service
from ..models.database import db

router = APIRouter()

class OAuthConfig(BaseModel):
    client_id: str
    client_secret: str
    project_id: str

class AuthCode(BaseModel):
    code: str

@router.get("/auth/status")
async def get_auth_status():
    """Check Gmail authentication status"""
    is_authenticated = gmail_service.is_authenticated()
    profile = None
    
    if is_authenticated:
        profile = gmail_service.get_user_profile()
    
    return {
        "authenticated": is_authenticated,
        "profile": profile
    }

@router.post("/auth/setup")
async def setup_oauth(config: OAuthConfig):
    """Setup OAuth flow"""
    try:
        client_config = {
            "installed": {
                "client_id": config.client_id,
                "client_secret": config.client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob"]
            }
        }
        
        auth_url = gmail_service.setup_oauth_flow(client_config)
        
        return {
            "auth_url": auth_url,
            "message": "Visit the auth_url to authorize the application"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/auth/complete")
async def complete_oauth(auth_code: AuthCode):
    """Complete OAuth flow with authorization code"""
    try:
        success = gmail_service.complete_oauth_flow(auth_code.code)
        
        if success:
            # Get user profile and create/update user in database
            profile = gmail_service.get_user_profile()
            if profile:
                user_id = db.create_user(
                    email=profile['email'],
                    name=profile['email'].split('@')[0]
                )
                
                return {
                    "success": True,
                    "message": "Authentication successful",
                    "profile": profile,
                    "user_id": user_id
                }
        
        raise HTTPException(status_code=400, detail="Authentication failed")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/messages")
async def get_messages(query: Optional[str] = "", limit: int = 50):
    """Get Gmail messages"""
    try:
        if not gmail_service.is_authenticated():
            raise HTTPException(status_code=401, detail="Not authenticated with Gmail")
        
        messages = gmail_service.get_messages(query=query, max_results=limit)
        
        return {
            "messages": messages,
            "count": len(messages)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync")
async def sync_emails(limit: int = 100):
    """Sync emails to local database"""
    try:
        if not gmail_service.is_authenticated():
            raise HTTPException(status_code=401, detail="Not authenticated with Gmail")
        
        # Get user profile to identify user
        profile = gmail_service.get_user_profile()
        if not profile:
            raise HTTPException(status_code=400, detail="Could not get user profile")
        
        user = db.get_user_by_email(profile['email'])
        if not user:
            raise HTTPException(status_code=400, detail="User not found in database")
        
        # Get recent messages
        messages = gmail_service.get_messages(max_results=limit)
        
        # Store in database and analyze
        stored_count = 0
        analyzed_count = 0
        for message in messages:
            message['user_id'] = user['id']
            if db.store_email(message):
                stored_count += 1
                result = analysis_service.analyze_email(
                    body_text=message.get('body_text', ''),
                    subject=message.get('subject', ''),
                )
                if db.store_analysis(message['id'], result):
                    analyzed_count += 1

        return {
            "success": True,
            "messages_synced": stored_count,
            "messages_analyzed": analyzed_count,
            "total_messages": len(messages)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/profile")
async def get_profile():
    """Get Gmail user profile"""
    try:
        if not gmail_service.is_authenticated():
            raise HTTPException(status_code=401, detail="Not authenticated with Gmail")
        
        profile = gmail_service.get_user_profile()
        return profile
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_email_stats():
    """Get email statistics from database"""
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
        
        # Calculate basic stats
        total_emails = len(emails)
        sent_emails = len([e for e in emails if e['message_type'] == 'sent'])
        received_emails = total_emails - sent_emails
        
        return {
            "total_emails": total_emails,
            "sent_emails": sent_emails,
            "received_emails": received_emails,
            "recent_emails": emails[:10]  # Last 10 emails
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))