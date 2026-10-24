"""Run in Blender with --factory-startup; output must be outside the release folder."""
import bpy
import hashlib
import json
import os
from pathlib import Path
import traceback

out=Path(os.environ['PACKAGE_TEST_OUTPUT'])
out.mkdir(parents=True,exist_ok=True)
assert bpy.app.version[:2] == (3,6)
assert Path(bpy.app.binary_path).resolve() == Path(os.environ['PACKAGE_EXPECTED_BINARY']).resolve()
assert bpy.app.build_hash.decode() == '112f061a999b'
mode=os.environ.get('PACKAGE_TEST_MODE','render')
checks=[]
metrics={}
(out/'report.json').write_text(json.dumps({'mode':mode,'passed':False}),encoding='utf8')
def check(label, condition):
    assert condition,label
    checks.append(label)
    print('PACKAGE_CHECK',label,flush=True)
def finish():
    (out/'report.json').write_text(json.dumps({'mode':mode,'passed':True,'checks':checks,'metrics':metrics},indent=2),encoding='utf8')

if mode == 'config':
    native=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/3.6/config'
    check('Native Blender 3.6 config path',Path(bpy.utils.user_resource('CONFIG')).resolve()==native.resolve())
    files={p:p.read_bytes() for p in native.iterdir() if p.is_file()}
    pref=native/'userpref.blend'
    check('Existing preferences available',pref.is_file())
    check('Native preferences read successfully',bpy.ops.wm.read_userpref()=={'FINISHED'})
    bpy.context.preferences.use_preferences_save=False
    check('Reading preferences did not modify config files',all(p.read_bytes()==v for p,v in files.items()))
    check('Packaged local config directory absent',not (Path(bpy.app.binary_path).parent/'3.6/config').exists())
    check('Native user add-on path discoverable',str(native.parent/'scripts') in bpy.utils.script_paths())
    finish()
elif mode == 'reopen':
    bpy.ops.wm.open_mainfile(filepath=str(out.parent/'render/Package-Test.blend'),load_ui=False)
    lamp=bpy.data.objects['Key']
    check('Light collection survives save/reopen',lamp.light_linking.receiver_collection is not None)
    check('Shared light collection survives save/reopen',bpy.data.objects['Shared Key'].light_linking.receiver_collection==lamp.light_linking.receiver_collection)
    check('SSRT setting survives save/reopen',bpy.context.scene.eevee.use_ssr)
    finish()
