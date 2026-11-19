"""Blender-only configured orthographic Action renderer. Source blend is never saved."""
import bpy,json,sys,argparse,math,hashlib
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--config',type=Path,required=True);args=p.parse_args(sys.argv[sys.argv.index('--')+1:]);cfgpath=args.config.resolve();cfg=json.loads(cfgpath.read_text(encoding='utf-8-sig'))
def path(value):
    q=Path(value);return (cfgpath.parent/q).resolve() if not q.is_absolute() else q.resolve()
source=path(cfg['blend']);O=path(cfg['output']);W=path(cfg['work'])
assert source.is_file() and O!=W and O not in W.parents and W not in O.parents,'Invalid input/output layout'
assert not O.exists() and not W.exists(),'Use fresh output/work directories; no implicit overwrite'
width,height=cfg['canvas'];ss=cfg.get('supersample',1);outline=cfg.get('outline_px',0);fps=cfg['fps'];pivot=cfg['pivot']
assert all(type(v)==int and v>0 for v in [width,height,ss]);assert type(outline)==int and outline>=0;assert isinstance(fps,(int,float)) and math.isfinite(fps) and fps>0
assert set(pivot)=={'x','y'} and all(type(v) in (int,float) and math.isfinite(v) and 0<=v<=1 for v in pivot.values())
assert cfg['directions'] and cfg['actions']
for name in list(cfg['directions'])+[a['name'] for a in cfg['actions']]:assert name and all(c.isalnum() or c in '_-' for c in name),'Unsafe action/direction name'
assert len(set(a['name'] for a in cfg['actions']))==len(cfg['actions'])
for a in cfg['actions']:
    assert a['frames'] and all(type(f) in (int,float) and math.isfinite(f) for f in a['frames'])
    assert all(y>x for x,y in zip(a['frames'],a['frames'][1:])),'Sample frames must advance'
    assert type(a['duration_ms'])==int and a['duration_ms']>=len(a['frames'])
bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene;arm=bpy.data.objects[cfg['armature']];assert arm.type=='ARMATURE' and arm.animation_data
assert not arm.animation_data.use_nla or not any(not t.mute for t in arm.animation_data.nla_tracks),'Active NLA needs dedicated adapter'
assert cfg['reset_action'] in bpy.data.actions
for a in cfg['actions']:assert a['source'] in bpy.data.actions
cams=[bpy.data.objects[n] for n in cfg['directions'].values()];assert all(c.type=='CAMERA' and c.data.type=='ORTHO' for c in cams)
assert max(c.data.ortho_scale for c in cams)-min(c.data.ortho_scale for c in cams)<1e-6,'Camera scale differs'
O.mkdir(parents=True);W.mkdir(parents=True)
scene.use_nodes=False;scene.render.engine='CYCLES';scene.cycles.samples=cfg.get('samples',16);scene.cycles.device='CPU';scene.render.film_transparent=True;scene.render.resolution_x=width*ss;scene.render.resolution_y=height*ss;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA'
# Native compositor: downsample before 1px alpha dilation, so thickness is measured at game resolution.
post=bpy.data.scenes.new('Native112OutlineExport');post.render.engine='CYCLES';post.cycles.samples=1;post.render.resolution_x=width;post.render.resolution_y=height;post.render.resolution_percentage=100;post.render.film_transparent=True;post.render.image_settings.file_format='PNG';post.render.image_settings.color_mode='RGBA';post.view_settings.view_transform='Standard';post.use_nodes=True
# A camera is required even though the compositor sources the rendered image.
post.camera=scene.camera;post.collection.objects.link(scene.camera)
tree=post.node_tree;tree.nodes.clear();im=tree.nodes.new('CompositorNodeImage');scale=tree.nodes.new('CompositorNodeScale');scale.space='RELATIVE';scale.inputs['X'].default_value=1/ss;scale.inputs['Y'].default_value=1/ss;tree.links.new(im.outputs['Image'],scale.inputs['Image'])
alpha=tree.nodes.new('CompositorNodeSepRGBA');tree.links.new(scale.outputs['Image'],alpha.inputs[0]);expand=tree.nodes.new('CompositorNodeDilateErode');expand.mode='DISTANCE';expand.distance=outline;tree.links.new(alpha.outputs['A'],expand.inputs[0])
black=tree.nodes.new('CompositorNodeSetAlpha');black.inputs['Image'].default_value=(0,0,0,1);tree.links.new(expand.outputs[0],black.inputs['Alpha']);over=tree.nodes.new('CompositorNodeAlphaOver');over.inputs[0].default_value=1;tree.links.new(black.outputs[0],over.inputs[1]);tree.links.new(scale.outputs['Image'],over.inputs[2]);composite=tree.nodes.new('CompositorNodeComposite');tree.links.new(over.outputs[0],composite.inputs[0])

records=[]
def setframe(f):scene.frame_set(math.floor(f),subframe=f-math.floor(f));bpy.context.view_layer.update()
def choose(name,frame):
    action=bpy.data.actions[name];arm.animation_data.action=action
    if hasattr(action,'slots') and len(action.slots):arm.animation_data.action_slot=action.slots[0]
    setframe(frame)
for action in cfg['actions']:
    choose(cfg['reset_action'],cfg.get('reset_frame',0));choose(action['source'],action['frames'][0])
    for direction,camera in cfg['directions'].items():
        scene.camera=bpy.data.objects[camera];dest=O/(action['name']+'_'+direction);dest.mkdir();raw=W/dest.name;raw.mkdir();digits=max(3,len(str(len(action['frames']))))
        for i,f in enumerate(action['frames'],1):
            setframe(f);png=raw/f'{i:0{digits}d}.png';scene.render.filepath=str(png);bpy.ops.render.render(write_still=True,scene=scene.name)
            loaded=bpy.data.images.load(str(png));im.image=loaded
            tree.links.new((over.outputs[0] if outline else scale.outputs['Image']),composite.inputs[0]);post.render.filepath=str(dest/png.name);bpy.ops.render.render(write_still=True,scene=post.name);bpy.data.images.remove(loaded)
        (dest/'animation.json').write_text(json.dumps({'duration':action['duration_ms'],'scale':100,'pivot':pivot},separators=(',',':')),encoding='utf8')
        records.append({'action':action['name'],'source':action['source'],'direction':direction,'source_frames':action['frames'],'loop':action.get('loop',False),'fps':fps,'duration_ms':action['duration_ms'],'canvas':[width,height]})
        (W/'progress.json').write_text(json.dumps(records,indent=2),encoding='utf8')
(W/'render-manifest.json').write_text(json.dumps({'blend':str(source),'blend_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'blender':bpy.app.version_string,'configuration':cfg,'animations':records,'review':'pending'},ensure_ascii=False,indent=2),encoding='utf8')
