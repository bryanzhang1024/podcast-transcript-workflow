#!/usr/bin/env python3
"""Podcast to Tingwu pipeline helper.

Features:
1) Resolve episode page URL (any platform with og:audio) to audio URL.
2) Accept direct audio URL as input.
3) Optionally download the audio file.
4) Submit the audio URL to Tingwu offline API and poll result.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse, urlunparse
from urllib.request import Request, urlopen


USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/123.0.0.0 Safari/537.36"
)
TINGWU_DOMAIN = "tingwu.cn-beijing.aliyuncs.com"
TINGWU_VERSION = "2023-09-30"
TINGWU_REGION = "cn-beijing"


class PipelineError(RuntimeError):
    """Domain-specific error."""


def http_get_text(url: str, timeout: int = 30) -> Tuple[str, Dict[str, str], int]:
    req = Request(url=url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,*/*"})
    try:
        with urlopen(req, timeout=timeout) as resp:
            data = resp.read()
            text = data.decode("utf-8", errors="replace")
            headers = {k: v for k, v in resp.headers.items()}
            return text, headers, getattr(resp, "status", 200)
    except URLError as exc:
        raise PipelineError(f"Failed to GET {url}: {exc}") from exc


def http_head(url: str, timeout: int = 30) -> Dict[str, str]:
    req = Request(url=url, headers={"User-Agent": USER_AGENT}, method="HEAD")
    try:
        with urlopen(req, timeout=timeout) as resp:
            return {k: v for k, v in resp.headers.items()}
    except HTTPError as exc:
        if exc.code not in (400, 403, 405, 501):
            raise PipelineError(f"HEAD {url} failed: {exc}") from exc
        # Fallback for servers that do not support HEAD.
        req = Request(
            url=url,
            headers={"User-Agent": USER_AGENT, "Range": "bytes=0-0"},
            method="GET",
        )
        with urlopen(req, timeout=timeout) as resp:
            return {k: v for k, v in resp.headers.items()}
    except URLError as exc:
        raise PipelineError(f"HEAD {url} failed: {exc}") from exc


def download_binary(url: str, output_path: Path, timeout: int = 60) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    req = Request(url=url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(req, timeout=timeout) as resp, output_path.open("wb") as f:
            while True:
                chunk = resp.read(1024 * 1024)
                if not chunk:
                    break
                f.write(chunk)
    except URLError as exc:
        raise PipelineError(f"Failed to download {url}: {exc}") from exc


def _extract_first(pattern: str, text: str) -> Optional[str]:
    m = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    return m.group(1).strip() if m else None


def _clean_url(url: str) -> str:
    parsed = urlparse(url)
    cleaned = urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", parsed.query, ""))
    return cleaned


def resolve_episode_page(input_url: str) -> Dict[str, Any]:
    html, _, _ = http_get_text(input_url)

    canonical = _extract_first(r'<link rel="canonical" href="([^"]+)"', html) or input_url
    title = _extract_first(r'<meta property="og:title" content="([^"]+)"', html)
    description = _extract_first(r'<meta name="description" property="og:description" content="([^"]*)"', html)
    audio_url = _extract_first(r'<meta property="og:audio" content="([^"]+)"', html)
    if not audio_url:
        audio_url = _extract_first(r'"associatedMedia":\{"@type":"MediaObject","contentUrl":"([^"]+)"', html)
    if not audio_url:
        raise PipelineError("Cannot find audio URL from episode page.")

    published_at = _extract_first(r'"datePublished":"([^"]+)"', html)
    podcast_name = _extract_first(r'"partOfSeries":\{"@type":"PodcastSeries","name":"([^"]+)"', html)

    episode_id_match = re.search(r"/episode/([0-9a-f]{24})", canonical, re.IGNORECASE)
    episode_id = episode_id_match.group(1) if episode_id_match else None

    return {
        "episode_url": _clean_url(canonical),
        "episode_id": episode_id,
        "title": title,
        "podcast_name": podcast_name,
        "published_at": published_at,
        "description": description,
        "audio_url": audio_url,
    }


def _is_audio_url(url: str) -> bool:
    parsed = urlparse(url)
    path = parsed.path.lower()
    return path.endswith((".mp3", ".m4a", ".aac", ".wav", ".flac", ".ogg", ".opus", ".mp4"))


def resolve_input(input_url: str) -> Dict[str, Any]:
    if _is_audio_url(input_url):
        filename = Path(urlparse(input_url).path).name
        return {
            "episode_url": None,
            "episode_id": None,
            "title": filename or "audio",
            "podcast_name": None,
            "published_at": None,
            "description": None,
            "audio_url": input_url,
            "source_type": "audio_url",
        }
    data = resolve_episode_page(input_url)
    data["source_type"] = "page_url"
    return data


def probe_audio(audio_url: str) -> Dict[str, Any]:
    headers = http_head(audio_url)
    content_length = headers.get("Content-Length") or headers.get("content-length")
    size_bytes = int(content_length) if content_length and content_length.isdigit() else None
    return {
        "content_type": headers.get("Content-Type") or headers.get("content-type"),
        "size_bytes": size_bytes,
        "accept_ranges": headers.get("Accept-Ranges") or headers.get("accept-ranges"),
        "last_modified": headers.get("Last-Modified") or headers.get("last-modified"),
    }


def _load_aliyun_sdk():
    try:
        from aliyunsdkcore.auth.credentials import AccessKeyCredential
        from aliyunsdkcore.client import AcsClient
        from aliyunsdkcore.request import CommonRequest
    except ImportError as exc:
        raise PipelineError(
            "Missing dependency `aliyun-python-sdk-core`. Install with: "
            "`pip install aliyun-python-sdk-core`"
        ) from exc
    return AccessKeyCredential, AcsClient, CommonRequest


def _build_tingwu_client(access_key_id: str, access_key_secret: str):
    AccessKeyCredential, AcsClient, _ = _load_aliyun_sdk()
    credentials = AccessKeyCredential(access_key_id, access_key_secret)
    return AcsClient(region_id=TINGWU_REGION, credential=credentials)


def _create_common_request(method: str, uri: str):
    _, _, CommonRequest = _load_aliyun_sdk()
    request = CommonRequest()
    request.set_accept_format("json")
    request.set_domain(TINGWU_DOMAIN)
    request.set_version(TINGWU_VERSION)
    request.set_protocol_type("https")
    request.set_method(method.upper())
    request.set_uri_pattern(uri)
    request.add_header("Content-Type", "application/json")
    return request


def _do_tingwu_request(
    client: Any,
    method: str,
    uri: str,
    query: Optional[Dict[str, str]] = None,
    body: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    request = _create_common_request(method, uri)
    for k, v in (query or {}).items():
        request.add_query_param(k, v)
    if body is not None:
        request.set_content(json.dumps(body, ensure_ascii=False).encode("utf-8"))
    raw = client.do_action_with_exception(request)
    if isinstance(raw, bytes):
        return json.loads(raw.decode("utf-8"))
    return json.loads(raw)


def create_tingwu_offline_task(
    *,
    file_url: str,
    app_key: str,
    source_language: str,
    access_key_id: str,
    access_key_secret: str,
    enable_text_polish: bool = False,
    enable_diarization: bool = True,
    speaker_count: int = 2,
) -> Dict[str, Any]:
    client = _build_tingwu_client(access_key_id, access_key_secret)
    task_key = "podcast_" + dt.datetime.now().strftime("%Y%m%d%H%M%S")

    body: Dict[str, Any] = {
        "AppKey": app_key,
        "Input": {
            "SourceLanguage": source_language,
            "TaskKey": task_key,
            "FileUrl": file_url,
        },
    }

    parameters: Dict[str, Any] = {}
    if enable_diarization:
        transcription: Dict[str, Any] = {"DiarizationEnabled": True}
        if speaker_count > 0:
            transcription["Diarization"] = {"SpeakerCount": speaker_count}
        parameters["Transcription"] = transcription

    if enable_text_polish:
        parameters["TextPolishEnabled"] = True

    if parameters:
        body["Parameters"] = parameters

    return _do_tingwu_request(
        client=client,
        method="PUT",
        uri="/openapi/tingwu/v2/tasks",
        query={"type": "offline"},
        body=body,
    )


def get_tingwu_task_info(task_id: str, access_key_id: str, access_key_secret: str) -> Dict[str, Any]:
    client = _build_tingwu_client(access_key_id, access_key_secret)
    return _do_tingwu_request(
        client=client,
        method="GET",
        uri=f"/openapi/tingwu/v2/tasks/{task_id}",
    )


def wait_for_task(
    task_id: str,
    *,
    access_key_id: str,
    access_key_secret: str,
    poll_interval_sec: int,
    timeout_sec: int,
) -> Dict[str, Any]:
    started = time.time()
    while True:
        info = get_tingwu_task_info(task_id, access_key_id, access_key_secret)
        status = ((info.get("Data") or {}).get("TaskStatus") or "").upper()
        if status in {"COMPLETED", "FAILED"}:
            return info
        if time.time() - started > timeout_sec:
            raise PipelineError(f"Polling timeout after {timeout_sec}s. Last status: {status or 'UNKNOWN'}")
        print(f"[poll] task={task_id} status={status or 'UNKNOWN'}", file=sys.stderr)
        time.sleep(poll_interval_sec)


def save_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def guess_filename_from_url(url: str, fallback: str) -> str:
    parsed = urlparse(url)
    name = Path(parsed.path).name
    return name or fallback


def download_tingwu_result_files(task_info: Dict[str, Any], output_dir: Path) -> Dict[str, str]:
    data = task_info.get("Data") or {}
    task_id = data.get("TaskId") or "task"
    result = data.get("Result") or {}
    downloaded: Dict[str, str] = {}
    for key, value in result.items():
        if not isinstance(value, str) or not value.startswith(("http://", "https://")):
            continue
        ext = Path(urlparse(value).path).suffix or ".json"
        filename = f"{task_id}_{key}{ext}"
        out = output_dir / filename
        download_binary(value, out)
        downloaded[key] = str(out)
    return downloaded


def cmd_resolve(args: argparse.Namespace) -> int:
    episode = resolve_input(args.input_url)
    episode["audio_probe"] = probe_audio(episode["audio_url"])
    if args.output_json:
        save_json(Path(args.output_json), episode)
    print(json.dumps(episode, ensure_ascii=False, indent=2))
    return 0


def cmd_download(args: argparse.Namespace) -> int:
    episode = resolve_input(args.input_url)
    audio_url = episode["audio_url"]
    filename = guess_filename_from_url(audio_url, f"{episode.get('episode_id') or 'episode'}.m4a")
    output_path = Path(args.output or filename).expanduser().resolve()
    print(f"[download] {audio_url} -> {output_path}", file=sys.stderr)
    download_binary(audio_url, output_path)
    print(json.dumps({"audio_url": audio_url, "output_file": str(output_path)}, ensure_ascii=False, indent=2))
    return 0


def cmd_tingwu(args: argparse.Namespace) -> int:
    access_key_id = args.access_key_id or os.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID")
    access_key_secret = args.access_key_secret or os.getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET")
    app_key = args.app_key or os.getenv("TINGWU_APP_KEY")

    if not access_key_id or not access_key_secret:
        raise PipelineError("Missing AccessKey env. Set ALIBABA_CLOUD_ACCESS_KEY_ID / ALIBABA_CLOUD_ACCESS_KEY_SECRET.")
    if not app_key:
        raise PipelineError("Missing TINGWU_APP_KEY (or pass --app-key).")

    episode = resolve_input(args.input_url)
    audio_url = args.file_url or episode["audio_url"]

    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    save_json(output_dir / "episode.json", episode)

    create_resp = create_tingwu_offline_task(
        file_url=audio_url,
        app_key=app_key,
        source_language=args.source_language,
        access_key_id=access_key_id,
        access_key_secret=access_key_secret,
        enable_text_polish=args.enable_text_polish,
        enable_diarization=not args.disable_diarization,
        speaker_count=args.speaker_count,
    )
    save_json(output_dir / "tingwu_create_task.json", create_resp)
    print(json.dumps({"create_task_response": create_resp}, ensure_ascii=False, indent=2))

    task_id = ((create_resp.get("Data") or {}).get("TaskId") or "").strip()
    if not task_id:
        raise PipelineError("CreateTask succeeded but no TaskId found in response.")

    if args.no_wait:
        print(json.dumps({"task_id": task_id, "status": "SUBMITTED"}, ensure_ascii=False, indent=2))
        return 0

    final_info = wait_for_task(
        task_id=task_id,
        access_key_id=access_key_id,
        access_key_secret=access_key_secret,
        poll_interval_sec=args.poll_interval,
        timeout_sec=args.timeout,
    )
    save_json(output_dir / "tingwu_task_final.json", final_info)
    print(json.dumps({"task_final": final_info}, ensure_ascii=False, indent=2))

    if args.download_results:
        downloaded = download_tingwu_result_files(final_info, output_dir)
        save_json(output_dir / "downloaded_result_files.json", downloaded)
        print(json.dumps({"downloaded_result_files": downloaded}, ensure_ascii=False, indent=2))

    return 0


def _load_credentials_from_args(args: argparse.Namespace) -> Tuple[str, str, str]:
    access_key_id = args.access_key_id or os.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID")
    access_key_secret = args.access_key_secret or os.getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET")
    app_key = args.app_key or os.getenv("TINGWU_APP_KEY")
    if not access_key_id or not access_key_secret:
        raise PipelineError("Missing AccessKey env. Set ALIBABA_CLOUD_ACCESS_KEY_ID / ALIBABA_CLOUD_ACCESS_KEY_SECRET.")
    return access_key_id, access_key_secret, app_key


def cmd_status(args: argparse.Namespace) -> int:
    access_key_id, access_key_secret, _ = _load_credentials_from_args(args)
    info = get_tingwu_task_info(args.task_id, access_key_id, access_key_secret)
    print(json.dumps(info, ensure_ascii=False, indent=2))
    return 0


def cmd_wait(args: argparse.Namespace) -> int:
    access_key_id, access_key_secret, _ = _load_credentials_from_args(args)
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    final_info = wait_for_task(
        task_id=args.task_id,
        access_key_id=access_key_id,
        access_key_secret=access_key_secret,
        poll_interval_sec=args.poll_interval,
        timeout_sec=args.timeout,
    )
    save_json(output_dir / "tingwu_task_final.json", final_info)
    print(json.dumps({"task_final": final_info}, ensure_ascii=False, indent=2))

    if args.download_results:
        downloaded = download_tingwu_result_files(final_info, output_dir)
        save_json(output_dir / "downloaded_result_files.json", downloaded)
        print(json.dumps({"downloaded_result_files": downloaded}, ensure_ascii=False, indent=2))

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Xiaoyuzhou -> Tingwu automation helper.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_resolve = subparsers.add_parser("resolve", help="Resolve page URL/audio URL to metadata and audio URL.")
    p_resolve.add_argument("input_url", help="Episode page URL or direct audio URL.")
    p_resolve.add_argument("--output-json", help="Optional JSON output path.")
    p_resolve.set_defaults(func=cmd_resolve)

    p_download = subparsers.add_parser("download", help="Download episode audio.")
    p_download.add_argument("input_url", help="Episode page URL or direct audio URL.")
    p_download.add_argument("--output", help="Output audio file path.")
    p_download.set_defaults(func=cmd_download)

    p_tingwu = subparsers.add_parser("tingwu", help="Submit offline Tingwu task and poll.")
    p_tingwu.add_argument("input_url", help="Episode page URL or direct audio URL.")
    p_tingwu.add_argument("--file-url", help="Override audio URL. If omitted, resolve from episode page.")
    p_tingwu.add_argument("--output-dir", default="./output", help="Directory to save artifacts.")
    p_tingwu.add_argument("--source-language", default="cn", help="Source language. Example: cn/en/fspk/ja/yue/ko.")
    p_tingwu.add_argument("--enable-text-polish", action="store_true", help="Enable Tingwu text polish.")
    p_tingwu.add_argument("--disable-diarization", action="store_true", help="Disable speaker diarization.")
    p_tingwu.add_argument("--speaker-count", type=int, default=2, help="Speaker count for diarization.")
    p_tingwu.add_argument("--poll-interval", type=int, default=180, help="Polling interval in seconds.")
    p_tingwu.add_argument("--timeout", type=int, default=4 * 60 * 60, help="Polling timeout in seconds.")
    p_tingwu.add_argument("--no-wait", action="store_true", help="Only create task, do not poll.")
    p_tingwu.add_argument("--download-results", action="store_true", help="Download result URLs after completion.")
    p_tingwu.add_argument("--app-key", help="TINGWU app key. Can also use env TINGWU_APP_KEY.")
    p_tingwu.add_argument("--access-key-id", help="Alibaba Cloud AccessKeyId (or env ALIBABA_CLOUD_ACCESS_KEY_ID).")
    p_tingwu.add_argument(
        "--access-key-secret",
        help="Alibaba Cloud AccessKeySecret (or env ALIBABA_CLOUD_ACCESS_KEY_SECRET).",
    )
    p_tingwu.set_defaults(func=cmd_tingwu)

    p_status = subparsers.add_parser("status", help="Get existing Tingwu task status by TaskId.")
    p_status.add_argument("task_id", help="Tingwu TaskId.")
    p_status.add_argument("--app-key", help="Unused in status query; kept for symmetric CLI.")
    p_status.add_argument("--access-key-id", help="Alibaba Cloud AccessKeyId (or env ALIBABA_CLOUD_ACCESS_KEY_ID).")
    p_status.add_argument(
        "--access-key-secret",
        help="Alibaba Cloud AccessKeySecret (or env ALIBABA_CLOUD_ACCESS_KEY_SECRET).",
    )
    p_status.set_defaults(func=cmd_status)

    p_wait = subparsers.add_parser("wait", help="Wait for existing Tingwu task to complete.")
    p_wait.add_argument("task_id", help="Tingwu TaskId.")
    p_wait.add_argument("--output-dir", default="./output", help="Directory to save artifacts.")
    p_wait.add_argument("--poll-interval", type=int, default=180, help="Polling interval in seconds.")
    p_wait.add_argument("--timeout", type=int, default=4 * 60 * 60, help="Polling timeout in seconds.")
    p_wait.add_argument("--download-results", action="store_true", help="Download result URLs after completion.")
    p_wait.add_argument("--app-key", help="Unused in wait query; kept for symmetric CLI.")
    p_wait.add_argument("--access-key-id", help="Alibaba Cloud AccessKeyId (or env ALIBABA_CLOUD_ACCESS_KEY_ID).")
    p_wait.add_argument(
        "--access-key-secret",
        help="Alibaba Cloud AccessKeySecret (or env ALIBABA_CLOUD_ACCESS_KEY_SECRET).",
    )
    p_wait.set_defaults(func=cmd_wait)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except PipelineError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
