# Code verbosity audit, 2026-09-20

Input for ConciseClaude 3.0: extend the reply rules to the code Claude writes.
What shipped from it: the Code and Commits sections in
`output-styles/concise.md` and the `hooks/diff_shape.py` git-hook meter.

Method: three read-only subagents each read the diffs of 6–10 recent commits
authored by Claude (as `yepgent`) in four repos, classified what they saw with
`file:line` evidence, and estimated how many added lines could go without
changing behaviour or readability. Numbers below are theirs; I read the
reports, not every diff.

## Headline

| repo | commits read | added lines | comment lines | cuttable |
|---|---|---|---|---|
| Yep (Python) | 10 | 1,574 | 256 (16%) | ~23% |
| yep-edu (TypeScript) | 5 | 1,903 | 413 (22%) | ~18% |
| C3 (Python) | 10 | 6,522 | 955 docstring+comment (15%) | ~15% |
| GentChat (Kotlin/Python/JS) | 5 | 1,257 | 125 (10%) | ~6% |

Weighted across the four: roughly one added line in seven is removable, and
**over half of the removable mass is prose, not logic.** All three auditors
said the executable code is tight: no emoji logs, no stray prints, no unused
flags, minimal type ceremony, few one-implementation abstractions. GentChat,
the repo with the least prose, is near the floor.

So the problem is not code verbosity in the usual sense. It is reply verbosity
that moved into the code: the narration, restating, and significance
inflation that ConciseClaude cut from chat replies now lives in comments,
docstrings, test docstrings, and commit messages.

## Patterns, most frequent first

1. **Incident forensics in comments and docstrings.** Dates, PR numbers,
   measured counts, percentile tables, probe results. Present in every Yep
   commit and most C3 commits. Examples: a 16-line comment above a 2-line
   constant pair (`yep/scripts/start_yep_server.py:80`); a 27-line docstring
   on a 22-line body (`c3/services/shell_output.py:965`); a module header
   rewritten to record that a probe returned `400 NoSuchBucket`
   (`yep-edu/src/lib/edu-media.ts:6`). The commit message already holds all
   of it.
2. **The same reason at three or four altitudes.** Commit message, module
   header, function docstring, call-site comment, test docstring. The
   yep-edu budget guard's "charged before the model, never after" appears in
   `llm-budget.server.ts:8`, `problem-gen.ts:282`, `api/tutor/route.ts:30`
   and the commit body. C3's `agent_downshift.py` header restates the PR and
   `core/config.py:317` restates the header.
3. **Docstring longer than the body; docs on trivial helpers.** A 44-line
   docstring on a 153-line file (`yep/scripts/_interpreter_probe.py`); a
   7-line docstring on a one-line ternary (`c3/cli/tools/delegate.py`
   `claude_default_tier_key`); `/** First letter for the ring glyph. */` over
   three lines (`gentchat/hub/gentchat_hub/web/needsyou.js`).
4. **Section dividers.** `# ── lifecycle ──`, `// ---- generate_set ----`.
   14 in one C3 commit, 18 in another; 19 yep-edu files carry them; three
   lines each for one word of information.
5. **Test prose in three layers.** Module docstring restating the commit,
   then a banner, then a per-test docstring restating a sentence-length test
   name (`test_a_continuation_takes_an_ordinary_slot_when_one_is_free`). The
   test bodies themselves are dense and mostly table-driven.
6. **Single-use wrappers and callerless exports.** `probe_timeout_s()` is a
   one-line pass-through with a docstring (Yep); `usageToday()` and
   `isLlmKind` are exported, tested, and never called (yep-edu); `436c0c9`
   in C3 wrote `_hub_policy_audit` and then inlined a copy of the same block
   in the same commit.
7. **Guards the types already give.** `raw === null` on a
   `string | undefined`; `Array.isArray` checked by the caller and again by
   the callee; `try/except Exception: pass` around setting an attribute;
   a catch-all nested inside a catch-all (`c3/cli/hook_agent_model.py`).
   The fail-closed parsing at real RPC boundaries is legitimate and stays.
