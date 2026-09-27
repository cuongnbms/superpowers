# spendlog — design

Date: 2026-09-26 · Status: Approved

## Purpose

A personal, single-user Python CLI that imports transaction CSV exports from Vietcombank and
Techcombank, categorizes them with user-defined rules, never double-counts a transaction when
overlapping exports are re-imported, and prints a monthly spending report per category with
alerts for categories over their monthly budget. All data stays on the local machine.

**Constraints:** single user, one machine, VND only, CSVs downloaded manually (no bank API).
Python 3.12, zero runtime dependencies (stdlib `argparse`, `csv`, `sqlite3`, `tomllib`,
`unicodedata`), pytest for tests, uv project with a `spendlog` console script.

**Success criteria:**
- Importing the same or overlapping exports any number of times yields each real transaction
  exactly once, including two genuinely identical same-second transactions.
- Changing a rule immediately changes how past transactions are categorized; manual overrides
  survive rule changes.
- The monthly report shows net spending per category, an Uncategorized row, and flags every
  category whose spending exceeds its budget.

## Domain rules

- **Amount sign:** every stored transaction has one signed integer amount in VND; negative is
  money out (debit), positive is money in (credit).
- **Category resolution** (computed at read time, never stored), in order:
  1. the transaction's manual override, if set;
  2. the first rule in config-file order whose `match` is a case-insensitive substring of the
     description (both sides NFC-normalized and casefolded);
  3. otherwise `Uncategorized` if the amount is negative, `Income` if positive.
- **Reserved categories:** `Transfer` and `Income` are excluded from spending and budgets.
  `Uncategorized` is implicit: it cannot be the target of a rule or override, nor have a budget.
  `Transfer` and `Income` may be the target of rules and overrides but may not have budgets.
- **Spending** of a category in a month = `−sum(amount)` over that month's transactions in the
  category. Credits that resolve to a spending category (refunds) therefore reduce it; spending
  may be negative.
- **Month** of a transaction is taken from its transaction date (`YYYY-MM`).
- **Over budget** means spending is strictly greater than the budget.

## Architecture

`src/spendlog/` — every module except `store.py` and `cli.py` is pure.

| Module | Responsibility |
|---|---|
| `models.py` | `ParsedTransaction`, `Transaction`, `Rule`, `Config` dataclasses |
| `amounts.py` | Parse bank amount strings to `int`; format `int` as `1,250,000` |
| `parsers/vietcombank.py` | Recognize header, parse rows, handle footer + cross-check, fingerprint |
| `parsers/techcombank.py` | Recognize header, parse rows, fingerprint |
| `parsers/__init__.py` | `detect_and_parse(path) -> ParseResult` — reads file, picks bank by header |
| `config.py` | `load_config(path) -> Config`; validation errors raise `ConfigError` |
| `categorize.py` | `categorize(txn, rules) -> str` (implements category resolution) |
| `report.py` | `build_report(txns, config, month) -> Report`; `render_report(Report) -> str` |
| `store.py` | SQLite schema, insert-or-ignore, fingerprint lookup, queries, overrides |
| `cli.py` | `main(argv=None) -> int`; argparse subcommands wiring the above |

### Storage

SQLite database, default `$XDG_DATA_HOME/spendlog/spendlog.db`
(`~/.local/share/spendlog/spendlog.db`). Created with its parent directory on first use.
Schema version tracked with `PRAGMA user_version = 1`.

```sql
CREATE TABLE transactions (
    id                INTEGER PRIMARY KEY,
    bank              TEXT NOT NULL,           -- 'vcb' | 'tcb'
    date              TEXT NOT NULL,           -- ISO YYYY-MM-DD
    amount            INTEGER NOT NULL,        -- signed VND, negative = out
    description       TEXT NOT NULL,
    reference         TEXT,                    -- NULL when the bank gave none
    fingerprint       TEXT NOT NULL UNIQUE,
    override_category TEXT,                    -- NULL = use rules
    imported_at       TEXT NOT NULL            -- ISO datetime
);
CREATE INDEX transactions_date ON transactions(date);
```

