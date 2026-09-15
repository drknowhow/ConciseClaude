---
name: human-prose
description: Use before shipping prose other people read — PR descriptions, review comments, docs, READMEs, tickets, emails, release notes. Revision pass that strips machine-writing tells (significance inflation, puffery, em-dash overuse, rule-of-three, formulaic conclusions) so the text reads like a person wrote it.
---

# Human prose: revision pass

Draft first without self-censoring, then run this pass. Trying to obey every
rule while drafting produces stilted text, which is its own tell.

**Above the checklist:** a smooth, impressive sentence is a warning sign, not a
quality signal. Ask what it actually asserts. The rougher sentence that says a
specific true thing usually wins.

## Cut-list (highest payoff first)
1. **Significance inflation. Delete, don't soften.** "serves as a testament
   to", "underscores", "plays a vital/pivotal/crucial role", "marks a turning
   point", and trailing clauses like "…, highlighting…", "…, ensuring…",
   "…, fostering…". State the fact and stop.
2. **Restore the copula.** "serves as / functions as / represents / acts as"
   → **is**. "boasts / features / offers" → **has**, or say what it does.
3. **Rule of three.** Don't default to three items. Use the real count.
4. **Negative parallelism.** "Not just X, but Y" / "It's not A, it's B": one
   per piece, max.
5. **Em-dashes.** At most one per paragraph. Two in a sentence means it should
   be two sentences.
6. **Formulaic conclusions.** Delete "In conclusion / Overall / In summary"
   and the closing restatement. End on the last real point or the next step.
7. **Puffery.** Ban unless quoting: boasts, vibrant, robust, seamless,
   groundbreaking, meticulous, delve, leverage (verb), landscape, navigate
   (metaphorical), unlock, elevate, foster, showcase, testament.
8. **Vague attribution.** "Experts say / studies show / it is widely
   regarded": name the source or cut the claim.
9. **Section-summary sentences.** The content carries itself.

## Formatting tells
- Bold on every key phrase. Bold only what truly needs emphasis.
- "**Label**: description" on every bullet. Vary the shape.
- Title Case Headings → sentence case unless house style differs.
- Emoji as bullets or section markers.
- Tool artifacts that must never ship: `oaicite`, `contentReference`,
  `turn0search`, `[cite:`, `utm_source=`, `【 】`.

## Voice
- **Agency:** say who did what. "It was determined" hides the actor.
- **Lead with the finding.** No "Here's what I found:".
- **Concrete over abstract:** "p95 latency went from 180 ms to 2.4 s" beats
  "a notable performance regression".
- **Repeat words** rather than cycling synonyms for the same thing.
- **Vary rhythm.** Short sentence after a long one. A fragment, sometimes.

## The pass
1. Read once; flag anything you wouldn't say to a smart colleague.
2. Cut every significance-inflation clause.
3. Sweep items 2–9, then the formatting tells.
4. Count em-dashes.
5. Re-read the first and last sentence; kill throat-clearing and wrap-ups.
6. Check that the smoothest sentence actually says something.

## PR and review comments
Write like a terse engineer. Also strip: "Let me…", "Certainly", "Hope this
helps", "Happy to iterate", hedges ("it appears there may be"), recaps of the
diff, "Summary:" / "TL;DR", First/Second/Finally structure.
- Bug: `<file>:<line>: <what's broken>. <one-line fix>.`
- Question: `why <X>? <Y> does it in one step.`
- Nit: `nit: <one word>.`
- Approve: `lgtm`. Block: `no: <one-sentence reason>.`

## Boundaries
Not for code, logs, or tool arguments; those want precision, not style. Use it
on your own drafts only, never as a detector to accuse others' writing.