8. **Shouting.** `// FAILS CLOSED.`, `THE TENANCY RULE, and it has no
   exceptions:`, `test('AN EXISTING FAMILY NEVER MEETS THE GATE')`. When
   everything is emphasised nothing is.
9. **Commit messages as PR bodies** (C3). A 48-line message with `WHAT
   SHIPS.` / `VERIFIED BY LOADING IT` headers and a note about an unrelated
   failing test.
10. **Retired code kept as a test oracle** (C3). `_override_widenings_legacy`
    and `_write_override_section_legacy` in `mobile_api.py`, ~65 lines, so
    a test can assert old equals new.

## How this maps onto ConciseClaude

The current `concise.md` Cut list already names the failure classes. They
just were not applied to code:

| Reply rule (Cut) | Code equivalent found |
|---|---|
| Narration of work the user just watched | Incident history and probe results in comments (1) |
| Restating the request | Same reason at four altitudes (2); comment restates next line |
| Padding, lists stretched | Dividers (4), three-layer test prose (5) |
| Significance inflation, puffery | ALL-CAPS comments and test names (8) |
| Suspense, colon cliffhangers | Docstrings with underlined section headers |

The Never-cut list also translates: the invariant and the non-obvious why
stay, exact error strings stay, "who did what" stays in the commit message.

One line in the current rules is doing damage. Under Never cut: "Tool
arguments, file contents, commit messages, and docs you write stay complete
and exact." It was written to stop literals being shortened. It reads as
licence to write essays in code, and it exempts commit messages entirely.

## Candidate rules for 3.0

One sentence each, in the style of the existing Cut list. Draft, not final.

1. **Say a reason once, at the lowest level that owns it.** A comment names
   the invariant the next five lines cannot show. Dates, PR numbers, counts,
   and probe results go in the commit message; the code gets one pointer at
   most.
2. **A docstring is never longer than the body it documents. A comment
   block is at most three lines.** Longer means it is a design note; file it
   and point to it.
3. **No dividers or banners.** A file that needs them needs splitting.
4. **No helper, export, or constant with one caller, and none with zero
   non-test callers.** Inline it; extract on the second use, and use the
   helper you extracted in the same change.
5. **Guard only where the shape is genuinely unknown.** Name the exception
   you catch. Never nest a catch-all in a catch-all. Delete retired code
   instead of keeping it as a test oracle.
6. **Tests: the name says what, one docstring line at most, never the name
   again. No shouting anywhere.**
7. **Commit message: subject plus a body that says what changed and its
   observable effect.** No headed sections, no verification transcripts, no
   notes on unrelated failures.

Rule 7 conflicts with the current Yep habit of long PR bodies. That is a
decision for Dimitri, not an oversight.

## Measuring it

The reply meter is a Stop hook and cannot see code. Three options, cheapest
first:

- **Pre-commit or PostToolUse diff meter.** On `git diff --cached` (or the
  Edit/Write payload): comment-line share, longest docstring versus its body,
  divider count, comment lines containing a date or `#NNN`. Report, nudge,
  optionally block. Same shape as `reply_shape.py`.
- **Commit-message meter.** Body line count and headed-section detection in a
  `commit-msg` hook.
- **Ratio target.** The auditors' numbers suggest a healthy diff sits under
  10% comment lines (GentChat) and an unhealthy one over 15% (Yep, yep-edu).
  A threshold, not a law: a one-line ordering-invariant comment on a moved
  line (`c3 1f16eb1`) is worth every character.

## Federated review (Vi, Ola, Gro, Cod)

Vi (Gemini) and Ola (GLM via Ollama Cloud) reviewed the summary above.
Gro (Grok) reviewed it plus Vi's and Ola's answers, with web research.
Cod (Codex) ran two read-only tasks on the Yep and GentChat repos
themselves; his findings follow the three asks.

### Where they agree, and disagree with my ranking

