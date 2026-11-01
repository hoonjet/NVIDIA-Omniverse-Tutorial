"""
Tutorial 14: Skeletal Animation
================================

Introduces skinned character animation in USD using the UsdSkel schema set.
Creates a simple skeleton with joints, bind/rest poses, an animation with
keyframed joint rotations, a skinned mesh with joint weights, a blend shape,
and links everything together via BindingAPI.

UsdSkel is USD's system for:
  - Skeletons (joint hierarchies)
  - Skinning (deforming meshes based on joint transforms)
  - Blend shapes (morph targets like facial expressions)
  - Animation (keyframed joint transforms)

This tutorial runs on pure USD authoring APIs (no Kit, no GPU required).
The scene is written to a .usda file. To *play* the animation, open it in
USDView or Omniverse USD Composer.

Run:
    cd E:\\omniverse_env
    Scripts\\activate
    python tutorials\\usd_advanced\\14_skeletal_animation\\14_skeletal_animation.py
"""

import os
import sys

try:
    from pxr import Usd, UsdGeom, UsdSkel, Sdf, Gf, Vt
except ImportError as e:
    print("ERROR: Could not import pxr. Activate the virtual environment first:")
    print("  cd E:\\omniverse_env")
    print("  Scripts\\activate")
    raise


# ---------------------------------------------------------------------------
# 1. Skeleton (joint hierarchy + bind/rest poses)
# ---------------------------------------------------------------------------

def create_skeleton(stage, path):
    """
    A UsdSkel.Skeleton defines a hierarchy of joints with two pose sets:
      - bindTransforms: the pose at which the mesh was rigged (bind pose)
      - restTransforms:  the default pose (often same as bind)
    Each transform is a 4x4 matrix (Gf.Matrix4d).
    """
    skel = UsdSkel.Skeleton.Define(stage, path)

    # Joint names define the hierarchy (parent-child via naming convention)
    # In UsdSkel, the hierarchy is encoded in the joint path strings,
    # like a file path: "root", "root/spine", "root/spine/head", etc.
    joints = [
        "root",                # 0: root (hips)
        "root/spine",          # 1: lower spine
        "root/spine/head",     # 2: head
        "root/spine/arm_L",    # 3: left arm
        "root/spine/arm_R",    # 4: right arm
    ]
    skel.GetJointsAttr().Set(joints)

    # Bind transforms: where each joint sits in the bind (T-pose)
    # Each is a 4x4 matrix: translation + rotation
    def make_transform(translate, rotate_deg=(0, 0, 0)):
        m = Gf.Matrix4d()
        m.SetIdentity()
        m.SetTranslateOnly(Gf.Vec3d(*translate))
        # Apply rotation (XYZ Euler)
        rx, ry, rz = [Gf.DegreesToRadians(a) for a in rotate_deg]
        rot = (
            Gf.Rotation(Gf.Vec3d.XAxis(), rotate_deg[0]) *
            Gf.Rotation(Gf.Vec3d.YAxis(), rotate_deg[1]) *
            Gf.Rotation(Gf.Vec3d.ZAxis(), rotate_deg[2])
        )
        m.SetRotateOnly(rot)
        return m

    bind_transforms = [
        make_transform((0, 0, 0)),               # root
        make_transform((0, 1.0, 0)),              # spine (1m up)
        make_transform((0, 2.0, 0)),              # head (2m up)
        make_transform((0.8, 1.5, 0)),            # arm_L (left, slightly up)
        make_transform((-0.8, 1.5, 0)),           # arm_R (right)
    ]
    skel.GetBindTransformsAttr().Set(bind_transforms)

    # Rest transforms: same as bind for this example
    skel.GetRestTransformsAttr().Set(bind_transforms)

    print(f"  [Skeleton] {path} - {len(joints)} joints (root, spine, head, "
          f"arm_L, arm_R)")
    return skel


# ---------------------------------------------------------------------------
# 2. SkelAnimation (keyframed joint transforms)
# ---------------------------------------------------------------------------

