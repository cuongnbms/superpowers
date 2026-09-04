# Skill authoring best practices (offline copy)

Condensed from Anthropic's official guidance. Keep this file in sync with the sources; the
section order mirrors the skill-authoring page so it can be diffed against it.

- Source 1: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
- Source 2: https://code.claude.com/docs/en/skills (Claude Code frontmatter and listing budget)
- Source 3: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices and the per-model pages for Claude Fable 5 / 5.1 (model notes)
- Spec: https://agentskills.io/specification
- Last synced: 2026-09-04

## Contents

- Core principles
- Skill structure (frontmatter, naming, descriptions, progressive disclosure)
- Workflows and feedback loops
- Content guidelines
- Common patterns
- Evaluation and iteration
- Anti-patterns
- Skills with executable code
- Checklist
- Model and Claude Code notes (not from the skill-authoring page)

---

## Core principles

### Concise is key

The context window is shared with the system prompt, conversation, other skills' metadata, and
the user's request. Only name and description are pre-loaded; the body loads when the skill
triggers, and bundled files only when read. Once loaded, every token competes with everything
else.

**Default assumption: Claude is already very smart.** Only add context Claude doesn't have.
Challenge each paragraph: does Claude need this explanation? Can I assume it knows this? Does
this justify its token cost?

Good (about 50 tokens):

```markdown
## Extract PDF text
Use pdfplumber for text extraction:
```python
import pdfplumber
with pdfplumber.open("file.pdf") as pdf:
    text = pdf.pages[0].extract_text()
```
```

Bad (about 150 tokens): explaining what a PDF is, that libraries exist, how to pip install,
and why this one is recommended.

### Set appropriate degrees of freedom

Match specificity to how fragile and variable the task is.

| Freedom | Form | Use when |
|---|---|---|
| High | Text instructions, heuristics | Several valid approaches; decisions depend on context (e.g. code review) |
| Medium | Pseudocode or a script with parameters | A preferred pattern exists; some variation is fine |
| Low | A specific script, few or no parameters, "do not modify the command" | Fragile, error-prone, consistency-critical, fixed sequence (e.g. migrations) |

Analogy: a narrow bridge with cliffs needs exact guardrails; an open field needs only a direction.

### Test with all models you plan to use

A skill is an addition to a model, so its effect depends on the model. Test on every model you
will run it with:

- **Haiku**: does the skill provide enough guidance?
- **Sonnet**: is it clear and efficient?
- **Opus and above**: does it avoid over-explaining?

What is perfect for Opus may need more detail for Haiku; aim for instructions that work on all.

## Skill structure

### Frontmatter

Two fields are required by the spec; the rest are optional.

`name`
- Maximum 64 characters
- Lowercase letters, numbers, and hyphens only
- No XML tags
- Cannot contain the reserved words `anthropic` or `claude`

`description`
- Non-empty, maximum 1,024 characters
- No XML tags
- Describes what the skill does **and** when to use it

Other spec fields: `license`, `compatibility`, `metadata`, `allowed-tools`. See the Claude Code
section below for harness-specific fields.

### Naming conventions

Prefer gerund form (verb + -ing): `processing-pdfs`, `analyzing-spreadsheets`,
`writing-documentation`. Noun phrases (`pdf-processing`) and imperatives (`process-pdfs`) are
acceptable. Avoid vague (`helper`, `utils`, `tools`), overly generic (`documents`, `data`), the
reserved words, and inconsistent patterns within one collection.

### Writing effective descriptions

The description is the primary discovery mechanism: Claude picks from potentially 100+ skills
using it. It must say **what the skill does and when to use it**, with the key terms a user
would actually say.

**Always third person.** The description is injected into the system prompt; inconsistent
point of view harms discovery.

- Good: "Processes Excel files and generates reports"
- Avoid: "I can help you process Excel files"
- Avoid: "You can use this to process Excel files"

Effective examples:

