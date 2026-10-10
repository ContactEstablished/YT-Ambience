PERMISSION PREFLIGHT, settings-location probe. The user authorized this test. It is not a coordinator job: there is no dispatch, and no workflow, scene or Unreal work.

Make exactly one tool call: the Bash tool (not PowerShell) with this command, copied character for character:

node Workflow/permission-check/echo-args.mjs PROBE-LOCATION render Scripts/render.py --tag TRAIN-00-mid --frames 180-181 --temporal 4

If it is denied, do not retry it or try anything else. Do not use any other tool, read files, call MCP tools, write memory or start subagents. Then reply with one line: `allowed` or `denied`, plus the command output or the denial text.
