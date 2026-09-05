from dataclasses import dataclass


@dataclass
class Note:
    id: int
    text: str


class NoteStore:
    def __init__(self) -> None:
        self._notes: list[Note] = []

    def add(self, text: str) -> Note:
        note = Note(id=len(self._notes) + 1, text=text)
        self._notes.append(note)
        return note

    def list(self) -> list[Note]:
        return list(self._notes)
