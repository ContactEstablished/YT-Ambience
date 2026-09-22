"""Run after opening solar_observatory.blend in a background Blender process.

Checks evaluated native drivers and independent controls. Does not save changes.
"""
import json
import math
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parents[1]
scene = bpy.context.scene
control = bpy.data.objects['SUN CONTROLS']
original = {key: control[key] for key in control.keys()}
checks = []

def check(condition, description):
    if not condition:
        raise AssertionError(description)
    checks.append(description)

def update(frame=180, **values):
    for key, value in values.items():
        control[key] = value
    control.update_tag()
    scene.frame_set(frame)
    bpy.context.view_layer.update()

def mat(prefix):
    return next(m for m in bpy.data.materials if m.name.startswith(prefix))

def phases():
    return tuple(n.inputs['W'].default_value for n in mat('Photosphere').node_tree.nodes
                 if n.bl_idname == 'ShaderNodeTexNoise')

loops = [o for o in scene.objects if o.name.startswith('Magnetic loop ')]
plumes = [o for o in scene.objects if o.name.startswith('Plasma plume ')]
events = [o for o in scene.objects if o.name.startswith('Eruption ')]
stars = next(o for o in scene.objects if o.name.startswith('Stars '))
root = bpy.data.objects['Solar rotation']

check(not bpy.app.autoexec_fail, 'Saved scene opens without blocked driver execution')
update(surface_flow=0.)
p0 = phases()
ages0 = tuple(e['age'] for e in events)
update(240)
check(phases() == p0, 'Surface flow 0 freezes all photosphere noise phases')
check(tuple(e['age'] for e in events) != ages0, 'Flares continue while surface flow is 0')
update(surface_flow=1.)
p1 = phases()
update(flare_activity=3.)
check(phases() == p1, 'Flare activity does not retime photosphere noise')
check(sum(not o.hide_render for o in loops) == 72, 'Maximum activity enables 72 magnetic loops')
update(flare_activity=0.)
check(all(o.hide_render and o.hide_viewport for o in loops + plumes), 'Activity 0 disables every loop and plume')
update(240)
check(phases() != p1, 'Photosphere evolves while flares are disabled')
update(flare_activity=1., sunspots=0.)
check(mat('Photosphere').node_tree.nodes['Sunspot amount'].outputs[0].default_value == 0., 'Sunspots 0 removes the magnetic dark mask')
check(any(not o.hide_render for o in loops), 'Sunspots 0 retains magnetic loops')
update(flare_intensity=0.)
check(all(o.hide_render for o in loops + plumes), 'Flare intensity 0 hides all flare geometry')
update(corona_glow=0., stars=False, rotation_speed=0., sun_size=1.2)
check(mat('Corona').node_tree.nodes['Independent corona breath'].outputs[0].default_value == 0., 'Corona glow 0 removes volume emission')
check(stars.hide_render and stars.hide_viewport, 'Stars toggle hides the star field')
check(all(abs(v - 1.2) < 1e-5 for v in root.scale), 'Sun size updates the entire solar rig')
r0 = tuple(root.rotation_euler)
update(360)
check(tuple(root.rotation_euler) == r0, 'Rotation 0 holds the rig orientation')

update(**{k: v for k, v in original.items() if k != 'seed'})
driver_count = 0
for frame in (1, 180, 500, 1200, 1800):
    update(frame)
    blocks = list(bpy.data.objects) + [m.node_tree for m in bpy.data.materials if m.node_tree]
    for block in blocks:
        if not block.animation_data:
            continue
        for fc in block.animation_data.drivers:
            driver_count += 1
            check(fc.driver.is_valid, f'Valid driver: frame {frame}, {block.name}, {fc.data_path}')
    for event in events:
        check(all(math.isfinite(event[key]) for key in ('age', 'envelope', 'population')), f'Finite event state: {frame}, {event.name}')
check(not any(i.source == 'FILE' and not i.packed_file for i in bpy.data.images), 'No unpacked external image dependencies')
# Register the optional UI twice: catches API errors and duplicate registration.
namespace = {'__name__': '__main__'}
exec(compile((ROOT/'scripts'/'sun_controls.py').read_text(), 'sun_controls.py', 'exec'), namespace)
namespace['register']()
check(hasattr(bpy.types, 'SOLAR_PT_observatory'), 'Optional sidebar registers and re-registers')
report = {'blender': bpy.app.version_string, 'checks_passed': len(checks),
          'driver_evaluations_checked': driver_count, 'frames_checked': [1, 180, 500, 1200, 1800],
          'functional_checks': checks[:14], 'external_assets_required': False,
          'note': 'Checks evaluate scene data and drivers; interactive GUI usability is not automated.'}
(ROOT/'validation.json').write_text(json.dumps(report, indent=2), encoding='utf8')
print('SOLAR_VALIDATION', json.dumps(report), flush=True)
