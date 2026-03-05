---
name: podcast-transcript-editor
description: Transcript polishing skill that converts rough ASR text into readable markdown while preserving complete meaning and details. Use when the user provides a raw transcript (json/txt/md) and asks for editing, punctuation fixes, speaker labeling, paragraph restructuring, or final publish-ready transcript output.
---

# Podcast Transcript Editor

## Overview

Polish raw transcript content into clear, structured markdown.  
Do not summarize or delete substantive information.

## Input Types

Accept:
- ASR JSON from Tingwu or other engines
- plain text transcript
- markdown transcript draft
- optional episode metadata (title/podcast/date/show notes/guest/host/timestamps)

If input is JSON, extract spoken text fields first, then edit.

## Workflow

1. Read the full source transcript.
2. Fix obvious ASR errors, typos, and broken phrases.
3. Improve punctuation and sentence boundaries.
4. Reconstruct paragraph breaks for readability.
5. Add speaker labels when inferable.
6. If metadata exists, prepend episode information and show notes summary.
7. Use host/guest names and show notes terms to correct obvious ASR entity errors.
8. Keep full information coverage.
9. Output final markdown.

## Non-Negotiable Constraints

- Preserve original meaning.
- Do not delete important content.
- Do not compress into summary.
- Maintain traceable structure for long episodes.

## Output Standard

Write output as readable markdown:
- metadata header (`节目名/播客名/发布时间/链接/嘉宾/主播`)
- render 发布时间 and 时长 in human-readable Chinese format without technical suffixes (for example: `2026年03月03日 20:00`, `3小时26分钟`)
- output `Show Notes` as complete-information version:
  - keep high-signal lines (episode summary, guests/hosts, timestamps, references, concept annotations, creator credits)
  - remove low-signal boilerplate tail (platform distribution list, generic legal disclaimers, repetitive copyright statements)
- avoid duplicate timestamp display:
  - if show notes already contain richer timestamps, do not render a second standalone timestamp section
  - render standalone timestamp section only when it adds net new information
- optional section headings for long transcripts
- in `Show Notes`, use mixed formatting by content type instead of forcing all lines into bullet points
- short paragraphs with breathing room
- bold speaker prefixes like `**主持人：**` where useful

## Information Completeness Principle

Interpret `完整信息` as preserving the full useful information needed for understanding, retrieval, and later correction.

Keep:
- all content that carries semantic signal, identity signal, or retrieval value
- all unique timestamps and topic anchors
- all named entities useful for transcript correction (people, books, papers, products, terms)

Remove:
- low-information template text that does not improve understanding
- duplicated blocks that repeat the same information with lower quality

Recommended output path:
- `runs/<run_id>/99-final/transcript-final.md`

## Resources (optional)

### references/
Read [references/style-guide.md](references/style-guide.md) before finalizing transcript style.
