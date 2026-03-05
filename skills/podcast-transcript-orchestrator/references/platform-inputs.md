# Platform Input Strategy

Use this file to classify user input and select extraction path.

## Supported Input Types

## 1) Direct audio URL (Best)

Examples:
- `https://.../episode.mp3`
- `https://.../audio.m4a`

Action:
1. Pass URL directly to `tingwu_pipeline.py resolve`.
2. Submit to Tingwu with `tingwu_pipeline.py tingwu`.

## 2) Episode page URL with public metadata

Examples:
- Xiaoyuzhou, many independent podcast hosts, show-note pages.

Action:
1. Run `tingwu_pipeline.py resolve <page_url>`.
2. If `audio_url` extracted, continue normally.

## 3) RSS feed route

Use when user gives podcast home/feed URL instead of episode URL.

Action:
1. Parse RSS.
2. Find target episode.
3. Use item `enclosure` URL as `audio_url`.
4. Continue via Tingwu script.

## 4) Blocked/closed platforms

Typical blockers:
- requires login session
- anti-bot restrictions
- DRM/protected media

Action:
1. Stop automatic extraction early.
2. Ask user for downloadable audio file or direct URL.
3. Resume workflow from direct audio URL path.

## Heuristics

- If URL path ends with known audio extension, treat as direct audio.
- If HTML has `og:audio`, use it.
- If neither works, try RSS path.
- If still unavailable, switch to manual fallback.
