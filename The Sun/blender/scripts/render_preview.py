"""Render a short preview from the loaded .blend; never saves scene changes.

Example: blender -b solar_observatory.blend -P scripts/render_preview.py
Output is 120 PNGs at 960x540, covering 8 seconds at 15 fps.
"""
import json
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parents[1]
out = ROOT/'renders'/'preview_frames'
out.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene
scene.render.resolution_percentage = 50
scene.render.image_settings.color_depth = '8'
scene.cycles.samples = 32
scene.cycles.use_denoising = True
for i, frame in enumerate(range(1, 241, 2)):
    scene.frame_set(frame)
    scene.render.filepath = str(out/f'{i:04d}.png')
    bpy.ops.render.render(write_still=True)
    print(f'SOLAR_PREVIEW {i+1}/120 (scene frame {frame})', flush=True)
(ROOT/'renders'/'preview_settings.json').write_text(json.dumps({
    'scene_frames': [1, 239], 'step': 2, 'video_fps': 15, 'duration_seconds': 8,
    'resolution': [960, 540], 'samples': 32,
    'controls': {key: bpy.data.objects['SUN CONTROLS'][key] for key in bpy.data.objects['SUN CONTROLS'].keys()}
}, indent=2), encoding='utf8')
