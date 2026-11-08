# Gothic Black Knight

## Current continuation — 2026-11-09

The new reference is [Reference_2026-11-09.png](docs/Reference_2026-11-09.png).
The latest continuation is in **[artifacts/refined/](artifacts/refined/)**:
[BLEND](artifacts/refined/Gothic_Black_Knight.blend),
[GLB](artifacts/refined/Gothic_Black_Knight.glb),
[front](artifacts/refined/preview_front.png),
[back](artifacts/refined/preview_back.png),
[side](artifacts/refined/preview_side.png),
[perspective](artifacts/refined/preview_perspective.png).

This pass opens the existing saved BLEND from `92c98ee`; it does not rebuild the
character from primitives. It adds swept helmet blades, articulated pointed
breast/shoulder/hip plates, engraving and portable localized wear maps, reshapes
the original cape, and reposes the existing forearm and sword. Superseded forms
are retained in a hidden archive collection. The previous artifact set below is
unchanged. The new source and GLB contain no ground or environment geometry.

**This remains an intermediate static character study, below the supplied
reference's sculptural detail and production-game quality.** See
[continuation review](docs/REFINEMENT_2026-11-09.md). Legacy FBX/USDZ files and
legacy validation reports describe the previous version only.

Reproduce with official Blender 4.5.3 LTS and a Python interpreter with Pillow:

```powershell
$env:KNIGHT_PYTHON = 'path/to/python.exe'
blender -b --python-exit-code 1 --python GothicBlackKnight/scripts/refine_saved.py
blender -b --python-exit-code 1 --python GothicBlackKnight/scripts/validate_refined.py
node GothicBlackKnight/scripts/check_refined_glb.cjs
python GothicBlackKnight/scripts/finalize_refined.py
```

The Node check expects `gltf-validator` unpacked into `GothicBlackKnight/.deps/gltf-validator`.
Set `KNIGHT_PROOF=1` for reduced proofs under ignored `proof/refinement/`.
Only the reports inside `artifacts/refined/` apply to this continuation.

## Previous checkpoint

An editable, static Gothic knight modeled in Blender 4.3.2 against [the supplied reference](docs/Reference.jpg). Current artistic fidelity remains below the reference; this is not a finished production game asset.

## Deliverables

- `artifacts/GothicBlackKnight.blend`: editable detailed surfaces, packed materials and lit studio.
- `artifacts/GothicBlackKnight.glb`: self-contained mobile mesh, embedded PBR maps and explicit tangent frames; exact size and triangle count are recorded in `webgl_check.json`.
- `artifacts/GothicBlackKnight.usdz`: Quick Look format; reopened and validated using OpenUSD and independently imported/rendered in Blender. Physical iPhone testing has not been performed.
- `artifacts/GothicBlackKnight.fbx`: static interchange geometry, independently reimported; FBX material fidelity is not certified.
- `Preview_Front.png`, `Preview_Back.png`, `Preview_Side.png`, `Preview_Right.png`, `Preview_45.png`: real Cycles renders of the detailed source.
- `GLB_Import_Preview.png` and `USDZ_Import_Preview.png`: separate clean-scene Blender renders of the exported files.
- `WebGL_Mobile_Preview.png`: actual Chromium WebGL rendering at a 430×932 mobile viewport.
- `manifest.json`, `render_check.json`, `pipeline_check.json`, `glb_import_check.json`, `gltf_validator.json`, `webgl_check.json`, `usdz_check.json`, `usdz_import_check.json`, `fbx_import_check.json`: hashes and machine-readable validation results.

Raw model files and ZIP copies are provided. The native BLEND is more detailed than the mobile exports; ornaments and fabric subdivision are reduced during export without modifying the editable source.

## Geometry and materials