def create_animation(stage, path, num_joints=5):
    """
    A UsdSkel.Animation holds keyframed joint transforms: translations,
    rotations (quaternions), and scales per joint over time.
    """
    anim = UsdSkel.Animation.Define(stage, path)

    # Joint names must match the skeleton
    joints = [
        "root", "root/spine", "root/spine/head",
        "root/spine/arm_L", "root/spine/arm_R"
    ]
    anim.GetJointsAttr().Set(joints)

    # Translations: constant per joint (no translation animation here)
    translations = [
        Gf.Vec3f(0, 0, 0),       # root
        Gf.Vec3f(0, 1.0, 0),     # spine
        Gf.Vec3f(0, 1.0, 0),     # head
        Gf.Vec3f(0.8, 0.5, 0),   # arm_L
        Gf.Vec3f(-0.8, 0.5, 0),  # arm_R
    ]
    anim.GetTranslationsAttr().Set(translations)

    # Rotations: keyframed! Different at t=0 and t=24 (1 sec at 24fps)
    # UsdSkel uses quaternions (real, i, j, k) = (w, x, y, z)
    # At t=0: arms in T-pose (identity rotation)
    rot_t0 = [
        Gf.Quatf(1, 0, 0, 0),  # root: identity
        Gf.Quatf(1, 0, 0, 0),  # spine: identity
        Gf.Quatf(1, 0, 0, 0),  # head: identity
        Gf.Quatf(1, 0, 0, 0),  # arm_L: identity (T-pose)
        Gf.Quatf(1, 0, 0, 0),  # arm_R: identity (T-pose)
    ]
    # At t=24: arms raised up (rotate arm_L by -60deg around Z, arm_R by +60deg)
    import math
    half = math.radians(60.0) / 2.0
    rot_t24 = [
        Gf.Quatf(1, 0, 0, 0),                          # root: no change
        Gf.Quatf(1, 0, 0, 0),                          # spine: no change
        Gf.Quatf(1, 0, 0, 0),                          # head: no change
        Gf.Quatf(math.cos(half), 0, 0, -math.sin(half)),   # arm_L: rotate -60 Z
        Gf.Quatf(math.cos(half), 0, 0, math.sin(half)),    # arm_R: rotate +60 Z
    ]

    rot_attr = anim.GetRotationsAttr()
    rot_attr.Set(rot_t0, time=0)
    rot_attr.Set(rot_t24, time=24)

    # Scales: all (1,1,1) (no scaling animation)
    # UsdSkel scales use half-precision Vec3h (half3[])
    scales = Vt.Vec3hArray([Gf.Vec3h(1.0, 1.0, 1.0)] * num_joints)
    anim.GetScalesAttr().Set(scales)

    print(f"  [Animation] {path} - 5 joints, arms raise over frames 0->24")
    return anim


# ---------------------------------------------------------------------------
# 3. Skinned mesh (geometry + joint influences)
# ---------------------------------------------------------------------------

