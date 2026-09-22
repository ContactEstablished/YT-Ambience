"""Build the native Blender solar observatory. Run in a NEW background process.

blender --background --factory-startup --python build_sun.py -- --seconds 60 --seed 73491
All generated data and renders remain in the parent blender directory.
"""
import argparse
import json
import math
import random
import sys
from pathlib import Path

import bpy
from mathutils import Vector, Matrix

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--seconds', type=int, default=60)
parser.add_argument('--seed', type=int, default=73491)
parser.add_argument('--render', action='store_true')
parser.add_argument('--frame', type=int, default=180)
parser.add_argument('--preview', action='store_true')
parser.add_argument('--engine', choices=['EEVEE','CYCLES'], default='CYCLES')
args = parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
if not 10 <= args.seconds <= 1800:
    raise ValueError('--seconds must be between 10 and 1800')

# This script is a builder, not an in-place editor. Launch it using the supplied command.
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.name = 'SOLAR OBSERVATORY'
scene.render.engine = 'BLENDER_EEVEE'
if args.engine == 'CYCLES':
    scene.render.engine='CYCLES'
    prefs=bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type='OPTIX'
    prefs.refresh_devices()
    for device in prefs.devices: device.use=device.type=='OPTIX'
    scene.cycles.device='GPU' if any(d.type=='OPTIX' for d in prefs.devices) else 'CPU'
    scene.cycles.samples=64
    scene.cycles.use_denoising=True
    scene.cycles.max_bounces=6
    scene.cycles.transparent_max_bounces=12
    scene.cycles.volume_bounces=1
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100
scene.render.fps = 30
scene.frame_start = 1
scene.frame_end = args.seconds * 30
scene.eevee.taa_render_samples = 64
scene.eevee.taa_samples = 24
scene.eevee.volumetric_samples = 64
scene.eevee.volumetric_tile_size = '4'
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGB'
scene.render.image_settings.color_depth = '16'
scene.render.filepath = '//renders/frames/sun_'
scene.render.film_transparent = False
scene.view_settings.view_transform = 'Standard'
scene.view_settings.look = 'None'
scene.view_settings.exposure = -.8
scene.world.color = (0, 0, 0)
scene.world.use_nodes = True
scene.world.node_tree.nodes.get('Background').inputs['Color'].default_value = (.00015,.00003,.00001,1)
scene.world.node_tree.nodes.get('Background').inputs['Strength'].default_value = .1

def collection(name):
    c = bpy.data.collections.new(name)
    scene.collection.children.link(c)
    return c

surface_collection = collection('01 · Photosphere')
corona_collection = collection('02 · Corona volume')
loops_collection = collection('03 · Magnetic loops')
eruption_collection = collection('04 · Random eruptions')
stars_collection = collection('05 · Star field')
rig_collection = collection('00 · Camera & controls')

def move(obj, coll):
    for c in list(obj.users_collection): c.objects.unlink(obj)
    coll.objects.link(obj)
    return obj

def empty(name, coll):
    obj = bpy.data.objects.new(name, None)
    coll.objects.link(obj)
    obj.empty_display_size = .22
    return obj

control = empty('SUN CONTROLS', rig_collection)
control.empty_display_type = 'PLAIN_AXES'
control.show_in_front = True
defaults = {
    'rotation_speed': (1.,0.,20.,'Automatic rotation multiplier. 1x = one revolution in about 349 seconds.'),
    'surface_flow': (1.,0.,3.,'Surface mixing speed; independent of flares. Zero holds a static material phase.'),
    'sunspots': (1.,0.,3.,'Magnetic dark region coverage; zero removes the magnetic masks.'),
    'flare_activity': (1.,0.,3.,'Loop population and eruption frequency. Zero disables all flares.'),
    'flare_intensity': (1.,0.,3.,'Flare emission brightness, independently of frequency.'),
    'corona_glow': (1.,0.,2.,'Volumetric corona emission; does not change the flare clock.'),
    'sun_size': (1.,.55,1.35,'Size in the fixed camera composition.'),
}
for key,(value,lo,hi,description) in defaults.items():
    control[key] = value
    control.id_properties_ui(key).update(min=lo,max=hi,soft_min=lo,soft_max=hi,description=description)
