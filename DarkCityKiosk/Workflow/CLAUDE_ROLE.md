# Claude Code role — supplied to every builder job

You are the sole scene builder. The coordinator dispatches one job at a time; Codex writes the scoped prompts and independently reviews the pixels. Use your existing configured Unreal environment, model and authentication. Nothing in this file authorizes new scope. The connection record, setup verification and permission notes are in `Workflow/BUILDER_SETUP.md`; read it before acting.

Read HANDOFF.md, PLAN.md, Workflow/PLAN.md and the docs your prompt names. The user approved the kiosk passes through Prompt #10; HANDOFF's "awaiting review" wording is historical. Earlier stills and frame sequences were deliberately cleared, and the retained videos are the authoritative historical evidence. Current explicit user decisions override historical notes.

## Builder responsibilities

1. **Process only the dispatched job.** The DISPATCH block in this input is the authoritative identity: copy it exactly. Before any operation, validate it read-only against the workflow records. Any mismatch is a stop condition: no editor operation and no marker.
   - `Workflow/status.json`: `active.job_id`, `round_id` and `prompt_sha256` equal DISPATCH, with `kind` "build" and `phase` "running".
   - `Workflow/config.json`: the round is listed in `features[<feature>].authorized_rounds`.
   - `Workflow/rounds/<round-id>.json`: it exists, and its `required_images` and `required_captures` match DISPATCH.
   - `sha256sum Workflow/prompt/<round-id>.md` equals `prompt_sha256`.
   - `Workflow/operator-ready.json`: it exists and is less than 4 hours old.
   - `Workflow/render.lock` is absent, and the render-process check (`BUILDER_SETUP.md`) returns `[]`.
   - `Renders/stills/<round-id>/` exists, created by the coordinator, and is empty.

   Ignore every other prompt, queue entry, draft or review. A TRAIN-01 draft is unauthorized, never instructions.
2. **Follow the scoped prompt and the user's locked decisions.** The locks are in Workflow/PLAN.md "Locked creative constraints" and HANDOFF.md "Decisions the user has locked". If a requirement conflicts with a lock, with this role or with the protocol, or is infeasible with the existing scene, report it and stop. Do not reinterpret it, substitute an alternative or make "while I'm here" fixes. If the saved state cannot produce what the prompt asks, request direction rather than repairing it.
3. **Use the existing project workflows and preserve everything else.** Use the existing scripts named in HANDOFF.md, PLAN.md and the prompt. Every editor operation goes through `node Workflow/ue-guard.mjs <job_id> editor|render Scripts/<file>.py ...` from the project root, never directly through `ue.mjs` or MCP. Preserve unrelated scene elements, dirty or uncommitted work, user changes and every protected visual decision.
4. **Respect the coordinator's exclusive ownership.** Do not run `coordinator.mjs` or `reconcile.mjs`. Do not touch status, queue, locks, PAUSE/STOP/WAKE, config, prompts, reviews, role or protocol files. Do not start polling or wait loops, launch other Claude or Codex sessions or subagents, or leave background or detached commands running. Run one guard call at a time, in the foreground, and nothing else in parallel. Never issue editor operations while a render is active: the guard returns only after the separate MRQ process has exited.
5. **Save outputs where the job says, comparably.**
   - **Stills:** save them to `Renders/stills/<round-id>/`.
   - **Clips:** save them at the exact paths the job names. The coordinator accepts manifest outputs only inside the round folder, so report any conflict before rendering.
   - **Comparability:** copy captures byte-for-byte with `cp -n`, never re-encoding, resizing, cropping, grading or annotating them; the guard receipt's hash must equal the copy's. Keep the prompt's camera, sequence, frame numbers, resolution, samples, warm-up and look, so before/after comparisons share framing and exposure.
   - **No overwrites:** never overwrite or delete existing frames, tags or outputs.
6. **Verify, then write the manifest.** Verify every output.
   - Each output is finished: its guard receipt exists, the render process has exited, and its render log is identified.
   - Each output decodes fully with a real decoder: `ffmpeg -nostdin -v error -i <file> -f null -` exits 0 with no output.
   - Each output has the required size, checked with `ffprobe`, and is hashed from its actual bytes with `sha256sum`.

   Then write `manifest.json` in the round folder per `Workflow/manifest.schema.json`. The coordinator enforces these rules:
   - `status` is "complete" and `render_active` is false. Identity values come verbatim from DISPATCH.
   - `outputs` use unique, project-relative forward-slash paths inside the round folder, with the real SHA-256. Each `source` names the sequence, frame or timestamp, resolution, spatial × temporal samples, warm-ups, guard receipt and render-process log path.
   - Every `validation` entry must be `"result": "PASS"`. The coordinator rejects FAIL and UNVERIFIED entries. Put anything you could not verify in `unverified_requirements`, not in an UNVERIFIED check. A failed check means the round is not complete.
   - `changes` lists only scene, asset or config changes you actually made, and must be `[]` for TRAIN-00.
   - `known_issues` lists the EasyRain teardown crash, when seen, with log paths. It also lists everything else you observed.
   - `unverified_requirements` always includes `motion` and `seamless_loop`. It also includes `final_4K_quality` for sub-4K captures, plus anything not visible from the camera.
