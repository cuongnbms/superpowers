---
name: show-me
description: Shows what is hard to picture in chat (UI mockups and layouts, architecture and flow diagrams, data structures, how code runs) as pages in a browser tab that refreshes itself. Use only when the user asks to see something drawn or mocked up ("vẽ ra cho tôi xem", "show me", "mock it up"); do not offer it on your own.
---

# Show Me

Some things are faster to look at than to read: a layout, a flow between services, the shape of a data structure, the path a request takes through code. This skill puts them on a page in a browser tab that your human partner keeps open. Each screen you write replaces the page in that tab within a second, so there is nothing for them to click or reload.

Use it only when your human partner asks to see something. One request covers its revisions: when they say "make the sidebar narrower", write the screen again as `-v2`, then `-v3`. A later question, even a visual one, is answered in the terminal unless they ask to see it again. The tab is for looking during the conversation. If they want a diagram file to keep, make that file instead.

## Start or reuse the server

Run this from the project being discussed:

```
python3 <this skill's dir>/scripts/server.py start
```

When the shell is in a different directory, add `--project-dir <that project's root>`. The session lives in that project, so the screens and the URL stay with the work they describe.

It prints one JSON line. Read `url` and `screen_dir` from it. Running `start` again reuses the live server and returns the same URL, so run it whenever you are unsure the server is up. A stopped server (idle shutdown, or a restart of the machine) comes back the same way. It keeps its key, and it keeps its port when that port is still free, so the open tab usually reconnects; when the port moved, give your human partner the new URL.

Codex reaps detached processes, so there add `--foreground` and run the command with the harness's background mechanism. Then read the JSON line from the process output.

## Pick the form

Choose by what your human partner needs to see:

- Architecture, flow, sequence, state, schema, history: a `diagram`, written as Mermaid (`flowchart`, `sequenceDiagram`, `stateDiagram-v2`, `erDiagram`, `gitGraph`).
- A UI or layout, or a choice between layouts: the mock kit inside `compare`, so the options sit side by side with pins and notes.
- A data structure, config, or directory layout: a `tree`.
- How code runs: a `trace` stepping through the real functions. When the path crosses services, a Mermaid sequence diagram shows it better.

Read `references/components.md` the first time in a conversation that you write a screen. It holds copy-ready markup for every component.

## Write the screen

Write `<screen_dir>/<semantic-name>.html` with the file tool, not a shell heredoc: HTML and code snippets break under shell quoting. Use a name that says what is on the screen, such as `settings-layouts.html`.

Write a fragment by default. The frame supplies the page, the theme, the tabs, and the live refresh. Write a full document only when the frame gets in the way. The server adds the refresh script to it.

Never reuse a name. The newest file is what the tab shows, and an old name keeps its tab for your human partner to look back at, so a revision gets a new file. Use real content from the project (its actual routes, fields, function names) instead of placeholders, because the point is to check the idea against the real thing.

## Reply and stop

Give the full URL every time, including `?key=`, because the key is what lets the browser in. Add at most two sentences on what the screen shows, then end your turn. The page already carries the detail and your human partner is about to look at it, so a recap in the terminal only duplicates the screen. Your human partner reads the tab, and their reply tells you what to change.
