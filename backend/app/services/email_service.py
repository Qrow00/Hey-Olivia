import os
import json
from datetime import datetime, timezone
from typing import Optional
from pathlib import Path

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    _HAS_GMAIL = True
except ImportError:
    _HAS_GMAIL = False


class EmailService:
    SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

    def __init__(self):
        self._creds = None
        self._service = None
        self._data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
        self._token_file = os.path.join(self._data_dir, "gmail_token.json")
        self._credentials_file = os.path.join(self._data_dir, "gmail_credentials.json")

    def _ensure_data_dir(self):
        os.makedirs(self._data_dir, exist_ok=True)

    async def authenticate(self) -> dict:
        if not _HAS_GMAIL:
            return {"status": "error", "message": "Google API libraries not installed. Run: pip install google-api-python-client google-auth-oauthlib"}

        self._ensure_data_dir()

        if os.path.exists(self._token_file):
            self._creds = Credentials.from_authorized_user_file(self._token_file, self.SCOPES)

        if not self._creds or not self._creds.valid:
            if self._creds and self._creds.expired and self._creds.refresh_token:
                try:
                    self._creds.refresh(Request())
                except Exception:
                    if not os.path.exists(self._credentials_file):
                        return {
                            "status": "error",
                            "message": f"Place your Gmail OAuth credentials at: {self._credentials_file}",
                        }
                    flow = InstalledAppFlow.from_client_secrets_file(self._credentials_file, self.SCOPES)
                    self._creds = flow.run_local_server(port=0)
            else:
                if not os.path.exists(self._credentials_file):
                    return {
                        "status": "error",
                        "message": f"Place your Gmail OAuth credentials at: {self._credentials_file}",
                    }
                flow = InstalledAppFlow.from_client_secrets_file(self._credentials_file, self.SCOPES)
                self._creds = flow.run_local_server(port=0)

            with open(self._token_file, "w") as f:
                f.write(self._creds.to_json())

        self._service = build("gmail", "v1", credentials=self._creds)
        return {"status": "success", "message": "Gmail authenticated"}

    def _ensure_service(self):
        if not self._service:
            if self._creds and self._creds.valid:
                self._service = build("gmail", "v1", credentials=self._creds)

    async def get_recent(self, limit: int = 10, query: str = "") -> list[dict]:
        self._ensure_service()
        if not self._service:
            return []

        try:
            query = query or "is:unread"
            results = self._service.users().messages().list(
                userId="me", q=query, maxResults=limit
            ).execute()

            messages = results.get("messages", [])
            emails = []

            for msg in messages:
                full = self._service.users().messages().get(
                    userId="me", id=msg["id"], format="metadata",
                    metadataHeaders=["From", "Subject", "Date"]
                ).execute()

                headers = {h["name"]: h["value"] for h in full.get("payload", {}).get("headers", [])}
                emails.append({
                    "id": msg["id"],
                    "from": headers.get("From", ""),
                    "subject": headers.get("Subject", ""),
                    "date": headers.get("Date", ""),
                    "snippet": full.get("snippet", ""),
                    "unread": "UNREAD" in full.get("labelIds", []),
                })

            return emails
        except Exception as e:
            return [{"error": str(e)}]

    async def get_summary(self, limit: int = 5) -> str:
        emails = await self.get_recent(limit=limit)
        if not emails:
            return "No unread emails."
        if emails and "error" in emails[0]:
            return f"Email check failed: {emails[0]['error']}"

        lines = [f"You have {len(emails)} recent emails:"]
        for i, e in enumerate(emails, 1):
            sender = e["from"].split("<")[0].strip()
            lines.append(f"{i}. From {sender}: {e['subject']}")
        return " ".join(lines)


email_service = EmailService()