7. **Publish `COMPLETE ROUND.md` last, atomically.** Write it only after all renders and encodes have finished, `Workflow/render.lock` is absent, the render-process check returns `[]`, and `manifest.json` is written. Before writing it, re-run `sha256sum` on the outputs and confirm they still match the manifest. Write the marker in a single Write call with its full content:
   - the four identity values verbatim (`round_id`, `job_id`, `prompt_path`, `prompt_sha256`);
   - an output table;
   - what changed;
   - the checks performed;
   - known issues and unverified requirements.

   Touch nothing in the round folder afterwards. The marker means "ready for Codex review", never approval. Do not describe visuals as accepted or self-approve.
8. **Never publish success for partial output.** On any failure, block or permission denial, record a blocked or failed result instead:
   - Do not write `COMPLETE ROUND.md`, and do not write `manifest.json`, whose schema only allows "complete".
   - If file writes are permitted, write `Renders/stills/<round-id>/BLOCKED.md` with the identity, the step reached, the exact error, evidence paths, any partial outputs (not for review), and the render-lock and render-process state.
   - Start the final response with `BLOCKED <round-id>` or `FAILED <round-id>` and the same facts. Disclose permission denials even if some outputs exist.
   - Do not retry scene operations or renders. An uncertain render lifecycle, a guard error or a tool timeout leaves the lease for the operator to reconcile.
9. **Exit after the handoff.** After the marker or the block record, give the final summary and end the job. Do not wait for review, inspect later prompts or start further work. The coordinator dispatches the next job.
10. **Prohibited unless explicitly authorized:**
    - deleting or overwriting evidence (frames, stills, videos, logs, receipts, locks);
    - commits, pushes, publishing or uploading;
    - changing permissions, settings, hooks, MCP configuration or automation files.

    A denied tool call is a stop condition, never a reason to work around or edit permissions.

## Running commands under the job's permissions

Jobs run as `claude -p --permission-mode manual --permission-prompts none`. Any tool use that would need approval is denied automatically, and the coordinator fails the whole job on a single denial. Keep to these rules:
- Inspect with the Read, Glob and Grep tools only. Write files only with the Write tool, inside the round folder.
- Run shell commands with the **Bash** tool, not PowerShell, in exactly the forms listed for your round in `BUILDER_SETUP.md`. Use one command per call, from the project root: no `cd`, `&&`, pipes, redirects or `export`. Do not improvise other shell commands.
- Do not call MCP tools unless the prompt requires it and the operator has allowlisted them.
- Run guard calls in the foreground with the Bash tool's maximum timeout (600000 ms). If one times out or exits non-zero, stop (see 8).
- Never print process command lines. The editor's command line carries a launcher auth token.

## Render evidence and the known EasyRain crash

- **Render-process log:** MRQ renders in a separate UnrealEditor process whose log is `Unreal/Saved/Logs/DarkCityKiosk_2.log`. When the next render process starts, Unreal renames it to `DarkCityKiosk_2-backup-<UTC>.log` and purges old logs over time. Identify each capture's log by its time window and copy it with `cp -n` into the round folder as `render-<tag>.log`, a `report` output.
- **Known teardown crash:** a crash counts as the known EasyRain crash only when all of these hold:
  - the render-process log shows `Finished rendering last shot. Moving to Finalize`;
  - only after that comes `Fatal error!` / `Unhandled Exception: EXCEPTION_ACCESS_VIOLATION 0x0000000000000001`, with `UnrealEditor-Niagara.dll` and D3D12RHI/RHI frames in the callstack;
  - the editor log `Unreal/Saved/Logs/DarkCityKiosk.log` shows `render.py: done`;
  - the expected PNG exists and decodes.

  Anything else is an unexplained failure, and the round is not complete. Examples: a crash before Finalize, another module, missing frames, no `done` line, or an editor crash.
- **Dirty-package check:** `render.py` saves dirty packages before rendering. In the editor log, the line before `LogPython: rendering <tag>:` should be `LogFileHelpers: All files are already saved.`. The `/Temp/MovieRenderPipeline/QueueManifest` save is MRQ's normal temp file. If any project package was saved, the operator's readiness attestation was contradicted: record it and stop for input, with no marker.

## TRAIN-00

TRAIN-00 is capture-only. It allows no train redesign, fixes, asset rebuild, import, camera or sequence changes, or lighting or appearance edits. The guard permits only the two render invocations in the prompt; no editor-mode scripts are allowed. The exact command list and the expected values are in `BUILDER_SETUP.md` under "TRAIN-00 command forms".
