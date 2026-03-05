# Xiaoyuzhou -> Tingwu Pipeline

## What it does

`tingwu_pipeline.py` provides five commands:

1. Resolve input URL to metadata + audio URL
2. Download audio file
3. Submit Tingwu offline task and poll until completion
4. Query task status by TaskId
5. Wait an existing task to completion by TaskId

## Requirements

- Python 3.9+
- For Tingwu API call:
  - `pip install aliyun-python-sdk-core`
  - Alibaba Cloud credentials and Tingwu `AppKey`

## Credentials

Set these environment variables before running `tingwu` command:

```bash
export ALIBABA_CLOUD_ACCESS_KEY_ID="your_ak"
export ALIBABA_CLOUD_ACCESS_KEY_SECRET="your_sk"
export TINGWU_APP_KEY="your_tingwu_app_key"
```

## Usage

Run commands from repo root.

Resolve audio URL:

```bash
python3 pipeline/scripts/tingwu_pipeline.py resolve "https://www.xiaoyuzhoufm.com/episode/69a64629de29766da93331ec"
```

Direct audio URL also works:

```bash
python3 pipeline/scripts/tingwu_pipeline.py resolve "https://example.com/path/to/episode.mp3"
```

Download audio:

```bash
python3 pipeline/scripts/tingwu_pipeline.py download "https://www.xiaoyuzhoufm.com/episode/69a64629de29766da93331ec" --output ./runs/20260305-69a64629-e45/00-input/episode.m4a
```

Submit Tingwu task and wait for completion:

```bash
python3 pipeline/scripts/tingwu_pipeline.py tingwu "https://www.xiaoyuzhoufm.com/episode/69a64629de29766da93331ec" \
  --output-dir ./runs/20260305-69a64629-e45/02-asr \
  --poll-interval 180 \
  --download-results
```

If you only want to submit without polling:

```bash
python3 pipeline/scripts/tingwu_pipeline.py tingwu "https://www.xiaoyuzhoufm.com/episode/69a64629de29766da93331ec" --no-wait --output-dir ./runs/20260305-69a64629-e45/02-asr
```

Check existing task status:

```bash
python3 pipeline/scripts/tingwu_pipeline.py status 23eab1c182a04d269df2152a5b2fa414
```

Wait for an existing task every 3 minutes:

```bash
python3 pipeline/scripts/tingwu_pipeline.py wait 23eab1c182a04d269df2152a5b2fa414 \
  --output-dir ./runs/20260305-69a64629-e45/02-asr \
  --poll-interval 180 \
  --download-results
```
