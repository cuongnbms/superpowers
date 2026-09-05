import json
import todo


def run(monkeypatch, tmp_path, capsys, *argv):
    monkeypatch.setattr(todo, "STORE", tmp_path / "todo.json")
    todo.main(list(argv))
    return capsys.readouterr().out


def test_add_and_list(monkeypatch, tmp_path, capsys):
    run(monkeypatch, tmp_path, capsys, "add", "milk")
    out = run(monkeypatch, tmp_path, capsys, "list")
    assert out == "[ ] #1 milk\n"


def test_done(monkeypatch, tmp_path, capsys):
    run(monkeypatch, tmp_path, capsys, "add", "milk")
    run(monkeypatch, tmp_path, capsys, "done", "1")
    out = run(monkeypatch, tmp_path, capsys, "list")
    assert out == "[x] #1 milk\n"
