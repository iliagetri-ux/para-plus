"""Package verified artifacts for the connector's 16 MiB request limit."""
from pathlib import Path
import hashlib,json,zipfile
root=Path(__file__).resolve().parents[1];out=root/'artifacts';manifest={}
for ext in ['blend','glb','fbx']:
 p=out/f'GothicBlackKnight.{ext}'
 with zipfile.ZipFile(str(p)+'.zip','w',zipfile.ZIP_DEFLATED,9) as archive:archive.write(p,p.name)
 with zipfile.ZipFile(str(p)+'.zip') as archive:
  assert archive.testzip() is None
  assert archive.read(p.name)==p.read_bytes()
for p in sorted(out.iterdir()):
 if p.suffix in ['.png','.blend','.glb','.fbx','.zip'] and not p.name.startswith('QA_'):
  data=p.read_bytes();manifest[p.name]={'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'git_blob_sha1':hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(manifest,indent=2))
