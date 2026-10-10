# Builder setup record (Claude Code)

Verified 2026-10-10 by read-only checks in a supervised setup session. No scene, editor, render, coordinator or permission changes were made, and no model or render job ran. This file records configuration, never credentials.

## Launch configuration the coordinator uses (unchanged)

- **Executable:** `config.json` → `claude.executable` = `C:/Users/matth/.local/bin/claude.exe`, Claude Code 2.1.289.
- **Command:** `-p --output-format json --permission-mode manual --permission-prompts none`. It receives the role, protocol, dispatch and prompt over stdin, with cwd = the `DarkCityKiosk` project root. Model and effort come from the user's normal settings and are not overridden. Authentication is the user's existing login and is not recorded here.
- **Flag semantics, from the installed `--help`:** `manual` is a valid mode. With `--permission-prompts none`, "anything that would prompt is denied automatically; the permission mode still decides everything else."
- **Settings in effect:** there are no `permissions.allow` rules at user, project or local scope, and no managed settings. No CLAUDE.md files are on the path. The repo's `~/.claude.json` project entry has `allowedTools: []`.
- **Output parsing:** the coordinator parses all of `stdout.log` as one JSON envelope. The MCP SDK sometimes prints `[mcp-sdk] SEP-2352 ...` warnings at startup. Which stream they use is unverified, because two later runs printed none. If a build job fails with a parse error, check `stdout.log` first.

## Unreal connections

- **Editor:** UnrealEditor.exe 5.8.3 with `Unreal/DarkCityKiosk.uproject`, map `/Game/DarkCity/Maps/L_DarkCity`. It was launched from the Epic launcher, so its process command line contains a launcher auth exchange code: never copy process command lines into logs or workflow files.
- **Editor bridge (the only path jobs use):**
  - `ue-guard.mjs` → `Unreal/Scripts/ue.mjs` → PythonScriptPlugin remote execution.
  - Remote execution is enabled with `bRemoteExecution=True` in `Unreal/Config/DefaultEngine.ini`.
  - Discovery uses UDP multicast 239.0.0.1:6766, bound to 127.0.0.1 with TTL 0. Commands go over a TCP channel on an ephemeral localhost port. The bridge picks the editor whose `project_name` is DarkCityKiosk.
  - `render.py` starts render processes with remote execution off, so they never answer the bridge.
- **MCP:** server `unreal-mcp`, HTTP `http://127.0.0.1:8000/mcp`. It is configured at local scope on the YT-Ambience repo entry in `~/.claude.json`, with no credentials. `claude mcp list` run from `DarkCityKiosk` shows it Connected, so the coordinator's cwd inherits it. The server is hosted by the editor and must be running after an editor restart. Jobs use it only for permitted discovery, never for editor commands. Under the job's permission mode an un-allowlisted MCP call is denied, which fails the job.
- **Render processes:** MRQ's `MoviePipelineNewProcessExecutor` launches a second `UnrealEditor.exe` whose command line contains `-game`/`MoviePipeline`. `lib.mjs` `renderProcesses()` detects it and prints only the PID and name. Its log is `Unreal/Saved/Logs/DarkCityKiosk_2.log`, rotated to `DarkCityKiosk_2-backup-<UTC>.log` when the next render process starts.
- **Tools:** Node 22.14.0; ffmpeg/ffprobe 8.1.1 (WinGet Gyan build, on PATH); Playwright Chromium (`lib.mjs` `decodeImages`). `python` is the Store stub, so no step uses it.

## Read-only verification results (2026-10-10)

| Check | Result |
|---|---|
| MCP `list_toolsets` / `SceneTools.get_current_level` | Connected; `/Game/DarkCity/Maps/L_DarkCity` |
| `ue.mjs` query-only evaluation | Engine 5.8.3-58210709; world L_DarkCity; MRQ `is_rendering` False; 0 dirty map packages; 0 dirty content packages; LS_Sweep playback 0–720 at 24 fps |
| Unreal processes | Editor PID 48120 only; command line readable (not elevated); `renderProcesses()` → `[]` |
| Workflow state | Paused; queue empty; `jobs_started` 0 of 3; no render.lock or coordinator.lock; `operator-ready.json` absent (the operator records it) |
| TRAIN-00 paths | `Renders/stills/TRAIN-00`, `Renders/frames/TRAIN-00-mid` and `-train` all absent |
| Saved loop `Renders/kiosk_polish_loop_30s.mp4` | h264 1920×1080, 24/1, 720 frames, start 0, 30.0 s: 7.5 s = frame 180, 18 s = frame 432 |
| `Workflow/prompt/TRAIN-00.md` SHA-256 | `fc743e3dab41e981993aa9240fd6ce4ab948abd2e672f2ea6ce3f3a96de5bb82` |
| Past render processes (2026-10-10 logs) | 1–7 min each; each ended in the known EasyRain teardown crash after "Finished rendering last shot", and render.py logged `done (ok)` |
| Command forms below | `sha256sum`, the `renderProcesses()` one-liner, the ffmpeg null decode and ffprobe size all ran successfully |

## Readiness gap: builder permissions (blocks TRAIN-00)