### Config

TOML, default `$XDG_CONFIG_HOME/spendlog/config.toml` (`~/.config/spendlog/config.toml`).

```toml
[[rules]]
match = "GRAB"          # case-insensitive substring of description
category = "Transport"

[[rules]]
match = "CHUYEN TIEN"
category = "Transfer"

[[rules]]
match = "LUONG"
category = "Income"

[budgets]
Transport = 1_500_000
Food = 4_000_000
```

Validation (`ConfigError`, exit 2): invalid TOML; unknown top-level keys; a rule missing
`match` or `category`, or with a non-string / empty value; a rule targeting `Uncategorized`;
a budget value that is not a positive integer; a budget on `Transfer`, `Income`, or
`Uncategorized`. A missing config file is **not** an error: rules and budgets are empty and
`report`/`list` print one hint line naming the expected path.

## Import

`spendlog import FILE... [--dry-run]`

1. **Parse all files first.** Each file is read as `utf-8-sig` (strips the Techcombank BOM,
   harmless otherwise). Lines are scanned until one, parsed as CSV and with each cell stripped
   and NFC-normalized, matches a known bank header (comparison casefolded). If no header is
   found in the first 20 lines the file is unrecognized. Columns are located by header name.
2. **All-or-nothing.** If any file is unrecognized or any row fails to parse, nothing is
   written; the error names file and line (`b.csv line 17: cannot parse amount "1,25O,000"`)
   and the command exits 1. Blank lines are skipped; any other unparseable row is an error.
3. **Insert** every file's transactions in a single SQLite transaction with
   `INSERT OR IGNORE` on `fingerprint`. With `--dry-run`, fingerprints are only looked up and
   nothing is written.
4. **Summary per file:** `vcb-aug.csv (Vietcombank): 42 rows, 12 new, 30 already present`;
   with `--dry-run` a final line `Dry run: nothing written.`
5. **Same-file fingerprint collision:** if a row's fingerprint equals an earlier row's in the
   same file, the later row is skipped and a warning naming both line numbers is printed. The
   same applies across files within one command.

### Vietcombank format

```
NGAN HANG TMCP NGOAI THUONG VIET NAM
Tai khoan: 0011001234567
Tu ngay 01/08/2026 den ngay 31/08/2026
STT,Ngày giao dịch,Số tham chiếu,Số tiền ghi nợ,Số tiền ghi có,Mô tả
1,02/08/2026,FT26214A1B2C,"85.000",,"GRAB*A-7XK2 HCM"
2,03/08/2026,FT26215D3E4F,,"25.000.000","LUONG THANG 7"
3,05/08/2026,FT26217G5H6I,"1.250.000",,"THANH TOAN HOA DON DIEN EVN"
,Tổng cộng,,"1.335.000","25.000.000",
```

- Header: `STT, Ngày giao dịch, Số tham chiếu, Số tiền ghi nợ, Số tiền ghi có, Mô tả`.
  Lines above it are ignored.
- Date `dd/mm/yyyy`. Amounts use `.` as thousands separator; after removing `.` the value must
  be a non-negative integer.
- Exactly one of debit / credit must be non-empty: amount = `−debit` or `+credit`. Both or
  neither is a row error. Empty `Số tham chiếu` is a row error.
- Fingerprint: `vcb:<Số tham chiếu>`.
- **Footer:** a row whose `STT` cell is empty and whose second cell equals `Tổng cộng`
  (NFC-normalized, casefolded) ends the data section; all lines after it are ignored. The
  footer is optional. When present, its debit and credit totals (empty = 0) must equal the sums
  of the parsed debits and credits; a mismatch is an import error.

### Techcombank format

```
Transaction Date,Description,Amount,Balance,Reference
2026-08-02 12:31:05,SHOPEE PAY TOPUP,"-500,000","12,300,000",TCB26080211
2026-08-04 19:02:44,HIGHLANDS COFFEE Q1,"-65,000","12,235,000",
2026-08-04 19:02:44,HIGHLANDS COFFEE Q1,"-65,000","12,170,000",
```

