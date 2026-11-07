# Gothic Black Knight

An editable, static Gothic knight modeled in Blender 4.3.2 against [the supplied reference](docs/Reference.jpg). Current artistic fidelity remains below the reference; this is not a finished production game asset.

## Deliverables

- `artifacts/GothicBlackKnight.blend`: editable detailed surfaces, packed materials and lit studio.
- `artifacts/GothicBlackKnight.glb`: self-contained mobile mesh, 7.4 MB, 171,440 triangles, embedded PBR maps.
- `artifacts/GothicBlackKnight.usdz`: 6.0 MB Quick Look format; reopened and validated using OpenUSD. Physical iPhone testing has not been performed.
- `artifacts/GothicBlackKnight.fbx`: static interchange geometry; FBX material fidelity is not certified.
- `Preview_Front.png`, `Preview_Back.png`, `Preview_Side.png`, `Preview_Right.png`, `Preview_45.png`: real Cycles renders of the detailed source.
- `GLB_Import_Preview.png`: a separate clean-scene Blender render of the exported GLB.
- `WebGL_Mobile_Preview.png`: actual Chromium WebGL rendering at a 430×932 mobile viewport.
- `manifest.json`, `glb_import_check.json`, `webgl_check.json`, `usdz_check.json`: hashes and machine-readable validation results.

Raw model files and ZIP copies are provided. The native BLEND is more detailed than the mobile exports; ornaments and fabric subdivision are reduced during export without modifying the editable source.

## Geometry and materials

Connected shaped surfaces define armor, pointed visor, continuous crown, overlapping shoulder and hip plates, individual fingers, greaves, boots, sword and draped fabric. Foliage follows the actual armor using ray projection. The stance widens naturally toward the feet. Tailored tabards have dedicated UVs and faded heraldic pigment.

Packed color and roughness maps survive export. `fix_glb_color.py` converts the generator's linear Non-Color albedo pixels to sRGB, as required by glTF; data maps remain linear. The correction is idempotent and was checked in the independent WebGL renderer. Additional procedural Blender micro-bump is not baked into the mobile files.

## Rebuild in an agent/cloud session

```sh
python -m pip install --target GothicBlackKnight/.deps -r GothicBlackKnight/requirements-usd.txt
blender -b -t 6 --python GothicBlackKnight/scripts/build.py
blender -b -t 2 --python GothicBlackKnight/scripts/validate.py
python GothicBlackKnight/scripts/export_usdz.py
python GothicBlackKnight/scripts/package.py
```

Pillow must also be available to the `python` command used by the Blender build's GLB postprocessor. Fast art proofs use `KNIGHT_FAST=1` and write to `proof/`, preserving the current deliverables. CPU Cycles is used; this Blender build lacks OpenImageDenoise. These commands are for the agent, not work required from the iPhone user.

## Independent viewer test

`viewer/index.html` is a dependency-free local WebGL 2 GLB viewer with touch orbit/pinch controls. Serve this project directory locally on port 8766, then run `node viewer/test.cjs` with Playwright installed. It is a local verification tool, not a published website. The test uses Chromium/SwiftShader and a mobile viewport; it does not emulate iOS Safari or certify physical iPhone performance.

USDZ is generated directly from the corrected GLB through OpenUSD 26.11. The source Blender binary lacks USD support. The package was checked for uncompressed entries, 64-byte alignment, resolved texture assets and zero issues from all registered OpenUSD validators. This is not an Apple-device test.

## Remaining work

The reference has substantially more organic and ornate surfaces. Prioritize the chest and shoulder transitions, full facial relief and crown treatment, authored localized wear, irregular fabric damage, anatomical hand grasp and rear attachments. The current foliage remains repetitive and surfaces too regular. A production game pipeline also needs authored retopology, texture atlases and normal/AO baking, rigging, LODs and animation clearance testing. See `docs/ART_REVIEW.md` for the continuation checklist. Preserve this working artifact set before major sculptural edits.
