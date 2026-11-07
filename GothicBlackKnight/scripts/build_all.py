"""Rebuild or resume renders, then validate and package without manual Blender work."""
from pathlib import Path
import os,subprocess,sys,json,time,argparse
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--resume-renders',action='store_true');args=parser.parse_args()
official=ROOT.parent/'tools'/'blender-4.3.2-linux-x64'/'blender'
blender=os.environ.get('BLENDER_BIN',str(official) if official.exists() else 'blender')
env=dict(os.environ);env['KNIGHT_DENOISE']='1' if Path(blender)==official else env.get('KNIGHT_DENOISE','0')
def blend(script,threads=4):return [blender,'-b','-t',str(threads),'--python-exit-code','1','--python',str(ROOT/'scripts'/script)]
steps=[('resume studio views' if args.resume_renders else 'model and five renders',blend('render_saved.py' if args.resume_renders else 'build.py')),('Khronos glTF validation',['node',str(ROOT/'scripts/validate_gltf.cjs')]),('independent GLB import',blend('validate.py',2)),('USDZ export and validation',[sys.executable,str(ROOT/'scripts/export_usdz.py')]),('independent USDZ import',blend('validate_usdz.py',2)),('WebGL mobile viewport',['node',str(ROOT/'viewer/test.cjs')]),('archive integrity and hashes',[sys.executable,str(ROOT/'scripts/package.py')])]
report={'blender':blender,'denoising':env['KNIGHT_DENOISE']=='1','resumed':args.resume_renders,'steps':[]}
for name,command in steps:
 start=time.time();print('START',name,flush=True)
 result=subprocess.run(command,env=env,cwd=ROOT)
 report['steps'].append({'name':name,'exit_code':result.returncode,'seconds':round(time.time()-start,2)})
 (ROOT/'artifacts'/'pipeline_check.json').write_text(json.dumps(report,indent=2)+'\n')
 if result.returncode:sys.exit(result.returncode)
 print('PASS',name,flush=True)
