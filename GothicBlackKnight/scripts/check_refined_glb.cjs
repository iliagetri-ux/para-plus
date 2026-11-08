const fs = require('fs');
const path = require('path');
const validator = require('../.deps/gltf-validator');
const out = path.resolve(__dirname, '../artifacts/refined');
(async () => {
  const bytes = fs.readFileSync(path.join(out, 'Gothic_Black_Knight.glb'));
  const result = await validator.validateBytes(new Uint8Array(bytes), {
    uri: 'Gothic_Black_Knight.glb', maxIssues: 0,
  });
  fs.writeFileSync(path.join(out, 'gltf_validator_refined.json'), JSON.stringify(result, null, 2));
  const {numErrors, numWarnings, numInfos, truncated} = result.issues;
  console.log(JSON.stringify({numErrors, numWarnings, numInfos, truncated}));
  if (result.issues.numErrors) process.exitCode = 1;
})();
