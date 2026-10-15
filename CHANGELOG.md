# Changelog

Versions follow semver. `VERSION` is canonical; `tests/test_version_sync.py`
fails if the hooks, the output style marker, `.claude-plugin/plugin.json`, or
this file disagree with it.

- **Major:** a rule or budget change that makes existing replies score
  differently, or a settings/hook wiring change that needs reinstalling.
- **Minor:** new rules, report columns, or commands; adding or removing an
  optional module.
- **Patch:** fixes and wording that don't change what gets measured.

## 6.2.0 (2026-10-15)
Cost. The 6.1 benchmark found the plugin cheaper in conversation but dearer
in coding and single cold calls, because its rule text adds input tokens to
every session.
- The style is about 3,600 characters instead of 7,558 and the code rules
  3,359 instead of 6,425, with the same rules. The session-start pointer is
  gone: subagents never received it, and the forced style now carries its
  human-prose reminder. A cold call adds about 1,225 input tokens, down from
  2,950.
- In the benchmark, 6.2 costs 23% less than default on Opus and 13% less on
  Sonnet (6.1: 8% less and 9% more), and covers 85% of key points (6.1: 82%).
- New rule: answer every part of the question, including the distinction an
  explanation turns on and the choice a plan depends on. In the 6.1
  benchmark, rate-limiting plans skipped the algorithm and some
  process-versus-thread answers skipped race conditions.

## 6.1.1 (2026-10-15)
- The diff meter flags `## Summary`-style headings in commit messages passed
  with `-m` or `-F`, which is how Claude commits. It used to drop every line
  starting with `#`, though git strips those only from an edited message.
  This fix was pushed to the 6.1 PR after it merged and missed 6.1.0.
- One line saying what verification ran no longer counts as a transcript,
  since the rules ask for it. A second such line, or pasted command output,
  still does.

## 6.1.0 (2026-10-15)
Code comments and repo text: less is more. The evidence is in
`docs/repo-text-audit-2026-10-15.md`.
- The code rules load when C3's `c3_edit` makes the first edit, as well as
  on `Edit` and `Write`. Before this, sessions that edit through C3 never
  received them.
- Comments default to none. One that exists states, in a line or two, what
  the code can't show: an invariant, a policy, a failure consequence or an
  external constraint. A comment whose deletion wouldn't confuse a future
  reader isn't written. No history, task references, internal-rule
  citations or guarantees the code doesn't enforce, and a comment that
  explains why is never deleted.
- New sections for tests, PR descriptions (two to five sentences, under
  about 800 characters, checked against the diff), issues and Jira tickets,
  review comments and READMEs, with short examples from real rewrites.
  Commits follow the repo's own style.
- The diff meter warns on a block of six or more added comment lines, and
  no longer counts a TODO that cites its issue as a forensic comment.

## 6.0.0 (2026-10-15)
Rules against the writing habits readers complain about in Claude's output.
The evidence, from four research passes and 45 days of our own transcripts,
is in `docs/claude-slop-research-2026-10-15.md`. Update with
`claude plugin update`.
- The compact budget is 600 prose characters, up from 400. IDE replies
  already had a median of 532 to 648 under the old budget, and asking for
  brevity alone made Claude's text dense and cryptic. Labeled replies keep
  900, `/u` keeps 150.
- The first line is a bold plain-word tag and a plain verdict:
  `**DONE**`, `**CAVEAT**`, `**BLOCKED**` or `**WORKING**`. The ✅ ⚠️ ❌ ⏳
  glyphs and `▸` bullets are gone, and nothing else in a reply is bold
  except the labels. The meter still recognises the old glyph line, so
  rule sets that ask for it score the same.
- A new "Write plainly" section in the style: cut points before words, keep
  sentences whole, use the literal word in place of a decorative metaphor,
  explain coined terms, state the positive claim, drop importance and
  sincerity labels, tie completion claims to what ran.
- The human-prose skill's cut list is reordered for current models: density,
  metaphor, contrast framing and staging first, the older puffery word list
  last.
- The code rules ban emoji in code, comments and logs and unrequested
  summary files, and hold PR descriptions to the problem, the behaviour and
  the verification that ran.
- The reply meter logs counts of writing tells per reply (metaphor, contrast
  framing, salience and sincerity words, overclaiming, offers, arrows,
  emoji, em-dashes, extra bold). The report shows rates per category. It
  never nudges on them yet.
