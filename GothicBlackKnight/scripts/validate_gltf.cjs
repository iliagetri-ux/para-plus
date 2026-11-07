const fs = require('fs');
const path = require('path');
const validator = require('../.deps/node_modules/gltf-validator');
const root = path.resolve(__dirname, '..');
(async () => {
 const report = await validator.validateBytes(new Uint8Array(fs.readFileSync(path.join(root,'artifacts/GothicBlackKnight.glb'))), {uri:'GothicBlackKnight.glb', maxIssues:1000});
 fs.writeFileSync(path.join(root,'artifacts/gltf_validator.json'),JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify(report.issues,null,2));
 if (report.issues.numErrors) process.exitCode=1;
})().catch(e=>{console.error(e);process.exitCode=1});
