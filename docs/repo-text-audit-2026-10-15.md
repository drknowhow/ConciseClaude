# Code comments and repo text, 2026-10-15

Input for ConciseClaude 6.1. Dimitri's rule: comments, PR descriptions,
READMEs and tickets are read by other people, so they should be human
readable and verbose only when needed. This measures where Claude's repo
text stands, finds why the September code rules didn't hold everywhere, and
records the rewrites Cod and Vi did.

## Before and after the September code rules

Claude-authored commits (author `yepgent` or a Claude trailer) and merged
PRs, measured with the diff meter's own analyzers. "Before" is 1 August to
19 September, "after" is 21 September to 15 October. Up to 120 commits per
window and repo.

| repo | window | comment share | findings per 1k added lines | median commit body | bodies over 8 lines | median PR prose chars |
|---|---|---:|---:|---:|---:|---:|
| Yep | before | 18.3% | 22.7 | 16 lines | 79% | 2,068 |
| Yep | after | 9.8% | 12.2 | 8 lines | 43% | 1,258 |
| C3 | before | 11.3% | 11.1 | 21 lines | 83% | 1,785 |
| C3 | after | 6.4% | 8.1 | 8 lines | 50% | 935 |
| yep-edu | before | 13.5% | 9.8 | 18 lines | 79% | 1,530 |
| yep-edu | after | 8.9% | 4.3 | 14 lines | 68% | 1,470 |

GentChat had two commits in the after window and CardMaker none with PRs,
so they are left out.

Comment share roughly halved and commit bodies got shorter, but the change
can't be credited to the rules. Opus 5.5 arrived on 22 September, at the
boundary, and the rules weren't reaching most sessions (next section). PR
bodies are still long: the slowest tenth runs 2,400 to 3,600 prose
characters. Dividers and dated incident comments still land in every repo.

## Why the rules didn't hold

- `rules/code.md` loads on a session's first file edit through a
  PostToolUse hook that matched `Edit|Write|MultiEdit|NotebookEdit`. Dimitri's
  projects edit through C3's `c3_edit`, so the rules never loaded there. A
  session that made dozens of `c3_edit` calls on 2026-10-15 never received
  them. 6.1 adds `mcp__c3__c3_edit` to the matcher.
- The diff meter's git hooks are installed per repo with
  `/conciseclaude:diff-hooks`. None of the six repos measured has them, so
  no commit was checked.

## A comment, rewritten (Cod)

Yep commit `106f0af1` (8 October) added a 14-line comment above a constant:
the incident date, the two messages involved, where the domains were
measured, and a "failure polarity" paragraph citing an internal rule. The
commit message already told the same story. Cod's rewrite:

```
# Hold these senders even when the message looks like a newsletter.
```

He also removed the docstring on `hold_sender` (it repeated the predicate
and described Google mail by content when the code checks domains), the
per-entry `# account, device, security notices` (the code holds all mail
from the domain), and "fail-safe, not lost" (an unwanted archive is still a
failure). The test comments became test names:
`test_hold_sender_accepts_listed_subdomain`,
`test_hold_sender_rejects_domain_lookalike`.

His rule changes, adopted in 6.1: a comment covers a non-obvious invariant,
policy, failure consequence or external constraint; each sentence adds a
distinct fact; no guarantee the code doesn't enforce; a collection is
commented once; a safety restriction sits beside the operation it
restricts. He argued against a hard line cap, so the new diff-meter check
for blocks of six or more comment lines only warns.

## A PR description, rewritten (Vi)

Vi cut the body of Yep #1816 from 973 to 307 characters:

```
Idle ide_mcp sessions exhausted the 15-connection pool (EMAXCONNSESSION)
because 20 s heartbeats prevented the 60 s idle release from freeing slots.
Heartbeats now use one-shot connections that release immediately after
updating. Existing ide_mcp processes hold slots until restarted.
Verification: 42 tests passed.
```

She dropped the investigation (the failing job, the time, the host, the
connection count), the file-by-file list, the bold headers and the bot
signature, and kept the cause, the new behaviour, the rollout risk and the
verification. Her issue and Jira rules (title with component and symptom,
numbered steps, observable expected and actual, testable acceptance
criteria, explicit scope) are in `rules/code.md`.

## What the published guidance adds

A research subagent read Google's engineering practices and style guides,
Git's and the Linux kernel's patch guidance, Chris Beams on commit
messages, PEP 257, Go's doc-comment guide, Ousterhout's debate with Robert
Martin, Mozilla's bug-writing guidelines, Microsoft's Azure Boards
guidance, Diátaxis, digital.gov's plain-language guide, Keep a Changelog,
Anthropic's own prompts and issue threads about Claude's comments
(anthropics/claude-code #65961, #52808, #69095, #98907). The additions it
supported:

- A removal test for comments, from Anthropic's prompt: "If removing the
  comment wouldn't confuse a future reader, don't write it." The
  "invariant" test alone lets through comments shaped like invariants that
  are still noise (#65961).
- No task or caller references ("used by X", "added for the Y flow").
- The over-correction guard. A Claude Code prompt that said to default to
  no comments made Claude delete docstrings that explained why (#52808).
  6.1 says never delete a comment that explains why, and update or delete
  a comment in the same change as its code.
- Commit subjects follow the repo's `git log` style, imperative, with
  Conventional Commits only where the repo already uses them. Git and the
  kernel both start the body with the problem.
- A PR description is checked against the diff before it opens. A 2026
  study of 23,247 agent PRs found that PRs whose description claimed
  changes the code didn't make were accepted 28% of the time, against 80%.
- One problem per ticket, titled by the problem rather than the fix
  (Mozilla).
- Review comments are about the code, start with their weight (`nit:`,
  `suggestion:`), and carry the suggested code. In 54,791 agent review
  comments, an inline suggestion was the strongest predictor that a comment
  got resolved.

No authoritative source gives a numeric cap on comment length. The sources
agree on the shape (short, explaining why) and disagree on how many
comments are enough, so 6.1 sets "one or two lines" as the default and the
diff meter only warns.

## What 6.1 changes

- `rules/code.md` becomes the code and repo-text rules: comments default to
  none, new sections for tests, PR descriptions (two to five sentences,
  under about 800 characters), issues and tickets, and READMEs.
- The rules load on `c3_edit`.
- The diff meter warns on comment blocks of six or more added lines.

## Open

- Installing the diff meter's git hooks in the main repos, in warn mode, so
  each commit's findings show up in the commit output Claude reads.
- Nothing measures PR bodies or tickets as they are written. A check on
  `gh pr create` would need a PreToolUse deny, since context a hook adds
  arrives only with the tool result.
- Jira isn't connected in C3 (`c3 jira login`), so the ticket rules come
  from Vi's review and published guidance, not from Dimitri's tickets.
