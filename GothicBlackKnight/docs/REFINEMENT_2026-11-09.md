# Continuation review — 2026-11-09

## Repository analysis

The model branch was `art/gothic-black-knight`, at
`92c98eefedf760f42ad7a9bf96388e32fc80c7df` (2026-11-08). Eleven model commits
were examined, from `6bcf3d3` through the latest relief/fabric pass. Main and
backup-before-v2 contain the unrelated Para Plus web application; no model work
was found there. The existing model branch contains BLEND, GLB, FBX and USDZ,
five source previews, independent import previews, Python generation/export/
validation scripts and a local WebGL viewer. There is no OBJ in the checkout.

The latest saved Blender source was usable and is the input of this continuation.
It already has shaped armor shells, fitted limbs, individual fingers, cloth UVs,
portable texture maps, relief, sword and small fittings. These were retained.
The stored `docs/Reference.jpg` depicts a different crowned knight with a
vertical sword and chest mantle. The newly attached reference is preserved as
`docs/Reference_2026-11-09.png` and drives this pass.

## Art iterations

1. Opened the previous source and inspected its front, back and perspective
   renders. Added broad swept crown blades, cheek and brow armor, layered
   shoulder blades, chevron breastplates, long waist flanges, fanned hip lames,
   forearm/knee blades, a broader sword and folded side cloth. Preserved older
   crown and mantle pieces in a hidden collection. Removed the studio floor.
2. Inspected four 520-pixel-wide Cycles proofs. Reduced the tall crown tips;
   added UV-aligned patina, fine scratches and edge wear using packed albedo,
   roughness and normal maps. Added surface-following engraved branching scrolls.
   Lowered the original right forearm and transformed its fingers and thumb
   together. Moved the sword into the grip in a diagonal carrying pose.
3. Inspected the second four-view proofs. Corrected detached merged ornament
   components near the moved forearm. Produced the full-resolution artifact set.
4. Independent checks found zero tangent frames on 28 bevel/UV corners and 11
   microscopic collapsed triangles at horn tips. Added an orthonormal tangent
   fallback to the export pipeline and removed unnecessary bevels on already
   smooth horn tapers. Closed the exposed clavicle transition with paired fitted
   plates, then regenerated the source, GLB and all four full-resolution views.
   Repeated native reopening and independent GLB import/material rendering.

All preview images are actual Blender geometry renders. No generated concept
image was substituted for a model render. Transparent PNG backgrounds contain
no ground plane. Cameras and lights are studio utilities; the GLB exports only
the visible character meshes. The native source keeps eight archived original
objects hidden for reversible editing.

## Limits and next work

The new silhouette and sword pose are closer to the new reference. The result
still lacks the reference's irregular sculptural integration, dense individually
authored relief and convincing accumulated wear. Some shapes are visibly
procedural; bilateral symmetry remains strong. Cloth folds are authored mesh
surfaces, not physically simulated drapery; hems and tears remain too regular.
Hand contact is visually assessed for this static pose, not certified for animation.

This is **not a completed AAA/game-ready asset**. It has no deformation rig,
production retopology, atlas baking or LODs. Further sculpting and art direction,
especially helmet/shoulder integration, natural fabric damage, hands and bespoke
ornament, are needed. The export checks establish usability, not reference parity.

## Reproducibility and delivery

`scripts/refine_saved.py` opens the preserved source rather than running
`build.py`. `scripts/validate_refined.py` reopens the new BLEND, imports the new
GLB into factory-empty Blender, checks finite geometry/UVs/texture resolution,
and renders the imported model. `scripts/check_refined_glb.cjs` runs Khronos
glTF validation. New results are isolated under `artifacts/refined/`; the old
FBX/USDZ and their checks have not been regenerated and do not represent this pass.

Blender: official Windows 4.5.3 LTS portable build. Download SHA-256:
`6b657c8bdd3a7b65b07b9e1ae17eb4be7dd4aa23121da7f3d3354fc2551330a7`.
Final render settings: Cycles, CUDA GTX 1050 Ti, 48 samples, denoising,
1280 × 1440 pixels. See the accompanying machine-readable reports for actual
file hashes and validation counts.

The tangent repair changes only undefined tangent frames; it leaves geometry,
normals, indices, UVs and images unchanged. The glTF validator is run with an
unlimited issue count, so informational unused-UV/tangent notices cannot hide
later errors. Such notices on untextured metal trim are retained in the report.
