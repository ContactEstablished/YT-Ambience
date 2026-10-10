# TRAIN-00 — existing-scene baseline capture and assessment

Approved scope: small baseline only. Kiosk visual passes through Prompt #10 are approved. Do not redesign or fix the train or any other part of the scene. Preserve all source/assets/configuration and saved videos. Earlier stills/frame sequences were deliberately removed.

Read the shared instructions, HANDOFF.md, PLAN.md, Workflow/PLAN.md, docs/KIOSK-SPEC.md final polish section and Unreal/Scripts/render.py before acting. Use the active dispatch job_id and prompt hash. Confirm the operator has reserved the project and resolved unsaved editor changes before invoking render.py (it saves dirty packages). If this precondition is uncertain, stop for input.

## Claude capture job

The coordinator creates `Renders/stills/TRAIN-00`. Render the existing LS_Sweep, existing map and unchanged look. From project root run these sequentially, substituting only JOB_ID:

```powershell
node Workflow/ue-guard.mjs JOB_ID render Scripts/render.py --tag TRAIN-00-mid --frames 180-181 --temporal 4
node Workflow/ue-guard.mjs JOB_ID render Scripts/render.py --tag TRAIN-00-train --frames 432-433 --temporal 4
```

Wait for each guard to finish before the next operation. No --fog-clear, setup scripts, make_sweep, make_review, SceneCapture2D, re-import, sequence edits or look changes. Existing render.py defaults to 1920x1080. Copy the one corresponding PNG from each tag's frame folder to `current-mid.png` and `current-train.png` inside this round's still folder. Do not overwrite pre-existing tag frames: if either tag folder already exists, stop for reconciliation before rendering.

Extract two frames from the saved approved loop, without touching the video:

```powershell
ffmpeg -nostdin -n -ss 7.5 -i Renders/kiosk_polish_loop_30s.mp4 -frames:v 1 Renders/stills/TRAIN-00/accepted-mid.png
ffmpeg -nostdin -n -ss 18 -i Renders/kiosk_polish_loop_30s.mp4 -frames:v 1 Renders/stills/TRAIN-00/accepted-train.png
```

Required review images: current-mid.png, current-train.png, accepted-mid.png, accepted-train.png. No full-loop render or new close-up camera. If a frame does not clearly show the train, record that limitation rather than changing framing or time. Report exact source frame/timestamp, sequence, resolution, sample count and render logs. Preserve all generated frames and logs.

Validate all four images open, correct source/identity and no render process remains. Manifest changes must be an empty array. Known EasyRain exit failures must be evidenced in logs and explicitly explained; other unexplained failures prevent completion. Write manifest.json, then COMPLETE ROUND.md last. Include unverified motion, seamless_loop, final_4K_quality and any train details not visible from the existing camera. A successful screenshot does not establish animation correctness.

## Codex assessment job

Inspect all four images and PrimaryReference.png. Compare current mid/train views against the corresponding accepted saved-video frames and the reference. Assess train visibility, silhouette, relation to viaduct/city/kiosk, apparent material/light issues, and preservation of approved kiosk appearance. Do not assume the reference specifies a detailed train design. Separate observations from proposals and compression/weather differences. Return PASS, REVISE or NEEDS INPUT; missing evidence never passes. Record requirements unverified by these stills.

After this assessment only, an optional separate Codex draft job may propose TRAIN-01. It remains unauthorized and unqueued for user review. No production redesign follows automatically.