- **Robustness hazards outrank prose volume in reviewer cost.** All three.
  A 16-line comment is skimmed in two seconds; an `except Exception: pass`
  is studied, because the reviewer must work out what it hides. Ola's
  order: retired code kept alive (10), dead guards and swallowed errors (7),
  single-use wrappers (6), then repeated reasons (2). Gro's refinement: two
  axes, not one list. Swallowed errors are defects; comment bloat is a
  review tax. Volume is what makes the defects unreviewable, so fix both.
- **Repeated reasons are a synchronisation risk, not just length** (Ola).
  Three copies of one rationale can diverge, and then the reviewer has to
  check which one is true.
- **Length caps get gamed** (Vi, Gro). A docstring-shorter-than-body rule
  invites inflating the body or splitting one essay into four 3-line
  blocks. A line cap on functions invites nested ternaries and `a && b()`
  chains. Rule by content, not length: a docstring states the contract
  (inputs, outputs, exceptions, side effects) or does not exist; a comment
  never restates the identifier, the test name, or the next line.
- **Rule 4 is too absolute** (Ola, Gro). A single-use helper that names a
  non-trivial operation is documentation by extraction; inlining it can
  produce a 40-line body. Public API, the first caller of a new seam, and
  test factories all look like one caller. Keep the hard part: zero
  non-test callers is a fail.
- **Rule 5 is the most valuable and the least complete.** Add: never catch
  to `pass`; catch the specific type; no `try` around code that cannot raise
  the caught type; `assert` is not error handling in production; a guard
  must cover the whole domain of the invariant, not the directory where the
  bug was first seen (Vi); fail loudly on a DB or API failure instead of
  returning an empty structure that looks like data (Vi).
- **Forensics belong in the commit, not the code, and not nowhere.**
  Gro against Ola: a hard 3-line commit body would push dates, PR numbers
  and probe counts back into comments. Budget the shape of the message,
  not its length. Vi: a reviewer needs the intent, the why, the evidence
  of verification, and what was deliberately not tested. Headed 48-line
  bodies with notes on unrelated failures are the actual problem.
- **Start warn-only for two weeks, then set fail thresholds from the
  distribution** (Ola, Gro). A hook that fires on every commit gets
  disabled.

### Missing rules they proposed

- No commented-out code, no unused imports (Ola).
- No speculative generality: no `isinstance` guards "in case the input
  changes" (Ola); no unverified default identifiers such as model names or
  env vars introduced as production defaults (Vi).
- Tests must include a negative control that fails when the implementation
  is broken (Vi). Source-text greps as tests are the vacuous-pass case.
- Prefer types and names over comments (Gro): the positive form of rule 2.

### Measurement, corrected

Gro's research changes the thresholds. Arafat and Riehle (ICSE 2009)
measured a mean comment density near 19% across 5,000 open-source
projects; a 2026 arXiv study of AI versus human commits in real repos
(2603.27130) found comment ratios nearly identical at about 18%, with AI
code larger in statements and structure, not comments. So a 10% "healthy"
line would flag ordinary human Python, and a hook that counts only
comments would train the model to write denser code instead of shorter
comments. Threshold the added hunk, and lean on the signals that are
defects regardless of ratio.

| Signal (per staged diff) | Start |
|---|---|
| `except` with empty or `pass` body, or catch-all with no log or re-raise | fail |
| New function or constant with zero non-test callers | fail |
| Divider or banner comment | fail |
| Comment containing an ISO date or `#NNN` | fail |
| Docstring lines exceed body lines, per function | warn |
| Same 8+ token phrase in the commit message and a new docstring | warn |
| Comment and docstring share of added non-blank lines | warn over 15%, fail over 25% |
| Commit body with headed sections or verification transcript | fail |

Implementation: `git diff --cached` plus a tree-sitter or `ast` pass for the
`except` and caller checks, regex for the rest. Ola's single-caller check
needs a grep of the tree for each new name; tractable on a diff.

### Cod, on the Yep repo itself (task a8f3f08d1560)

Cod read eight Python commits directly (e9bdcea, ac7abc2, bf343b5,
b99c408, 61b3893, b8f6198, 238e736, 9f4b812): 7,848 added lines, 4,523
production and 3,325 test, 578 comment lines, 102 divider lines. His
cut estimate is 22–28%, in line with my subagent's 23%. He confirmed every
pattern on the checklist except callerless exports, and he agrees the
redundant guards are mostly legitimate boundary checks.