- The README hero shows a real 6.0 reply from Opus 5.5: the median-length of
  three runs of the benchmark's rebase question, all three free of counted
  tells. The token and cost figures were measured on 5.x and haven't been
  re-run on 6.0; the plugin description no longer quotes them.

## 5.1.0 (2026-10-04)
- **Sonnet and Opus only.** Haiku sessions skip the meter, the nudge and the
  code rules: the hooks read the model off the session transcript and stand
  down for Haiku. The style and the session pointer tell a Haiku model to
  ignore them. No output-style setting can scope a style by model, so Haiku
  still loads the style text (about 1,500 input tokens) and some replies come
  out shorter than with no plugin.
- **Why.** In a 435-reply Haiku benchmark the 5.0 style cut no cost (+15% in
  one run, −4% in another) and left coverage flat: most Haiku output is
  hidden thinking, which the style doesn't touch. Block mode raised cost by
  19–28% and cut coverage.

## 5.0.0 (2026-10-04)
Rule and scoring changes from a 448-reply benchmark against blind checklist
grading. The plugin picks them up with `claude plugin update`. Manual installs
need step 2, 5 and 6 of IMPLEMENT.md again, for `rules/code.md` and the new
`PostToolUse` hook.
- **A plain ask for depth gets depth.** "In depth", "in detail", "the full
  picture" or "as much space as you need" makes that reply verbose, in the
  style and in the meter. The meter doesn't log it as "asked for more".
  Before this, Sonnet answered such a request with about 900 output tokens
  and a pointer to `/v`.
- **Look-first steps are never cut.** The dry run, listing or backup that
  goes with a destructive command stays in the reply, as does any
  precondition the result depends on and every defect found in a review.
- **Drafts are deliverables.** A PR description, email or doc the user will
  send goes complete inside a fence, which the meter doesn't count.
- **Labels are narrower.** A protected label requires that the user asked
  for a plan, review, migration or debugging, or that the reply carries real
  risk. An explanation, recommendation or how-to stays compact. `report`
  now shows the share of labeled replies.
- **Code rules load on demand.** The Code and Commits sections move to
  `rules/code.md`, and `hooks/code_rules.py` adds them on a session's first
  file edit. The Example section is gone. Together that is about 540 fewer
  input tokens on every call. `hooks/run.sh` now takes the script name.

## 4.0.0 (2026-10-03)
Wiring change: ConciseClaude installs as a Claude Code plugin. A manual install
from 3.x must be removed first, or every reply is metered twice; see
"Moving from a manual install" in the README.
- **Plugin.** `claude plugin marketplace add drknowhow/ConciseClaude`, then
  `claude plugin install conciseclaude@conciseclaude`. Upgrades are
  `claude plugin update`.
- **The style is forced.** It is on in every session while the plugin is
  enabled, even over an explicit `outputStyle`. Disabling the plugin turns it off.
- **No interpreter path in settings.** Hooks run through `hooks/run.sh`, which
  uses the first real Python 3.8+ (`py -3`, `python3`, `python`) and fails open.
- **No CLAUDE.md edit.** A SessionStart hook prints the rules pointer instead.
- **Namespaced commands.** `/conciseclaude:v`, `/conciseclaude:u`,
  `/conciseclaude:diff-hooks` (new: installs the git diff meter),
  `/conciseclaude:meter` (new: report and mode for both meters), and the
  `conciseclaude:human-prose` skill. The meter scores both `/u` and
  `/conciseclaude:u` as the ultra stage.
- **Diff meter shims survive upgrades.** Installed from the plugin cache, the
  git hooks call a copy at `~/.claude/conciseclaude/diff_shape.py`, which the
  SessionStart hook refreshes.

## 3.1.0 (2026-09-20)
- **`diff_shape.py scan [--ref]`** runs a whole tree through the meter, for
  seeing what a repo looks like before the hooks go in.
- **`except Specific: pass` is warn-class** (`silent-except`). Only a bare or
  catch-all handler that swallows is fail-class (`swallowed-except`). A
  handler that `continue`s past a bad record is neither.
- **The repo follows its own rules.** `reply_shape.py` loses four section
  dividers, a 20-line module docstring, a catch-all in `get_mode`, and two
  `except OSError: pass`; `diff_shape.py` loses its own dividers. `scan` on
  this tree reports no findings.

