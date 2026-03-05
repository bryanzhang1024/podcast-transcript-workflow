# Tingwu Error Handling

Use this file only when `TaskStatus=FAILED` or API response `Code != "0"`.

## Common Errors

## `PRE.AudioDurationQuotaLimit`

Meaning:
- Current Tingwu quota is insufficient for this audio duration.

Action:
1. Increase Tingwu quota/package in Alibaba Cloud console.
2. Submit a new task.

## `PRE.InvalidFileUrl` / inaccessible URL

Meaning:
- Tingwu cannot fetch the `FileUrl`.

Action:
1. Verify URL is publicly accessible without auth.
2. Confirm URL returns `200` and supports ranged download.
3. Re-resolve audio URL and resubmit.

## `PRE.AppKeyNotFound` or auth-related failures

Meaning:
- AppKey or AccessKey credentials are incorrect, missing, or not authorized.

Action:
1. Re-check:
   - `ALIBABA_CLOUD_ACCESS_KEY_ID`
   - `ALIBABA_CLOUD_ACCESS_KEY_SECRET`
   - `TINGWU_APP_KEY`
2. Confirm the project is created and API is enabled in the target account.

## `FAILED` without explicit detail

Action:
1. Query the task again after 60 seconds.
2. Keep raw response JSON in output folder for inspection.
3. Retry with a new `TaskKey` via new submission.