else:
    import numpy as np
    from mathutils import Vector
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob,do_unlink=True)
    bpy.context.view_layer.active_layer_collection=bpy.context.view_layer.layer_collection
    bpy.context.preferences.use_preferences_save=False
    s=bpy.context.scene
    s.render.engine='BLENDER_EEVEE'
    check('SSGI RNA available','ssr_diffuse_intensity' in s.eevee.bl_rna.properties)
    check('Light linking RNA available','light_linking' in bpy.types.Object.bl_rna.properties)
    check('Cycles not compiled',not bpy.app.build_options.cycles)
    s.render.resolution_x=400;s.render.resolution_y=300;s.render.resolution_percentage=100
    s.render.image_settings.file_format='PNG';s.render.dither_intensity=0
    s.view_settings.view_transform='Standard';s.view_settings.look='None';s.view_settings.exposure=0;s.view_settings.gamma=1
    s.eevee.taa_render_samples=32;s.eevee.use_ssr=True;s.eevee.ssr_diffuse_intensity=1
    s.eevee.use_gtao=False;s.eevee.use_soft_shadows=False
    s.eevee.volumetric_samples=32;s.eevee.volumetric_tile_size='4';s.eevee.volumetric_start=.1;s.eevee.volumetric_end=30
    s.world=bpy.data.worlds.new('Black world');s.world.use_nodes=True
    s.world.node_tree.nodes['Background'].inputs[0].default_value=(0,0,0,1)
    mat=bpy.data.materials.new('Neutral');mat.use_nodes=True
    bsdf=mat.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Base Color'].default_value=(.35,.4,.5,1);bsdf.inputs['Roughness'].default_value=.3
    objects=[]
    bpy.ops.mesh.primitive_plane_add(size=12);floor=bpy.context.view_layer.objects.active;floor.name='Ground';floor.data.materials.append(mat);objects.append(floor)
    bpy.ops.mesh.primitive_cube_add(size=1.5,location=(-1,0,.75));cube=bpy.context.view_layer.objects.active;cube.name='Cube';cube.data.materials.append(mat);objects.append(cube)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=16,radius=.8,location=(1.1,.3,.8));sphere=bpy.context.view_layer.objects.active;sphere.name='Sphere';sphere.data.materials.append(mat);objects.append(sphere)
    cam=bpy.data.objects.new('Camera',bpy.data.cameras.new('Camera'));s.collection.objects.link(cam);s.camera=cam
    cam.location=(5,-8,5);cam.rotation_euler=(Vector((0,0,.5))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=6
    lamp=bpy.data.objects.new('Key',bpy.data.lights.new('Key','AREA'));s.collection.objects.link(lamp)
    lamp.location=(-3,-2,5);lamp.rotation_euler=(Vector((0,0,.5))-lamp.location).to_track_quat('-Z','Y').to_euler();lamp.data.energy=800;lamp.data.size=.1
    receivers=bpy.data.collections.new('Receivers')
    for ob in objects:receivers.objects.link(ob)
    blockers=bpy.data.collections.new('Blockers')
    for ob in objects:blockers.objects.link(ob)
    def render(name):
        s.render.image_settings.file_format='PNG';s.render.filepath=str(out/(name+'.png'));bpy.context.view_layer.update();bpy.ops.render.render(write_still=True)
        s.render.image_settings.file_format='OPEN_EXR';s.render.image_settings.color_depth='32'
        bpy.data.images['Render Result'].save_render(str(out/(name+'.exr')),scene=s)
        image=bpy.data.images.load(str(out/(name+'.exr')),check_existing=False)
        result=np.array(image.pixels[:],dtype=np.float32);bpy.data.images.remove(image)
        check(name+' finite and bounded',bool(np.isfinite(result).all() and result.max()<5))
        np.save(out/(name+'.npy'),result)
        if not bpy.app.background:
            w=bpy.context.window_manager.windows[0];a=max(w.screen.areas,key=lambda x:x.width*x.height);a.type='IMAGE_EDITOR'
            a.spaces.active.image=bpy.data.images.load(str(out/(name+'.png')),check_existing=False)
            with bpy.context.temp_override(window=w,area=a,region=next(r for r in a.regions if r.type=='WINDOW')):
                bpy.ops.image.view_all(fit_view=True)
                bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP',iterations=2)
                bpy.ops.screen.screenshot(filepath=str(out/(name+'-screen.png')))
        return result
    baseline=render('01-unlinked')
    repeats=[render('01-repeat-'+str(i)) for i in range(3)]
    noise_max=max(float(np.abs(baseline-v).max()) for v in repeats)
    noise_mean=max(float(np.abs(baseline-v).mean()) for v in repeats)
    metrics['repeat_noise']={'maximum':noise_max,'mean':noise_mean}
    check('Repeated SSGI renders remain stable',noise_max<.05 and noise_mean<.002)
    def equivalent(label,a,b,exact=False):
        maximum=float(np.abs(a-b).max());mean=float(np.abs(a-b).mean())
        metrics[label]={'maximum':maximum,'mean':mean}
        check(label,maximum<1e-6 if exact else (maximum<max(.005,noise_max*1.5) and mean<max(.0001,noise_mean*1.5)))
    lamp.light_linking.receiver_collection=receivers
    included=render('02-included')
    equivalent('Include all matches unlinked within measured SSGI noise',baseline,included)
    for item in receivers.collection_objects:item.light_linking.link_state='EXCLUDE'
    excluded=render('03-excluded')
    lamp.light_linking.receiver_collection=None;lamp.data.energy=0
    dark=render('04-light-off')
    equivalent('Exclude all equals light off with SSRT',excluded,dark,exact=True)
    check('Light contributes to baseline',np.abs(baseline-dark).mean()>.01)
    lamp.data.energy=800;lamp.light_linking.blocker_collection=blockers
    for item in blockers.collection_objects:item.light_linking.link_state='EXCLUDE'
    no_blockers=render('05-shadow-excluded')
    lamp.light_linking.blocker_collection=None;lamp.data.use_shadow=False
    no_shadows=render('06-shadows-off')
    equivalent('Exclude blockers matches shadows off',no_blockers,no_shadows)
    check('Shadow exclusion has visible effect',np.abs(baseline-no_blockers).mean()>.0001)
    lamp.data.use_shadow=True
    bpy.ops.mesh.primitive_cube_add(size=3,location=(0,0,1.3));fog=bpy.context.view_layer.objects.active;fog.name='Object fog'
    fm=bpy.data.materials.new('Fog');fm.use_nodes=True;fm.node_tree.nodes.clear()
    scatter=fm.node_tree.nodes.new('ShaderNodeVolumeScatter');scatter.inputs['Density'].default_value=.12
    output=fm.node_tree.nodes.new('ShaderNodeOutputMaterial');fm.node_tree.links.new(scatter.outputs[0],output.inputs['Volume']);fog.data.materials.append(fm)
    fog_col=bpy.data.collections.new('Fog exclusion');fog_col.objects.link(fog);fog_col.collection_objects[0].light_linking.link_state='EXCLUDE'
    lamp.light_linking.receiver_collection=fog_col
    fog_excluded=render('07-fog-excluded')
    lamp.light_linking.receiver_collection=None;lamp.data.volume_factor=0
    volume_off=render('08-volume-light-off')
    equivalent('Volume exclusion matches volume light off',fog_excluded,volume_off)
    lamp.data.volume_factor=1;fog.hide_render=True
    lamp.light_linking.receiver_collection=receivers
    for item in receivers.collection_objects:item.light_linking.link_state='INCLUDE'
    for ob in list(receivers.objects):
        if ob!=sphere:receivers.objects.unlink(ob)
    target=bpy.data.objects.new('Shared Key',bpy.data.lights.new('Shared Key','AREA'));s.collection.objects.link(target);target.data.energy=0
    for ob in s.objects:ob.select_set(False)
    lamp.select_set(True);target.select_set(True);bpy.context.view_layer.objects.active=lamp
    bpy.ops.object.make_links_data(type='LIGHT_LINKING')
    check('Ctrl+L shares receiver collection',target.light_linking.receiver_collection==receivers)
    selective=render('09-selective')
    check('Selective linking changes render',np.abs(baseline-selective).mean()>.005)
    bpy.ops.wm.save_as_mainfile(filepath=str(out/'Package-Test.blend'))
    lamp.light_linking.receiver_collection=None
    for index in range(12):
        s.frame_set(index+1)
        s.eevee.use_ssr=(index%4!=0)
        s.eevee.ssr_diffuse_intensity=0 if index%4==1 else 1
        s.render.resolution_percentage=75 if index%3==0 else 100
        render('10-history-switch-'+str(index))
    s.render.resolution_percentage=100;s.eevee.use_ssr=True;s.eevee.ssr_diffuse_intensity=1;s.frame_set(1)
    restored=render('11-restored')
    equivalent('SSGI survives frame resolution and enable switches',baseline,restored)
    s.eevee.ssr_diffuse_intensity=0
    no_gi=render('12-diffuse-gi-off')
    check('Diffuse GI remains effective after fix',np.abs(restored-no_gi).mean()>.001)
    finish()
    if not bpy.app.background:
        w=bpy.context.window_manager.windows[0];a=max(w.screen.areas,key=lambda x:x.width*x.height);a.type='IMAGE_EDITOR'
        image=bpy.data.images.load(str(out/'09-selective.png'),check_existing=False);a.spaces.active.image=image
        with bpy.context.temp_override(window=w,area=a,region=next(r for r in a.regions if r.type=='WINDOW')):
            bpy.ops.image.view_all(fit_view=True)
        def screenshot():
            bpy.ops.screen.screenshot(filepath=str(out/'render-window.png'))
            bpy.ops.wm.quit_blender()
            return None
        bpy.app.timers.register(screenshot,first_interval=3)
