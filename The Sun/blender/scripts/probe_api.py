import bpy
s=bpy.context.scene
m=bpy.data.materials.new('probe'); m.use_nodes=True
for t in ['ShaderNodeTexNoise','ShaderNodeVolumePrincipled','ShaderNodeEmission','ShaderNodeMixShader','ShaderNodeAttribute']:
 n=m.node_tree.nodes.new(t); print(t, [(i.name,i.identifier) for i in n.inputs])
g=bpy.data.node_groups.new('comp','CompositorNodeTree'); s.compositing_node_group=g
for t in ['CompositorNodeRLayers','CompositorNodeGlare','NodeGroupOutput']:
 n=g.nodes.new(t); print(t,[(i.name,i.identifier) for i in n.inputs])
 if t=='CompositorNodeGlare': print('GLARE',[(p.identifier) for p in n.bl_rna.properties])
print('EEVEE', [p.identifier for p in s.eevee.bl_rna.properties])
print('VIEWS',s.view_settings.bl_rna.properties['view_transform'].enum_items.keys())
print('MATERIAL',[p.identifier for p in m.bl_rna.properties if 'surface' in p.identifier or 'render' in p.identifier])
