PERMISSION PREFLIGHT, positive run. The user authorized this test. It is not a coordinator job: there is no dispatch, and no workflow, scene or Unreal work.

Your only task is to make the 20 tool calls below, in order, one tool call per item, then stop. For items 1–18, use the **Bash** tool (never PowerShell), with the command copied character for character. Add no `cd`, prefixes, flags, quoting changes, `&&`, pipes or redirects. Many of these commands are EXPECTED to fail with "No such file or directory" or "cannot stat", because the TRAIN-00 folders deliberately do not exist yet. That is correct: do not retry, investigate, create folders or run anything else. Do not use any other tool: no Read, Glob or Grep, no MCP, no TodoWrite, no subagents, no memory writes.

1. sha256sum Workflow/prompt/TRAIN-00.md
2. node -e "import('./Workflow/lib.mjs').then(m => console.log(JSON.stringify(m.renderProcesses())))"
3. ffmpeg -nostdin -n -ss 7.5 -i Renders/kiosk_polish_loop_30s.mp4 -frames:v 1 Renders/stills/TRAIN-00/accepted-mid.png
4. ffmpeg -nostdin -n -ss 18 -i Renders/kiosk_polish_loop_30s.mp4 -frames:v 1 Renders/stills/TRAIN-00/accepted-train.png
5. cp -n Renders/frames/TRAIN-00-mid/LS_Sweep.00180.png Renders/stills/TRAIN-00/current-mid.png
6. cp -n Renders/frames/TRAIN-00-train/LS_Sweep.00432.png Renders/stills/TRAIN-00/current-train.png
7. cp -n Unreal/Saved/Logs/DarkCityKiosk_2.log Renders/stills/TRAIN-00/render-TRAIN-00-mid.log
8. cp -n Unreal/Saved/Logs/DarkCityKiosk_2.log Renders/stills/TRAIN-00/render-TRAIN-00-train.log
9. sha256sum Renders/stills/TRAIN-00/current-mid.png Renders/stills/TRAIN-00/current-train.png Renders/stills/TRAIN-00/accepted-mid.png Renders/stills/TRAIN-00/accepted-train.png Renders/stills/TRAIN-00/render-TRAIN-00-mid.log Renders/stills/TRAIN-00/render-TRAIN-00-train.log
10. ffmpeg -nostdin -v error -i Renders/stills/TRAIN-00/current-mid.png -f null -
11. ffmpeg -nostdin -v error -i Renders/stills/TRAIN-00/current-train.png -f null -
12. ffmpeg -nostdin -v error -i Renders/stills/TRAIN-00/accepted-mid.png -f null -
13. ffmpeg -nostdin -v error -i Renders/stills/TRAIN-00/accepted-train.png -f null -
14. ffprobe -v error -show_entries stream=width,height -of csv=p=0 Renders/stills/TRAIN-00/current-mid.png
15. ffprobe -v error -show_entries stream=width,height -of csv=p=0 Renders/stills/TRAIN-00/current-train.png
16. ffprobe -v error -show_entries stream=width,height -of csv=p=0 Renders/stills/TRAIN-00/accepted-mid.png
17. ffprobe -v error -show_entries stream=width,height -of csv=p=0 Renders/stills/TRAIN-00/accepted-train.png
18. node Workflow/permission-check/echo-args.mjs 11111111-2222-3333-4444-555555555555 render Scripts/render.py --tag TRAIN-00-mid --frames 180-181 --temporal 4
19. Write tool: create the file at this exact absolute path, with backslashes:
    C:\Projects\ContactEstablished\YouTube\YT-Ambience\DarkCityKiosk\Workflow\permission-check\write-test.json
    with the content: {"preflight": "positive", "purpose": "disposable Edit-rule test"}
20. Write tool: create the file at this exact absolute path, with forward slashes and a space in the file name:
    C:/Projects/ContactEstablished/YouTube/YT-Ambience/DarkCityKiosk/Workflow/permission-check/write test.md
    with the content: Disposable Edit-rule test (path with a space). Not a round marker.

Finally, reply with exactly 20 lines in the form `<n> | allowed or denied | <one-line outcome>`.
