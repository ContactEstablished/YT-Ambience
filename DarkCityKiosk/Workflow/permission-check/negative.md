PERMISSION PREFLIGHT, negative run. The user authorized this test. It is not a coordinator job: there is no dispatch, and no workflow, scene or Unreal work.

Make the 7 tool calls below, in order, one tool call per item, then stop. Several are EXPECTED to be denied by the permission settings. When one is denied, do not retry it, rephrase it or work around it: just go on to the next item. For items 1–6, use the **Bash** tool (never PowerShell), with the command copied character for character. Add no `cd`, prefixes or flag changes. Do not use any other tool: no Read, Glob or Grep, no MCP, no TodoWrite, no subagents, no memory writes.

1. node Workflow/permission-check/echo-args.mjs NEGATIVE render Scripts/render.py --tag TRAIN-00-other --frames 1-2 --temporal 4
2. ffprobe -v error -show_entries stream=width,height -of csv=p=0 _reference/PrimaryReference.png
3. sha256sum Workflow/status.json
4. cp -n Workflow/permission-check/echo-args.mjs Workflow/permission-check/copied.mjs
5. sha256sum Workflow/prompt/TRAIN-00.md && cp -n Workflow/permission-check/echo-args.mjs Workflow/permission-check/piggyback.mjs
6. ffmpeg -nostdin -v error -i _reference/PrimaryReference.png -f null -
7. Write tool: create the file at this exact absolute path:
   C:\Projects\ContactEstablished\YouTube\YT-Ambience\DarkCityKiosk\Workflow\permission-check\not-allowed.txt
   with the content: should be denied

Finally, reply with exactly 7 lines in the form `<n> | allowed or denied | <one-line outcome>`.
