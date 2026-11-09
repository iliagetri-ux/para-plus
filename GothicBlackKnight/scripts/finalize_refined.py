"""Bind validated source, export and all inspected renders into one manifest."""
from pathlib import Path
import json,hashlib
out=Path(__file__).resolve().parents[1]/'artifacts/refined'
files=['Gothic_Black_Knight.blend','Gothic_Black_Knight.glb','preview_front.png','preview_back.png','preview_side.png','preview_perspective.png','preview_glb_reimport.png']
files.extend(p.name for p in sorted(out.glob('detail_*.png')))
check=json.loads((out/'validation_refined.json').read_text())
assert check['independent_render'] and not check['nonfinite_vertices'] and not check['degenerate_faces']
assert not check['textures_missing'] and not check['uv_missing']
gltf=json.loads((out/'gltf_validator_refined.json').read_text())
assert not gltf['issues']['numErrors'] and not gltf['issues']['truncated']
manifest={name:{'bytes':(out/name).stat().st_size,'sha256':hashlib.sha256((out/name).read_bytes()).hexdigest()} for name in files}
for name in ['Gothic_Black_Knight.blend','Gothic_Black_Knight.glb','preview_glb_reimport.png']:
    assert check['sha256'][name]==manifest[name]['sha256'], f'Revalidate changed file: {name}'
render_check=json.loads((out/'refinement_check.json').read_text())
for view in ['front','back','side','perspective']:
    assert render_check['views'][view]==manifest[f'preview_{view}.png']['sha256'], f'Rerender changed view: {view}'
check['sha256']={name:value['sha256'] for name,value in manifest.items()}
(out/'validation_refined.json').write_text(json.dumps(check,indent=2))
(out/'manifest_refined.json').write_text(json.dumps({'files':manifest,'artistic_reference_target_met':False,'status':'Validated intermediate sculptural refinement; not a finished production game asset'},indent=2))
print(json.dumps({'triangles':check['triangles'],'meshes':check['glb_meshes'],'glTF_errors':gltf['issues']['numErrors'],'glTF_warnings':gltf['issues']['numWarnings'],'files':len(files)}))
