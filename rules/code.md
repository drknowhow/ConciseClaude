# ConciseClaude: code and commit rules

These apply to the code, tests and commit messages you write from here on in
this session. They are part of the Concise rules and are loaded on the first
file edit so chat-only sessions don't pay for them.

## Code
A reviewer has about ten minutes per commit and cannot read thousands of
lines of change and commentary. A git hook measures each staged diff.
- **One reason, once, at the layer that owns it.** A comment states the
  invariant the next few lines cannot show. Dates, PR numbers, counts, probe
  results, and "before this change" belong in the commit message, not the
  code, and not in a test docstring either.
- **A docstring is a contract**: inputs, outputs, exceptions, side effects.
  No contract beyond the signature, no docstring. Never a history or a design
  note; those go in a doc the code points to.
- **No comment that restates the identifier, the test name, or the next
  line.** No dividers or banners. No ALL-CAPS emphasis. Prefer a better name
  to a comment.
- **Tests: the name says what, once.** No docstring repeating it. No test
  that asserts source text. Every test must be able to fail.
- **Guard at real boundaries** (I/O, RPC, parsed input), not against what
  the types already give. Catch the specific exception. Never
  `except Exception: pass`, never a catch-all inside a catch-all. Delete
  retired code instead of keeping it as a test oracle.
- **Nothing with zero non-test callers**: no helper, wrapper, export, or
  import that exists for a test or for monkeypatching. Extract on the second
  use and use the helper in the same change. One parameterised
  implementation, not a cloned sibling module.
- **One reviewable commit**: one behaviour, at most about 800 changed lines
  and 8 files. Split larger work by independently verifiable behaviour.

## Commits
Subject ≤72 characters, stating the observed change. Body ≤8 lines: what
changed, why the old behaviour was wrong, one non-obvious risk or
compatibility note, what verification ran. Links for chronology and
measurements. No headed sections, no verification transcripts, no notes on
unrelated failures, no session narrative. The body is where forensics live,
so the code does not need them.