def create_skinned_mesh(stage, path, skeleton_path):
    """
    Creates a simple mesh (a capsule-like shape using points) and binds it
    to the skeleton via joint indices and weights primvars.

    Each vertex has:
      - jointIndices: which joints influence it (up to 4 typically)
      - jointWeights: how much each joint influences it (must sum to 1)
    """
    # Create a simple mesh: a vertical "spine" of points
    mesh = UsdGeom.Mesh.Define(stage, path)

    # 5 vertices forming a vertical line (simplified character spine)
    points = [
        Gf.Vec3f(0, 0, 0),      # 0: root level
        Gf.Vec3f(0, 0.5, 0),    # 1: lower spine
        Gf.Vec3f(0, 1.0, 0),    # 2: spine
        Gf.Vec3f(0, 1.5, 0),    # 3: upper spine
        Gf.Vec3f(0, 2.0, 0),    # 4: head
    ]
    mesh.GetPointsAttr().Set(points)

    # Simple face (a line strip won't render; use a triangle fan from origin)
    # For simplicity, connect consecutive points as degenerate faces
    face_counts = [3, 3, 3]
    face_indices = [0, 1, 2, 1, 2, 3, 2, 3, 4]
    mesh.GetFaceVertexCountsAttr().Set(face_counts)
    mesh.GetFaceVertexIndicesAttr().Set(face_indices)

    # --- Skinning data via BindingAPI ---
    binding = UsdSkel.BindingAPI.Apply(mesh.GetPrim())

    # Link mesh to skeleton
    binding.CreateSkeletonRel().SetTargets([skeleton_path])

    # Geom bind transform: the mesh's transform in bind space (identity here)
    binding.CreateGeomBindTransformAttr().Set(Gf.Matrix4d().SetIdentity())

    # Skinning method: classic linear blend skinning (LBS)
    binding.CreateSkinningMethodAttr().Set("classicLinear")

    # Joint influences: each vertex influenced by 2 joints
    # (max 4 influences per vertex is the standard; we use 2)
    num_influences_per_vertex = 2

    # Joint indices (which joints affect each vertex)
    # Matches the skeleton's joint order: root=0, spine=1, head=2, arm_L=3, arm_R=4
    joint_indices = Vt.IntArray([
        0, 1,  # vertex 0: root + spine
        0, 1,  # vertex 1: root + spine
        1, 2,  # vertex 2: spine + head
        1, 2,  # vertex 3: spine + head
        2, 2,  # vertex 4: head only (weight 1.0 on head)
    ])

    # Joint weights (how much each joint influences the vertex; must sum to 1)
    joint_weights = Vt.FloatArray([
        0.5, 0.5,  # vertex 0: 50% root, 50% spine
        0.3, 0.7,  # vertex 1: 30% root, 70% spine
        0.5, 0.5,  # vertex 2: 50% spine, 50% head
        0.3, 0.7,  # vertex 3: 30% spine, 70% head
        0.0, 1.0,  # vertex 4: 100% head
    ])

    # Set joint indices and weights as primvars (constant interpolation:
    # all vertices share the same influence structure)
    indices_primvar = binding.CreateJointIndicesPrimvar(
        False, num_influences_per_vertex
    )
    indices_primvar.Set(joint_indices)

    weights_primvar = binding.CreateJointWeightsPrimvar(
        False, num_influences_per_vertex
    )
    weights_primvar.Set(joint_weights)

    print(f"  [Mesh] {path} - 5 verts, skinned to {skeleton_path}")
    print(f"         {num_influences_per_vertex} influences/vertex, LBS skinning")
    return mesh, binding


# ---------------------------------------------------------------------------
# 4. BlendShape (morph target)
# ---------------------------------------------------------------------------

def create_blend_shape(stage, path):
    """
    A UsdSkel.BlendShape defines a morph target: a set of point offsets
    that deform the mesh when the blend shape weight is > 0.
    Common use: facial expressions (smile, blink, etc.)
    """
    bs = UsdSkel.BlendShape.Define(stage, path)

    # Offsets: how much each point moves when weight = 1.0
    # Here we create a "wave" deformation (shift the top points sideways)
    offsets = [
        Gf.Vec3f(0, 0, 0),      # vertex 0: no move
        Gf.Vec3f(0, 0, 0),      # vertex 1: no move
        Gf.Vec3f(0.1, 0, 0),    # vertex 2: shift right
        Gf.Vec3f(0.2, 0, 0),    # vertex 3: shift right more
        Gf.Vec3f(0.3, 0, 0),    # vertex 4: shift right most
    ]
    bs.GetOffsetsAttr().Set(offsets)

    print(f"  [BlendShape] {path} - 5 offsets (wave deformation)")
    return bs


# ---------------------------------------------------------------------------
# 5. Link animation source and blend shapes via BindingAPI
# ---------------------------------------------------------------------------

def link_animation_and_blendshapes(mesh_prim, anim_path, blendshape_path):
    """Connect the mesh to its animation source and blend shape targets."""
    binding = UsdSkel.BindingAPI(mesh_prim)

    # Animation source: which SkelAnimation drives this mesh's skeleton
    binding.CreateAnimationSourceRel().SetTargets([anim_path])

    # Blend shape targets: map blend shape names to BlendShape prims
    binding.CreateBlendShapeTargetsRel().SetTargets([blendshape_path])
    # Blend shape names (the names used in the animation's blendShape weights)
    binding.CreateBlendShapesAttr().Set(["wave"])

    print(f"  [Link] AnimationSource -> {anim_path}")
    print(f"  [Link] BlendShape 'wave' -> {blendshape_path}")