control['stars'] = True
control['seed'] = args.seed
control.id_properties_ui('seed').update(description='Build seed (informational). Rebuild with --seed to generate new geometry/events.')

def driver(target, prop, expression, variables=None, index=None):
    fc = target.driver_add(prop) if index is None else target.driver_add(prop,index)
    d = fc.driver
    d.type = 'SCRIPTED'
    d.expression = expression
    for name,(obj,path) in (variables or {}).items():
        v = d.variables.new(); v.name = name; v.type = 'SINGLE_PROP'
        v.targets[0].id = obj; v.targets[0].data_path = path
    return fc

def cv(key): return (control, f'["{key}"]')
def ev(obj,key): return (obj, f'["{key}"]')

root = empty('Solar rotation',rig_collection)
root.rotation_euler = (.15,.4,-.12)
driver(root,'rotation_euler','.4 + (frame-1)/30*.018*speed',{'speed':cv('rotation_speed')},1)
for i in range(3): driver(root,'scale','size',{'size':cv('sun_size')},i)

def material(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    m.node_tree.nodes.clear()
    m.diffuse_color = (1,.12,.005,1)
    return m,m.node_tree

def node(nt,kind,name,x=0,y=0):
    n = nt.nodes.new(kind); n.label=name; n.name=name; n.location=(x,y)
    return n

def wire(nt,source,dest): nt.links.new(source,dest)

def mathnode(nt,op,a,b=0,name=None):
    n=node(nt,'ShaderNodeMath',name or op); n.operation=op
    for i,value in enumerate((a,b)):
        if isinstance(value,(int,float)): n.inputs[i].default_value=value
        else: wire(nt,value,n.inputs[i])
    return n.outputs[0]

def ramp(nt,value,stops,name):
    n=node(nt,'ShaderNodeValToRGB',name)
    r=n.color_ramp
    while len(r.elements)>2: r.elements.remove(r.elements[-1])
    for i,(pos,color) in enumerate(stops):
        e=r.elements[i] if i<2 else r.elements.new(pos)
        e.position=pos; e.color=(*color,1)
    r.interpolation='EASE'
    wire(nt,value,n.inputs[0])
    return n.outputs[0]

def noise(nt,coords,scale,detail=3,name='Noise',clock=None):
    n=node(nt,'ShaderNodeTexNoise',name)
    n.noise_dimensions='4D' if clock else '3D'
    n.inputs['Scale'].default_value=scale
    n.inputs['Detail'].default_value=detail
    n.inputs['Roughness'].default_value=.66
    wire(nt,coords,n.inputs['Vector'])
    if clock:
        driver(n.inputs['W'],'default_value',f'(frame-1)/30*rate*{clock[1]}',{'rate':cv(clock[0])})
    return n

def sphere(name,radius,coll,mat,segments=128,rings=80):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,radius=radius)
    obj=move(bpy.context.object,coll); obj.name=name
    for p in obj.data.polygons:p.use_smooth=True
    obj.data.materials.append(mat)
    obj.parent=root
    return obj

