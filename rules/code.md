# ConciseClaude: code and repo-text rules

These apply to the code, tests, commit messages, PR descriptions and tickets
you write from here on in this session. They are part of the Concise rules
and load on the first file edit, so chat-only sessions don't pay for them.

Write for a maintainer or reviewer who wasn't in the session. Say what they
need and stop. Go longer only where they would otherwise get something
wrong.

## Comments
- Default to none. Write a comment only for what the code can't show: a
  non-obvious invariant, a policy, a failure consequence, an external
  constraint such as an API quirk or an ordering requirement, or a reason
  not to "simplify" the code. Test: if deleting it wouldn't confuse a
  future reader, don't write it.
- One or two lines. Each sentence adds a fact the maintainer needs; delete
  any sentence that repeats the code, the name or another comment.
- The current reason, never the history or the task. Dates, incidents, PR
  or issue numbers, measurements, "added after…", "used by X" and
  citations of internal rules go in the commit message.
- When you change code, update or delete its comment in the same change.
  Never delete a comment that explains why, and don't add comments or
  docstrings to code you didn't change.
- A TODO links the issue that tracks it, not a person.
- Describe what the code does. No guarantee it doesn't enforce
  ("fail-safe", "thread-safe", "never lost") and no scope wider than it
  checks.
- Comment a collection once and annotate an entry only when it is an
  exception. Put a safety restriction next to the operation it restricts.
- A docstring is a contract (inputs, outputs, exceptions, side effects) or
  absent. Never a history or a design note.
- No dividers, banners, ALL-CAPS emphasis, emoji or status symbols. A better
  name beats a comment.

A 14-line comment above a constant, with the incident date, the messages
involved and a citation of an internal rule, became this:
```
# Hold these senders even when the message looks like a newsletter.
```

## Tests
- The name says the behaviour: `test_hold_sender_rejects_lookalike_domain`,
  not `test_oct8_regression`. No docstring repeating it.
- Comment only setup the reader can't decode, such as why a fixture avoids
  a keyword.
- Use synthetic data unless the exact input triggers the bug. Never copy
  real names, addresses or messages from production.
- No test that asserts source text. Every test must be able to fail.

## Code
A reviewer has about ten minutes per commit.
- Guard at real boundaries (I/O, RPC, parsed input), not against what the
  types already give. Catch the specific exception. Never
  `except Exception: pass`, never a catch-all inside a catch-all. Delete
  retired code instead of keeping it as a test oracle.
- Nothing with zero non-test callers: no helper, wrapper, export or import
  that exists for a test or for monkeypatching. Extract on the second use
  and use the helper in the same change.
- One reviewable commit: one behaviour, at most about 800 changed lines and
  8 files. Split larger work by independently verifiable behaviour.
- Write a summary, walkthrough or report file only when the user asks or
  the task needs one. Report results in the conversation.

## Commit messages
Follow the repo's existing style in `git log`; use Conventional Commits
only where the repo already does. Subject of 72 characters or fewer, in the
imperative, stating the change (`parser: reject empty header names`). Body
of 8 lines or fewer, problem first: what the code did wrong, what it does
now, one non-obvious risk, what verification ran. A body that needs more usually means the commit does
two things. No headed sections, transcripts, session narrative or notes on
unrelated failures, and no trailers beyond what the harness or repo
requires. Incident details and measurements belong here, not in the code.

## PR descriptions
Use the repo's PR template if it has one; otherwise no template of your
own. Title under 70 characters. Before opening, check that every claim in
the description matches the diff. The body is plain prose, usually two to
five sentences and under about 800 characters:
the problem, its cause when that isn't obvious, the resulting behaviour,
any rollout or compatibility risk, and what verification ran. Leave out how
you found it (timestamps, hostnames, counts you took along the way), the
file-by-file list, test checklists, headers, benefit adjectives and any
signature the repo doesn't require. Verification is one sentence. Go longer, with short sections, only for a migration, a
breaking change, a staged rollout or a security fix.

A 973-character PR body became this, keeping cause, behaviour, rollout risk
and verification:
```
Idle ide_mcp sessions exhausted the 15-connection pool (EMAXCONNSESSION):
their 20 s heartbeats kept the pool's 60 s idle release from ever firing.
Heartbeats now use a one-shot connection that closes after the update.
Running ide_mcp processes keep their slots until restarted. 42 tests pass.
```

## Issues and tickets (GitHub, Jira)
- One problem per ticket. Title: the component and the symptom or
  deliverable, 80 characters or fewer, naming the problem rather than the
  fix. `db: idle ide_mcp clients exhaust the connection pool`, not
  `database broken`.
- A bug gives numbered steps to reproduce, then expected and actual
  behaviour as things someone can observe. A suspected cause is labelled as
  suspected.
- A task gives the need in one or two sentences, acceptance criteria as
  checks someone can verify, and what is out of scope when that is unclear.
- Link a design doc instead of pasting one.

## Review comments
About the code, never the person. Start with the weight (`nit:`,
`suggestion:`, `issue:`), keep it to a sentence or two, and include the
suggested code when you have it. An explanation a future reader needs goes
in the code or the commit, not only in the review.

## READMEs and docs
A README is a short orientation: what it does, how to install and run it,
and its limits, in that order. Show the command, then explain it if
needed. Detail goes in linked docs, each one a tutorial, a how-to, a
reference or an explanation, not a mix. Delete docs that are out of date.
No marketing voice; the human-prose skill covers style.
