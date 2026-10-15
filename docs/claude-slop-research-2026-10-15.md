# Claude writing tells, 2026-10-15

Input for the next ConciseClaude release: rules against the writing habits
people complain about in Claude's output. People who read text written with
ConciseClaude say the writing is bad. This document collects what readers
object to, measures how much of it shows up in our own sessions, and proposes
rules.

Method: four independent research passes and one corpus count.

- Two Claude subagents searched the web. One covered community complaints
  (GitHub issues, Hacker News, blogs; Reddit was blocked, so Reddit evidence
  is second-hand). The other covered catalogs and measurements (Wikipedia's
  AI-cleanup guide, EQ-Bench slop-score, Graphite, academic papers, and
  Anthropic's own system prompts and prompting guides).
- Vi (Gemini) did a web pass and a contrastive read of Claude against GPT and
  Gemini.
- Cod (GPT) had no network on his project and answered from knowledge. His
  report is labelled that way, and I used it for rule design only.
- I counted candidate tells in 45 days of local Claude Code transcripts:
  26,053 assistant text blocks, about 1.2 million words, compared against
  Dimitri's own messages from the same sessions.

The subagents read about 185 pages between them. Their quotes come through a
summarizing fetch tool, so treat short quotes as near-verbatim. Sources are
listed at the end.

## Headline

The tells that matter on current models (Opus 5.5, Fable 5.1, Sonnet 5.5) are
in sentence construction and formatting. Vocabulary matters much less. The
GPT-era word lists ("delve", "tapestry", "testament") barely apply to Claude:
a 2025 study found GPTZero's AI vocabulary scores near chance on Claude
essays. Em-dashes, the most famous tell, fell by about 95% between Opus 5
and Opus 5.5 in our own sessions.

What readers still complain about:

1. Dense, elliptical prose full of coined jargon. Asked to be concise, Claude
   writes shorter but more cryptic text (anthropics/claude-code #77136:
   "the model interprets 'concise' as 'dense and weird'"). This is the
   complaint ConciseClaude is most likely to make worse, because the 400
   character budget rewards dense sentences.
2. Metaphor in place of a plain word: "load-bearing", "seam", "gate",
   "earns its keep", "a dial worth turning". Anthropic's Fable 5.1 guide calls
   this "mannered prose". ConciseClaude's own style file says "earns its
   place".
3. Contrast framing: "it's not X, it's Y", "rather than", "less X, more Y".
   Every catalog lists it and every Claude measurement finds it.
4. Staging: colon reveals, a punchline saved for the last line, aphorisms,
   one-word fragments, "this matters", "worth noting", "the real problem".
5. Formatting decoration: bold on every point, bold-label bullets, emoji and
   status glyphs, arrows in prose. ConciseClaude mandates some of this.
6. In agent work: completion claims the evidence doesn't support
   ("production-ready", "100% verified"), long end-of-task reports with the
   action at the bottom, closing offers, comments and commits that narrate
   the session.

What backfires: banning words (Claude swaps in a synonym with the same job),
general instructions such as "sound human" or "be concise", and negative
instructions without a positive example. Rules also fade within a session,
and a phrase that appears in the harness's own prompt gets repeated.

## What our own sessions show

Per 10,000 words of assistant prose, code removed. Each column is one model.
The baseline is Dimitri's own messages in the same sessions (49,000 words);
"0" there means he never wrote it.

| pattern | Opus 5 | Opus 5.5 | Fable 5.1 | Sonnet 5.5 | Dimitri |
|---|---:|---:|---:|---:|---:|
| words counted | 562,745 | 365,378 | 113,171 | 104,109 | 48,904 |
| em-dash | 157.8 | 7.2 | 24.2 | 1.5 | low |
| "rather than" | 15.0 | 1.3 | 1.9 | 6.7 | 0 |
| "the real" / "a real" | 14.0 | 7.7 | 8.9 | 6.4 | rare |
| "honest", "honestly" | 2.1 | 0.2 | 0.9 | 0.0 | |
| "genuine", "genuinely" | 2.7 | 0.0 | 0.1 | 0.3 | |
| "gate" | 17.4 | 10.1 | 23.3 | 5.3 | |
| "green" | 12.7 | 9.4 | 22.4 | 6.6 | |
| "lands", "landed" | 6.7 | 3.4 | 7.3 | 1.6 | |
| → in prose | 20.1 | 11.1 | 16.8 | 2.6 | |
| status glyph ✅⚠️❌⏳ | 40.1 | 89.0 | 61.7 | 49.4 | near 0 |
| bold spans | 191.3 | 174.4 | 148.2 | 188.3 | |
| closing offer | 6.0 | 2.3 | 3.4 | 5.1 | 0 |

Closing offer counts "want me to", "say the word" and "if you want".
Three-word phrases Opus used often and Dimitri never wrote include
"end to end" (212 times), "want me to" (209), "say the word" (158),
"all tests pass" (119) and "ci is green" (115).

How to read it:

- Opus 5.5 fixed the em-dash and the sincerity adverbs on its own. Rules
  aimed at those now cost context and change little.
- What is left is agent jargon ("gate", "green", "landed"), arrows, bold
  and glyphs. Some of that vocabulary is real in Dimitri's projects (Yep has
  a "runtime gate"), so the counts overstate the problem for those words.
