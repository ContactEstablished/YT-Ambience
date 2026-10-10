# Local workflow commands

Setup is PAUSED, with an empty queue and zero real jobs. TRAIN-00 is prepared. TRAIN-01 is neither drafted nor authorized. No scene files were changed during setup. No task/service is installed and nothing starts on login.

Use PowerShell in the project directory:

```powershell
Set-Location 'C:\Projects\ContactEstablished\YouTube\YT-Ambience\DarkCityKiosk'
node Workflow/coordinator.mjs status
node --test Workflow/tests/coordinator.test.mjs
# Just the fixture handoff/assessment cycle, with no real models:
node --test --test-name-pattern='normal handoff' Workflow/tests/coordinator.test.mjs
```

Tests use isolated, retained fixture workspaces under Workflow/logs/tests. They never invoke Codex, Claude, Unreal, render scripts, authentication, or production scene edits. Fixture images are synthetic; their mock PASS verdicts say nothing about the scene. `cycle` is the single-job REAL execution command, not the fixture test command.

## First supervised baseline

1. Keep this project's Unreal Editor open with the intended saved map/sequence. Inspect and resolve unsaved changes yourself: existing render.py saves dirty packages. Reserve the project for this workflow; stop other scene-writing sessions and renders. Keep the existing Unreal Python remote execution / MCP infrastructure available. Do not change permission settings just to make automation succeed.
2. Ensure Codex and Claude are already authenticated normally. Their configured models, credentials and normal config discovery are retained. No real authentication or permission exercise was performed during setup. Claude's noninteractive manual permission mode denies operations that would need a new approval; resolve those deliberately in a supervised session if encountered, then reconcile the interrupted job. Do not blindly rerun the baseline or remove its folder.
   **Prerequisite:** the builder needs permission rules for its exact commands and writes. Without them, `manual` mode plus `--permission-prompts none` denies the first guard call, and the failed job consumes TRAIN-00's only round slot. See `Workflow/BUILDER_SETUP.md` ("Readiness gap") and verify with `/permissions` before step 3.
3. Record readiness and queue exactly once:

```powershell
node Workflow/coordinator.mjs ready 'Project reserved; no active render or other builder; unsaved editor changes inspected and resolved'
node Workflow/coordinator.mjs enqueue TRAIN-00
node Workflow/coordinator.mjs resume
node Workflow/coordinator.mjs cycle
node Workflow/coordinator.mjs status
```

That first cycle launches Claude only and waits for the two serial captures, historical frame extractions and completion package. Stay present. If it fails/pauses, inspect the named job logs and follow recovery; do not continue to the next command as though it passed.

After a successful capture, the queue should contain `kind: review`. Run the next cycle and inspect the independent review:

```powershell
node Workflow/coordinator.mjs cycle
Get-Content Workflow/reviews/TRAIN-00.md
node Workflow/coordinator.mjs status
```

If the review queued `kind: draft`, run one final supervised cycle:

```powershell
node Workflow/coordinator.mjs cycle
node Workflow/coordinator.mjs status
```

It saves Workflow/prompt/TRAIN-01.md as DRAFT / UNAUTHORIZED / UNQUEUED and pauses. NEEDS INPUT pauses without drafting. REVISE can produce a proposal but never triggers redesign. Missing evidence is not a pass; motion, seamless loop and final 4K quality remain unverified by this baseline.

## Scheduler and controls

```powershell
node Workflow/coordinator.mjs start
```

`start` runs in the foreground: keep that terminal and computer awake. It checks work immediately, every 600 seconds while idle, and immediately after each completed job. It starts no models while paused or with no queued work. Resume wakes an idle scheduler; lightweight control-file checks are local only.

Run controls from another terminal:

```powershell
node Workflow/coordinator.mjs pause
node Workflow/coordinator.mjs resume
node Workflow/coordinator.mjs stop
node Workflow/coordinator.mjs status
```

Pause blocks subsequent dispatches while the current job drains. Stop additionally exits the scheduler after active work drains; neither kills models or renders. Resume refuses an active/ambiguous job. To resume a normally paused running job, wait for it to drain first. Use stop for a clean scheduler exit; closing the terminal/interrupting it can require reconciliation. After stop exits, resume then start again.