# The photosphere remains native shader nodes: editable, seamless, and no bitmap dependency.
mat,nt=material('Photosphere · flowing golden plasma')
coords=node(nt,'ShaderNodeTexCoord','Local coordinates').outputs['Object']
warp=noise(nt,coords,4.8,4,'Slow convection',('surface_flow',.075))
warpvec=node(nt,'ShaderNodeVectorMath','Warp amplitude'); warpvec.operation='SCALE'
wire(nt,warp.outputs['Color'],warpvec.inputs[0]); warpvec.inputs['Scale'].default_value=.26
add=node(nt,'ShaderNodeVectorMath','Advected coordinates'); add.operation='ADD'
wire(nt,coords,add.inputs[0]); wire(nt,warpvec.outputs['Vector'],add.inputs[1])
turb=noise(nt,add.outputs[0],24,4,'Turbulent granulation',('surface_flow',.12))
fine=noise(nt,add.outputs[0],140,2,'Fine plasma texture',('surface_flow',.08))
heat=mathnode(nt,'ADD',mathnode(nt,'MULTIPLY',turb.outputs['Fac'],.82),mathnode(nt,'MULTIPLY',fine.outputs['Fac'],.18))
color=ramp(nt,heat,[(.23,(.085,.001,.0001)),(.39,(.6,.013,.0002)),(.52,(1,.115,.001)),(.65,(1,.40,.009)),(.80,(1,.78,.15))],'Solar temperature palette')
magnetic=noise(nt,coords,4.5,3,'Magnetic dark regions',('surface_flow',.038))
spot_amount=node(nt,'ShaderNodeValue','Sunspot amount')
driver(spot_amount.outputs[0],'default_value','amount',{'amount':cv('sunspots')})
threshold=mathnode(nt,'SUBTRACT',.63,mathnode(nt,'MULTIPLY',spot_amount.outputs[0],.04))
mask=mathnode(nt,'MULTIPLY',mathnode(nt,'MAXIMUM',mathnode(nt,'SUBTRACT',magnetic.outputs['Fac'],threshold),0),22)
mask=mathnode(nt,'MINIMUM',mask,.92)
mask=mathnode(nt,'MULTIPLY',mask,mathnode(nt,'MINIMUM',spot_amount.outputs[0],1))
mix=node(nt,'ShaderNodeMixRGB','Dark magnetic patches'); mix.blend_type='MIX'
wire(nt,mask,mix.inputs[0]); wire(nt,color,mix.inputs[1]); mix.inputs[2].default_value=(.025,.0007,.00005,1)
facing=node(nt,'ShaderNodeLayerWeight','Limb darkening')
limb=mathnode(nt,'ADD',.62,mathnode(nt,'MULTIPLY',facing.outputs['Facing'],.38))
emit=node(nt,'ShaderNodeEmission','Radiant photosphere')
wire(nt,mix.outputs[0],emit.inputs['Color'])
wire(nt,mathnode(nt,'MULTIPLY',limb,2.4),emit.inputs['Strength'])
out=node(nt,'ShaderNodeOutputMaterial','Surface output'); wire(nt,emit.outputs[0],out.inputs['Surface'])
sun=sphere('Sun · Photosphere',1,surface_collection,mat,192,128)

# A real volume around the opaque photosphere. No billboard texture is required.
mat,nt=material('Corona · emissive turbulent volume')
coords=node(nt,'ShaderNodeTexCoord','Corona object coordinates').outputs['Object']
length=node(nt,'ShaderNodeVectorMath','Distance from center'); length.operation='LENGTH'; wire(nt,coords,length.inputs[0])
radial=mathnode(nt,'MAXIMUM',mathnode(nt,'SUBTRACT',length.outputs['Value'],1),0)
falloff=mathnode(nt,'EXPONENT',mathnode(nt,'MULTIPLY',radial,-10))
outer=mathnode(nt,'POWER',mathnode(nt,'MAXIMUM',mathnode(nt,'SUBTRACT',1,mathnode(nt,'DIVIDE',mathnode(nt,'MAXIMUM',mathnode(nt,'SUBTRACT',length.outputs['Value'],1.05),0),.5)),0),2)
inner=mathnode(nt,'GREATER_THAN',length.outputs['Value'],.995)
n=noise(nt,coords,9,3,'Coronal wisps')
n.noise_dimensions='4D'
driver(n.inputs['W'],'default_value','(frame-1)/30*.07')
density=mathnode(nt,'MULTIPLY',falloff,mathnode(nt,'MULTIPLY',inner,outer))
wisps=mathnode(nt,'ADD',.18,mathnode(nt,'MULTIPLY',n.outputs['Fac'],1.1))
strength=node(nt,'ShaderNodeValue','Independent corona breath')
driver(strength.outputs[0],'default_value','glow*(1+.045*sin((frame-1)/30*.48))*2.8',{'glow':cv('corona_glow')})
volume=node(nt,'ShaderNodeVolumePrincipled','Coronal plasma volume')
volume.inputs['Density'].default_value=0
volume.inputs['Emission Color'].default_value=(1,.095,.001,1)
wire(nt,mathnode(nt,'MULTIPLY',mathnode(nt,'MULTIPLY',density,wisps),strength.outputs[0]),volume.inputs['Emission Strength'])
out=node(nt,'ShaderNodeOutputMaterial','Volume output'); wire(nt,volume.outputs['Volume'],out.inputs['Volume'])
halo=sphere('Corona · volume shell',1.55,corona_collection,mat,64,32)
# Corona scale follows zoom, but its own variation uses unscaled timeline time.

