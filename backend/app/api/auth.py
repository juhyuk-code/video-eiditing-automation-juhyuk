"""Authentication API routes."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from ..config import get_settings
from ..db.database import get_db
from ..db.models import User, Settings

router = APIRouter(prefix="/api/auth", tags=["auth"])
settings = get_settings()

# Google OAuth scopes
SCOPES = [
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive.metadata.readonly",
]


def get_google_flow() -> Flow:
    """Create Google OAuth flow."""
    return Flow.from_client_config(
        {
            "web": {
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.google_redirect_uri],
            }
        },
        scopes=SCOPES,
        redirect_uri=settings.google_redirect_uri,
    )


@router.get("/google")
async def google_login():
    """Initiate Google OAuth login."""
    flow = get_google_flow()
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return {"auth_url": auth_url}


@router.get("/google/callback")
async def google_callback(
    code: str,
    db: AsyncSession = Depends(get_db),
):
    """Handle Google OAuth callback."""
    try:
        flow = get_google_flow()
        flow.fetch_token(code=code)
        credentials = flow.credentials

        # Get user info
        service = build("oauth2", "v2", credentials=credentials)
        user_info = service.userinfo().get().execute()

        # Find or create user
        result = await db.execute(
            select(User).where(User.google_id == user_info["id"])
        )
        user = result.scalar_one_or_none()

        if not user:
            # Create new user
            user = User(
                email=user_info["email"],
                google_id=user_info["id"],
                google_access_token=credentials.token,
                google_refresh_token=credentials.refresh_token,
            )
            db.add(user)
            await db.flush()

            # Create default settings
            user_settings = Settings(user_id=user.id)
            db.add(user_settings)
        else:
            # Update tokens
            user.google_access_token = credentials.token
            if credentials.refresh_token:
                user.google_refresh_token = credentials.refresh_token

        await db.commit()

        # In production, create a session token and redirect to frontend
        # For now, return user info
        return {
            "user_id": user.id,
            "email": user.email,
            "message": "Login successful",
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/me")
async def get_current_user(
    user_id: str,  # In production, this would come from session/JWT
    db: AsyncSession = Depends(get_db),
):
    """Get current user info."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": user.id,
        "email": user.email,
        "telegram_connected": user.telegram_chat_id is not None,
        "created_at": user.created_at,
    }


@router.post("/logout")
async def logout():
    """Logout user."""
    # In production, invalidate session/JWT
    return {"message": "Logged out successfully"}
