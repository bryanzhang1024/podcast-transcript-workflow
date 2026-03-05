---
name: podcast-transcript-orchestrator
description: Workflow router for podcast transcript production. Use when agent must decide between split execution (ASR first, polish later) or full chained execution (ASR plus polish), and when handling inputs from multiple podcast platforms with fallback source-resolution strategies.
---

# Podcast Transcript Orchestrator

## Overview

Choose execution mode and invoke the right skills in the right order.  
Use this skill as the default entrypoint for transcript jobs.

## Mode Selection

Choose one mode before running commands.

### Mode A: ASR Only (Split Step 1)

Use when user wants only raw transcript generation.

Run:
1. Invoke `$podcast-tingwu-e2e` through Step 4 only (stop before polishing).
2. Output ASR artifacts in `runs/<run_id>/02-asr/`.

### Mode B: Polish Only (Split Step 2)

Use when raw transcript already exists.

Run:
1. Load raw transcript JSON/TXT provided by user.
2. Invoke `$podcast-transcript-editor`.
3. Produce `runs/<run_id>/99-final/transcript-final.md`.

### Mode C: Full Chain (One Shot)

Use when user wants start-to-finish processing in one run.

Run:
1. Invoke `$podcast-tingwu-e2e` full workflow.
2. Immediately invoke `$podcast-transcript-editor` on downloaded transcription result.
3. Deliver `transcript-final.md` plus all intermediate artifacts.

## Input Strategy (Multi-Platform)

Use this source resolution priority from [references/platform-inputs.md](references/platform-inputs.md):

1. Direct audio URL (`.mp3` / `.m4a` / etc.).
2. Episode page URL with `og:audio` metadata.
3. RSS feed entry with `enclosure` audio URL.
4. Manual fallback: user downloads audio and provides file or URL.

If platform blocks direct extraction (authentication/DRM), stop automated extraction and request manual audio input.

## Execution Contract

Always state:
- selected mode (`ASR only` / `Polish only` / `Full chain`)
- input type (`audio_url` / `page_url` / `rss` / `manual`)
- current step and next step

Always save outputs under:
- `runs/<run_id>/`

## Resources (optional)

### references/
Read [references/platform-inputs.md](references/platform-inputs.md) for platform-specific extraction patterns and fallback rules.