def emission_material(name,color,strength):
    m,nt=material(name)
    e=node(nt,'ShaderNodeEmission','Plasma emission'); e.inputs[0].default_value=(*color,1); e.inputs[1].default_value=strength
    o=node(nt,'ShaderNodeOutputMaterial','Output'); wire(nt,e.outputs[0],o.inputs['Surface'])
    return m,e

def curve_object(name,paths,bevel,mat,coll,parent=root):
    data=bpy.data.curves.new(name,'CURVE'); data.dimensions='3D'; data.resolution_u=1
    data.bevel_depth=bevel; data.bevel_resolution=2; data.resolution_u=1
    for path in paths:
        s=data.splines.new('POLY'); s.points.add(len(path)-1)
        for p,v in zip(s.points,path):p.co=(*v,1)
    obj=bpy.data.objects.new(name,data); coll.objects.link(obj); obj.parent=parent
    obj.data.materials.append(mat)
    return obj

rng=random.Random(args.seed)
for i in range(72):
    angle=rng.uniform(0,math.tau); latitude=rng.uniform(-1.1,1.1)
    normal=Vector((math.cos(latitude)*math.cos(angle),math.sin(latitude),math.cos(latitude)*math.sin(angle)))
    tangent=normal.cross(Vector((0,1,0))).normalized(); side=normal.cross(tangent).normalized()
    height=rng.uniform(.10,.34); span=rng.uniform(.10,.25); phase=rng.uniform(0,math.tau)
    paths=[]
    for strand in range(3):
        path=[]
        for j in range(49):
            u=j/48; a=u*math.pi
            p=normal*(.977+math.sin(a)*height)+tangent*(math.cos(a)*span)
            p+=side*((strand-1)*.006+math.sin(u*19+phase+strand)*.004*math.sin(a))
            path.append(tuple(p))
        paths.append(path)
    m,e=emission_material(f'Loop {i:02d} · emission',(1,.16,.006),1)
    activity=f'min(max(activity*24-{i},0),1)'
    driver(e.inputs['Strength'],'default_value',f'intensity*{activity}*(1.7+1.5*sin((frame-1)/30*activity*.22+{phase}))',
           {'intensity':cv('flare_intensity'),'activity':cv('flare_activity')})
    obj=curve_object(f'Magnetic loop {i:02d}',paths,rng.uniform(.001,.0023),m,loops_collection)
    for prop in ('hide_render','hide_viewport'):
        driver(obj,prop,f'activity*24<={i} or intensity<=0',{'activity':cv('flare_activity'),'intensity':cv('flare_intensity')})

events=[]
for slot in range(15):
    start=-4-slot*3 if slot<2 else rng.uniform(3,25)
    while start < args.seconds*3:
        violent=rng.random()<.26
        events.append(dict(slot=slot,start=start,duration=rng.uniform(11,28),violent=violent,
            kind='arch' if rng.random()<.4 else 'jet',longitude=rng.uniform(0,math.tau),latitude=rng.uniform(-.9,.9),
            length=rng.uniform(.65,1.1) if violent else rng.uniform(.25,.6),
            width=rng.uniform(.15,.28) if violent else rng.uniform(.055,.14),
            span=rng.uniform(.13,.36),bend=rng.uniform(-.35,.35),twist=rng.uniform(-1.2,1.2),phase=rng.uniform(0,100)))
        start+=events[-1]['duration']+rng.uniform(5,29)

