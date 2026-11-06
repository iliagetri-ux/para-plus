# Gothic Black Knight

Work in progress, modeled and rendered in Blender 4.3.2 in a cloud environment. Based on the knight reference supplied in the Codex conversation. This is a static posed character study, **not a finished production game asset**.

## Files

- `artifacts/GothicBlackKnight.blend`: editable surfaces, materials, studio and camera.
- `artifacts/GothicBlackKnight.glb`: self-contained mesh and PBR image materials.
- `artifacts/GothicBlackKnight.fbx`: static mesh interchange; shader fidelity is not guaranteed.
- `artifacts/Preview_Front.png`, `Preview_Back.png`, `Preview_Side.png` (left), `Preview_Right.png`, `Preview_45.png`: actual Cycles renders.
- `artifacts/GLB_Import_Preview.png`: independent render after importing exported GLB into a clean Blender scene.
- `artifacts/glb_import_check.json`: import, finite vertex, degenerate face and UV checks.
- `scripts/build.py`: deterministic complete reconstruction pipeline.
- `scripts/validate.py`: independent GLB import and render check.

## Construction

Armor is built from connected ring surfaces, shaped shoulder patches and separate fitted articulated plates. Cape and split tabard are continuous draped quad surfaces with thickness. Individual fingers, full enclosed helmet, crown, blade, guard and wrapped grip are modeled. Foliate chasing is ray-projected onto armor surfaces and consolidated into a decorative mesh. This is not a cloud of stock primitives. Deliberate overlaps between plates remain; the character is not one watertight printable solid.

PBR metallic/roughness materials include packed albedo and roughness images. The Blender source additionally uses procedural fine bump, which is not baked into the GLB. No external texture downloads are needed for GLB. Meshes have automatically packed UVs; these are not final artist-authored UV layouts.

## Reproduce in an agent/cloud session

```sh
blender -b -t 6 --python GothicBlackKnight/scripts/build.py
blender -b -t 2 --python GothicBlackKnight/scripts/validate.py
```

These commands are instructions for the next agent, not work required from the iPhone user. Denoising is disabled because this environment's Blender build lacks OpenImageDenoise. Rendering is CPU Cycles. Rebuild overwrites the named outputs; preserve working artifacts before major changes.

## Remaining art and engineering work

The reference has much more organic plate shaping, dense worn relief, richer cloth distress and a more natural asymmetric pose. The current sculpt remains more regular and stylized. Priorities:

1. Further sculpt the helmet/brow and shoulder transitions against the reference; improve palm/thumb anatomy and grasp.
2. Replace repetitive spirals with authored gothic foliage and localized wear. Refine chest/hip plate silhouettes and back attachments.
3. Sculpt irregular cloth folds and tears; add the faded heraldry from the reference.
4. Retopologize and bake relief/normal/AO maps to a lower resolution game mesh. Add deliberate UV seams and texture atlases.
5. Inspect armor collision clearance in animation; add skeleton, skinning, LODs and engine integration tests.

A valid GLB import and clean numeric checks do not certify absence of all intersections or production readiness. No claim is made of exact reference matching, completed rigging, or a mobile-browser compatibility test.

## GitHub delivery

The GitHub connector limits each request to 16 MiB including base64 overhead. Model binaries are therefore stored in individual `.blend.zip`, `.glb.zip`, and `.fbx.zip` archives in the repository; each archive contains its original named file. PNG previews and source files are stored directly. ZIP integrity and per-file SHA-256 hashes are recorded in `artifacts/manifest.json`.
