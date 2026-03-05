---
name: podcast-tingwu-e2e
description: End-to-end podcast transcription workflow for podcast episode page URLs or direct audio URLs using Tingwu offline ASR plus local transcript polishing. Use when agent needs to convert an input URL into an editable, readable markdown transcript, including task submission, 3-minute polling, result download, and final text cleanup.
---

# Podcast Tingwu E2E

## Overview

Run podcast transcription from input link to final readable markdown.  
Use existing local scripts in this repo for deterministic execution, and keep all run artifacts in one output directory.

## Workflow Decision Tree

1. Receive an input URL (episode page or direct audio URL).
2. Resolve audio URL from the input.
3. Submit Tingwu offline task with `FileUrl`.
4. Poll task status every 180 seconds until completion.
5. Download Tingwu result files.
6. Polish transcript into readable markdown without deleting content.

If no public audio URL is available, manually download audio and upload through Tingwu web console as fallback, then continue polishing from exported text.

## Step 0: Prepare Environment

Run commands from repo root: `/Users/clover/Develop/播客转文字稿工作流`.

Load secrets:

```bash
source /Users/clover/.config/secrets/tingwu.env
```

Ensure dependency:

```bash
python3 -m pip install aliyun-python-sdk-core
```

Use this script for all API operations:
`pipeline/scripts/tingwu_pipeline.py`

## Step 1: Resolve Input to Audio URL

```bash
python3 pipeline/scripts/tingwu_pipeline.py resolve "<input_url>"
```

Capture these fields from output:
- `episode_id`
- `audio_url`
- `audio_probe.size_bytes`

## Step 2: Submit Tingwu Task

Use a dedicated output directory per run:

```bash
python3 pipeline/scripts/tingwu_pipeline.py tingwu "<input_url>" \
  --no-wait \
  --output-dir ./runs/<run_id>/02-asr \
  --source-language cn
```

Read `TaskId` from:
`./runs/<run_id>/02-asr/tingwu_create_task.json`

## Step 3: Poll Every 3 Minutes

Check once:

```bash
python3 pipeline/scripts/tingwu_pipeline.py status "<TaskId>"
```

Wait continuously at 180-second interval and auto-download results:

```bash
python3 pipeline/scripts/tingwu_pipeline.py wait "<TaskId>" \
  --output-dir ./runs/<run_id>/02-asr \
  --poll-interval 180 \
  --download-results
```

Treat `TaskStatus` as:
- `ONGOING`: continue polling.
- `COMPLETED`: proceed to polishing.
- `FAILED`: inspect `ErrorCode` and apply fallback from [references/tingwu-errors.md](references/tingwu-errors.md).

## Step 4: Prepare Raw Transcript Input

Open:
- `./runs/<run_id>/02-asr/downloaded_result_files.json`

Use the downloaded transcription JSON as the source transcript.  
If multiple files exist, prioritize the transcription/body text file over summaries.

## Step 5: Polish Transcript to Final Markdown

Load and follow:
- `skills/podcast-transcript-editor/SKILL.md`
- `skills/podcast-transcript-editor/references/style-guide.md`

Apply these non-negotiable constraints:
- Preserve all source information.
- Do not summarize away details.
- Improve punctuation, sentence breaks, speaker labels, and paragraph structure.

Write final output to:
- `./runs/<run_id>/99-final/transcript-final.md`

## Output Contract

Always produce these artifacts:
- `01-metadata/episode.json`
- `02-asr/tingwu_create_task.json`
- `02-asr/tingwu_task_final.json` (after completion)
- `02-asr/downloaded_result_files.json` (if `--download-results`)
- `99-final/transcript-final.md`

## Resources (optional)

### scripts/
Keep scripts in `pipeline/scripts/` as the source of truth.  
Add wrappers here only if cross-project reuse is required.

### references/
Read [references/tingwu-errors.md](references/tingwu-errors.md) when task creation or polling fails.
