"""Consistent mobile export from live source objects; leaves editable modifiers intact."""
import bpy,os,subprocess

def export_assets(assets,out,root):
 bpy.ops.object.select_all(action='DESELECT')
 for ob in assets:ob.select_set(True)
 saved_levels=[];temporary=[]
 try:
  for ob in assets:
   for mod in ob.modifiers:
    if mod.type=='SUBSURF':saved_levels.append((mod,mod.levels));mod.levels=0
  decor=bpy.data.objects.get('Chased tracery, rolled edges and bindings')
  reduction=decor.modifiers.new('Mobile relief density','DECIMATE');reduction.ratio=.65;temporary.append((decor,reduction))
  for ob in assets:
   mod=ob.modifiers.new('Export cap triangulation','TRIANGULATE');mod.min_vertices=5;temporary.append((ob,mod))
  bpy.ops.export_scene.gltf(filepath=out+'/GothicBlackKnight.glb',export_format='GLB',use_selection=True,export_apply=True,export_tangents=True)
  subprocess.run(['python',root+'/scripts/fix_glb_color.py',out+'/GothicBlackKnight.glb'],check=True)
  subprocess.run(['python',root+'/scripts/compact_glb.py',out+'/GothicBlackKnight.glb'],check=True)
  bpy.ops.export_scene.fbx(filepath=out+'/GothicBlackKnight.fbx',use_selection=True,apply_unit_scale=True,bake_anim=False,add_leaf_bones=False)
 finally:
  for ob,mod in reversed(temporary):ob.modifiers.remove(mod)
  for mod,level in saved_levels:mod.levels=level

if __name__=='__main__':
 root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));out=root+'/artifacts'
 bpy.ops.wm.open_mainfile(filepath=out+'/GothicBlackKnight.blend')
 export_assets([o for o in bpy.context.scene.objects if o.type=='MESH' and not o.name.startswith('STUDIO')],out,root)
