# Surface continuation from 4526999

The next pass loads the actual saved scene from `4526999d0d75787b148da734cb5ee2e97313a39a`.
The earlier checkpoint is recoverable from Git, and superseded relief/cape data
are archived in hidden collections in the new native source. The character was
not regenerated from the original primitive construction script.

## Work and visual decisions

- Rendered 1000-pixel close-ups of armor, the sword hand and rear helmet before
  editing. They exposed tubular-looking fingers, a broad brass cuff, jagged
  projected relief margins and featureless helmet sides.
- Added fitted temple shells, hinge pins, vents, a continuous brow foundation
  and a pointed central occipital plate. Kept the existing facial lancets and
  swept crown silhouette.
- Added three overlapping plates per finger with rolled lips and small pins.
  Darkened the cuffs and finger joints; kept the original curved fingers,
  opposing thumbs and sword contact pose underneath.
- Archived the old broad foil-like acanthus patches and a copy of the merged
  tracing mesh. Removed only its fine hairline tracing components, preserving
  substantial plate edging, chain and sword binding.
- Rejected an experimental projected line ornament after close-up inspection:
  it bridged plate transitions and read as wire. Replaced it with packed
  UV-authored albedo/roughness/normal microengraving on the plate surfaces.
- Kept the connected cloak, added evolving smaller folds, narrow irregular
  tears, a finer hem, physical frayed strands and a stitched back seam. Packed
  unique 1024-square cloth maps locate abrasion around the hem and tears.
  These are authored cloth surfaces, not a cloth simulation.
- Inspected two sets of four proofs and repeated the detail views. Final
  four-view source renders use Cycles at 1280 × 1440, 64 samples and denoising.
- Full-resolution inspection exposed padding intersecting the upper-arm shell.
  Inset the padded sleeve rings by 10% without changing their joint centers or
  the outer armor silhouette, then repeated export and visual checks.

## Export

The BLEND keeps editable pieces and hidden archives. In a temporary export
scene, subdivision is evaluated at render level, UV names are normalized, and
static meshes are joined into material batches. The original saved scene is
then reopened for source rendering. This avoids thousands of small draw nodes
while retaining geometric details, UV data and portable textures. It is not
retopology or an animation rig.

The exported result has one mesh with 15 material batches and 1,150,606
triangles. This is a detailed static export, not a mobile/LOD-optimized model;
the file is about 49 MB. Native subdivision and individual details are retained.

The existing color-space correction and tangent repair are applied. The GLB
is independently imported into factory-empty Blender, checked and rendered.
Khronos validation runs with unlimited issue output. Only reports in
`artifacts/refined/` describe this version; the older FBX/USDZ are unchanged.

## Remaining limitations

This still does not match the reference's authored sculptural complexity.
The chest layering is regular and leaf-like; stronger irregular forged plate
transitions, denser bespoke relief and more natural cloth wear remain necessary.
Some helmet panel transitions remain mechanically regular, and hand topology
is still a static approximation. No rig, production retopology, texture atlas
or LOD set has been added. Successful export is not artistic completion.

Independent reimport found zero nonfinite coordinates, zero degenerate faces,
no missing UVs and no unresolved textures. Khronos validation reports zero
errors and warnings; 16 informational unused-attribute notices remain.

Rebuild entry point: `scripts/refine_surface_pass.py`. Baseline SHA-256:
`06ba4a0efa1a57774e041ea448553c7d33080cfa25238d452b524a52aba89085`.
