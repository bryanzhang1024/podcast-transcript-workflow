## Skills

### Available skills

- podcast-transcript-orchestrator: Workflow router for choosing split mode (ASR-only or polish-only) or full chained mode across multiple podcast platforms and fallback paths. Use when the request is about how to run the pipeline, selecting execution mode, or handling non-Xiaoyuzhou sources. (file: skills/podcast-transcript-orchestrator/SKILL.md)
- podcast-tingwu-e2e: End-to-end podcast workflow from episode URL/audio URL to Tingwu ASR result and final readable transcript markdown. Use when the request involves running the full pipeline, polling Tingwu tasks, downloading transcription files, or producing final transcript deliverables. (file: skills/podcast-tingwu-e2e/SKILL.md)
- podcast-transcript-editor: Professional transcript polishing workflow for converting rough ASR text to readable markdown while preserving full content. Use when the request focuses on editing, punctuation, speaker labeling, paragraph reconstruction, and style polishing. (file: skills/podcast-transcript-editor/SKILL.md)

### How to use skills

- Trigger rules: If a user names a skill (`$skill-name`) or the task clearly matches a listed description, load and follow that skill.
- Skill coordination: Prefer `podcast-transcript-orchestrator` first for mode selection; then invoke `podcast-tingwu-e2e` and/or `podcast-transcript-editor` based on chosen mode.
- Default intent routing:
  - If user says "把链接变成润色后的文字稿": choose full-chain mode (orchestrator -> tingwu-e2e -> transcript-editor).
  - If user says "先出 ASR/只转写": choose ASR-only mode (tingwu-e2e only).
  - If user gives transcript text/json and says "润色": choose polish-only mode (transcript-editor only).
- Progressive loading: Read only `SKILL.md` first, then load referenced files only when needed.
- Path resolution: Resolve relative paths from the skill directory first.

### Workspace layout

- `skills/`: skill definitions only (no run artifacts)
- `pipeline/scripts/`: executable workflow scripts (source of truth)
- `runs/<run_id>/`: per-episode working directory
- `runs/<run_id>/00-input`: raw inputs and source URL
- `runs/<run_id>/01-metadata`: extracted episode metadata
- `runs/<run_id>/02-asr`: Tingwu task artifacts and raw transcription
- `runs/<run_id>/03-polish/_history`: polishing drafts/history
- `runs/<run_id>/99-final/transcript-final.md`: single final deliverable
- `archive/`: legacy folders kept only for backward compatibility/reference
