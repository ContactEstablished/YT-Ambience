"""Optional Solar sidebar. Run from Blender's Text Editor or the supplied launcher.
The saved scene's native controls and drivers work without this UI script.
"""
import bpy

class SOLAR_OT_reset_view(bpy.types.Operator):
    bl_idname='solar.reset_view'
    bl_label='Reset view'
    bl_description='Restore Sun size and the fixed camera view; retain effect settings'
    bl_options={'REGISTER','UNDO'}
    def execute(self,context):
        control=bpy.data.objects.get('SUN CONTROLS')
        if control:control['sun_size']=1.
        if context.space_data.type=='VIEW_3D':
            context.space_data.region_3d.view_perspective='CAMERA'
        context.view_layer.update()
        return {'FINISHED'}

class SOLAR_PT_observatory(bpy.types.Panel):
    bl_label='Solar Observatory'
    bl_idname='SOLAR_PT_observatory'
    bl_space_type='VIEW_3D'
    bl_region_type='UI'
    bl_category='Solar'
    def draw(self,context):
        layout=self.layout
        control=bpy.data.objects.get('SUN CONTROLS')
        if not control:
            layout.label(text='Open solar_observatory.blend first.')
            return
        for key,label in [('rotation_speed','Rotation'),('surface_flow','Surface flow'),('sunspots','Sunspots'),
                          ('flare_activity','Flare activity'),('flare_intensity','Flare intensity'),
                          ('corona_glow','Corona glow'),('sun_size','Sun size')]:
            layout.prop(control,f'["{key}"]',text=label,slider=True)
        layout.prop(control,'["stars"]',text='Stars')
        row=layout.row(align=True)
        row.operator('screen.animation_play',text='Pause' if context.screen.is_animation_playing else 'Play',icon='PAUSE' if context.screen.is_animation_playing else 'PLAY')
        row.operator('solar.reset_view',text='Reset view')
        layout.operator('render.render',text='Render image',icon='RENDER_STILL')

def register():
    for cls in (SOLAR_OT_reset_view,SOLAR_PT_observatory):
        old=getattr(bpy.types,cls.__name__,None)
        if old:bpy.utils.unregister_class(old)
        bpy.utils.register_class(cls)

if __name__=='__main__':register()
