from notes.cli import run
from notes.store import NoteStore


def test_add_prints_line(capsys):
    assert run(["add", "hello"], NoteStore()) == 0
    assert capsys.readouterr().out == "1\thello\n"


def test_list_prints_all(capsys):
    store = NoteStore()
    store.add("one")
    store.add("two")
    run(["list"], store)
    assert capsys.readouterr().out == "1\tone\n2\ttwo\n"
