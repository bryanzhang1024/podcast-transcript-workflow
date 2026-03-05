# Podcast Transcript Workflow

端到端播客转写与润色工作流，支持：

- 输入播客页面 URL 或音频直链
- 调用通义听悟离线 ASR
- 自动轮询任务状态并下载转写结果
- 基于技能规范输出可读性高、信息完整的文字稿

## Repository Layout

```text
.
├─ skills/                  # Skills only
├─ pipeline/scripts/        # Executable scripts (source of truth)
├─ runs/<run_id>/           # Per-episode working artifacts
├─ AGENTS.md                # Skill routing and workspace conventions
└─ WORKSPACE.md             # Run folder contract and naming rules
```

## Quick Start

### 1) Prepare credentials

```bash
mkdir -p "$HOME/.config/secrets"
cat > "$HOME/.config/secrets/tingwu.env" <<'EOF'
export ALIBABA_CLOUD_ACCESS_KEY_ID="your_ak"
export ALIBABA_CLOUD_ACCESS_KEY_SECRET="your_sk"
export TINGWU_APP_KEY="your_app_key"
EOF
chmod 600 "$HOME/.config/secrets/tingwu.env"
source "$HOME/.config/secrets/tingwu.env"
```

### 2) Install dependency

```bash
python3 -m pip install aliyun-python-sdk-core
```

### 3) Create a run id

建议格式：`YYYYMMDD-<episode_id>-<slug>`

示例：

```bash
RUN_ID="20260305-69a64629-e45"
mkdir -p "runs/$RUN_ID/02-asr"
```

### 4) Submit Tingwu ASR task

```bash
python3 pipeline/scripts/tingwu_pipeline.py tingwu "<input_url>" \
  --no-wait \
  --output-dir "./runs/$RUN_ID/02-asr"
```

### 5) Poll every 3 minutes and download results

```bash
python3 pipeline/scripts/tingwu_pipeline.py wait "<TaskId>" \
  --poll-interval 180 \
  --download-results \
  --output-dir "./runs/$RUN_ID/02-asr"
```

## Execution Modes

- Full chain: URL -> ASR -> polishing (`podcast-transcript-orchestrator`)
- ASR only: URL -> transcription artifacts (`podcast-tingwu-e2e`)
- Polish only: raw transcript -> final markdown (`podcast-transcript-editor`)

## Output Convention

- Final deliverable: `runs/<run_id>/99-final/transcript-final.md`
- Historical polishing drafts: `runs/<run_id>/03-polish/_history/`

## Security Notes

- `.gitignore` excludes `runs/` by default to avoid pushing large or sensitive local artifacts.
- Do not commit credential files under `$HOME/.config/secrets/`.
