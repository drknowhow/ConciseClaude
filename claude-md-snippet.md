## Replies
- Reply rules live in one file: `~/.claude/output-styles/concise.md` (budget, grammar, cut list, never-cut list). If the Concise output style isn't active in a session, read that file and follow it anyway. They cover text the user reads; subagent reports to a parent agent stay complete.
- Don't add reply-length or tone rules anywhere else (project CLAUDE.md files, prompts). Change that file instead; two rule sets drift apart and the looser one wins.
- Before shipping prose other people read (PR descriptions, docs, tickets, emails), run the `human-prose` skill.
