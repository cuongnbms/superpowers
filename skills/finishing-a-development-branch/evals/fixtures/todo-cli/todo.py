#!/usr/bin/env python3
"""Tiny todo CLI. Items live in todo.json next to this file."""
import argparse
import json
import sys
from pathlib import Path

STORE = Path(__file__).with_name("todo.json")


def load():
    if STORE.exists():
        return json.loads(STORE.read_text())
    return []


def save(items):
    STORE.write_text(json.dumps(items, indent=2))


def cmd_add(args):
    items = load()
    items.append({"id": len(items) + 1, "text": args.text, "done": False})
    save(items)
    print(f"added #{items[-1]['id']}")


def cmd_list(args):
    for item in load():
        mark = "x" if item["done"] else " "
        print(f"[{mark}] #{item['id']} {item['text']}")


def cmd_done(args):
    items = load()
    for item in items:
        if item["id"] == args.id:
            item["done"] = True
            save(items)
            print(f"done #{args.id}")
            return
    print(f"no item #{args.id}", file=sys.stderr)
    sys.exit(1)


def main(argv=None):
    parser = argparse.ArgumentParser(prog="todo")
    sub = parser.add_subparsers(dest="command", required=True)
    p_add = sub.add_parser("add")
    p_add.add_argument("text")
    p_add.set_defaults(func=cmd_add)
    p_list = sub.add_parser("list")
    p_list.set_defaults(func=cmd_list)
    p_done = sub.add_parser("done")
    p_done.add_argument("id", type=int)
    p_done.set_defaults(func=cmd_done)
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
