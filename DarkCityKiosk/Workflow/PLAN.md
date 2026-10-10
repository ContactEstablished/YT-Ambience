# Approved workflow scope and durable progress

## Authority — 2026-10-10

Automation setup only. User approved visual passes through kiosk Prompt #10. Root HANDOFF.md's awaiting-review wording is historical. Preserve root instructions and all existing modifications. Earlier stills and frame sequences were deliberately cleared; saved videos remain. No cleanup is authorized.

Roles: Codex authors prompts and independently reviews pixels; Claude Code builds using its existing Unreal/MCP setup; local coordinator schedules and records state without creative decisions.

## Locked creative constraints

- Yellow kiosk remains the warm hero; macro geometry, proportions, construction, utilities, roof, weathering, signage, kitchen, exterior clusters, rain contact and Prompt #10 polish are approved.
- Preserve 20 mm camera, 10 cm floor height, distance scale 0.807, pitch 15.8 degrees and +/-45-degree ping-pong arc; UE 5.8/MRQ, scripted Blender 5.2 assets, 24 fps.
- Concrete with puddles and foreground kiosk reflection, not a flooded pool. Low ground fog, no global exposure/bloom/fog/rain-density changes.
- Viaduct at 14 m; train once per loop. Moving lights must not shine through the viaduct. No distracting front-right standing figure. Preserve pedestrian/access clearances and practical steam sources.
- Preserve MPC_WetFX loop timing and existing crossfade strategy. Still reviews do not verify motion or seamless looping.
- Do not import from old Night Kiosk; no scene changes, rebuilds, material tuning, extra workers, or train redesign in setup/baseline.

## Current authorization and budget

Feature `train-baseline`: TRAIN-00 only, max_rounds=1, max_corrective_rounds=0. Two one-frame 1080p MRQ captures, at frames 180 and 432, plus two corresponding historical frame extractions. No full loop render. Initial persistent run limit: 3 jobs (Claude capture, Codex review, optional Codex unqueued draft). Run limit is cumulative, including failed/ambiguous launches; resume never resets it.

TRAIN-01 is not authorized and cannot be queued. After a completed baseline review other than NEEDS INPUT, Codex may write a proposal only. Broader production/corrective work requires the user to approve its scope and budgets, then an operator to record that authority in config.json and a bounded round descriptor/prompt. Maximum two corrective rounds per feature, regardless of a larger run limit. This setup deliberately pauses on a revision request instead of inventing fixes.

## Evidence and decisions

- Reference: `_reference/PrimaryReference.png`.
- Historical accepted source: `Renders/kiosk_polish_loop_30s.mp4`; Prompt #10 motion/seam clips and seam-difference report remain available but are not automatically revalidated.
- Baseline compares current MRQ frames against saved-loop frames at 7.5 s and 18 s. Encoding/crossfade/rain differences must be distinguished from visual regressions. Frame 432 samples the train passage; visibility is an assessment, not a pretext to alter the scene.
- Required outputs and identities are in Workflow/rounds/TRAIN-00.json and prompt/TRAIN-00.md. Structured manifest and independent review schema are versioned locally.
- Logs and accepted evidence are retained. Automated deletion disabled. Existing Renders git-ignore remains unchanged.

## Progress

- Setup: instructions and relevant render/spec documentation inspected; existing scene work preserved. Node 22.14.0, Codex CLI 0.160.1 and Claude Code 2.1.289 installed. Existing Playwright Chromium decoder works. Python command is a Store stub; coordinator uses Node.
- TRAIN-00 prompt prepared, not initially queued. No real agent or Unreal jobs launched during setup. System starts paused. TRAIN-01 not drafted before baseline review.

Automated completion entries append below; narrative scope changes require user authority.

- 2026-10-10T15:23:36.610Z: Setup verification complete: 20/20 fixture tests passed, including handoff, missing/corrupt evidence, duplicates, pause, failure, explicit restart recovery, render exclusion and budgets. Report: Workflow/logs/setup-tests.tap. Saved approved loop metadata confirms 1920x1080 at 24 fps. Production state remains paused, empty queue, zero real jobs.

- 2026-10-10: Claude builder setup verified by read-only checks. The MCP server and the ue.mjs remote-execution bridge both respond. L_DarkCity is loaded, MRQ is idle with no render process, and no packages are dirty. The TRAIN-00 inputs are present and its output paths are free. CLAUDE_ROLE.md now carries the reconciled builder responsibilities; the connection and launch record is in Workflow/BUILDER_SETUP.md. BLOCKING: the build job's `--permission-mode manual --permission-prompts none` auto-denies TRAIN-00's commands and writes, because no allow rules exist. Do not enqueue TRAIN-00 until the user decides on builder permissions (BUILDER_SETUP.md has a narrow proposal, not applied). The workflow is still paused, with an empty queue and zero jobs.