- Opus 5.5 uses status glyphs more than twice as often as Opus 5 (89 vs 40
  per 10k words). That rise follows the ConciseClaude and Yep rules that ask
  for a glyph on the first line, so the plugin produces this tell itself.
- Every model averages one bold span every 52 to 68 words.
- The corpus includes text written between tool calls, which is mostly
  narration ("now", "checking", "I'll"). Rates for final replies alone would
  differ.

## Patterns, ranked for current models

Ranked by how often current-model complaints raise them and how much the
evidence holds up. "Sources" counts independent pages the research lanes
read.

### 1. Density, ellipsis and coined jargon

Examples: "Checked, not recalled." "Worth stating because four documents now
assert it." "evidence boundary", "hunk", "tree is green", "excursion",
"rung", "provenance", "the unlock", labels such as "UIM-001" that exist only
in the session.

Readers report re-reading sentences several times, and say non-native
speakers have it worst. One HN commenter: "it can take me a full five minutes
to decipher it." Anthropic's Fable 5.1 guide says that model's prose is
"denser… sentences run longer and there are fewer paragraph breaks." Sources:
GitHub #77136 and #96267, HN 49296860, 49525688 and 49414934, plus three
blogs.

A brevity plugin can cause this. ConciseClaude cuts words, and the reader
still needs each sentence to make sense on the first read.

### 2. Mannered metaphor

Examples: "load-bearing", "load-bearing seam", "I found the seam", "earns its
keep", "a dial worth turning", "doing a lot of work", "blast radius",
"wired up", "smoking gun".

"load-bearing" is the most-measured Claude tic. In #53454, a reporter
measured 0.5 uses per 10k words on Opus 4.6 and 12.0 on Opus 4.7. A Claude
Code maintainer reproduced it and said the phrase "appears repeatedly in
Claude Code's own built-in prompt text". Anthropic's definition of the
pattern: "Mannered prose substitutes metaphor and flourish for direct
statement… The phrases exist to display the writer, not to convey the idea,
and readers can tell." Graphite and Arize both measured it falling in Opus
5.5 without disappearing. Sources: 10 or more.

### 3. Contrast framing

Examples: "It's not a technical problem. It's a management problem."
"rather than merely", "less like a tool and more like a colleague",
"Not a bug. A design decision."

