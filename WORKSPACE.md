# Workspace Conventions

## Directory roles

- `skills/`: skill definitions and references for agent behavior.
- `pipeline/scripts/`: executable scripts for URL resolving, Tingwu submission, polling, and downloads.
- `runs/`: all per-episode working files and outputs.
- `archive/`: legacy structure kept for reference only.

## Run folder contract

Use one directory per episode:

`runs/<run_id>/`

Recommended `run_id` format:

`YYYYMMDD-<episode_id>-<short-slug>`

Inside each run:

- `00-input/`: source URL and optional downloaded audio.
- `01-metadata/`: episode metadata from page/RSS.
- `02-asr/`: Tingwu task creation/final responses and transcription JSON.
- `03-polish/_history/`: intermediate polishing versions.
- `99-final/transcript-final.md`: final single source of truth.

## Naming rules

- Keep one final file per run: `99-final/transcript-final.md`.
- Keep iterative drafts only in `03-polish/_history/`.
- Do not write run artifacts into `skills/` or `pipeline/`.
