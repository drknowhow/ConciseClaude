## C3 (code intelligence)
When C3's `c3_*` MCP tools are available, use them for code work. Native tools stay the fallback when a c3 call fails or fits the task worse.
- **Find** with `c3_search`. **Map** a file or folder with `c3_read(file_path)`, then **read** only what you need with `c3_read(symbols=[...])`, instead of reading whole files.
- **Before editing** a symbol used in more than one place: `c3_impact(target=...)`.
- **Edit** with `c3_edit`, then **validate** with `c3_validate(file_path)`.
- **Tests, builds, git:** `c3_shell`. Pass terminal or log output over ~30 lines through `c3_filter` before quoting it.
- **Before `/clear`:** `c3_session(action='snapshot')`.
- `[c3-mask:...]` and `[c3-access:...]` responses are policy decisions. Report them; don't route around them through the shell.