What he added that nobody else saw, because he read the code rather than
the summary:

- **Megadiffs are the first cost.** 9f4b812 is 4,310 added lines across
  11 Python paths; ac7abc2 is 1,486 across 20. His single best rule for
  review speed is a per-commit budget of roughly 800 changed Python lines
  and 8 paths, excluding generated and vendored code; split otherwise.
- **Three patterns missing from my list:** copy-and-substitute sibling
  modules (a clone with names changed instead of a shared implementation),
  source-text meta-tests (asserting a substring appears in a file), and
  several semantic fixes squashed into one commit narrative.
- **Commit bodies ran 147–905 words, mean about 307.**
- **Six robustness findings hiding under the prose**, which is the point
  the other three siblings made in the abstract:
  1. e9bdcea: the Grok retry promise has a hole. `clicked=True` lives only
     in child memory until persisted; if transport dies between click and
     result write, the stage reports "wrote no result" without `clicked`,
     and a duplicate paid render is possible.
  2. e9bdcea: `probe_video` lets `TimeoutExpired` and `JSONDecodeError`
     escape while `main` catches only `RuntimeError`, breaking the
     advertised one-JSON-object contract.
  3. bf343b5: overflow suppression drops the whole detected error whenever
     the overflow regex matches anywhere, so a real error mixed with an
     overflow notice becomes `None` (`tool_error_capture.py:72-76`).
  4. ac7abc2: breaker state load, save and delete catch `Exception` and log
     at debug; malformed state is `pass`. The 53-line header promises a
     breaker that can silently reset.
  5. b99c408: typed timeout information is converted back into substring
     matching (`_BLIND_MARKER = "timed out"`), so unrelated `OSError` text
     can be misclassified; a production import is kept only for tests.
  6. 238e736: every exception in tag probing is labelled `UNREACHABLE`,
     conflating daemon outage with malformed JSON and programmer error.