Keep Unreal and the existing MCP/remote-execution services running during Claude jobs. Claude/Codex CLI child processes are launched per job and do not need separate permanent terminals. Do not simultaneously run an interactive builder on the same project. Chromium launches briefly for image validation. The scheduler alone stays running between jobs. `cycle` exits after one job and needs no permanent coordinator process.

The initial cumulative limit is three agent jobs. Failed/ambiguous launches consume their slot. To change it explicitly after stopping the scheduler:

```powershell
node Workflow/coordinator.mjs limit 3
```

Use the intended total, not "three additional jobs". Increasing this limit does not authorize additional features/rounds. Edit config.json/round descriptors only after a new user scope decision; record that decision in PLAN.md. At most two corrective rounds per feature are enforced even if a larger number is configured. The current feature permits zero corrections. Stop the scheduler before enqueue/limit/configuration changes; pause/resume/stop/status work while it runs.

## Recovery

A surviving coordinator lock, render lock, active state, failed exit, permission denial, malformed completion or timeout requires investigation. Inspect Workflow/status.json, events.jsonl, logs/<job-id>/{job.json,input.md,command.json,stdout.log,stderr.log,exit.json}, render guard logs/receipts, actual processes and children, scene state, outputs and marker. Do not infer that the scene is unchanged because a tool failed. No automatic retries or lock stealing occur.

After all related processes are verified idle, choose one explicit action, with factual notes:

```powershell
# Accept only an already successful exit and valid package; never rerun the builder.
node Workflow/reconcile.mjs accept --confirmed-idle 'Describe inspected processes, render state, exit receipt and verified outputs'
# Or permanently abandon the interrupted job/round, retaining all evidence.
node Workflow/reconcile.mjs abandon --confirmed-idle 'Describe scene/output inspection and why this job is abandoned'
# For a stale scheduler lock only, with no active job:
node Workflow/reconcile.mjs unlock --confirmed-idle 'Describe how scheduler and child-process termination were verified'
```

Recovery refuses live PIDs/render processes, archives removed lock records, and leaves the system paused. A new attempt needs a new immutable round ID and user-approved scope; even permission failures are not replayed automatically. Partial persistence during review/draft can make acceptance ambiguous: preserve files and request direction instead of editing state to force success. Do not use unlock while any active record exists.

## Installed dependencies and boundaries

- Node 22.14.0; existing project Playwright 1.62.1 and installed Chromium verified by real image-decoding tests. No new package installs. Python is not required.
- Codex 0.160.1 is invoked via the installed npm JS entry point and Node executable to avoid Windows `.cmd` shell quoting. Its command uses `exec --sandbox read-only --json --output-schema ... --output-last-message ... --image ... -`. It receives role/protocol/job text over stdin. No model/profile/auth overrides or approval-bypass flags.
- Claude Code 2.1.289 uses `-p --output-format json --permission-mode manual --permission-prompts none`, with role/protocol/job text over stdin. This tightens permissions rather than bypassing them; existing allow/deny rules still apply. It does not use --bare, --strict-mcp-config, --model, --settings, or an authentication override. A permission denial in the result pauses the workflow.
- FFmpeg is installed and needed for saved-video frame extraction. Unreal 5.8 and the project's existing ue.mjs bridge remain unchanged. The baseline guard permits only its two named render invocations and rejects pre-existing output tags.
- Required live setup checks remain: configured account access/model image support, CLI permission readiness, editor saved state, and a successful supervised render lifecycle. They were intentionally not tested with real model/render jobs.
- One-hour job/render timeout pauses with ownership retained; it does not kill descendants. Adjust job_timeout_seconds before a future authorized larger job. OS render detection is conservative across Unreal render processes; this prevents conflict with another project's render too.
- File contracts/locks coordinate cooperative clients; they cannot stop arbitrary direct MCP/manual editor actions. The operator's exclusive project reservation is required. The guard must observe the separate MRQ process; ambiguous or too-fast-to-observe lifecycles pause safely.
- All outputs/logs remain local and retained; automated deletion disabled. Renders/ remains git-ignored as before. Back up accepted images/videos separately if needed.

CLI options were checked against installed help and the [official Codex command reference](https://learn.chatgpt.com/docs/developer-commands?surface=cli) and [Claude CLI reference](https://code.claude.com/docs/en/cli-reference). Recheck installed help after upgrading either CLI; the coordinator does not update them.
