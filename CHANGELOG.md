# Changelog

Versions follow semver. `VERSION` is canonical; `tests/test_version_sync.py`
fails if the hook, the output style marker, or this file disagree with it.

- **Major:** a rule or budget change that makes existing replies score
  differently, or a settings/hook wiring change that needs reinstalling.
- **Minor:** new rules, report columns, or commands; adding or removing an
  optional module.
- **Patch:** fixes and wording that don't change what gets measured.

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
