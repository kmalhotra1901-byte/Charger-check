#!/usr/bin/env python3
"""
Statiq EV Charger Availability Monitor
----------------------------------------
Scrapes a Statiq charging station page, extracts the status of each
connector (e.g. "available", "unavailable", "charging"), compares it
to the last known state (stored in state.json), and emails you when
anything changes.

Configuration is read from environment variables (see README.md):
  CHARGER_URL     - the station page URL to monitor
  SMTP_HOST       - e.g. smtp.gmail.com
  SMTP_PORT       - e.g. 587
  SMTP_USER       - the sending email address
  SMTP_PASS       - the app password for that account
  NOTIFY_EMAIL    - where to send alerts (can be same as SMTP_USER)
"""

import os
import re
import sys
import json
import smtplib
from email.mime.text import MIMEText

import requests
from bs4 import BeautifulSoup

STATE_FILE = "state.json"

DEFAULT_URL = (
    "https://www.statiq.in/uk-rudrapur-hotel-rudra-continental-"
    "ev-charging-station-id-8632?longLat=79.389541,28.975838"
)


def fetch_statuses(url: str) -> dict:
    """Fetch the page and return {connector_label: status_lowercase}."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0 Safari/537.36"
        )
    }
    resp = requests.get(url, headers=headers, timeout=20)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    text = soup.get_text(separator="\n")
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    statuses = {}
    for i, line in enumerate(lines):
        m = re.match(r"^Connector\s+(\d+)$", line, re.IGNORECASE)
        if not m:
            continue
        connector_label = f"Connector {m.group(1)}"
        # The status line looks like "CCS-2·available" and normally
        # appears within the next couple of lines.
        for j in range(i + 1, min(i + 4, len(lines))):
            if "\u00b7" in lines[j]:  # the '·' separator character
                _, status = lines[j].split("\u00b7", 1)
                statuses[connector_label] = status.strip().lower()
                break

    if not statuses:
        raise RuntimeError(
            "No connector status found on page — the site's layout may "
            "have changed. Inspect the page HTML and update the parser."
        )

    return statuses


def load_previous_state() -> dict:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {}


def save_state(state: dict) -> None:
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def send_email(subject: str, body: str) -> None:
    smtp_host = os.environ["SMTP_HOST"]
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ["SMTP_USER"]
    smtp_pass = os.environ["SMTP_PASS"]
    notify_email = os.environ.get("NOTIFY_EMAIL", smtp_user)

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = notify_email

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, [notify_email], msg.as_string())


def main() -> None:
    url = os.environ.get("CHARGER_URL", DEFAULT_URL)

    try:
        current = fetch_statuses(url)
    except Exception as e:
        print(f"Error fetching/parsing page: {e}", file=sys.stderr)
        sys.exit(1)

    previous = load_previous_state()

    print("Current status:", current)

    if not previous:
        # First run ever — just record the baseline, no email needed.
        save_state(current)
        print("No previous state found. Saved baseline, no email sent.")
        return

    changes = {
        conn: (previous.get(conn), status)
        for conn, status in current.items()
        if previous.get(conn) != status
    }

    if changes:
        lines = [f"Status change detected at {url}\n"]
        for conn, (old, new) in changes.items():
            lines.append(f"  {conn}: {old or 'unknown'} -> {new}")
        body = "\n".join(lines)
        print(body)

        try:
            send_email("⚡ Charger status changed", body)
            print("Notification email sent.")
        except Exception as e:
            print(f"Failed to send email: {e}", file=sys.stderr)
            # still save state so we don't spam-retry the same change forever
    else:
        print("No change since last check.")

    save_state(current)


if __name__ == "__main__":
    main()
