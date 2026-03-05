# Podcast Transcript Workflow

这是一个“AI 代理可直接执行”的播客转文字稿项目。  
目标是让用户 `clone` 后，直接用自然语言给 AI 下指令，就能完成：

- 播客链接/音频链接 -> 通义听悟 ASR
- 自动轮询任务并下载结果
- 文字稿润色与排版（保留完整信息）

## 适用方式（推荐）

把本仓库交给你的 AI 编程代理（如 Codex / Claude Code / Cursor Agent），然后直接说：

- `把这个链接变成润色后的文字稿：<url>`
- `先只跑ASR，不润色：<url>`
- `这是原始文字稿，帮我润色成最终版：<file-path>`

仓库内的 `AGENTS.md` + `skills/` 已定义好路由与执行规则，AI 会自动选择流程。

## 第一步：开通通义听悟服务

1. 登录通义听悟控制台：  
   [https://nls-portal.console.aliyun.com/tingwu/overview?spm=a2c4g.11186623.0.0.2b5f2be1BsltKB](https://nls-portal.console.aliyun.com/tingwu/overview?spm=a2c4g.11186623.0.0.2b5f2be1BsltKB)
2. 在概览页点击“立即开通”。
3. 进入产品开通页并选择服务类型：  
   [https://common-buy.aliyun.com/?spm=a2c4g.11186623.0.0.2b5f2be1BsltKB&commodityCode=nls_tingwupaas_public_cn](https://common-buy.aliyun.com/?spm=a2c4g.11186623.0.0.2b5f2be1BsltKB&commodityCode=nls_tingwupaas_public_cn)
4. 选择开通模式：
   - 试用：新开通用户可免费试用 90 天。
   - 商用：按接口请求时长计费，费用从阿里云账户余额扣除。

## 第二步：配置阿里云与通义听悟（跨平台）

你需要 3 个凭证：

- `ALIBABA_CLOUD_ACCESS_KEY_ID`
- `ALIBABA_CLOUD_ACCESS_KEY_SECRET`
- `TINGWU_APP_KEY`（通义听悟项目 AppKey）

### macOS / Linux

```bash
mkdir -p "$HOME/.config/secrets"
cat > "$HOME/.config/secrets/tingwu.env" <<'EOF'
export ALIBABA_CLOUD_ACCESS_KEY_ID="your_ak"
export ALIBABA_CLOUD_ACCESS_KEY_SECRET="your_sk"
export TINGWU_APP_KEY="your_app_key"
EOF
chmod 600 "$HOME/.config/secrets/tingwu.env"
source "$HOME/.config/secrets/tingwu.env"

python3 -m pip install aliyun-python-sdk-core
python3 pipeline/scripts/tingwu_pipeline.py -h
```

### Windows (PowerShell)

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\\.config\\secrets" | Out-Null
@'
$env:ALIBABA_CLOUD_ACCESS_KEY_ID="your_ak"
$env:ALIBABA_CLOUD_ACCESS_KEY_SECRET="your_sk"
$env:TINGWU_APP_KEY="your_app_key"
'@ | Set-Content "$env:USERPROFILE\\.config\\secrets\\tingwu.env.ps1"

. "$env:USERPROFILE\\.config\\secrets\\tingwu.env.ps1"

py -3 -m pip install aliyun-python-sdk-core
py -3 pipeline/scripts/tingwu_pipeline.py -h
```

说明：
- macOS/Linux 推荐使用 `python3`
- Windows 推荐使用 `py -3`（避免多 Python 版本冲突）

## 对 AI 的自然语言指令模板

### 一条龙（ASR + 润色）

`把这个播客链接转成最终文字稿，按项目默认规范输出：<url>`

### 只做 ASR

`只做ASR并下载转写结果，不润色：<url>`

### 只做润色

`我给你一份原始转写稿，请直接润色输出最终稿：<path>`

## 目录说明

```text
.
├─ skills/                     # 技能定义（给 AI 读）
├─ pipeline/scripts/           # 可执行脚本（source of truth）
├─ runs/<run_id>/              # 单期工作目录
├─ AGENTS.md                   # 触发规则与路由
└─ WORKSPACE.md                # 目录规范
```

`runs/<run_id>/` 中最重要的文件：

- 最终稿：`runs/<run_id>/99-final/transcript-final.md`
- ASR 结果：`runs/<run_id>/02-asr/*Transcription*.json`

## 手动命令（可选，跨平台）

如果你想不用自然语言、直接手动跑。

### macOS / Linux

```bash
RUN_ID="20260305-69a64629-e45"

python3 pipeline/scripts/tingwu_pipeline.py tingwu "<input_url>" \
  --no-wait \
  --output-dir "./runs/$RUN_ID/02-asr"

python3 pipeline/scripts/tingwu_pipeline.py wait "<TaskId>" \
  --poll-interval 180 \
  --download-results \
  --output-dir "./runs/$RUN_ID/02-asr"
```

### Windows (PowerShell)

```powershell
$RUN_ID = "20260305-69a64629-e45"

py -3 pipeline/scripts/tingwu_pipeline.py tingwu "<input_url>" `
  --no-wait `
  --output-dir "./runs/$RUN_ID/02-asr"

py -3 pipeline/scripts/tingwu_pipeline.py wait "<TaskId>" `
  --poll-interval 180 `
  --download-results `
  --output-dir "./runs/$RUN_ID/02-asr"
```

## 安全说明

- `.gitignore` 默认忽略 `runs/`，避免把本地转写产物和潜在敏感内容提交到仓库。
- 不要把凭证文件提交到 git：
  - macOS/Linux: `$HOME/.config/secrets/tingwu.env`
  - Windows: `%USERPROFILE%\\.config\\secrets\\tingwu.env.ps1`