# ---------------------------------------------------------------------------
# 6. Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 80)
    print("Tutorial 14: Skeletal Animation")
    print("=" * 80)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "output")
    os.makedirs(output_dir, exist_ok=True)
    usd_file = os.path.join(output_dir, "14_skeletal_animation.usda")

    if os.path.exists(usd_file):
        os.remove(usd_file)

    stage = Usd.Stage.CreateNew(usd_file)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)

    # Set time range for animation playback
    stage.SetStartTimeCode(0)
    stage.SetEndTimeCode(24)  # 1 second at 24fps

    world = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(world.GetPrim())

    print("\n[1/6] Creating SkelRoot (required container)...")
    # UsdSkel.Root is required to contain skinned prims
    skel_root = UsdSkel.Root.Define(stage, "/World/Character")
    print("  [SkelRoot] /World/Character")

    print("\n[2/6] Creating skeleton...")
    skeleton = create_skeleton(stage, "/World/Character/Skeleton")

    print("\n[3/6] Creating animation...")
    anim = create_animation(stage, "/World/Character/Animation")

    print("\n[4/6] Creating skinned mesh...")
    mesh, binding = create_skinned_mesh(
        stage, "/World/Character/Body", "/World/Character/Skeleton"
    )

    print("\n[5/6] Creating blend shape...")
    blendshape = create_blend_shape(
        stage, "/World/Character/BlendShapes/Wave"
    )

    print("\n[6/6] Linking animation and blend shapes...")
    link_animation_and_blendshapes(
        mesh.GetPrim(),
        "/World/Character/Animation",
        "/World/Character/BlendShapes/Wave"
    )

    print("\n[7/7] Saving stage...")
    stage.GetRootLayer().Save()
    print(f"\n  [OK] Stage saved to: {usd_file}")

    # --- Verification ---
    print("\n--- Verification: UsdSkel prims in stage ---")
    for p in stage.Traverse():
        prim = stage.GetPrimAtPath(p.GetPath())
        if UsdSkel.Skeleton(prim):
            joints = UsdSkel.Skeleton(prim).GetJointsAttr().Get()
            print(f"  Skeleton  {p.GetPath()}: {len(joints)} joints")
        elif UsdSkel.Animation(prim):
            joints = UsdSkel.Animation(prim).GetJointsAttr().Get()
            rot_attr = UsdSkel.Animation(prim).GetRotationsAttr()
            times = rot_attr.GetTimeSamples()
            print(f"  Animation {p.GetPath()}: {len(joints)} joints, "
                  f"{len(times)} keyframes at t={list(times)}")
        elif UsdSkel.BlendShape(prim):
            offsets = UsdSkel.BlendShape(prim).GetOffsetsAttr().Get()
            print(f"  BlendShape {p.GetPath()}: {len(offsets)} offsets")
        elif UsdSkel.Root(prim):
            print(f"  SkelRoot  {p.GetPath()}")
        elif UsdSkel.BindingAPI(prim):
            skel_rel = UsdSkel.BindingAPI(prim).GetSkeletonRel().GetTargets()
            anim_rel = UsdSkel.BindingAPI(prim).GetAnimationSourceRel().GetTargets()
            method = UsdSkel.BindingAPI(prim).GetSkinningMethodAttr().Get()
            print(f"  Binding   {p.GetPath()}: skel={skel_rel}, "
                  f"anim={anim_rel}, method={method}")

    # Verify joint influences
    mesh_prim = stage.GetPrimAtPath("/World/Character/Body")
    ba = UsdSkel.BindingAPI(mesh_prim)
    indices_pv = ba.GetJointIndicesPrimvar()
    weights_pv = ba.GetJointWeightsPrimvar()
    if indices_pv and weights_pv:
        print(f"\n  Joint indices primvar: {indices_pv.GetName()} "
              f"(elementSize={indices_pv.GetElementSize()})")
        print(f"  Joint weights primvar: {weights_pv.GetName()} "
              f"(elementSize={weights_pv.GetElementSize()})")

    # Verify animation has time samples
    anim_prim = stage.GetPrimAtPath("/World/Character/Animation")
    rot_attr = UsdSkel.Animation(anim_prim).GetRotationsAttr()
    print(f"\n  Rotation keyframes: {rot_attr.GetTimeSamples()}")
    rot_t0 = rot_attr.Get(time=0)
    rot_t24 = rot_attr.Get(time=24)
    print(f"  Rotations at t=0:  arm_L quat = {rot_t0[3]}")
    print(f"  Rotations at t=24: arm_L quat = {rot_t24[3]} (arms raised)")

    print(f"\nOutput file: {usd_file}")
    print("Open in USDView or Omniverse USD Composer to see the skinned")
    print("character animate. The arms raise from T-pose over frames 0->24.")
    print("=" * 80)
    print("Tutorial 14 complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()


