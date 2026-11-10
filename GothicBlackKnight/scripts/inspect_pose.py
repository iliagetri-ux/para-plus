"""Inspect the saved character's rigid pieces and connected ornament groups."""
import bpy,json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'artifacts/refined/Gothic_Black_Knight.blend'))
report=[]
for o in bpy.context.scene.objects:
    if o.type!='MESH' or o.hide_render:continue
    pts=[o.matrix_world@Vector(c) for c in o.bound_box]
    report.append({'name':o.name,'v':len(o.data.vertices),'center':[round(sum(p[i] for p in pts)/8,4) for i in range(3)],'bounds':[[round(min(p[i] for p in pts),4),round(max(p[i] for p in pts),4)] for i in range(3)]})
out=ROOT/'proof/pose';out.mkdir(parents=True,exist_ok=True)
(out/'objects.json').write_text(json.dumps(report,indent=2))
for r in report:
    if not any(k in r['name'] for k in ['D2 |','chased margin','raised keel','incised line','engraved branching','inlaid scroll','forged ridge']):print(r)