- Header: `Transaction Date, Description, Amount, Balance, Reference`. UTF-8 with BOM.
- `Transaction Date` is `YYYY-MM-DD HH:MM:SS`; its date part is the transaction date.
- `Amount` and `Balance` use `,` as thousands separator with optional leading `-`; after
  removing `,` each must be an integer.
- Fingerprint: `tcb:<Reference>` when Reference is non-empty; otherwise
  `tcb:<Transaction Date>|<amount>|<balance>|<description>` using the normalized integer
  values. The balance keeps genuinely identical same-second transactions distinct.

## Other commands

Global options (before the subcommand): `--db PATH`, `--config PATH`.

- `spendlog report [--month YYYY-MM]` — default is the current local month.
- `spendlog list [--month YYYY-MM] [--category NAME | --uncategorized]` — default month is
  the current one. Columns: `ID  DATE  BANK  AMOUNT  CATEGORY  DESCRIPTION`, ordered by date
  then id; an overridden category is marked with a trailing `*`. Category filter compares
  casefolded.
- `spendlog categorize ID CATEGORY` sets a manual override; `spendlog categorize ID --clear`
  removes it. Unknown ID exits 1. `Uncategorized` is rejected as a target (use `--clear`).

Exit codes: 0 success, 1 runtime/input error (bad CSV, unknown ID), 2 usage or config error.

## Report

For the chosen month, resolve every transaction's category, then:

- One row per spending category with non-zero spending, plus one row per budgeted category
  (shown even at 0). Columns: `Category`, `Spent`, `Budget` (`-` if none), `Used`
  (percentage rounded to the nearest integer, `-` if no budget), and `OVER by N` when over
  budget.
- Rows sorted by spending descending, ties by name; **`Uncategorized` is always the last row**
  and is shown whenever its spending is non-zero.
- `Total` = sum of all shown rows.
- A `Not counted:` line lists `Income N` (net sum of Income amounts) and the Transfer part,
  joined by ` · `. The Transfer part is `Transfer N out, M in`, dropping whichever side is zero
  (`Transfer 5,000,000 out`, `Transfer 2,000,000 in`). Income and Transfer are each shown only
  when non-zero; the line is omitted when both are.
- Alerts at the bottom: `⚠ K categor{y,ies} over budget: Food (4,350,000 / 4,000,000), ...`.
- Amounts formatted with `,` thousands separators.
- A month with no transactions prints `No transactions for 2026-09.` and exits 0.

```
Spending report — 2026-08

Category           Spent       Budget   Used
Food           4,350,000    4,000,000   109%  OVER by 350,000
Bills          1,250,000            -      -
Transport        985,000    1,500,000    66%
Shopping         500,000            -      -
Uncategorized    120,000            -      -
------------------------------------------------
Total          7,205,000

Not counted: Income 25,000,000 · Transfer 5,000,000 out

⚠ 1 category over budget: Food (4,350,000 / 4,000,000)
```

Exact column widths are an implementation detail fixed by the golden test.

## Testing

TDD with pytest.

- **Unit:** `amounts` (both separators, negatives, rejects decimals/garbage); Vietcombank
  parser on the exact sample above (junk lines, footer, cross-check pass and mismatch, both /
  neither debit-credit, NFD-encoded header and footer); Techcombank parser (BOM, empty
  reference, the two identical coffees get distinct fingerprints); `categorize` (override wins,
  first-match order, case-insensitivity, Uncategorized vs Income default); `config` validation
  cases; `build_report` (refund nets against category, Transfer/Income excluded, Uncategorized
  last, zero-spend budgeted row, strict over-budget); `render_report` golden output.
- **Integration** via `cli.main([...])` with temp `--db` / `--config`: re-import of an
  overlapping file reports 0 new; `--dry-run` writes nothing; a malformed second file rolls back
  the first; an override survives a rule change; `list` filters; `report` golden output.

## Out of scope

Regex rules, automatic transfer pairing, multiple accounts per bank, other currencies, other
banks, budget warnings below 100%, editing transactions, exporting data.