Connected shaped surfaces define armor, pointed visor, continuous crown, overlapping shoulder and hip plates, curved articulated fingers, opposed thumbs, pointed elbow/knee wings, greaves, boots, sword and draped fabric. Broad, lobed acanthus leaves and their center veins are composed per armor plate and seated onto its surface by ray projection; `scripts/relief.py` generates these relief surfaces. The left pauldron has a stronger raised silhouette, while the greaves use a single tibial crest rather than regular radial fluting. The stance widens naturally toward the feet. Tailored tabards have dedicated UVs and faded heraldic pigment.

Packed color, roughness and tangent normal maps survive export. The chest now has two fitted pointed plackart leaves, the helmet reaches the collar, and the cape gathers around a shaped neckline. A seated garnet and suspension chain complete the weapon and belt details. `fix_glb_color.py` converts the generator's linear Non-Color albedo pixels to sRGB, as required by glTF; data maps remain linear. The correction is idempotent and was checked in the independent WebGL renderer. The cape has continuous UVs with a finer fabric scale, and the cloth maps use restrained stochastic grain. Normal maps use 256² tileable images, explicit glTF tangents and the same source data in USDZ; glTF normal strength is baked into the USDZ texture to follow UsdPreviewSurface requirements.

Vector frames use KHR_mesh_quantization (normalized signed 16-bit normals/tangents) to reduce mobile download size without changing positions. Polygonal caps are triangulated only for export so every normal-mapped primitive receives a tangent frame.

## Rebuild in an agent/cloud session

```sh
python GothicBlackKnight/scripts/setup_cloud.py
python GothicBlackKnight/scripts/build_all.py
```

`setup_cloud.py` installs official Linux x64 Blender 4.3.2 after checking its pinned SHA-256, plus OpenUSD, Pillow and Khronos glTF Validator. The official Blender includes OpenImageDenoise and USD import. Set `BLENDER_BIN` to override it. Playwright and Chromium must be available for the browser check (`CHROMIUM_BIN` overrides the executable).

The pipeline defaults to 1024×1280 Cycles views with 48 samples and denoising. `KNIGHT_PREVIEW_SCALE` and `KNIGHT_SAMPLES` control preview cost; the latest delivery uses 768×960 and 24 samples, recorded in `render_check.json`. It checks glTF, independently reimports GLB and USDZ, tests WebGL, and packages the artifacts. Blender scripts use `--python-exit-code 1` so errors fail the pipeline. After interruption, `build_all.py --resume-renders` reuses only views whose PNG, native BLEND and source-GLB hashes match; it then reruns export validation and packaging. `render_check.json` records per-view hashes.

Fast art proofs use `KNIGHT_FAST=1` and optional `KNIGHT_FAST_VIEWS=Front,45,Back`; they write to `proof/`, preserving deliverables. These commands are for the cloud agent, not work required from the iPhone user.

## Independent viewer test

`viewer/index.html` is a dependency-free local WebGL 2 GLB viewer with touch orbit/pinch controls. Run `node viewer/test.cjs` with Playwright installed; the test serves project files through intercepted local browser requests, without an external server. It is a local verification tool, not a published website. The test uses Chromium/SwiftShader and a mobile viewport; it does not emulate iOS Safari or certify physical iPhone performance.

USDZ is generated directly from the corrected GLB through OpenUSD 26.11. Conversion is followed by an independent import in the official Blender build. An explicit geometry Xform preserves the stage axis conversion in Blender; the import test checks upright world-space bounds. The package is checked for uncompressed entries, 64-byte alignment, resolved texture assets and zero issues from all registered OpenUSD validators. This is not an Apple-device test.

## Remaining work

The reference has substantially more organic and ornate surfaces. Prioritize the chest and shoulder transitions, full facial relief and crown treatment, authored localized wear, irregular fabric damage, anatomical hand grasp and rear attachments. The current foliage remains repetitive and surfaces too regular. A production game pipeline also needs authored retopology, texture atlases and normal/AO baking, rigging, LODs and animation clearance testing. See `docs/ART_REVIEW.md` for the continuation checklist. Preserve this working artifact set before major sculptural edits.
