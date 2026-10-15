---
name: human-prose
description: Use before shipping prose other people read (PR descriptions, review comments, docs, READMEs, tickets, emails, release notes). A revision pass that strips the habits readers flag in Claude's writing.
---

# Human prose: revision pass

Draft first without self-censoring, then run this pass. Trying to obey every
rule while drafting produces stilted text, which is its own tell.

**Above the checklist:** a smooth, impressive sentence is a warning sign, not a
quality signal. Ask what it actually asserts. The rougher sentence that says a
specific true thing usually wins.

Accuracy and the reader's understanding come first. Never cut a fact, a
qualification, or an uncertainty to satisfy this list, and keep exact
technical terms, identifiers and quotations as they are.

## Cut-list (highest payoff first)
Ordered for current Claude models (Opus 5.5, Fable 5.1, Sonnet 5.5). The
evidence is in `docs/claude-slop-research-2026-10-15.md` in the
ConciseClaude repo.
1. **Density.** Dropped articles and pronouns, coined labels, sentences that
   need a second read ("Checked, not recalled."). Rewrite them longer and
   plainer. Explain a term the reader hasn't seen when it affects what they
   understand or do.
2. **Decorative metaphor.** "load-bearing", "seam", "earns its keep", "a dial
   worth turning", "doing a lot of work". Say what you mean. Keep a
   technical term when it is accurate.
3. **Contrast framing.** "It's not X, it's Y", "rather than merely", "less X,
   more Y", rebutting a position nobody took. State the positive claim; keep
   a contrast only when the distinction matters to the reader.
4. **Staging.** "Here's the part that…", a point held back for the last
   line, a closing slogan or aphorism, runs of fragments ("Fast. Simple.
   Effective.").
5. **Importance and sincerity labels.** "This matters", "worth noting", "the
   real story", "honestly", "genuinely". Show the consequence instead.
6. **Significance inflation. Delete, don't soften.** "serves as a testament
   to", "underscores", "plays a vital/pivotal/crucial role", and trailing
   clauses like "…, highlighting…", "…, ensuring…", "…, fostering…". State
   the fact and stop.
7. **Overclaiming.** "fully verified", "production-ready", "comprehensive",
   "no regressions". Say what changed, what ran, and what didn't.
8. **Restore the copula.** "serves as / functions as / represents / acts as"
   → **is**. "boasts / features / offers" → **has**, or say what it does.
9. **Rule of three.** Use the real count.
10. **Formulaic conclusions.** Delete "In conclusion / Overall / In summary"
    and the closing restatement. End on the last real point or the next step.
11. **Vague attribution.** "Experts say / studies show / it is widely
    regarded": name the source or cut the claim.
12. **Puffery.** Older models' words, still worth one sweep: boasts, vibrant,
    robust, seamless, groundbreaking, meticulous, delve, leverage (verb),
    landscape, navigate (metaphorical), unlock, elevate, foster, showcase,
    testament.

## Formatting tells
- Bold on every key phrase, or "**Label**: description" on every bullet.
  Bold only what needs emphasis.
- Emoji, check marks or status symbols anywhere in the text.
- `→` standing in for a verb in a sentence.
- Em-dashes: at most one per paragraph. Two in a sentence means it should be
  two sentences.
- Title Case Headings → sentence case unless house style differs.
- Tool artifacts that must never ship: `oaicite`, `contentReference`,
  `turn0search`, `[cite:`, `utm_source=`, `【 】`.

## Voice
- **Agency:** say who did what. "It was determined" hides the actor.
- **Lead with the finding.** No "Here's what I found:".
- **Concrete over abstract:** "p95 latency went from 180 ms to 2.4 s" beats
  "a notable performance regression".
- **Repeat words** rather than cycling synonyms for the same thing.
- **Vary rhythm.** A short sentence after a long one.

## The pass
1. Read once; flag anything you wouldn't say to a smart colleague who
   wasn't there.
2. Rewrite every sentence that needs a second read.
3. Sweep items 2–12, then the formatting tells.
4. Re-read the first and last sentence; kill throat-clearing and wrap-ups.
5. Check that the smoothest sentence actually says something.
6. Check that nothing true got cut on the way.

## PR and review comments
Write like a terse engineer. A PR body is usually two to five sentences,
under about 800 characters: the problem, its cause when that isn't obvious,
the resulting behaviour, any rollout risk, and the verification that ran.
Tickets follow `rules/code.md`. Also strip: "Let me…", "Certainly", "Hope this
helps", "Happy to iterate", hedges ("it appears there may be"), recaps of the
diff, "Summary:" / "TL;DR", First/Second/Finally structure, the debugging
story.
- Bug: `<file>:<line>: <what's broken>. <one-line fix>.`
- Question: `why <X>? <Y> does it in one step.`
- Nit: `nit: <one word>.`
- Approve: `lgtm`. Block: `no: <one-sentence reason>.`

## Boundaries
Not for code, logs, or tool arguments; those want precision, not style. Use it
on your own drafts only, never as a detector to accuse others' writing.
