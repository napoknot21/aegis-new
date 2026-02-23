from __future__ import annotations

"""
email.py
--------
Two email strategies merged into one file:

1. Microsoft Graph API (send_mail_graph)
   → Production use — sends via Azure AD app credentials
   → No Outlook installation needed, works on servers

2. Outlook COM (create_outlook_email)
   → Windows-only dev/manual use — creates a draft in local Outlook
   → Kept for backwards compatibility with the payments workflow

Both functions now receive their config as arguments (not from global imports)
so they work cleanly with TenantConfig.
"""

import os
import base64
import json
import requests
import datetime as dt

from email.message import EmailMessage
from typing import Dict, List, Optional

from src.utils.formatters import check_email_format
from src.utils.logger import log


# ================================================================
# Microsoft Graph API (production)
# ================================================================

def get_azure_token(
    client_id: str,
    client_secret: str,
    tenant_id: str,
    url_template: str,
) -> Optional[str]:
    """
    Get a Bearer token from Azure AD using client credentials flow.
    url_template should contain the placeholder 'TENANT_ID'.
    """
    url = url_template.replace("TENANT_ID", tenant_id)
    payload = {"client_id": client_id, "client_secret": client_secret}

    try:
        response = requests.post(url=url, data=payload)
        token = response.json().get("access_token")
        if token:
            log("[+] Azure token retrieved successfully.")
        else:
            log("[-] Azure token not found in response.", "error")
        return token

    except Exception as e:
        log(f"[-] Error getting Azure token: {e}", "error")
        return None


def send_mail_graph(
    client_id: str,
    client_secret: str,
    tenant_id: str,
    token_url: str,
    send_url_template: str,       # must contain 'SENDER_MAIL' placeholder
    from_email: str,
    to_email: List[str],
    subject: str,
    content: str,
    cc_email: Optional[List[str]] = None,
    file_abs_path: Optional[str] = None,
) -> bool:
    """
    Send an email via Microsoft Graph API.
    Returns True on success, False on failure.
    """
    token = get_azure_token(client_id, client_secret, tenant_id, token_url)
    if not token:
        return False

    endpoint = send_url_template.replace("SENDER_MAIL", from_email)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    recipients = [
        {"emailAddress": {"address": e}}
        for e in to_email if check_email_format(e)
    ]
    cc_recipients = [
        {"emailAddress": {"address": e}}
        for e in (cc_email or []) if check_email_format(e)
    ]

    message: Dict = {
        "subject": subject,
        "body": {"contentType": "text", "content": content},
        "toRecipients": recipients,
    }
    if cc_recipients:
        message["ccRecipients"] = cc_recipients

    if file_abs_path and os.path.exists(file_abs_path):
        with open(file_abs_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        message["attachments"] = [{
            "@odata.type": "#microsoft.graph.fileAttachment",
            "name": os.path.basename(file_abs_path),
            "contentType": "application/octet-stream",
            "contentBytes": b64,
        }]

    payload = {"message": message, "saveToSentItems": "true"}

    try:
        response = requests.post(endpoint, headers=headers, data=json.dumps(payload))
        log(f"[+] Email sent. Status: {response.status_code}")
        return response.status_code in (200, 202)

    except Exception as e:
        log(f"[-] Error sending email: {e}", "error")
        return False


# ================================================================
# Outlook COM (Windows / dev / manual use)
# ================================================================

def create_outlook_email(
    to_email: Optional[str | List[str]],
    from_email: str,
    subject: str,
    body: str,
    cc_email: Optional[str | List[str]] = None,
    attachment_paths: Optional[str | List[str]] = None,
) -> Optional[EmailMessage]:
    """
    Build an EmailMessage object (RFC 5322 .eml format).
    Used to create drafts that can be opened in Outlook or saved to disk.
    Does NOT send — call save_email() to persist.
    """
    if not from_email:
        return None

    to_list = [to_email] if isinstance(to_email, str) else (to_email or [])
    cc_list = [cc_email] if isinstance(cc_email, str) else (cc_email or [])
    attachments = [attachment_paths] if isinstance(attachment_paths, str) else (attachment_paths or [])

    if not to_list:
        return None

    msg = EmailMessage()
    msg["From"] = from_email
    msg["To"] = ", ".join(to_list)
    msg["Subject"] = subject
    if cc_list:
        msg["Cc"] = ", ".join(cc_list)
    msg["X-Unsent"] = "1"

    html_body = body.replace("\n", "<br>")
    msg.set_content("This email requires an HTML-capable client.")
    msg.add_alternative(html_body, subtype="html")

    for path in attachments:
        if not os.path.isfile(path):
            continue
        with open(path, "rb") as f:
            data = f.read()
        msg.add_attachment(
            data,
            maintype="application",
            subtype="octet-stream",
            filename=os.path.basename(path),
        )

    return msg


def save_email(
    email_item: EmailMessage,
    dir_abs_path: str,
    filename: Optional[str] = None,
) -> Dict:
    """
    Save an EmailMessage to disk as a .eml file.
    Returns {success, message, path}.
    """
    response = {"success": False, "message": "", "path": ""}
    os.makedirs(dir_abs_path, exist_ok=True)

    filename = filename or f"message_{dt.datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.eml"
    save_path = os.path.join(dir_abs_path, filename)

    try:
        with open(save_path, "wb") as f:
            f.write(bytes(email_item))
        response.update({"success": True, "message": "Email saved.", "path": save_path})

    except Exception as e:
        response["message"] = f"Failed to save email: {e}"

    return response