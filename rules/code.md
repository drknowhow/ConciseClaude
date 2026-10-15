# ConciseClaude: code and repo-text rules
For the code, tests, commits, PRs and tickets you write in this session.
Write for a maintainer or reviewer who wasn't there: say what they need,
and go longer only where they would otherwise get something wrong.

## Comments
- Default to none. Comment only what the code can't show: a non-obvious
  invariant, policy, failure consequence, external constraint, or why not to
  "simplify" it. If deleting it wouldn't confuse a future reader, don't
  write it. One or two lines.
- The current reason, never history or task: dates, incidents, PR or issue
  numbers, measurements, "used by X" and internal-rule citations go in the
  commit. A TODO links its issue, not a person.
- Describe what the code does; no guarantee it doesn't enforce
  ("fail-safe", "thread-safe"). Comment a collection once.
- Update or delete a comment with its code. Never delete one that explains
  why; don't add comments or docstrings to code you didn't change.
- A docstring is a contract (inputs, outputs, exceptions, side effects) or
  absent. No dividers, banners, ALL-CAPS or emoji.

A 14-line comment with an incident date and an internal-rule citation
became `# Hold these senders even when the message looks like a newsletter.`

## Tests and code
- Test names say the behaviour (`test_hold_sender_rejects_lookalike_domain`),
  with no docstring repeating them. Synthetic data unless the exact input is
  the bug; never real names or messages. Every test must be able to fail.
- Guard at real boundaries (I/O, RPC, parsed input). Catch the specific
  exception; never `except Exception: pass`.
- Nothing with zero non-test callers. One behaviour per commit, at most
  about 800 changed lines and 8 files.
- No summary or report files unless asked; report in the conversation.

## Commits
Follow the repo's `git log` style; Conventional Commits only where the repo
uses them. Subject 72 chars or fewer, imperative, stating the change. Body
8 lines or fewer, problem first: what was wrong, what changed, one risk,
one line on what verification ran. No headers, transcripts, session story
or trailers the harness or repo doesn't require.

## PRs, reviews, tickets, docs
- PR: the repo's template if any; title under 70 chars; every claim checked
  against the diff. Two to five sentences, under about 800 chars: problem,
  cause, new behaviour, rollout risk, what ran. No discovery story, file
  list, test checklist, headers or benefit adjectives. Longer only for a
  migration, breaking change, staged rollout or security fix.
- Review comment: about the code, opens with its weight (`nit:`,
  `suggestion:`, `issue:`), a sentence or two, with the suggested code.
- Ticket: one problem, titled by component and symptom
  (`db: idle clients exhaust the connection pool`). A bug gives numbered
  steps and observable expected vs actual; a task gives the need and
  testable acceptance criteria. Label a guess as a guess.
- README: what it does, how to install and run it, its limits. Link detail;
  delete stale docs.

A 973-char PR body became: "Idle ide_mcp sessions exhausted the
15-connection pool: 20 s heartbeats kept the 60 s idle release from firing.
Heartbeats now use a one-shot connection. Running ide_mcp processes keep
their slots until restarted. 42 tests pass."
