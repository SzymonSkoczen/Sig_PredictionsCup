"""Send reports and alerts to every configured channel (Telegram, Discord, Slack, ntfy, email)."""
from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

import httpx

from .config import Settings

log = logging.getLogger(__name__)


class Notifier:
    def __init__(self, s: Settings, transport=None):
        self.s = s
        self._http = httpx.Client(timeout=15.0, transport=transport)

    @property
    def channels(self) -> list[str]:
        s = self.s
        out = []
        if s.telegram_bot_token and s.telegram_chat_id:
            out.append("telegram")
        if s.discord_webhook_url:
            out.append("discord")
        if s.slack_webhook_url:
            out.append("slack")
        if s.ntfy_topic:
            out.append("ntfy")
        if s.smtp_host and s.email_to:
            out.append("email")
        return out

    def send(self, title: str, body: str) -> list[str]:
        """Returns the channels that failed. Always logs locally too."""
        log.info("%s\n%s", title, body)
        failed = []
        for ch in self.channels:
            try:
                getattr(self, f"_{ch}")(title, body)
            except Exception as e:  # a broken channel must never stop the bot
                log.error("notify via %s failed: %s", ch, e)
                failed.append(ch)
        return failed

    def _telegram(self, title: str, body: str) -> None:
        text = f"*{title}*\n```\n{body[:3800]}\n```"
        self._http.post(f"https://api.telegram.org/bot{self.s.telegram_bot_token}/sendMessage",
                        json={"chat_id": self.s.telegram_chat_id, "text": text,
                              "parse_mode": "Markdown"}).raise_for_status()

    def _discord(self, title: str, body: str) -> None:
        self._http.post(self.s.discord_webhook_url,
                        json={"content": f"**{title}**\n```\n{body[:1850]}\n```"}).raise_for_status()

    def _slack(self, title: str, body: str) -> None:
        self._http.post(self.s.slack_webhook_url,
                        json={"text": f"*{title}*\n```{body[:3800]}```"}).raise_for_status()

    def _ntfy(self, title: str, body: str) -> None:
        self._http.post(f"{self.s.ntfy_server.rstrip('/')}/{self.s.ntfy_topic}", content=body[:3900].encode(),
                        headers={"Title": title.encode("ascii", "ignore").decode()}).raise_for_status()

    def _email(self, title: str, body: str) -> None:
        msg = EmailMessage()
        msg["Subject"], msg["From"], msg["To"] = title, self.s.smtp_user or self.s.email_to, self.s.email_to
        msg.set_content(body)
        with smtplib.SMTP(self.s.smtp_host, self.s.smtp_port, timeout=20) as smtp:
            smtp.starttls()
            if self.s.smtp_user:
                smtp.login(self.s.smtp_user, self.s.smtp_password)
            smtp.send_message(msg)