```yaml
description: Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction.
```
```yaml
description: Analyze Excel spreadsheets, create pivot tables, generate charts. Use when analyzing Excel files, spreadsheets, tabular data, or .xlsx files.
```
```yaml
description: Generate descriptive commit messages by analyzing git diffs. Use when the user asks for help writing commit messages or reviewing staged changes.
```

Avoid: "Helps with documents", "Processes data", "Does stuff with files".

Two additions from field testing (superpowers, not the official page):

- Describe the capability, not the procedure. A description that outlines the workflow's steps
  gets followed *instead of* the body, so a two-stage process collapses to one stage.
- No emphatic trigger language (`CRITICAL`, `MUST`, `ALWAYS`) in the description; see the
  model notes below for why.

### Progressive disclosure

SKILL.md is an overview that points to detail, like a table of contents.

- Keep the SKILL.md body **under 500 lines**; split when approaching it.
- Bundle as much reference material as you like: there is no context cost until a file is read.

Pattern 1, high-level guide with references:

```markdown
## Quick start
[inline essentials]

## Advanced features
**Form filling**: See [FORMS.md](FORMS.md)
**API reference**: See [REFERENCE.md](REFERENCE.md)
```

Pattern 2, domain-specific organization: one reference file per domain
(`reference/finance.md`, `reference/sales.md`) so a sales question never loads finance schemas.
Add grep hints for large files.

Pattern 3, conditional details: show the basic path inline, link the advanced path
("For tracked changes: see REDLINING.md").

**Keep references one level deep from SKILL.md.** When a referenced file references another,
Claude may preview with `head -100` instead of reading the whole thing. Every reference file
links directly from SKILL.md.

**Files longer than 100 lines get a table of contents** at the top so a partial read still
shows the full scope.

Name files descriptively (`form_validation_rules.md`, not `doc2.md`) and organize directories
by domain.

## Workflows and feedback loops

### Use workflows for complex tasks

Break complex operations into clear sequential steps. For long workflows, provide a checklist
Claude copies into its response and checks off:

```markdown
Task Progress:
- [ ] Step 1: Analyze the form (run analyze_form.py)
- [ ] Step 2: Create field mapping (edit fields.json)
- [ ] Step 3: Validate mapping (run validate_fields.py)
- [ ] Step 4: Fill the form (run fill_form.py)
- [ ] Step 5: Verify output (run verify_output.py)
```

Then one short paragraph per step, and "if X fails, return to step N".

### Implement feedback loops

Pattern: run validator, fix errors, repeat. Works with a script (`validate.py`) or with a
reference document as the validator (draft, review against STYLE_GUIDE.md checklist, revise,
review again, only proceed when all requirements are met).

## Content guidelines

### Avoid time-sensitive information

Never write "before August 2025 use the old API". Put the current method first and legacy
detail in a collapsed "Old patterns" section marked deprecated.

### Use consistent terminology

Pick one term per concept and use it everywhere: always "API endpoint", not a mix of "URL",
"route", "path". Always "field", not "box"/"element"/"control".

## Common patterns

### Template pattern

For strict formats: "ALWAYS use this exact template structure" followed by the template.
For flexible guidance: "Here is a sensible default format, but use your best judgment" with the
template and "adjust sections as needed". Match strictness to the need.

### Examples pattern

When output quality depends on style, give input/output pairs, as in normal prompting. Two or
three concrete examples convey style and level of detail better than description.

### Conditional workflow pattern

Guide through decision points: "Creating new content? Follow Creation workflow. Editing
existing content? Follow Editing workflow." If workflows grow large, move each into its own
file and tell Claude which to read.

## Evaluation and iteration

### Build evaluations first

Create evaluations **before** writing extensive documentation, so the skill solves observed
problems rather than imagined ones:

1. Identify gaps: run Claude on representative tasks without a skill; document the failures.
2. Create evaluations: three scenarios that test those gaps.
3. Establish baseline: measure performance without the skill.
4. Write minimal instructions: just enough to address the gaps.
5. Iterate: run, compare against baseline, refine.

Evaluation structure:

