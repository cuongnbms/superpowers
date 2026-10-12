"""Outgoing mail. The scheduler's environment points MAILER_OUTBOX at the SMTP relay queue."""
import json
import os


def send(to, subject, body):
    outbox = os.environ.get("MAILER_OUTBOX", os.path.join(os.getcwd(), "outbox.jsonl"))
    with open(outbox, "a") as f:
        f.write(json.dumps({"to": to, "subject": subject, "body": body}) + "\n")
