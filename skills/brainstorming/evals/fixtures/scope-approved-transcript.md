# Conversation so far (brainstorming session in progress)

**User:** Let's build a habit tracker. New repo, it's empty, you're in it now.

**Assistant:** This is architectural: a new project has no existing flow to change, so I'll go the full route with questions, approaches, and a written spec before any code. The directory is empty apart from `.git`.

First question: who is this for and what should it do for them day to day? For example just you checking off habits from the terminal, or something you'd share with other people?

**User:** Just me. I want to tick off 4-5 daily habits from the terminal in the morning and see my streaks. Nothing fancy.

**Assistant:** Understood. Here is what I've got, so you can correct it. You said: single user, terminal, 4-5 daily habits, tick off, see streaks. I'm assuming: local storage only, no reminders or notifications, no sync.

Proposed scope for v1:
- `habit add <name>` / `habit rm <name>`
- `habit done <name>` marks today
- `habit status` shows today's checklist and the current streak per habit
- data in a single local file

Left out of v1: reminders, weekly goals, history editing, export. Does that scope look right?

**User:** yeah that scope is ok, go ahead