```json
{
  "skills": ["pdf-processing"],
  "query": "Extract all text from this PDF file and save it to output.txt",
  "files": ["test-files/document.pdf"],
  "expected_behavior": [
    "Reads the PDF with an appropriate library or tool",
    "Extracts text from all pages",
    "Saves to output.txt in a readable format"
  ]
}
```

Evaluations are the source of truth for whether a skill works.

### Develop skills iteratively with Claude

Work with one instance (A) to author, and a fresh instance (B) to use the skill on real tasks.
Observe B, bring specifics back to A ("B forgot to filter test accounts; is the rule prominent
enough?"), apply, retest. Review A's output for conciseness ("remove the explanation of win
rate, Claude knows that") and information architecture ("move the schema to a reference file").

Official note: Claude understands the skill format natively. You do not need a special prompt
to get help writing a skill; the value of a skill like this one is the evaluation discipline
and the accumulated rules, not the format.

### Observe how Claude navigates skills

Watch for unexpected read order (structure not intuitive), missed references (links not
prominent), repeated reads of one file (content belongs in SKILL.md), and files never read
(unnecessary or poorly signposted). Iterate on observation, not assumption.

## Anti-patterns

- **Windows-style paths.** Always forward slashes: `scripts/helper.py`.
- **Too many options.** Give a default with an escape hatch ("Use pdfplumber. For scanned PDFs
  needing OCR, use pdf2image with pytesseract"), not a list of five libraries.
- **Time-sensitive statements** (see above).
- **Nested references** more than one level deep.

## Skills with executable code

- **Solve, don't defer.** Scripts handle their own error conditions (missing file: create a
  default; permission error: fall back) instead of failing and leaving Claude to figure it out.
- **No voodoo constants.** Every parameter is justified in a comment ("30s: HTTP requests
  usually finish well within; longer allows slow links"). If you don't know the right value,
  Claude won't either.
- **Provide utility scripts** for deterministic work: more reliable than generated code, no
  tokens spent on the code itself, consistent across uses.
- **Make execution intent clear**: "Run `analyze_form.py` to extract fields" (execute) versus
  "See `analyze_form.py` for the algorithm" (read as reference). Execution is preferred.
- **Verifiable intermediate outputs** for batch or destructive work: analyze, write a plan file,
  validate the plan with a script, execute, verify. Validation errors should be specific
  ("Field 'signature_date' not found. Available fields: ...").
- **Use visual analysis** when inputs render as images (convert PDF pages to images and look).
- **List dependencies** explicitly and verify they are available in the target runtime. Claude
  API code execution has no network and no runtime installs; claude.ai can install from npm
  and PyPI. The scripts in this skill need Python 3 and PyYAML (`pip install pyyaml`).
- **MCP tools**: always fully qualified, `ServerName:tool_name`, or Claude may not find them.
- **Don't assume tools are installed**: state the install command, then the usage.

## Checklist

Core quality
- [ ] Description is specific, includes key terms, says what and when, third person
- [ ] SKILL.md body under 500 lines; details in separate files
- [ ] No time-sensitive information (or in an "old patterns" section)
- [ ] Consistent terminology
- [ ] Examples are concrete, not abstract
- [ ] File references one level deep; progressive disclosure used appropriately
- [ ] Workflows have clear steps

Code and scripts
- [ ] Scripts solve problems rather than defer to Claude; explicit, helpful error handling
- [ ] No voodoo constants
- [ ] Required packages listed and verified; scripts documented
- [ ] Forward slashes only
- [ ] Validation steps for critical operations; feedback loops for quality-critical tasks

Testing
- [ ] At least three evaluations
- [ ] Tested on every model you will use (Haiku, Sonnet, Opus and above)
- [ ] Tested with real usage scenarios; team feedback incorporated

---

## Model and Claude Code notes

Not from the skill-authoring page. Sources: Claude Code skills docs and the prompting guides.

### Trigger language and over-triggering (Claude Opus 4.5 and later)

From the prompting best practices: "Claude Opus 4.5 and Claude Opus 4.6 are also more
responsive to the system prompt than previous models. If your prompts were designed to reduce
undertriggering on tools or skills, these models may now overtrigger. The fix is to dial back
any aggressive language. Where you might have said 'CRITICAL: You MUST use this tool when...',
you can use more normal prompting like 'Use this tool when...'."

Migration guidance: "Tune anti-laziness prompting: if your prompts previously encouraged the
model to be more thorough or use tools more aggressively, dial back that guidance." Instructions
like "If in doubt, use [tool]" cause overtriggering.

General principle, same page: give the reason, not just the rule. "NEVER use ellipses" is less
effective than "your response will be read aloud by a text-to-speech engine, so never use
ellipses". Claude generalizes from the explanation.

### Prescriptiveness (Claude Fable 5 and later)

From the Fable 5 prompting guide: "Skills developed for prior models are often too prescriptive
for Claude Fable 5 and can degrade output quality. Review and consider removing older
instructions if default performance is better." Instruction following is strong enough that a
brief instruction with its reason steers most behaviors; enumerating every case is unnecessary.
Also: do not instruct the model to reproduce its reasoning in the response; that can trigger a
refusal category on Fable 5.

Practical consequence: always measure the no-skill baseline on the model you will run. If the
baseline does not fail, do not write the guidance.

### Claude Code frontmatter reference

All fields optional in Claude Code; `description` is recommended. Frontmatter is read only when
`---` is the first line of the file.

| Field | Meaning |
|---|---|
| `name` | Display name; defaults to the directory name |
| `description` | What the skill does and when to use it. Combined with `when_to_use`, truncated at **1,536 characters**; put the key use case first |
| `when_to_use` | Extra trigger context (phrases, example requests); appended to the description, counts toward the cap |
| `argument-hint` | Autocomplete hint, e.g. `[issue-number]` |
| `arguments` | Named positional arguments for `$name` substitution |
| `disable-model-invocation` | `true`: only the user can invoke with `/name`; description is not loaded into context. Use for side-effecting workflows (deploy, commit, send) |
| `user-invocable` | `false`: only Claude can invoke; hidden from the `/` menu. Use for background knowledge |
| `allowed-tools` | Tools pre-approved for the turn that invokes the skill |
| `disallowed-tools` | Tools removed from the pool while the skill is active |
| `model`, `effort` | Overrides for the turn |
| `context: fork`, `agent`, `background` | Run the skill in a forked subagent |
| `hooks` | Hooks registered when the skill is invoked |
| `paths` | Glob patterns; the skill auto-loads only when working with matching files |
| `shell` | `bash` (default) or `powershell` for inline `!` commands |
| `metadata`, `license`, `compatibility` | Spec fields; Claude Code stores but does not act on them |

Substitutions available in the body: `${CLAUDE_SKILL_DIR}` (the skill's directory) and
`${CLAUDE_PROJECT_DIR}`.

### Listing budget

Claude Code loads every skill's name and description into context. The listing budget is
**1% of the model's context window**; when exceeded, descriptions are shortened and keywords
can be lost. `/doctor` estimates the listing cost; `/context` shows the Skills row after the
budget is applied. Raise with `skillListingBudgetFraction` or trim low-priority skills to
`"name-only"` via `skillOverrides`. This is why description length matters more than body
length.

### Where skills live

- Personal: `~/.claude/skills/<name>/SKILL.md` (Codex, Copilot CLI, Gemini CLI also read
  `~/.agents/skills/`)
- Project: `.claude/skills/<name>/SKILL.md`, discovered from the start directory up to the repo
  root; nested project skill dirs load lazily when a file under them is touched
- Plugins: `skills/<name>/SKILL.md` inside the plugin
- Validate frontmatter with `claude plugin validate <real directory>` (does not follow symlinks)

### Triggering mechanics

Claude consults a skill only for tasks it cannot trivially do itself. One-step requests
("read this PDF") may not trigger a matching skill; substantive, multi-step, or specialized
requests do. Eval queries for trigger tuning must therefore be substantive. If a skill triggers
too often: make the description more specific, or set `disable-model-invocation: true`.