def plume_material(name,event):
    m,nt=material(name); m.surface_render_method='DITHERED'
    uv=node(nt,'ShaderNodeTexCoord','Plume UV').outputs['UV']
    split=node(nt,'ShaderNodeSeparateXYZ','Along / across'); wire(nt,uv,split.inputs[0])
    u,v=split.outputs['X'],split.outputs['Y']
    n=noise(nt,uv,8,3,'Turbulent plasma sheets',('flare_activity',.25))
    edge=mathnode(nt,'MAXIMUM',mathnode(nt,'SUBTRACT',1,mathnode(nt,'ABSOLUTE',mathnode(nt,'SUBTRACT',mathnode(nt,'MULTIPLY',v,2),1))),0)
    edgemask=mathnode(nt,'POWER',edge,.75)
    tip=mathnode(nt,'MINIMUM',mathnode(nt,'MULTIPLY',mathnode(nt,'SUBTRACT',1,u),4),1) if event['kind']=='jet' else 1
    mask=mathnode(nt,'MULTIPLY',mathnode(nt,'MULTIPLY',edgemask,tip),mathnode(nt,'MULTIPLY',n.outputs['Fac'],1.4))
    color=ramp(nt,n.outputs['Fac'],[(.20,(.3,.002,.0001)),(.46,(1,.035,.0004)),(.68,(1,.35,.008)),(.88,(1,.8,.18))],'Plasma strands palette')
    root_distance=u if event['kind']=='jet' else mathnode(nt,'MINIMUM',u,mathnode(nt,'SUBTRACT',1,u))
    rootglow=mathnode(nt,'EXPONENT',mathnode(nt,'MULTIPLY',root_distance,-15))
    rootcolor=node(nt,'ShaderNodeMixRGB','Hot root'); wire(nt,rootglow,rootcolor.inputs[0]); wire(nt,color,rootcolor.inputs[1]); rootcolor.inputs[2].default_value=(1,.8,.32,1)
    e=node(nt,'ShaderNodeEmission','Event emission'); wire(nt,rootcolor.outputs[0],e.inputs[0])
    driver(e.inputs[1],'default_value','intensity*envelope*population*power',
      {'intensity':cv('flare_intensity'),'envelope':ev(event,'envelope'),'population':ev(event,'population'),'power':ev(event,'power')})
    transparent=node(nt,'ShaderNodeBsdfTransparent','Transparent edges')
    mix=node(nt,'ShaderNodeMixShader','Ragged silhouette'); wire(nt,mask,mix.inputs[0]); wire(nt,transparent.outputs[0],mix.inputs[1]); wire(nt,e.outputs[0],mix.inputs[2])
    out=node(nt,'ShaderNodeOutputMaterial','Plume output'); wire(nt,mix.outputs[0],out.inputs['Surface'])
    return m

