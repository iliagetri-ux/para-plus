# Visual review and continuation

Reference: the crowned black knight image supplied in this Codex conversation. The original image attachment is not present as a local project file.

Actual rendered views were inspected: front, back, left, right, three-quarter, and an independent GLB import render. This was visual inspection of the actual Blender images, not image generation.

Corrections made during this session:

- Replaced cone-like pauldrons with curved overlapping shells; then reduced their upper opening and corrected the mirrored surface winding.
- Lowered the right wrist to contact the sword pommel.
- Projected fine chasing onto plate surfaces and reduced decorative cross-section density.
- Added exportable albedo/roughness image maps.
- Brought the cape's upper edge against the back/shoulder region and introduced broader asymmetrical folds.
- After inspecting the rear render, moved the upper drape outward below its attachment to remove visible backplate penetration. A separate low-resolution rear render confirmed the correction.
- Raised studio floor to the soles; the initial images had a visible small clearance under the boots.

The reference remains substantially more sophisticated than this asset. Current weaknesses: rigid stance; overly regular chest and limb surfaces; crown spikes and round helmet silhouette; repetitive surface motifs instead of authored relief; cape still too regular and clean; automatic UVs; no baked detail/LOD/rig pipeline. Do not represent this checkpoint as meeting the user's final quality criterion.

Next session: read README and this file, retrieve the model ZIPs, inspect the blend and all final PNGs, then prioritize sculpted shoulder/chest/helmet transitions and authored cloth damage. Preserve these artifacts while making changes. Re-run `scripts/validate.py` and `scripts/package.py` after rebuilding. Confirm remote branch contents and blob hashes before claiming uploads succeeded.

The inner shoulder articulation still needs a fitted padded support and more convincing collar attachment; the three-quarter view remains the best diagnostic view for this area.

## Subsequent form and mobile-export pass

The supplied reference is now preserved as `Reference.jpg`. Replaced the round helmet/brow with a ridged angular faceplate and a connected ogival crown. Added fitted shoulder padding, curved breast shaping, pointed tasset hems, progressive leg stance widening, larger asymmetric cloth folds and faded heraldry. Replaced the spiral grid with surface-projected branching foliage. Inspect all five updated source renders and the new independent WebGL image before further edits.

Mobile GLB uses reduced fabric tessellation and relief density. Its linear albedo images initially rendered too dark in WebGL; `fix_glb_color.py` now performs the required sRGB conversion and marks the GLB so it cannot be applied twice. Do not remove this postprocessing step while the generator uses Non-Color albedo buffers. Blender renders and the exported GLB use different tessellation levels and studio lighting; compare material behavior accordingly.

OpenUSD is installed project-locally, enabling USDZ without Blender USD support. `export_usdz.py` rejects unexpected node transforms instead of silently dropping them. If the model is rigged or hierarchy transforms are introduced, extend that exporter before running it. The current USDZ passed all registered OpenUSD validators and package/texture checks. No physical iPhone or AR session was tested.

Next art priorities: less tubular vambraces and shin plates, individually composed relief on the breastplate and mask, more convincing shoulder/neck attachments, finer organic fabric erosion, varied armor thickness and hand gripping anatomy. The source still reads more stylized and regular than the reference. Do not equate successful export or mobile rendering with reaching the user's artistic target.
