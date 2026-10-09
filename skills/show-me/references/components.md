# Component catalog

Markup for every component the frame styles. Copy a snippet, then replace the content with the real thing. Start each screen with an `<h1>`: the tab title comes from it. Colors, spacing, and light and dark themes come from the frame, so write no `<style>` blocks. Inline `style` is fine for one-off layout, such as a width, never for color.

Use only the class names listed here. A class that is not in this file has no styling.

## diagram

Use it for flows, sequences, states, schemas, and history. The Mermaid source goes in a `pre` as plain text; the caption is optional.

```html
<figure class="diagram">
<pre class="mermaid">flowchart LR
  A[Agent] -->|writes fragment| S[(screens/)]
  S -->|listed by mtime| V[server.py]
  T[Browser tab] -->|GET /api/screens| V
  class T accent</pre>
<figcaption>The amber node is the only part that runs in your browser.</figcaption>
</figure>
```

See the Mermaid section below for the diagram types and the rules that keep them readable.

## compare

Use it to put two or three options side by side. Each `option` carries a letter, a title, the thing itself (usually a `mock`), and a `note` with the trade-off. The options stack on narrow screens.

```html
<div class="compare">
  <figure class="option">
    <figcaption><span class="letter">A</span>Sidebar on the left</figcaption>
    <!-- a mock, a diagram, or a tree goes here -->
    <p class="note">Fits more than six sections. Costs about 140px of width.</p>
  </figure>
  <figure class="option">
    <figcaption><span class="letter">B</span>Horizontal tabs</figcaption>
    <!-- the same thing, the other way -->
    <p class="note">Compact on narrow screens. Past five tabs the last ones scroll out of sight.</p>
  </figure>
</div>
```

## mock

Use it to sketch a UI: a browser window with a body inside. The parts below go in `mock-body`. Keep the mock to the screen your human partner asked about, with the real labels and field names from the project.

```html
<div class="mock">
  <div class="mock-bar"><i></i><i></i><i></i><span class="mock-url">app.local/settings/profile</span></div>
  <div class="mock-body">
    <!-- mock-nav or mock-tabs, mock-form, mock-actions -->
  </div>
</div>
```

`mock-nav` is a vertical list of sections, `mock-tabs` a horizontal one. Mark the current entry with `on`:

```html
<nav class="mock-nav">
  <span class="on">Profile</span><span>Security</span><span>Billing</span>
</nav>
<div class="mock-tabs"><span class="on">Profile</span><span>Security</span><span>Billing</span></div>
```

`mock-form` holds fields and toggles. A `field` is a label over an `input`; a `toggle` is a switch, and `on` turns it on:

```html
<div class="mock-form">
  <div class="field"><label>Display name</label><div class="input">Linh Tran</div></div>
  <div class="field"><label>Email</label><div class="input">linh@example.com</div></div>
  <div><span>Send me a weekly summary</span><span class="toggle on"></span></div>
</div>
```

`mock-actions` holds the buttons, and `btn` is a button:

```html
<div class="mock-actions"><span class="btn">Save changes</span></div>
```

`placeholder` is a hatched box for content that does not matter to the point, such as an image or a chart. Give it a label:

```html
<div class="placeholder">chart</div>
```

## annotations

Use pins to point at the parts of a mock that differ between options, then explain them in a legend below. Put the pin inside the element it marks, and number the legend the same way.

```html
<span class="btn">Save changes<b class="pin">2</b></span>

<ol class="legend">
  <li><b class="pin">1</b>The current section stays visible however long the list grows.</li>
  <li><b class="pin">2</b>Save sticks to the bottom of the form instead of scrolling away.</li>
</ol>
```

## tree

Use it for a data structure, a config file, or a directory layout. Each `row` has four cells: `k` the key or name, `t` the type, `v` the value, `n` a note. `tree-head` holds a title and a short meta line. Add `data-depth` (0 to 3) to indent nested rows; a row without it sits at the top level.