for i,data in enumerate(events):
    event=empty(f'Eruption {i:03d} · {data["kind"]}',eruption_collection); event.parent=root
    for key,value in data.items():event[key]=value
    for key,value in [('age',0.),('envelope',0.),('population',0.),('power',9. if data['violent'] else 5.)]: event[key]=value
    driver(event,'["age"]',f'min(max(((frame-1)/30*activity-({data["start"]}))/({data["duration"]}),0),1)',{'activity':cv('flare_activity')})
    driver(event,'["population"]',f'min(max(activity*5-{data["slot"]},0),1)',{'activity':cv('flare_activity')})
    driver(event,'["envelope"]','min(age/.12,1)**2*(3-2*min(age/.12,1))*(1-min(max((age-.48)/.52,0),1)**2*(3-2*min(max((age-.48)/.52,0),1)))',{'age':ev(event,'age')})
    normal=Vector((math.cos(data['latitude'])*math.cos(data['longitude']),math.sin(data['latitude']),math.cos(data['latitude'])*math.sin(data['longitude'])))
    tangent=Vector((0,1,0)).cross(normal).normalized(); side=normal.cross(tangent).normalized()
    event.rotation_mode='QUATERNION'; event.rotation_quaternion=Matrix((tangent,side,normal)).transposed().to_quaternion()
    event.location=normal*(math.sqrt(1-data['span']**2)-.006 if data['kind']=='arch' else .992)
    vertices=[]; faces=[]; uvcoords=[]
    for sheet in range(3):
        base=len(vertices)
        for j in range(49):
            u=j/48
            for k in range(13):
                v=k/12; across=v*2-1; angle=sheet*math.pi/3+u*data['twist']
                width=data['width']*(.36+u*.9)*(1+.12*math.sin(u*19+data['phase']))
                if data['kind']=='jet':
                    p=Vector((data['bend']*u*u,math.sin(u*3+data['phase'])*u*u*.12,u*data['length']))
                    p+=Vector((math.cos(angle),math.sin(angle),0))*across*width
                else:
                    a=u*math.pi
                    p=Vector((math.cos(a)*data['span'],data['bend']*math.sin(a)*.22,math.sin(a)*data['length']))
                    outward=Vector((data['length']*math.cos(a),0,data['span']*math.sin(a))).normalized()
                    p+=(Vector((0,1,0))*math.cos(angle)+outward*math.sin(angle))*across*data['width']*(.45+.55*math.sin(a))
                vertices.append(tuple(p)); uvcoords.append((u,v))
                if j<48 and k<12:
                    q=base+j*13+k; faces.append((q,q+13,q+14,q+1))
    mesh=bpy.data.meshes.new(f'Plasma mesh {i:03d}'); mesh.from_pydata(vertices,[],faces); mesh.update()
    uv=mesh.uv_layers.new(name='Plasma flow')
    for poly in mesh.polygons:
        poly.use_smooth=True
        for loop in poly.loop_indices:uv.data[loop].uv=uvcoords[mesh.loops[loop].vertex_index]
    obj=bpy.data.objects.new(f'Plasma plume {i:03d}',mesh); eruption_collection.objects.link(obj); obj.parent=event
    obj.data.materials.append(plume_material(f'Eruption {i:03d} · layered plasma',event))
    driver(obj,'scale','.16+.84*(1-(1-age)**3)',{'age':ev(event,'age')},2)
    visibility={'age':ev(event,'age'),'population':ev(event,'population'),'intensity':cv('flare_intensity')}
    for prop in ('hide_render','hide_viewport'):driver(obj,prop,'age<=0 or age>=1 or population<=0 or intensity<=0',visibility)

# Mesh stars cost one draw object; soft circular UV masks avoid polygonal stars.
rng=random.Random(9182); vertices=[]; faces=[]
for i in range(1400):
    x=rng.uniform(-5.8,5.8); y=rng.uniform(-3.3,3.3); z=-4
    size=.002+rng.random()**5*.010
    base=len(vertices); vertices.extend([(x-size,y-size,z),(x+size,y-size,z),(x+size,y+size,z),(x-size,y+size,z)])
    faces.append((base,base+1,base+2,base+3))
mesh=bpy.data.meshes.new('Warm star field'); mesh.from_pydata(vertices,[],faces)
uv=mesh.uv_layers.new(name='Star disks')
for poly in mesh.polygons:
    for loop,coord in zip(poly.loop_indices,[(0,0),(1,0),(1,1),(0,1)]):uv.data[loop].uv=coord
obj=bpy.data.objects.new('Stars · toggle on SUN CONTROLS',mesh); stars_collection.objects.link(obj)
m,nt=material('Stars · warm distant light'); m.surface_render_method='DITHERED'
uvnode=node(nt,'ShaderNodeTexCoord','Star UV')
dist=node(nt,'ShaderNodeVectorMath','Star radius'); dist.operation='DISTANCE'; wire(nt,uvnode.outputs['UV'],dist.inputs[0]); dist.inputs[1].default_value=(.5,.5,0)
opacity=mathnode(nt,'MAXIMUM',mathnode(nt,'SUBTRACT',1,mathnode(nt,'MULTIPLY',dist.outputs['Value'],2)),0)
e=node(nt,'ShaderNodeEmission','Starlight'); e.inputs[0].default_value=(.6,.43,.27,1); e.inputs[1].default_value=1.5
transparent=node(nt,'ShaderNodeBsdfTransparent','Empty space'); mix=node(nt,'ShaderNodeMixShader','Star disk')
wire(nt,opacity,mix.inputs[0]); wire(nt,transparent.outputs[0],mix.inputs[1]); wire(nt,e.outputs[0],mix.inputs[2])
out=node(nt,'ShaderNodeOutputMaterial','Stars output'); wire(nt,mix.outputs[0],out.inputs['Surface']); obj.data.materials.append(m)
for prop in ('hide_render','hide_viewport'):driver(obj,prop,'not enabled',{'enabled':cv('stars')})

