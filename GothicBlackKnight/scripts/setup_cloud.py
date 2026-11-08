"""Install pinned dependencies in an agent-owned Linux x64 cloud workspace."""
from pathlib import Path
import hashlib,platform,subprocess,sys,tarfile,urllib.request
ROOT=Path(__file__).resolve().parents[1];TOOLS=ROOT.parent/'tools';TOOLS.mkdir(exist_ok=True)
assert platform.system()=='Linux' and platform.machine() in ('x86_64','AMD64')
name='blender-4.3.2-linux-x64';archive=TOOLS/(name+'.tar.xz')
expected='4da1c956673c0485e63054e563ee69198cc8f80d8157dd7592dffc8a6a5592e6'
if not (TOOLS/name/'blender').exists():
 if not archive.exists():urllib.request.urlretrieve('https://download.blender.org/release/Blender4.3/'+archive.name,archive)
 assert hashlib.sha256(archive.read_bytes()).hexdigest()==expected, 'Blender archive checksum mismatch'
 with tarfile.open(archive) as package:package.extractall(TOOLS,filter='data')
subprocess.run([sys.executable,'-m','pip','install','--target',str(ROOT/'.deps'),'-r',str(ROOT/'requirements-usd.txt')],check=True)
subprocess.run(['npm','install','--prefix',str(ROOT/'.deps'),'gltf-validator@2.0.0-dev.3.10'],check=True)
print('Blender:',TOOLS/name/'blender')
print('Playwright and Chromium are also required for viewer/test.cjs; set CHROMIUM_BIN if needed.')
