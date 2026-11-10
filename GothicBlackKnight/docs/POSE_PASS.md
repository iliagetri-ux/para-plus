# Pose continuation — 10 November 2026

The user identified the previous pose as unnatural. This pass opens the native
scene committed as `29494cdf6b974546e7c70f7745b0da94514f83d6`; no character parts
are regenerated. The previous pose remains recoverable from Git.

## Changes

- Shifted the pelvis toward the left support leg. The left knee has about
  5 degrees of flexion; the advanced right knee has about 27 degrees. The
  right foot turns outward and its heel lifts slightly, with the toe on the
  same contact plane as the support foot.
- Added opposing pelvis/chest rotations and a restrained downward head tilt.
- Brought the sword arm closer to the body, bending the elbow forward rather
  than presenting the forearm sideways. Rotated the free forearm so its palm
  faces more toward the body.
- Retained the curved fingers and fitted finger plates. A small wrist
  adjustment aims the sword clear of the feet. The circular grip rotates
  about its own axis to set the blade's edge alignment without translating
  the handle out of the grasp.
- Transformed armor as rigid pieces. Soft underlayers blend across joints;
  hanging cloth keeps its lower drape and clears the advanced knee.
- Matched disconnected legacy trim to its corresponding surfaces, including
  tabard borders. A side-view proof exposed borders left behind by the first
  classification; those borders now deform with their cloth.
- Explicitly attached the boot articulation trim to the feet. Nearest-surface
  matching alone assigned one high toe strip to a greave, leaving an overhang
  when the feet turned; the full-size inspection caught this.

## Review and checks

Reviewed successive front, rear, side and perspective proofs, including a
rejected edge-on sword orientation. Final source images use 1280 × 1440 Cycles
renders at 64 samples. Close-up cameras follow the posed hand and torso.

`pose_check.json` records the actual foot contact heights, blade clearance,
wrist correction, joint locations and native source hash. It checks equal
foot contact heights, blade clearance and unit-determinant armor transforms.
This is a static posed model, not an animation rig or physical balance
simulation. Numerical checks do not certify anatomy or collision-free animation.

The native source retains all 1,085 visible mesh pieces and the earlier hidden
archives. The GLB uses the existing static material batching and render-level
subdivision. Export verification independently reopens the source, imports
the GLB in an empty scene, checks geometry/UVs/textures and renders it.
The manifest binds the delivered files to those validation results.

The updated GLB has 1,150,786 triangles and 15 material batches. Independent
reimport found no nonfinite vertices, degenerate faces, missing UVs or missing
textures. Khronos validation reports zero errors and warnings, with 16
informational unused-tangent notices. The blade clears the foot contact plane
by 45.5 mm; the additional wrist correction is 2.4 degrees.

## Remaining work

The pose is revised, but the model still falls short of the reference's
sculptural detail: chest repetition, forged transitions, cloth drape and hand
anatomy need further artistic work. The close-up of the feet also shows that
some older toe-trim ends extend beyond the boot shells; their placement now
follows the feet, but the underlying trim shapes still need a fitted redesign.
Production retopology, a rig and LODs
remain absent. The older FBX/USDZ exports have not been updated.

Rebuild: `scripts/refine_pose.py`, then the validation, detail rendering and
manifest commands in the main README. The input BLEND SHA-256 is
`8e5a89b7be7aebf711d4ceed16a6febbde1ec4800908aa7513ce018deb4f23ed`.