bpy.ops.object.camera_add(location=(0,0,8))
camera=move(bpy.context.object,rig_collection); camera.name='Camera · centered Sun'
camera.data.type='ORTHO'; camera.data.ortho_scale=6.1
camera.data.lens=50; camera.data.clip_end=100
scene.camera=camera

comp=bpy.data.node_groups.new('Solar bloom · restrained highlights','CompositorNodeTree')
scene.compositing_node_group=comp
comp.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor')
layers=node(comp,'CompositorNodeRLayers','Rendered Sun',0,0)
glare=node(comp,'CompositorNodeGlare','Solar glow',220,0)
glare.inputs['Type'].default_value='Fog Glow'
glare.inputs['Quality'].default_value='High'
glare.inputs['Threshold'].default_value=1.4
glare.inputs['Strength'].default_value=.3
glare.inputs['Size'].default_value=.35
out=node(comp,'NodeGroupOutput','Final image',480,0)
wire(comp,layers.outputs['Image'],glare.inputs['Image']); wire(comp,glare.outputs['Image'],out.inputs['Image'])

# A readable, portable control surface is always available in Object > Custom Properties.
# The optional sidebar script improves usability but is not needed for animation/rendering.
for m in bpy.data.materials:
    if m.node_tree:
        for idx,n in enumerate(m.node_tree.nodes):
            n.location=((idx%6)*230,-(idx//6)*230)
bpy.ops.object.select_all(action='DESELECT'); control.select_set(True); bpy.context.view_layer.objects.active=control
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA'
            area.spaces.active.shading.type='MATERIAL'
            area.spaces.active.shading.use_scene_world=True
            area.spaces.active.shading.use_scene_lights=True
            area.spaces.active.shading.use_compositor='ALWAYS'
        elif area.type=='PROPERTIES':area.spaces.active.context='OBJECT'

scene['solar_build_seed']=args.seed
scene['solar_schedule_seconds']=args.seconds*3
scene['solar_version']='1.0'
for filename in ('sun_controls.py',):
    path=ROOT/'scripts'/filename
    if path.exists():bpy.data.texts.load(str(path))
readme=bpy.data.texts.new('START HERE · Solar Observatory')
readme.write('Native Blender Sun. Select SUN CONTROLS, then Object Properties > Custom Properties.\n'
    'Optional: run the embedded sun_controls.py text once for the Solar sidebar (N panel).\n'
    'Space: play/pause timeline. Numpad 0: camera. Z then R: rendered shading. F12: render.\n'
    'Use Blender/renders for generated output. Read blender/README.md for full instructions.\n'
    'No external textures, add-ons, or frame handlers are needed to render this saved scene.\n')
scene.frame_set(min(args.frame,scene.frame_end))
bpy.context.view_layer.update()
ROOT.mkdir(exist_ok=True)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'solar_observatory.blend'))
manifest=dict(blender=bpy.app.version_string,seed=args.seed,seconds=args.seconds,fps=30,
    event_count=len(events),objects=len(scene.objects),engine=scene.render.engine,
    controls={key:control[key] for key in defaults},stars=True)
(ROOT/'build_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
print('SOLAR_BUILD',json.dumps(manifest),flush=True)
if args.render:
    scene.render.resolution_percentage=50 if args.preview else 100
    scene.render.filepath=str(ROOT/'renders'/f'preview_{scene.frame_current:04d}.png')
    bpy.ops.render.render(write_still=True)
    print('SOLAR_RENDER',scene.render.filepath,flush=True)
