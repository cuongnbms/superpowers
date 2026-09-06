# ADR Format

An ADR records one decision that passed the three-part test in [SKILL.md](./SKILL.md#offer-adrs-sparingly). This file is only about the shape of the file: where it goes, what it contains, and how it changes over time.

## Location and numbering

All ADRs live in `docs/adr/` at the repo root, including in a multi-context repo. One directory means one number sequence, one place to scan for "what has this project decided", and no question of which context a cross-cutting decision belongs to. A context-specific decision records its owner in the header's `Context` field instead.

Scan `docs/adr/` for the highest existing number and add one. Files are named `NNNN-slug.md`, four digits, where the slug is the title in kebab-case trimmed to its key words (`# 0003: Event-sourced write model for Orders` becomes `0003-event-sourced-orders.md`). Refer to another ADR as `[0003](./0003-event-sourced-orders.md)`.

## Template

The value of an ADR is in recording *that* a decision was made and *why*, not in filling out sections. Context and Decision are always present; Consequences and Alternatives appear when they have something to say. Sections keep this order so a reader scanning ten ADRs finds each thing in the same place.

```md
# {NNNN}: {The decision as a verb phrase, naming the accepted cost if there is one}

> Status: Accepted · Date: {YYYY-MM-DD} · Context: {name}

## Context

{Why a decision was needed. The forces at play, the constraint that made the obvious path unavailable.}

## Decision

{What we do.}

{Why this wins: the reason, stated against the forces in Context, naming the option it beat.}

## Consequences                      ← optional

{What gets better, what gets worse, what follows. Split into **Positive** / **Negative** / **Neutral** subheadings only when there are enough items for the split to help.}

## Alternatives considered           ← optional

| Alternative | Why not chosen |
|-------------|----------------|
| {option} | {the specific reason it lost} |
```

Rules for filling it in:

- **`Context:` in the header appears only when the repo has a `CONTEXT-MAP.md`.** Name the context from the map that owns the decision, or `System` when it spans contexts. A single-context repo omits the field.
- **Decision has two parts, the what and the why.** A Decision with only the what is incomplete even when the alternatives table is full, because the table records why the others lost, not why this one won. One sentence each is enough.
- **Consequences appears when a downstream effect is non-obvious**: something the reader would not predict from the decision alone and might otherwise treat as a bug. Omit it when the effects are the obvious ones.
- **Alternatives considered appears when more than one option lost, or when the losing option needs more than the phrase in Decision to be understood.** A decision between two options whose why already names the loser needs no table.
- **A one-sentence section is valid.** Write as much as the decision needs and no more. The sections exist so the reader knows where to look, not to be filled.
- **The title names the trade-off.** "Squash the four heaviest apps' migrations, accepting cosmetic constraint-name divergence" tells the reader the decision and its price before they open the file. "Migration squash" tells them nothing.
- **Every row of the alternatives table gives a specific reason.** "Not a good fit" is not a reason; "would keep the inline `RunPython` that references a since-deleted model" is.
- **Add a `Source:` line** at the end of Context when the ADR came out of a brainstorm or spec, for example `Source: [design spec](../superpowers/specs/2026-09-06-order-billing-design.md)`. Omit it when there is no such document.

### Example

```md
# 0004: Communicate between Ordering and Billing via domain events

> Status: Accepted · Date: 2026-09-06 · Context: System

## Context

Ordering needs Billing to invoice after an order is placed. Billing has had two multi-hour outages this quarter, and Ordering must keep accepting orders through the next one.

Source: [design spec](../superpowers/specs/2026-09-06-order-billing-design.md)

## Decision

Ordering publishes an `OrderPlaced` event that Billing consumes. Ordering never calls Billing directly.

An event lets Ordering keep accepting orders through a Billing outage, which a synchronous call to Billing cannot.

## Consequences

Ordering's uptime no longer depends on Billing's. Invoices lag order placement by the consumer's delay, so "invoice not yet created" is a normal state that the customer portal must display rather than treat as an error.

## Alternatives considered

| Alternative | Why not chosen |
|-------------|----------------|
| Synchronous HTTP call from Ordering to Billing | Couples the two services' uptime; an order would fail whenever Billing is down. |
| Ordering writes the invoice itself | Puts invoicing rules in two contexts; Billing already owns them. |
```

## Updates and supersession

The sections above are written once. The two ways an ADR changes afterwards:

**Something happened, the decision stands.** A follow-on phase shipped, a predicted consequence materialised, a workaround was needed. Append an `## Updates` section at the end of the file, with one dated subheading per entry, newest last. Create the section with the first update; never edit the original sections to fold the news in, because the reader needs to see what was known at decision time separately from what was learned later.

```md
## Updates

### 2026-10-02: Phase 2 shipped

{What happened, and anything non-obvious the reader needs.}
```

**The decision was reversed.** Do not edit the old file's body. Write a new ADR with the next number explaining what changed and why, then change the old file's header line to point at it:

```md
> Status: Superseded by [0007](./0007-sync-billing-calls.md) · Date: 2026-09-06 · Context: System
```

`Date` and `Context` stay as they were. A decision that is retired without a replacement uses `> Status: Deprecated · Date: ...` plus an update entry saying why. Editing in place erases the fact that the project once decided otherwise, which is exactly what the next reader needs to know before they propose the old approach again.
