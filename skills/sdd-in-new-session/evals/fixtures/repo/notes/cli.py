import argparse
import sys

from notes.store import Note, NoteStore


def format_line(note: Note) -> str:
    return f"{note.id}\t{note.text}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="notes")
    sub = parser.add_subparsers(dest="command", required=True)
    add_parser = sub.add_parser("add")
    add_parser.add_argument("text")
    sub.add_parser("list")
    return parser


def run(argv: list[str], store: NoteStore) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "add":
        note = store.add(args.text)
        print(format_line(note))
        return 0
    if args.command == "list":
        for note in store.list():
            print(format_line(note))
        return 0
    return 1


def main() -> None:
    sys.exit(run(sys.argv[1:], NoteStore()))
