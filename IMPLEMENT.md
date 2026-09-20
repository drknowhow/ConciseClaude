# Implement ConciseClaude (instructions for Claude Code)

Install this reply system at **user scope** (`~/.claude/`, on Windows
`%USERPROFILE%\.claude\`) so it applies in every project. Read `README.md`,
`CHANGELOG.md`, and every file in this folder first. The version being installed
is in `VERSION`.

If `~/.claude/hooks/reply_shape.py` already exists, this is an upgrade: run
`<PYTHON> ~/.claude/hooks/reply_shape.py version`, read the CHANGELOG entries
between that version and `VERSION`, and tell the user what changes before
replacing anything. A major version bump means replies or diffs score
differently or the settings wiring changed; its CHANGELOG entry says which.
Redo step 6 only when the entry says the wiring changed.

Merge into the user's existing configuration. Never overwrite their
`settings.json`, `CLAUDE.md`, or a same-named file without showing the conflict
and asking.

## Steps

1. **Preflight**
   - Back up `~/.claude/settings.json` to `settings.json.bak-conciseclaude`.
   - Check for managed (enterprise) settings that set `disableAllHooks` or
     `allowManagedHooksOnly`. If hooks are not allowed, skip steps 5, 6, and 8,
     and tell the user the rules will apply but won't be measured.
   - If any of these already exist and differ from this package, show the diff
     and ask before replacing: `~/.claude/output-styles/concise.md`,
     `~/.claude/commands/v.md`, `~/.claude/commands/u.md`,
     `~/.claude/skills/human-prose/`.

2. **Rules.** Copy `output-styles/concise.md` → `~/.claude/output-styles/concise.md`.

3. **One-turn stages.** Copy `commands/v.md` and `commands/u.md` → `~/.claude/commands/`.

4. **Writing pass.** Copy `skills/human-prose/` → `~/.claude/skills/human-prose/`.

5. **Meter**
   - Copy `hooks/reply_shape.py` → `~/.claude/hooks/reply_shape.py`.
   - Resolve an **absolute** path to Python 3.8 or newer. On Windows, don't use
     a `python.exe` under `WindowsApps`: that's the Store stub, and a hook that
     calls it fails silently. `py -3 -c "import sys; print(sys.executable)"`
     gives a real path.
   - Run the tests with that interpreter from this folder:
     `<PYTHON> tests/test_reply_shape.py`, `<PYTHON> tests/test_diff_shape.py`,
     and `<PYTHON> tests/test_version_sync.py`. All must pass before continuing.

5b. **Diff meter**
   - Copy `hooks/diff_shape.py` → `~/.claude/hooks/diff_shape.py`.
   - It is a git hook, not a Claude Code hook, so it is installed per
     repository: in each repo the user names, run
     `<PYTHON> ~/.claude/hooks/diff_shape.py install --repo <REPO>`. It writes
     `.git/hooks/pre-commit` and `.git/hooks/commit-msg`, and refuses to
     overwrite a hook it did not write; if one exists, show the user the one
     line to add to it. Ask which repos before writing anything.
   - Default mode is `warn`: findings print, commits proceed. Leave it there
     for two weeks, then let the user decide on `block` from
     `diff_shape.py report`.

6. **Wire settings.** Merge `settings-hooks.json` into `~/.claude/settings.json`:
   - Set `"outputStyle": "Concise"`. If a different style is already set, ask
     first.
   - **Append** the `Stop` and `UserPromptSubmit` entries to any existing hook
     arrays. Don't replace or reorder the user's existing hooks.
   - Replace `<PYTHON>` and `<HOOKS_DIR>` with absolute paths, using forward
     slashes, and keep the quotes.
   - Parse the file as JSON afterward to confirm it is still valid.

7. **CLAUDE.md pointer.** Append `claude-md-snippet.md` to `~/.claude/CLAUDE.md`
   (create it if missing). If that file or the current project's CLAUDE.md
   already has reply-length or tone rules ("≤N lines", "be thorough", "explain
   your reasoning"), list them and ask which to remove. Two rule sets is the
   failure this system exists to fix.

8. **Arm feedback.** `<PYTHON> ~/.claude/hooks/reply_shape.py mode nudge`

9. **Verify**
   - Pipe a sample Stop payload into the hook the way Claude Code will:
     `{"session_id":"install-check","last_assistant_message":"ok"}` → stdin of
     `<PYTHON> ~/.claude/hooks/reply_shape.py stop`. Then
     `<PYTHON> ~/.claude/hooks/reply_shape.py report --days 1` must show `n` ≥ 1.
   - Tell the user to start a new session, confirm the output style shows as
     Concise in `/config`, and send two or three prompts. Then run `report
     --days 1` again. It **must** show a `last reply logged` time from that new
     session and more than one session. A hook that installs cleanly but never
     records real replies is the failure to rule out here: the rules would look
     active while the feedback loop is dead. If no rows appear, rerun with the
     environment variable `REPLY_SHAPE_DEBUG=1` set, and check the hook command
     path and interpreter.

10. **Report** in the new style: a result line, the installed version, the
    `settings.json` diff, and anything skipped and why.

## Uninstall
Remove the two hook entries and `outputStyle` from `settings.json`. Delete the
copied files, `~/.claude/reply_shape/`, and `~/.claude/diff_shape/`. In each
repo, delete the `.git/hooks/pre-commit` and `commit-msg` files that mention
`diff-shape`. Remove the snippet from `~/.claude/CLAUDE.md`.
