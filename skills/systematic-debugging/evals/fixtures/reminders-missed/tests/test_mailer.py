import json

import pytest

from app import mailer


def test_queues_message(tmp_path, monkeypatch):
    monkeypatch.setenv("MAILER_OUTBOX", str(tmp_path / "outbox.jsonl"))
    mailer.send("a@example.com", "s", "b")
    assert json.loads((tmp_path / "outbox.jsonl").read_text())["to"] == "a@example.com"


def test_refuses_malformed_address(tmp_path, monkeypatch):
    monkeypatch.setenv("MAILER_OUTBOX", str(tmp_path / "outbox.jsonl"))
    with pytest.raises(ValueError):
        mailer.send("not an address", "s", "b")
