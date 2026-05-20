# PLAN.md — hummcode living architecture document

## Current version: 0.1.0 (published to PyPI)

## What is complete
- [x] Core async agent loop (core.py → HummcodeAgent)
- [x] Model-agnostic LLM client via LiteLLM (llm.py)
- [x] Tree-based session memory with rewind (memory.py → SessionTree)
- [x] Sliding window + LLM summarisation compaction (memory.compact())
- [x] Tool primitives: read_file, list_files, edit_file, execute_bash
- [x] Oracle pattern for secondary model delegation (oracle.py)
- [x] Permission gates: y/n/all with TUI modal and CLI fallback
- [x] Tool registry and async dispatcher (registry.py)
- [x] Textual TUI — dual-pane (chat + tool log) with permission modal
- [x] Headless CLI mode (hummcode --cli)
- [x] Slash commands: /info /list /model /key /clear /rewind
- [x] Langfuse observability wired via LiteLLM callback
- [x] Published to PyPI: pip install hummcode

## Architecture decisions (do not re-litigate)
- Tree memory over flat list: dead branches excluded from context,
  rewind is a pointer move, compaction doesn't need list surgery.
- Surgical edit over full rewrite: tokens scale with change size,
  not file size. Uniqueness validation prevents wrong-occurrence edits.
- ToolRegistry dispatcher: core loop stays 3 lines regardless of how
  many tools exist. Tools are independently testable.
- LiteLLM over direct SDKs: model swap is a one-string change.
- async generator (yield) over print(): brain is display-agnostic.
- Permission callback injection: TUI modal and CLI prompt are
  interchangeable with zero changes to agent or registry.

## Known issues / rough edges
- PermissionManager CLI fallback still uses blocking input() — fine for
  --cli mode but should be made properly async eventually.
- hello.txt test artifact needs to be removed from repo root.
- No .env.example file committed yet.
- Context compaction not yet triggered in TUI (only wired to --cli mode).

## Next tasks (in priority order)
1. Add .env.example to repo and commit README.md
2. Wire compaction trigger consistently across both TUI and CLI modes
3. /save and /load commands — persist and restore SessionTree to JSON
4. Streaming LLM responses — token-by-token into chat pane
5. Live token + cost counter in TUI header
6. Settings modal — in-TUI model and key management
7. Autocomplete dropdown for slash commands (Slack-style popup)