```html
<div class="tree">
  <div class="tree-head"><span>.superpowers/show-me/</span><span>git-ignored</span></div>
  <div class="row" data-depth="0"><span class="k">show-me/</span><span class="t">dir</span><span class="v"></span><span class="n">everything the skill writes</span></div>
  <div class="row" data-depth="1"><span class="k">screens/</span><span class="t">dir</span><span class="v"></span><span class="n">one .html fragment per screen</span></div>
  <div class="row" data-depth="2"><span class="k">settings-layouts.html</span><span class="t">file</span><span class="v">3.4 KB</span><span class="n">newest, so the tab opens on it</span></div>
  <div class="row" data-depth="1"><span class="k">server.json</span><span class="t">file</span><span class="v">212 B</span><span class="n">pid, port, key</span></div>
</div>
```

## trace

Use it to walk through how code runs. Write one `li` per step in `trace-steps`, with the function name in `fn` and `file:line` in `loc`, then one `pre` per step in the same order. The frame builds the step buttons, the why panel, the prev and next bar, and arrow-key stepping.

```html
<div class="trace">
  <ol class="trace-steps">
    <li><span class="fn">do_GET</span><span class="loc">server.py:88</span></li>
    <li><span class="fn">check_key</span><span class="loc">server.py:41</span></li>
  </ol>
<pre data-start="88" data-hl="4" data-why="Every request enters here. The key check runs before any routing."><code class="language-python">def do_GET(self):
    path, _, query = self.path.partition("?")
    path = unquote(path)
    if not check_key(self, query):
        return self.send_error(403)</code></pre>
<pre data-start="41" data-hl="3-4" data-why="The key comes from the query first, then the cookie."><code class="language-python">def check_key(req, query):
    given = parse_qs(query).get("key", [None])[0]
    given = given or cookie_value(req, "show_me_key")
    return hmac.compare_digest(given or "", KEY)</code></pre>
</div>
```

The attributes on each `pre`:

- `data-start` is the file line number of the block's first line, so the gutter matches the file.
- `data-hl` is the highlighted lines, counted from 1 within the block, not the file line. `4` is the fourth line of the block. Use commas and ranges for several: `2,5-6`.
- `data-why` is the sentence shown when the step is selected. Say why the step matters, not what the line does.

Use the real code, trimmed to the lines that carry the step, and set the language on the `code` element (`language-python`, `language-js`, and so on).

## callout

Use it for a point your human partner should not miss. `callout warn` is amber and marks a risk or a catch.

```html
<div class="callout">
  <p><strong>Tabs survive restarts.</strong> The server reopens on its old port with its old key.</p>
</div>
<div class="callout warn">
  <p><strong>Idle shutdown is now four hours.</strong> Open tabs do not count as activity.</p>
</div>
```

## Plain HTML

Headings, paragraphs, lists, tables, `code`, and `pre` are styled by the frame. A bare code block takes a language the same way as a trace step:

```html
<pre><code class="language-bash">python3 scripts/server.py status</code></pre>
```

## Mermaid

Pick the type by the question the picture answers:

- `flowchart`: how parts connect or how a process branches. Use `flowchart LR` for pipelines and `flowchart TD` for hierarchies. A wide diagram scrolls sideways inside its figure on a narrow screen, so prefer `TD` when it has many nodes.
- `sequenceDiagram`: who calls whom, in order. Use it when a request crosses services.
- `stateDiagram-v2`: the states of one thing and what moves it between them.
- `erDiagram`: tables or entities and their relations.
- `gitGraph`: branches and merges.

```html
<figure class="diagram">
<pre class="mermaid">sequenceDiagram
  participant B as Browser
  participant S as server.py
  B->>S: GET /?key=f3a9c1
  S-->>B: 200 + Set-Cookie
  loop every second
    B->>S: GET /api/screens
    S-->>B: screens, newest
  end</pre>
</figure>
```

Rules that keep diagrams readable:

- Keep labels short, two or three words. Move detail to the caption.
- Quote a label that holds punctuation or brackets: `A["parse(query)"]`.
- Do not start an edge or node label with a number and a period (`1. đọc`) or with a dash or asterisk and a space. Mermaid reads it as a markdown list and draws "Unsupported markdown: list". Write `đọc (1)` or `bước 1: đọc` instead.
- To mark the one node that matters, add `class X accent` as the last line. It turns the node amber, and it works in `flowchart` and `graph` only; other diagram types ignore it.
- Do not set colors with `style` or `classDef`. The frame themes every diagram for light and dark.
