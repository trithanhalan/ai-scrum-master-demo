import httpx
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.token import Connection
from app.config import settings
from app.logging_config import logger


class AuthService:
    """Service for managing Jira authentication and identity"""

    def __init__(self):
        self.client_id = settings.OAUTH_CLIENT_ID
        self.client_secret = settings.OAUTH_CLIENT_SECRET

    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        Return the authenticated Jira user's profile and resolved cloud_id.

        Flow:
          1) /oauth/token/accessible-resources  -> pick a Jira site (cloud_id)
          2) /ex/jira/{cloud_id}/rest/api/3/myself -> user profile
        """
        # 1) Determine which Jira Cloud(s) this token can access
        resources = await self.get_accessible_resources(access_token)
        if not resources:
            raise httpx.HTTPStatusError(
                "No accessible Jira Cloud found for this token",
                request=None,
                response=None,
            )

        # Choose the first resource that has an id (typical for Jira)
        jira = next((r for r in resources if r.get("id")), resources[0])
        cloud_id = jira["id"]

        # 2) Fetch the user's Jira profile for that cloud
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/myself",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                },
            )
            resp.raise_for_status()
            profile = resp.json()
            profile["_cloud_id"] = cloud_id
            return profile

    async def get_accessible_resources(self, access_token: str) -> list[Dict[str, Any]]:
        """Get accessible Jira sites"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://api.atlassian.com/oauth/token/accessible-resources",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            return response.json()

    def upsert_connection(
        self,
        db: Session,
        *,
        account_id: str,
        cloud_id: str,
        access_token: str,
        refresh_token: str,
        expires_at: datetime,
        display_name: Optional[str] = None,
        email: Optional[str] = None,
        scopes: Optional[str] = None,
        raw: Optional[Dict] = None,
    ) -> Connection:
        """Create or update a connection record"""

        # Check if connection already exists
        existing = (
            db.query(Connection)
            .filter_by(account_id=account_id, cloud_id=cloud_id)
            .first()
        )

        if existing:
            # Update existing connection
            existing.access_token = access_token
            existing.refresh_token = refresh_token
            existing.expires_at = expires_at
            existing.display_name = display_name
            existing.email = email
            existing.scopes = scopes
            existing.raw = raw or {}
            existing.is_active = True
            existing.updated_at = datetime.now(timezone.utc)
            connection = existing
            logger.info(
                "Updated existing connection",
                account_id=account_id,
                cloud_id=cloud_id,
            )
        else:
            # Create new connection
            connection = Connection(
                account_id=account_id,
                cloud_id=cloud_id,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=expires_at,
                display_name=display_name,
                email=email,
                scopes=scopes,
                raw=raw or {},
                is_active=True,
            )
            db.add(connection)
            logger.info(
                "Created new connection", account_id=account_id, cloud_id=cloud_id
            )

        db.commit()
        db.refresh(connection)
        return connection

    async def refresh_connection_if_needed(self, db: Session, connection: Connection) -> Connection:
        """Refresh connection tokens if expired"""
        if not connection.is_expired():
            return connection

        logger.info("Refreshing expired connection", connection_id=connection.id)

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                data = {
                    "grant_type": "refresh_token",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": connection.refresh_token,
                }

                response = await client.post(
                    settings.OAUTH_TOKEN_URL,
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                response.raise_for_status()
                token_data = response.json()

                # Update connection with new tokens
                connection.access_token = token_data["access_token"]
                if "refresh_token" in token_data:
                    connection.refresh_token = token_data["refresh_token"]

                expires_in = int(token_data.get("expires_in", 3600))
                connection.expires_at = datetime.now(timezone.utc) + timedelta(
                    seconds=expires_in
                )
                connection.updated_at = datetime.now(timezone.utc)

                db.commit()
                db.refresh(connection)

                logger.info(
                    "Successfully refreshed connection", connection_id=connection.id
                )
                return connection

        except Exception as e:
            logger.error(
                "Failed to refresh connection",
                connection_id=connection.id,
                error=str(e),
            )
            # Mark connection as inactive if refresh fails
            connection.is_active = False
            db.commit()
            raise Exception(f"Failed to refresh connection: {str(e)}")

    def get_connection_by_id(self, db: Session, connection_id: int) -> Optional[Connection]:
        """Get connection by ID"""
        return db.query(Connection).filter_by(id=connection_id, is_active=True).first()

    def get_connection_by_account(self, db: Session, account_id: str, cloud_id: str) -> Optional[Connection]:
        """Get connection by account and cloud ID"""
        return (
            db.query(Connection)
            .filter_by(account_id=account_id, cloud_id=cloud_id, is_active=True)
            .first()
        )

    def get_latest_active_connection(self, db: Session) -> Optional[Connection]:
        """Get the most recent active connection (fallback for MVP)"""
        return (
            db.query(Connection)
            .filter_by(is_active=True)
            .order_by(Connection.updated_at.desc())
            .first()
        )


# Global instance
auth_service = AuthService()