# Changelog

Versions follow semver. `VERSION` is canonical; `tests/test_version_sync.py`
fails if the hook, the output style marker, or this file disagree with it.

- **Major:** a rule or budget change that makes existing replies score
  differently, or a settings/hook wiring change that needs reinstalling.
- **Minor:** new rules, report columns, commands, or optional modules.
- **Patch:** fixes and wording that don't change what gets measured.

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