Two more patterns from his full report: programs embedded in giant strings
(a 664-line Python script carrying Python and JavaScript inside string
literals, which evades navigation and analysis), and test scaffolding
shaping production code (a `subprocess` import kept "re-exported for
tests", forwarding wrappers that exist to be monkeypatched). He also names
stringly typed state machines as a review cost: raw dicts and status
strings passed through many phases force the reviewer to reconstruct the
schema, and the defensive checks follow from the representation.

His rules, verbatim in substance:

1. A commit must fit a ten-minute review: at most about 800 changed Python
   lines and 8 paths; split larger work by independently verifiable
   behaviour.
2. State each rationale once: PR and design docs own incident chronology;
   code comments explain only the local invariant that remains true.
3. Docstrings carry contract, inputs, outputs and hazards; normally five
   lines or fewer, never longer than a trivial body.
4. Name tests by behaviour in 60 characters or fewer; historical evidence
   goes in the issue, not the test name or docstring.
5. No forwarding wrapper, public alias, or production import added solely
   to make monkeypatching convenient.
6. No broad `except Exception` or `pass` on correctness, billing, locking
   or alert-state paths without returning or recording the lost failure
   category.
7. Prefer one shared, parameterised implementation over cloning a sibling
   module, poller, or test suite.

Commit messages, his budget: a factual subject of 72 characters or fewer;
a body of about 120–150 words or eight lines holding only the changed
behaviour, why the old behaviour was wrong, material risk or
compatibility, and exact verification; links for chronology and
measurements. Not the session URL, not every timestamp, not every
intermediate defect. That sits between Ola's three lines and Gro's "shape
only", and is the one I would adopt.

He did not run pytest (the read-only sandbox had no writable temp dir);
syntax and whitespace checks passed on all 47 changed paths. The
duplicate-render finding is static analysis, not a live reproduction.

### Cod, on GentChat (task a09384221472)

Six commits, 1,641 added lines, 6–8% removable, almost all repeated prose.
He confirms GentChat as the good calibration set but will not certify
"cleanest of four" without auditing the other three himself.

What GentChat does that the other repos should copy:

- One narrow vertical slice per commit: API, state transform, UI, tests,
  with no unrelated refactoring discovered halfway through.
- Pure policy in small functions (`voiceTap`, `needsYouRows`,
  `delegateTierOptions`) understood without executing Compose, the DOM or
  the database, and tested with concrete examples.
- Names that expose the domain, not the mechanics.
- Unknown wire values preserved and displayed rather than reset to a
  default; both the normal route and the security boundary tested.
- Commit subjects that describe the observed problem, not the activity.

Same waste, smaller: the Needs-you refetch rationale appears in the commit,
two JS files, the HTML, the API wrapper and the test module. Dividers in
CSS, JS and Kotlin. ALL-CAPS "NATIVE SUBAGENTS" repeated. One commit body
that is a design note; another that spends paragraphs on eight lines.

Robustness under the prose, GentChat edition:

1. **The cross-repo drift tests cannot detect drift.** Both the Kotlin and
   Python helper-tier tests compare a locally copied daemon list against a
   local production list (`DelegateTierPickerTest.kt:17`,
   `hub/tests/test_delegate_picker.py:19`). They stay green when Yep's
   real vocabulary changes. The comments claim otherwise. His most
   important finding.
2. **Voice player lifecycle is stronger in prose than in tests.** Tests
   cover pure transitions only; the real path catches `Exception` (can
   swallow coroutine cancellation), can leak a `MediaPlayer` if
   `setDataSource` throws before assignment, and releases the slot but not
   the player on error (`VoicePlayer.kt:155`).
3. **Web ask refreshes can race**: overlapping `loadAsks()` calls with no
   generation or abort, so an older response can overwrite a newer one,
   and the catch block suppresses every error (`app.js:3078`).
4. **"Same predicate" is documentation, not enforcement**: the open-ask
   predicate is duplicated rather than shared (`store.py:2044`), and
   Android dropped ask identity so the list has no stable keys.

His commit-body budget: soft, 120–180 words or 8–12 lines, holding the
observable change, why, one non-obvious invariant or risk, and what
verification ran; longer only for migrations, incidents, security
decisions. Consistent with his Yep number and with Gro; Ola's three lines
is the outlier.

His suggested next step: apply the rules to an equivalent sample from the
worst-rated repo and compare removals by category, not raw line count.

## Consensus after five readers

Where my three subagents, Vi, Ola, Gro and Cod all land:

- Cut estimates hold: Yep 22–28%, yep-edu ~18%, C3 ~15%, GentChat 6–8%.
  The mass is prose, and the executable logic is mostly tight.
- The reviewer's cost ranks differently from the line count: diff size
  first (Cod), then hidden defects (swallowed errors, dead guards, retired
  code, tests that cannot fail), then repeated rationale, then the cheap
  visual noise. Rules must cover both axes.
- "Say each reason once, at the layer that owns it" is the rule with the
  largest line payoff, named first by all five.
- Rule by content, not by length caps: contract-only docstrings, no
  comment that restates the identifier or the next line, no forensics in
  code. Length caps get gamed.
- Hard-fail signals for a hook: empty or catch-all `except` without log or
  re-raise, zero non-test callers, dividers, dates or `#NNN` in comments,
  headed commit bodies. Warn-only for two weeks first.
- Commit bodies get a soft budget near eight lines, not three. The
  forensics live there, so the body cannot be squeezed to nothing.
- Added by the readers, not in my draft: a per-commit size budget
  (~800 lines, 8 paths), no clone-and-substitute sibling modules, no
  source-text meta-tests, no test scaffolding shaping production imports,
  negative controls in tests, no programs embedded in strings.

Eleven robustness findings came out of a verbosity audit. That is the
argument for 3.0 covering code: the prose was hiding them.

## Not verbose, for the record

Executable code across all four repos. Test bodies (parametrized, shared
fixtures). Type hints. Logging. The `_interpreter_probe.py` extraction in
Yep is a real deduplication with two callers. yep-edu's fail-closed RPC
parsing caught two real uncharged-spend bugs and is earned.
