# Local Codex–Claude handoff protocol

The user approved the kiosk's visual passes through Prompt #10. Earlier stills and frame sequences were deliberately cleared; saved videos remain. This supersedes stale "awaiting review" wording in HANDOFF.md. Preserve all existing work. Initial authorization is TRAIN-00 baseline capture/assessment only; train redesign is NOT authorized.

## Ownership and authority

- Codex writes bounded implementation prompts and independently reviews actual pixels. Codex never edits the scene, runs Unreal/MCP scene operations, or accepts Claude's claims as visual proof.
- Claude Code is the sole scene builder during production rounds, using its existing local Unreal/MCP setup. No model, authentication, MCP configuration, or permission allowlist is replaced by this workflow.
- The coordinator only dispatches, journals, validates, and enforces limits. It does not decide aesthetics or invent implementation scope.
- The operator exclusively reserves this project while jobs run: no other Claude session, manual editor operation, render, or scene-writing tool may run concurrently. The OS render check and shared guard protect participating jobs, not arbitrary external clients. This is cooperative local automation, not a security sandbox for Unreal/MCP.
- Read HANDOFF.md, root PLAN.md, Workflow/PLAN.md and relevant docs before each job. Current explicit user decisions take precedence over historical notes. Do not commit, delete evidence, change global instructions, or expand scope.

## Immutable jobs and files

Rounds use TRAIN-00, TRAIN-01, TRAIN-01-R1, TRAIN-01-R2. Never reuse an ID for a retry, overwrite a dispatched prompt, or rewrite accepted evidence. Prompts live at Workflow/prompt/<round-id>.md; review images at Renders/stills/<round-id>/; reviews at Workflow/reviews/<round-id>.json and .md. Dispatched job UUID plus SHA-256 of prompt bytes distinguish jobs from filenames. The dispatch object supplies identity; copy it exactly.

The operator queues only a prompt whose round appears in Workflow/config.json's explicit authorization ledger, with its descriptor in Workflow/rounds. Registration consumes a feature round slot even if work fails. At most two corrective rounds per feature are possible; total rounds and a persistent job run limit can be lower. A failed job is never automatically retried. REVISE/NEEDS INPUT pause for direction (baseline REVISE may first produce an unqueued proposal). Adding authorization is a human action recording the user's decision, never something a model may perform.

## Render exclusion

All Claude editor operations go through `node Workflow/ue-guard.mjs <job-id> editor|render Scripts/<file>.py ...` from the project root. Keep the existing MCP setup for permitted non-mutating discovery, but do not send editor commands directly through MCP or ue.mjs while participating in this workflow. Never issue editor operations during an active render.

The guard reserves Workflow/render.lock, invokes the existing bridge, observes the separate Unreal render process, and waits for its exit. A bridge return is NOT completion. A missing/ambiguous process lifecycle leaves the lock in place and requires operator reconciliation. A render process exit is also NOT evidence success: verify every output, logs and image readability. The known EasyRain teardown crash must be documented; do not silently treat other failures as that known issue. Do not kill active jobs to recover a lock.

For TRAIN-00 only the two exact capture commands in its prompt are allowed by the guard. No rebuild, setup, import, camera creation, look adjustment, fog override, sequence rebuild, or train edits. render.py saves dirty packages: the operator must first inspect/resolve unsaved editor changes, so unrelated dirty work is not inadvertently saved by the baseline.

## Completion package

Write `manifest.json` following Workflow/manifest.schema.json inside the round folder. It includes schema_version, round_id, job_id (Claude dispatch UUID), prompt_path, prompt_sha256, status, render_active, outputs (project-relative paths, kind, SHA-256, description and provenance), changes, validation results, known_issues and unverified_requirements. Every required output must finish first. Include render parameters, source video timestamps, and render log paths in source/details. Validate images with a real decoder, not just filename/size checks.

Write `COMPLETE ROUND.md` LAST, after all renders/encodes and validation have finished and all render processes are gone. Include all four identity values verbatim, an output table, what changed, checks performed, known issues and unverified requirements. If incomplete, do not write this marker; explain the block in the job response/log. A marker alone is never enough. Extra/duplicate markers outside the dispatched folder are ignored; a pre-existing dispatched folder is quarantined for reconciliation, never adopted as a new build.

The coordinator verifies identity, current prompt hash, output hashes, exact required images, path confinement and full browser pixel decoding before review. It records the validated package and passes current images, reference and previous accepted images to Codex. Evidence is checked again after review.

## Independent review and progression

Codex must inspect image pixels; compare the current frames with _reference/PrimaryReference.png and the prior accepted evidence supplied to the job. TRAIN-00 uses documented frame extractions from the saved Prompt #10 loop because historical stills are unavailable. Describe concrete observations, differences, and limits. Return PASS, REVISE, or NEEDS INPUT with the exact identity and evidence hashes. Missing/illegible evidence is never PASS. Review assertions are auditable in per-job logs; the coordinator can enforce file presence and declared inspection, not prove the model's visual judgment.

Stills cannot establish movement, timing, light animation or seamless looping. This setup's review contract explicitly keeps motion and seamless_loop unverified. PASS means the bounded still assessment passes, not final production approval. A future motion feature requires a separately authorized temporal-evidence contract and review implementation; do not simply change those booleans.

After baseline assessment, Codex may draft TRAIN-01. The coordinator saves it with an unauthorized/unqueued header and pauses. It must not create a TRAIN-01 descriptor, authorize it, queue it, or execute redesign. If baseline needs user input, pause immediately without drafting. Corrective rounds require a bounded Codex prompt and explicit existing authorization; R3 is forbidden. Exhausted limits and unresolved failures pause.

## Scheduling, pause and recovery

`start` checks immediately and then every 600 seconds when idle. Completion triggers an immediate scheduling check. Idle/paused checks are filesystem/process bookkeeping only: zero model calls. `cycle` runs at most one job. `pause` prevents subsequent dispatches; an already dispatched job drains. `stop` also exits the scheduler after active work drains. Neither kills agent/render processes. A timeout pauses and leaves process ownership unresolved.

Journal active intent before spawn, retain stdout/stderr, input, command, exit receipt, package hashes and reviews under Workflow/logs. A surviving active record or lock after restart blocks work. Inspect actual processes, children, render state, logs, files and scene state BEFORE `reconcile.mjs`. Never infer idle solely from a missing PID. Explicit reconciliation requires an operator note and an idle attestation; it never repeats edits. Accept only a successful recorded exit with valid outputs, or abandon permanently and seek direction for a new ID. PID reuse is treated conservatively as live. No automatic lock stealing, job retries, cleanup or deletion.

Accepted evidence and logs are retained indefinitely. Renders/ is already git-ignored; arrange an external backup if needed. No automated deletion is provided.
