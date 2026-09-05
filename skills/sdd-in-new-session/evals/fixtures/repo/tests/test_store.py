from notes.store import NoteStore


def test_add_assigns_incrementing_ids():
    store = NoteStore()
    assert store.add("one").id == 1
    assert store.add("two").id == 2


def test_list_returns_notes_in_insertion_order():
    store = NoteStore()
    store.add("one")
    store.add("two")
    assert [n.text for n in store.list()] == ["one", "two"]