## 3.0.0 (2026-09-20)
Major because the rules now cover the code Claude writes, and a second meter
ships. The Claude Code hook wiring is unchanged; step 6 is not needed. Install
step 5b adds the new git hooks per repo.
- **Code and Commits sections in `concise.md`.** One reason once, at the layer
  that owns it; contract-only docstrings; no dividers, shouting, or restating
  comments; tests that can fail; guards at real boundaries only; nothing with
  zero non-test callers; one behaviour per commit; commit body ≤8 lines. The
  Never-cut carve-out for "file contents and commit messages" now covers only
  literals, since it was read as licence for essays in code.
- **`hooks/diff_shape.py`.** A `pre-commit` and `commit-msg` meter. Fail-class:
  swallowed `except`, dividers, dates or `#NNN` in comments, comment share
  over 25% of added lines, headed commit bodies. Warn-class: docstring longer
  than its body, module docstring over 10 lines, catch-all that never
  re-raises, shouting, comment share over 15%, more than 800 changed lines or
  8 files, subject over 72, body over 8 lines, verification transcripts.
  `warn` mode (default) never refuses a commit; `block` refuses on fail-class.
  Not measured yet: zero-caller helpers and cloned sibling modules.
- **Evidence:** `docs/code-verbosity-audit-2026-09-20.md`. Thirty
  Claude-authored commits across four repos, read by three subagents and four
  federated agents. 15–28% of added lines were removable in three repos, over
  half of it comments and docstrings, and eleven robustness defects were
  found under the prose. Thresholds follow published comment-density means
  (about 18–19%) rather than a stricter guess.

## 2.0.0 (2026-09-16)
Major because replies now score differently. The hook wiring is unchanged, so
an upgrade only replaces `reply_shape.py` and `concise.md`; step 6 is not needed.
Four scoring fixes, all reported by Muninn:
- **Table cells count as prose** ([#1]). Only the pipes and the `|---|` row are
  scaffolding. Before, a reply could get under budget by moving its text into
  a table. Inline code inside a cell no longer splits the row.
- **Labels must be bold** ([#2]). `**Plan:**`, `**Risk: headline.**`, and
  `⚠️ **Risk:**` still get 900. An unformatted `Plan:`, or a quoted `ERROR:` log
  line anywhere in the reply, no longer does.
- **The quality signal counts only `/v` and `/u`** ([#3]). The phrase list
  ("explain this", "shorter", "elaborate", ...) matched requests about the code
  as feedback about the reply. On 14 days of real prompts, every phrase match
  was a false positive. `asked_more` and `asked_shorter` are now sparse but
  accurate.
- **Only real HTML tags are stripped** ([#4]). A `<...>` span is markup only
  when it names an HTML element and has nothing but `name=value` attributes, so
  `if a <b and c> d` and `Dict<str, int>` count in full. `>` and `#` are markup
  only at the start of a line (quote, header), so `a > b` and `issue #4` count too.

Measured on 1,723 replies from the same 14 days: 7 replies moved from within
budget to over, none moved the other way, and 6 of 137 labeled replies lost the
900 budget.

[#1]: https://github.com/drknowhow/ConciseClaude/issues/1
[#2]: https://github.com/drknowhow/ConciseClaude/issues/2
[#3]: https://github.com/drknowhow/ConciseClaude/issues/3
[#4]: https://github.com/drknowhow/ConciseClaude/issues/4

## 1.1.0 (2026-09-15)
- **Removed:** the optional C3 module (`c3/claude-md-snippet.md` and install
  step 10). The repo now contains only the reply system itself.
- **Repo hygiene:** `.gitignore` now excludes agent and tool config (`CLAUDE.md`,
  `AGENTS.md`, `GEMINI.md`, `.claude/`, `.mcp.json`, `.c3/`, and similar), so a
  session opened in this folder can't commit its own setup.

## 1.0.0 (2026-09-15)
First public release.
- **Rules:** `output-styles/concise.md` is the only rule set. It sets a 400-char
  default budget and a 900-char budget that applies only under a true label,
  plus `/v` (no limit) and `/u` (150). Replies follow a five-part grammar. The
  file also covers mid-turn updates and exempts subagent reports.
- **Meter:** `hooks/reply_shape.py` has Stop and UserPromptSubmit hooks, with
  nudge as the default mode and block optional. It reads Claude Code's
  `last_assistant_message` and falls back to the transcript. It logs a quality
  signal (the next prompt asks for more or for shorter). Subcommands: `report`,
  `mode`, `measure`, `version`.
- **C3 module:** optional install of C3 (`code-context-control` on PyPI) for
  cheaper code reading and filtered terminal output, with its own reply-style
  advisor turned off so only one rule set applies.
- **Writing pass:** `skills/human-prose`.
