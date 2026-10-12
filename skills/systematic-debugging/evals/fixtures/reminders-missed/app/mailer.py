"""Outgoing mail. The scheduler's environment points MAILER_OUTBOX at the SMTP relay queue."""
import json
import os
import re

ADDRESS = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def send(to, subject, body):
    # The relay drops the whole queue file on a malformed recipient, so refuse it here.
    if not ADDRESS.match(to):
        raise ValueError(f"invalid address {to!r}")
    outbox = os.environ.get("MAILER_OUTBOX", os.path.join(os.getcwd(), "outbox.jsonl"))
    with open(outbox, "a") as f:
        f.write(json.dumps({"to": to, "subject": subject, "body": body}) + "\n")