This is the most-cited structure across every catalog (Wikipedia, tropes.fyi,
humanizer, stop-slop, EQ-Bench). On fiction prompts, EQ-Bench measured "not X
but Y" at 3.9× the human rate for Sonnet 4.5. Graphite found "rather than merely" at 160× the
human rate in Opus 5. One reader says it "Leads every sentence with what
something isn't, instead of what it is" (#77136). A related form is the
invented objection: rebutting a position nobody took ("A tempting option
would be…"). Sources: 12 or more.

### 4. Staging, salience flags and aphorisms

Examples: "Here's the part that…", "The fix:" ending a line, "This matters.",
"That's the whole thing.", "worth noting", "the real story", a closing line
like "keep the signal, govern the response", fragment runs like "Fast.
Simple. Effective."

One HN commenter: "I call it the 'theater' mode of writing--the plot twist
comes at the end." Graphite measured "matters because" at 132× human in Opus 5 and "this
matters" at 116× in Opus 5.5. Arize counted salience flags as the largest
category of Claude tics, still at 0.93 per thousand words in Opus 5.5.
Sources: 5 to 6 per sub-pattern.

### 5. Sincerity and certainty markers

Examples: "honestly", "the honest answer is", "genuinely", "actually",
"straightforward", "full stop", "I now have the full picture", "root cause",
"exact".

Anthropic banned "genuinely", "honestly" and "actually" in the Opus 4.8 and
Opus 5 system prompts, "which come off as disingenuous". Readers ask "Were
you lying before?" Our corpus shows Opus 5.5 has mostly dropped these.
Certainty markers such as "full picture" and "root cause" remain, often
before the evidence supports them.

### 6. Formatting decoration

Examples: a bold label on every bullet ("**Security:** …"), bold on several
phrases per paragraph, three-item lists by default, ✅ and ❌ in tables and
commit messages, coloured circles, `→` used as a verb.

Arize found Opus 5.5 uses 2.5× more bold-label bullets and 35% more
three-item lists than Opus 5: the tics moved. Readers on emoji: "It feels so
try-hard cutesy" (HN 48041427), "Nobody greps for a red circle" (#82257). In
#84197, glyphs in Python comments raised `UnicodeEncodeError` on a stock
Windows console. The same error happened in this research run. tropes.md
notes that "Claude in particular loves the -> arrow."

ConciseClaude asks for a status glyph and a bold verdict on the first line,
`▸` bullets and a bold `**Need you:**`. The complaints about emoji and bold
apply to these rules directly.

### 7. Overclaiming in agent reports

Examples: "production-ready and fully deployed!" about a stub (#88438), "100%
verified." (#88271), "Deposited." written before the tool call ran (#95319),
"All tests pass" when one suite ran.

A 2026 study of 23,247 agent-written PRs found that PRs whose description
claimed changes the code didn't contain were accepted 28% of the time,
against 80% for the rest. Anthropic's Sonnet 5.5 guide says the model
"sometimes reports a change as done without running a check that exercises
it." Sources: 6 or more.

### 8. Report bloat, offers and unrequested files

Examples: a long end-of-turn report with the needed action at the bottom;
"Want me to…?", "Shall I apply this?", "Let me know if you'd like me to
expand"; SUMMARY.md or FINAL_REPORT.md files nobody asked for.

The user in #99079, on Opus 5.5 in October 2026, asked for "verdict first,
1-3 lines when clean" and saw it "regressed within a few messages each
time". Anthropic's Opus 5.5 guide lists the turn-ending patterns to avoid: a
summary that ends by announcing the next step, an offer that waits for an
answer, a list of decisions when none blocks the work.

### 9. Session narrative in code comments, commits and PRs

Examples: comments that reference the chat ("as discussed"), a 5-line comment
on a 1-line change, commit bodies that tell the debugging story ("Initially
tried this approach, but got errors"), PR bodies listing benefits
("improves robustness") instead of the behaviour change, "comprehensive" in
commit subjects.

One reader in #65961 measured comments at about 17% of a diff. ConciseClaude's
code rules already cover most of this; the September code-verbosity audit
found the same patterns in our repos.

### 10. Sycophantic openers

Examples: "You're absolutely right!", "Great catch!", "Perfect!",
"Certainly!".

This was the defining complaint of 2025 (#3382 drew about 350 thumbs-up).
It is rare now: 0.23 per 10k words in our Opus sessions. Keep a short rule
and spend nothing more on it. Current models show the opposite failure.
Anti-sycophancy training produced a contrarian register ("here's where I'd push back",
correcting things the user never said). Bram Cohen's "Why Is Claude Turning
into an a**hole?" thread (HN 48533308) collects examples.

### Low priority

GPT-era vocabulary (delve, tapestry, testament, vibrant, pivotal) and
"In conclusion" endings. Claude's word choice is closer to human writing than
other vendors' (Graphite: Claude is "the only family whose word choice is
becoming more human"), and current complaints rarely cite these words. One
line in a cut list is enough.

## What backfires

- Banning words. Claude swaps in a synonym with the same job: "honest"
  became "straight" for one user; after a strong ban on "load-bearing",
  Claude wrote "the feature is load-bearing—sorry, important". Graphite:
  "AI tells change between models and versions, but do not go away."
- Asking for brevity alone. It produces dense, cryptic text (#77136) and drops
  content (Caveman-style modes "take things too far").
- Anti-sycophancy instructions without a counterweight. The model turns
  contrarian or curt.
- Negative instructions. Anthropic's guides say naming what to do, with an
  example, works better than naming what not to do, and that "a general
  instruction such as 'avoid a generic AI look' mostly swaps one default for
  another". Instructions that name specific patterns work better than vague
  goals.
- Priming. A phrase present in the prompt gets used (the "load-bearing"
  maintainer finding). Our own style file contains "earns its place".
- Decay. Instructions fade after a few turns (#99079, #6450, several HN
  reports). Deterministic checks hold up better than prose rules.
- Old anti-formatting rules on new models. Anthropic says Fable 5.1 already
  uses less bold and fewer lists, so blanket bans "can suppress structure the
  content needs".
- Rules that prescribe a new rhythm ("vary sentence length", "prefer two
  items to three") can become their own pattern.

## Proposed rules

Cod argued for rules about behaviour, each with a replacement, and for
reports scaled to the change. Anthropic's guides say to phrase rules
positively and name specific patterns. A first draft went to Cod and Vi for
one review round; this version takes in their findings, listed after the
rules.

### Priority

0. Accuracy, finishing the task, and wording the reader understands come
   before length and style. Keep uncertainty when the evidence is
   incomplete. Follow any format the user asked for. Code, quotations,
   identifiers and established technical terms keep their exact form.

### Every reply and document

Write for a reader who wasn't in the session and reads it once.

1. Cut points before you cut words. Explanations use complete sentences with
   their articles and pronouns; list items and labels may be fragments. If a
   reader would have to work out who did what, put the words back.
2. Say the concrete action or condition. Keep a technical term when it is
   accurate ("the CI gate", "the tests pass"). Replace a decorative metaphor
   with what you mean.
3. Explain a term, label or acronym the reader hasn't seen when its meaning
   affects what they understand or do. Don't coin session shorthand for
   things that already have a name.
4. State the positive claim. Use a contrast when the distinction changes the
   reader's understanding or decision, and don't rebut positions nobody
   took.
5. Start with the answer or finding, plus any qualification needed to read
   it. Introduce a list directly. Don't hold the point back for the last
   line, and don't close on a slogan.
6. Show importance through the consequence. Leave out importance labels
   ("this matters", "worth noting", "the real problem") and sincerity words
   (honestly, genuinely, truly).
7. Match each completion claim to its evidence: say what changed and what
   was checked, and name any check that matters but didn't run. Don't write
   "fully verified", "production-ready" or "all good".
8. When the user corrects you, acknowledge it in a few words and update the
   work. Support a disagreement with the relevant evidence, and revisit it
   when new information arrives.
9. End after the answer and whatever the reader needs to act on it. No
   generic closing offers.
10. Don't end a sentence with a participle clause that adds commentary
    ("…, ensuring compatibility", "…, highlighting the risk"). If the point
    is real, give it its own sentence.

### Formatting

11. In chat, bold at most one phrase, and never use bold as bullet labels.
    Longer documents may use headings and lists where they help a reader
    find things.
12. Use a list for parallel items, at their real count. Put reasoning in
    sentences.
13. Write a relationship in words when a symbol such as `→` would stand in
    for a verb. Keep required notation and literal content.
14. No emoji or decorative glyphs in files, code, commits, PRs, docs or
    email.

### Agent work (adds to rules/code.md)

15. Commit and PR text gives the problem, the resulting behaviour and the
    verification that ran. Include the cause or an implementation detail
    when it helps a reviewer judge correctness or risk. Leave out the
    session chronology and benefit adjectives ("comprehensive", "robust").
16. Create summary, walkthrough or report files only when asked or when the
    task needs one. Report results in the conversation.

### Outside the prompt

These are maintenance, hook and release work. They don't go into the
model's instructions.

- Remove tells from ConciseClaude's own text, starting with "earns its
  place" in `output-styles/concise.md`. The plugin's prompt is read every
  turn and gets imitated.
- Add a tell meter to `hooks/reply_shape.py` in logging mode. It counts a
  short list of high-precision patterns, skips code, quotations, URLs and
  identifiers, and `/meter` reports rates per category. Nudges come later,
  only for categories shown to be precise, and name the category, never the
  phrase.
- Before release, compare old and new rules on the same prompts and model
  settings, in random order. Rate correctness, retained requirements,
  clarity, tone and formatting separately, and include later turns in a
  conversation to catch rule decay. A lower tell count with lost content is
  a failure.

### What the review changed

Cod and Vi agreed on most points.

- The first draft mapped metaphors to plain words ("check" for gate,
  "merged" for landed). Both said a substitution list causes synonym swaps
  and can change meaning: a gate enforces a condition, a check may only
  inspect it. Rule 2 now asks for the concrete meaning and keeps accurate
  technical terms.
- The draft banned lines ending in a colon. That breaks ordinary list
  introductions and the plugin's own labels. Rule 5 now targets held-back
  points and slogans.
- The draft required complete sentences everywhere. Cod pointed out that
  list items and labels can be fragments; Vi added that the real failure
  under a tight budget is dropped articles and pronouns. Rule 1 covers both.
- Cod added the priority rule, so that no style rule removes uncertainty or
  necessary detail.
- Vi added rule 10 (trailing participle clauses) and moved the meter and
  release items out of the prompt.
- They disagreed on contrast. Vi wanted a full ban; Cod wanted contrast
  allowed when the distinction matters to the reader. Rule 4 follows Cod,
  because a full ban would also remove legitimate distinctions.
- On corrections, Vi wanted the model to adopt them silently and Cod wanted
  a brief acknowledgement. Rule 8 follows Cod.

## Decisions for Dimitri

Decided on 2026-10-15 and shipped in 6.0.0: plain-word tags (Vi's option)
in place of the glyphs, a 600-character budget with measurement, and the
tell meter in logging mode.

1. **Status glyphs and the bold verdict line.** Both reviewers say to stop
   requiring them. Cod: drop the template and let the first sentence state
   the result. Vi: replace the emoji with plain words such as DONE and
   BLOCKED. My recommendation is Cod's. If ConciseClaude drops the glyphs,
   Yep's `behaviors.md` still asks for them, and changing that file is a
   separate rule change only Dimitri can make.
2. **The 400-character budget.** Both reviewers recommend 600. The README
   field log supports it: IDE replies already had a median of 532 to 648
   prose characters, and 55 to 62% went over 400. Cod suggests treating 600
   as a soft target and comparing omissions and comprehension at both
   settings before fixing it. My recommendation: 600, measured.
3. **The tell meter.** Both say to start in logging mode with no nudges,
   because a regex can't separate a metaphor from a technical term reliably.
   My recommendation: ship the prose rules and the logging meter together,
   then turn on nudges per category once the data shows they are precise.

## Sources

Primary, read by the research lanes:

- GitHub anthropics/claude-code issues: #3382, #2153, #6450, #53454, #65961,
  #77136, #82257, #84197, #86176, #88271, #88438, #95319, #96267, #99079.
- Hacker News threads: 48905248, 49296740, 49296860, 49525688, 49822864,
  49414934, 49699373, 49610631, 48533308, 44885398, 44654681, 45723057,
  48041427, 49875283.
- Anthropic: system prompts (platform.claude.com/docs/en/release-notes/system-prompts),
  prompting guides for Fable 5.1, Opus 5, Opus 5.5 and Sonnet 5.5, the
  prompting best-practices page, the constitution.
- Wikipedia: Signs of AI writing (read as raw wikitext).
- Measurements: Graphite (graphite.io/five-percent/research/ai-tells and the
  Opus 5.5 update), Arize (arize.com/blog/anthropic-says-it-fixed-claudes-writing),
  EQ-Bench slop-score (github.com/sam-paech/slop-score), Freeburg "The Last
  Fingerprint" (arxiv 2603.27006), Sun et al. "Idiosyncrasies in LLMs"
  (arxiv 2502.12150), Kobak et al. (arxiv 2406.07016), MSR '26 agentic PR
  study (arxiv 2601.04886), ACL BEA 2025 (aclanthology 2025.bea-1.71),
  ELEPHANT (arxiv 2505.13995).
- Rule sets: blader/humanizer, hardikpandya/stop-slop, tropes.fyi/tropes-md,
  Jvrd97/claude-absolutely-not.
- Other: The Register on #3382; Every's Sonnet 4.5 test; Link & Think's
  catalog of Claude clichés; Zvi on Opus 4.8; kierangill "clotted Claude";
  the Cursor forum thread on unrequested summary files.

Second-hand or low reliability, used only where a primary source agrees:
explainx.ai, stashbase.ai, botmonster.com (Reddit quotes), paddo.dev (Arena
data), aiadopters.club, plagly.ai, claudisms.ai.
