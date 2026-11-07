# Visual review and continuation

Reference: [the image supplied by the user](Reference.jpg). This is a real Blender mesh project; previews are rendered from geometry. The current result remains substantially below the reference's sculptural and material sophistication. Do not describe it as a finished production asset.

## Form corrections

The knight uses connected fitted armor surfaces, a closed pointed visor, a continuous crown, overlapping shoulder and hip plates, shaped greaves and sabatons. Surface-projected chasing follows the plates. Shoulder padding, cape clearance at the back, floor contact and a progressively wider stance address earlier floating or disconnected shapes.

The latest form pass extends the mask down to the collar, shortens the exposed neck wrap, adds paired pointed plackart leaves to the breastplate, and forms angular wings and central crests on the elbow and knee plates. Individual curved fingers now include joint bands and an opposed thumb at the sword pommel. The mantle crosses the chest diagonally. A short belt suspension chain, seated shoulder rivets and faceted guard garnet have actual mesh geometry.

The cape has a shaped upper boundary, folds that change phase down its length, asymmetric width and irregular hems. A physical cloth experiment was evaluated locally but not adopted: the tested settings collapsed the silhouette or lifted the hem. `cloth_study.py` is an experiment, not part of the production build. The selected cloak is a tailored continuous surface; it is not a certified cloth simulation result.

## Export and visual checks

Portable albedo, roughness and tangent normal images are embedded. `fix_glb_color.py` converts only linear albedo buffers to sRGB and is idempotent. Export-only triangulation of polygonal caps enables tangent calculation on every normal-mapped surface. `compact_glb.py` stores normals and tangents as normalized signed 16-bit vectors using KHR_mesh_quantization; positions and UVs are unchanged. Its report records the maximum vector component error.

The browser supports these attributes and normal maps. Its screenshot comes from Chromium/SwiftShader at a 430×932 mobile viewport, not Safari or a physical iPhone. The standalone viewer is local, not a deployed website.

USDZ receives the same geometry and maps, with normal strength baked into the USD-compatible texture. OpenUSD validators initially accepted a hierarchy that Blender imported sideways; defining an explicit Geometry Xform fixed the import. The independent USDZ test now asserts upright world-space bounds and produces a real render. This catches a failure that structural validation alone missed. No Apple device or AR test has been performed.

## Remaining artistic work, in priority order

1. Sculpt less regular chest/shoulder transitions and helmet panels. The silhouette is recognizable, but the plates still read as simplified fitted shells.
2. Replace repetitive foliage with individually composed deep relief, localized dents and wear. The reference has denser, more varied ornament.
3. Refine cloak attachments, organic fraying and weight at the ground. Existing tears are still too geometric and cloth too clean.
4. Refine the hand grasp and joint clearance in close-up; inspect concealed shoulder and hip attachments.
5. Establish authored retopology, texture atlases, detail baking, rigging and LODs if the asset is to enter a game pipeline. Current exports are static posed meshes.

Numerical checks cover finite coordinates, degenerate triangles, UV presence, glTF conformance, USD package structure and resolved maps. They do not certify every mesh intersection, animation clearance or anatomical proportion.

## Continue autonomously

Read README, inspect the five full-resolution previews and the independent GLB/USDZ/WebGL images against Reference.jpg, then modify the main source in place. Preserve the last working GitHub commit. Fast proofs go into ignored `proof/`; full rebuild uses `scripts/build_all.py`. After interruption, `--resume-renders` verifies GLB/PNG hashes before skipping any view. Blender Python errors must return a nonzero exit status. Commit source after a meaningful stage, upload coherent artifacts after validation, and verify the remote tree against local blob hashes. Do not claim artistic completion based on successful file export.