With no allow rules, `manual` mode plus `--permission-prompts none` auto-denies everything TRAIN-00 needs: the guard renders, ffmpeg, copies, hashing and the manifest and marker writes. The coordinator fails the job on the first denial. That job would consume TRAIN-00's only round slot (`max_rounds` 1, no retries, IDs never reused) and one of three run-limit slots. A retry would then need a new round ID and new user authorization.

**Do not enqueue TRAIN-00 until this is resolved.** Changing permissions is the user's decision, and this setup did not apply it. One narrow option, scoped to TRAIN-00, would go in `DarkCityKiosk/.claude/settings.local.json`:

```json
{
  "permissions": {
    "allow": [
      "Bash(sha256sum *)",
      "Bash(node Workflow/ue-guard.mjs *)",
      "Bash(node -e \"import('./Workflow/lib.mjs').then(m => console.log(JSON.stringify(m.renderProcesses())))\")",
      "Bash(cp -n Renders/frames/TRAIN-00-* Renders/stills/TRAIN-00/*)",
      "Bash(cp -n Unreal/Saved/Logs/DarkCityKiosk_2* Renders/stills/TRAIN-00/*)",
      "Bash(ffmpeg -nostdin -n -ss * -i Renders/kiosk_polish_loop_30s.mp4 -frames:v 1 Renders/stills/TRAIN-00/*)",
      "Bash(ffmpeg -nostdin -v error -i Renders/stills/TRAIN-00/* -f null -)",
      "Bash(ffprobe -v error *)",
      "Edit(Renders/stills/TRAIN-00/**)"
    ]
  }
}
```

After adding rules, verify them before enqueueing: start an interactive `claude` session in `DarkCityKiosk` and run `/permissions` to confirm each rule is listed and attributed to that file. Pattern parsing is the risk to check, especially the quoted `node -e` rule. Alternatives are the operator's choice; for example, `acceptEdits` for build jobs would replace the `Edit` rule but allow edits anywhere in the project. The `ue-guard.mjs` rule relies on the guard itself to restrict arguments. TRAIN-00 permits only its two renders, but later rounds allow editor-mode scripts, so revisit the allowlist with each newly authorized round.

## TRAIN-00 command forms (Bash tool, project root, one per call)

1. `sha256sum Workflow/prompt/TRAIN-00.md`
2. `node -e "import('./Workflow/lib.mjs').then(m => console.log(JSON.stringify(m.renderProcesses())))"` (expect `[]`)
3. `node Workflow/ue-guard.mjs <job_id> render Scripts/render.py --tag TRAIN-00-mid --frames 180-181 --temporal 4`
4. `node Workflow/ue-guard.mjs <job_id> render Scripts/render.py --tag TRAIN-00-train --frames 432-433 --temporal 4`
5. `cp -n Renders/frames/TRAIN-00-mid/LS_Sweep.00180.png Renders/stills/TRAIN-00/current-mid.png`
6. `cp -n Renders/frames/TRAIN-00-train/LS_Sweep.00432.png Renders/stills/TRAIN-00/current-train.png`
7. `ffmpeg -nostdin -n -ss 7.5 -i Renders/kiosk_polish_loop_30s.mp4 -frames:v 1 Renders/stills/TRAIN-00/accepted-mid.png`
8. `ffmpeg -nostdin -n -ss 18 -i Renders/kiosk_polish_loop_30s.mp4 -frames:v 1 Renders/stills/TRAIN-00/accepted-train.png`
9. `cp -n Unreal/Saved/Logs/<that capture's DarkCityKiosk_2 log> Renders/stills/TRAIN-00/render-TRAIN-00-mid.log` (and `-train`)
10. `ffmpeg -nostdin -v error -i Renders/stills/TRAIN-00/<name>.png -f null -` and `ffprobe -v error -show_entries stream=width,height -of csv=p=0 Renders/stills/TRAIN-00/<name>.png`, for each image
11. `sha256sum Renders/stills/TRAIN-00/<file>`, for each output, before the manifest and again before the marker

Then use the Write tool for `Renders/stills/TRAIN-00/manifest.json`, and `COMPLETE ROUND.md` last. Find the mid capture's render log before running step 4, because starting the next render process renames it. Run steps 3 and 4 in the foreground with a 600000 ms timeout.

**Expected values:**
- **Sequence:** LS_Sweep with CAM_Sweep, played at 24 fps over 0–720.
- **Frames:** MRQ's end frame is exclusive, so each capture writes one PNG: `LS_Sweep.00180.png` or `LS_Sweep.00432.png`.
- **Render settings:** 1920×1080, TSR, spatial 1 × temporal 4, 48 engine + 48 render warm-up frames, cinematic quality, and the cvars in `render.py`.
- **Timing:** the guard needs up to about 10 minutes per capture; past single renders took 1–7 minutes.
- **Train frame:** frame 432 is at 18 s, in the middle of the train's run. If the train is not clearly visible there, record that as a limitation.

## Limits for later rounds

- The Bash tool's per-call ceiling is 10 minutes, while the guard may wait up to `job_timeout_seconds` (3600 s). A full-loop render (~15 min at 1080p) cannot fit in one foreground call. Before authorizing such a round, decide how it should run, for example a raised `BASH_MAX_TIMEOUT_MS` or a different guard arrangement.
- Each new round needs its prompt's exact command forms and a matching allowlist before it is queued.
