"""Email skills: read inbox, write/send, summarize.

Backend: stdlib imaplib + smtplib. Credentials come from environment or
profile prefs (email.imap_host, email.imap_user, email.imap_password,
email.smtp_host, email.smtp_user, email.smtp_password). No external deps.
"""

import asyncio
import os
from typing import Any, Dict, Optional

import httpx

_IMAP = ("imap_host", "imap_user", "imap_password")
_SMTP = ("smtp_host", "smtp_user", "smtp_password")


def _creds(ctx: Any, kind: str) -> Optional[Dict[str, str]]:
    keys = _IMAP if kind == "imap" else _SMTP
    env_prefix = "JARVIS_EMAIL_" + ("IMAP_" if kind == "imap" else "SMTP_")
    out = {}
    for k in keys:
        short = k.split("_", 1)[1]
        val = os.environ.get(env_prefix + short.upper()) or (
            ctx.profile.get_pref(f"email.{k}") if getattr(ctx, "profile", None) else None
        )
        if val:
            out[short] = val
    needed = 3 if kind == "imap" else 3
    return out if len(out) == needed else None


def _unconfigured(kind: str) -> Dict[str, Any]:
    return {"success": False,
            "narration": f"Email not configured. Set JARVIS_EMAIL_{kind.upper()}_HOST/USER/PASSWORD.",
            "type": "email_result"}


async def email_read(params: Dict[str, Any], ctx: Any) -> Dict[str, Any]:
    creds = _creds(ctx, "imap")
    if not creds:
        return _unconfigured("imap")
    try:
        import imaplib, email as email_lib
        from email.header import decode_header
        loop = asyncio.get_running_loop()

        def _fetch():
            m = imaplib.IMAP4_SSL(creds["host"])
            m.login(creds["user"], creds["password"])
            m.select("INBOX")
            _, data = m.search(None, "ALL")
            ids = data[0].split()[-10:]  # last 10
            messages = []
            for i in ids:
                _, msg_data = m.fetch(i, "(RFC822)")
                raw = msg_data[0][1]
                em = email_lib.message_from_bytes(raw)
                subj = str(decode_header(em["Subject"])[0][0]) if em["Subject"] else "(no subject)"
                messages.append({"from": em.get("From", ""), "subject": subj})
            m.logout()
            return messages

        msgs = await loop.run_in_executor(None, _fetch)
        if not msgs:
            return {"success": True, "narration": "Your inbox is empty.", "type": "email_result",
                    "data": {"messages": []}}
        narration = f"You have {len(msgs)} recent messages. " + " ".join(
            f"{m['from'].split('<')[0].strip()}: {m['subject']}. " for m in msgs[:3])
        return {"success": True, "narration": narration.strip(), "type": "email_result",
                "data": {"messages": msgs}}
    except Exception as e:
        return {"success": False, "narration": f"Email read failed: {e}", "type": "email_result"}


async def email_write(params: Dict[str, Any], ctx: Any) -> Dict[str, Any]:
    creds = _creds(ctx, "smtp")
    if not creds:
        return _unconfigured("smtp")
    to = params.get("to") or params.get("recipient") or ""
    subject = params.get("subject") or "Message from Jarvis"
    body = params.get("body") or params.get("message") or ""
    if not to:
        return {"success": False, "narration": "Who should I send it to?", "type": "email_result"}
    try:
        import smtplib
        from email.message import EmailMessage

        def _send():
            msg = EmailMessage()
            msg["To"] = to
            msg["Subject"] = subject
            msg.set_content(body)
            with smtplib.SMTP_SSL(creds["host"], 465) as s:
                s.login(creds["user"], creds["password"])
                s.send_message(msg)

        await asyncio.get_running_loop().run_in_executor(None, _send)
        return {"success": True, "narration": f"Email sent to {to}.", "type": "email_result"}
    except Exception as e:
        return {"success": False, "narration": f"Email send failed: {e}", "type": "email_result"}


async def email_summarize(params: Dict[str, Any], ctx: Any) -> Dict[str, Any]:
    result = await email_read(params, ctx)
    if not result["success"]:
        return result
    msgs = result.get("data", {}).get("messages", [])
    summary = "Summary: " + "; ".join(
        f"{m['subject']} from {m['from'].split('<')[0].strip()}" for m in msgs[:5])
    return {"success": True, "narration": summary, "type": "email_result",
            "data": {"summary": summary, "count": len(msgs)}}


def register(reg) -> None:
    reg.skill("email_read", email_read, description="Read the latest emails")
    reg.skill("email_write", email_write, description="Compose and send an email")
    reg.skill("email_summarize", email_summarize, description="Summarize recent emails")
