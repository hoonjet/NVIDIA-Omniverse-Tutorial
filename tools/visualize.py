"""
USD Scene Visualizer
=====================

Loads any USD stage (.usda) and renders a 3D visualization using matplotlib.
Shows geometry (cubes, spheres, planes, cylinders, meshes), lights, cameras,
skeleton joints, and physics joints in a single 3D plot.

Requires: matplotlib (pip install matplotlib)

Usage:
    cd E:\\omniverse_env
    Scripts\\activate
    python tools\\visualize.py <path-to-usda-file> [--save] [--no-show]

Examples:
    # Interactive 3D window (rotate with mouse):
    python tools\\visualize.py tutorials\\usd_advanced\\12_usd_lighting\\output\\12_usd_lighting.usda

    # Save PNG without opening window:
    python tools\\visualize.py tutorials\\usd_advanced\\13_usd_physics\\output\\13_usd_physics.usda --save --no-show

    # Visualize all tutorials at once:
    python tools\\visualize.py --all --save --no-show
"""

import sys
import os
import argparse

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from pxr import Usd, UsdGeom, UsdLux, UsdPhysics, UsdSkel
from pxr import Gf

# ── Color palette ──
COLORS = {
    "cube": "#4A90D9", "sphere": "#E87E04", "plane": "#27AE60",
    "cylinder": "#8E44AD", "mesh": "#2C3E50",
    "light_distant": "#F1C40F", "light_dome": "#F39C12",
    "light_rect": "#E74C3C", "light_sphere": "#F39C12",
    "camera": "#1ABC9C", "skeleton_joint": "#E74C3C",
    "skeleton_bone": "#C0392B", "physics_joint": "#9B59B6",
    "physics_body": "#3498DB",
}


def get_world_transform(prim, time=Usd.TimeCode.Default()):
    xformable = UsdGeom.Xformable(prim)
    return xformable.ComputeLocalToWorldTransform(time)


def transform_point(matrix, point):
    p = Gf.Vec3d(point[0], point[1], point[2])
    result = matrix.Transform(p)
    return np.array([result[0], result[1], result[2]])


def transform_points(matrix, points):
    return np.array([transform_point(matrix, p) for p in points])


# ── Geometry drawing ──

def draw_cube(ax, prim, matrix):
    cube = UsdGeom.Cube(prim)
    size = cube.GetSizeAttr().Get() or 1.0
    h = size / 2.0
    corners = np.array([
        [-h,-h,-h],[ h,-h,-h],[ h, h,-h],[-h, h,-h],
        [-h,-h, h],[ h,-h, h],[ h, h, h],[-h, h, h],
    ])
    corners = transform_points(matrix, corners)
    edges = [[0,1],[1,2],[2,3],[3,0],[4,5],[5,6],[6,7],[7,4],
             [0,4],[1,5],[2,6],[3,7]]
    for e in edges:
        ax.plot3D(corners[e,0], corners[e,1], corners[e,2],
                  color=COLORS["cube"], linewidth=1.5, alpha=0.8)
    faces = [[0,1,2,3],[4,5,6,7],[0,1,5,4],[2,3,7,6],[1,2,6,5],[0,3,7,4]]
    verts = [[corners[i] for i in f] for f in faces]
    poly = Poly3DCollection(verts, alpha=0.08, facecolor=COLORS["cube"], edgecolor='none')
    ax.add_collection3d(poly)


def draw_sphere(ax, prim, matrix):
    sphere = UsdGeom.Sphere(prim)
    radius = sphere.GetRadiusAttr().Get() or 1.0
    u = np.linspace(0, 2*np.pi, 20)
    v = np.linspace(0, np.pi, 12)
    x = radius * np.outer(np.cos(u), np.sin(v))
    y = radius * np.outer(np.sin(u), np.sin(v))
    z = radius * np.outer(np.ones(np.size(u)), np.cos(v))
    pts = np.column_stack([x.ravel(), y.ravel(), z.ravel()])
    pts = transform_points(matrix, pts)
    xt = pts[:,0].reshape(x.shape)
    yt = pts[:,1].reshape(y.shape)
    zt = pts[:,2].reshape(z.shape)
    for i in range(0, len(u), 3):
        ax.plot3D(xt[i,:], yt[i,:], zt[i,:], color=COLORS["sphere"], linewidth=0.8, alpha=0.6)
    for j in range(0, len(v), 3):
        ax.plot3D(xt[:,j], yt[:,j], zt[:,j], color=COLORS["sphere"], linewidth=0.8, alpha=0.6)


def draw_plane(ax, prim, matrix):
    plane = UsdGeom.Plane(prim)
    w = plane.GetWidthAttr().Get() or 1.0
    l = plane.GetLengthAttr().Get() or 1.0
    hw, hl = w/2, l/2
    corners = np.array([[-hw,-hl,0],[hw,-hl,0],[hw,hl,0],[-hw,hl,0]])
    corners = transform_points(matrix, corners)
    poly = Poly3DCollection([corners], alpha=0.25, facecolor=COLORS["plane"], edgecolor=COLORS["plane"])
    ax.add_collection3d(poly)
    for i in range(4):
        e = [i, (i+1)%4]
        ax.plot3D(corners[e,0], corners[e,1], corners[e,2],
                  color=COLORS["plane"], linewidth=1.5, alpha=0.8)


def draw_cylinder(ax, prim, matrix):
    cyl = UsdGeom.Cylinder(prim)
    r = cyl.GetRadiusAttr().Get() or 1.0
    h = cyl.GetHeightAttr().Get() or 1.0
    hh = h/2
    n = 16
    theta = np.linspace(0, 2*np.pi, n)
    bottom = np.column_stack([r*np.cos(theta), r*np.sin(theta), np.full(n, -hh)])
    top = np.column_stack([r*np.cos(theta), r*np.sin(theta), np.full(n, hh)])
    bottom = transform_points(matrix, bottom)
    top = transform_points(matrix, top)
    ax.plot3D(bottom[:,0], bottom[:,1], bottom[:,2], color=COLORS["cylinder"], linewidth=1.0, alpha=0.7)
    ax.plot3D(top[:,0], top[:,1], top[:,2], color=COLORS["cylinder"], linewidth=1.0, alpha=0.7)
    for i in range(0, n, 2):
        ax.plot3D([bottom[i,0], top[i,0]], [bottom[i,1], top[i,1]], [bottom[i,2], top[i,2]],
                  color=COLORS["cylinder"], linewidth=0.6, alpha=0.5)


def draw_mesh(ax, prim, matrix):
    mesh = UsdGeom.Mesh(prim)
    points = mesh.GetPointsAttr().Get()
    if not points:
        return
    pts = np.array([[p[0], p[1], p[2]] for p in points])
    pts = transform_points(matrix, pts)
    ax.scatter3D(pts[:,0], pts[:,1], pts[:,2],
                color=COLORS["mesh"], s=8, alpha=0.6, depthshade=True)
    indices = mesh.GetFaceVertexIndicesAttr().Get()
    counts = mesh.GetFaceVertexCountsAttr().Get()
    if indices and counts:
        idx = 0
        for count in counts:
            face_idx = list(indices[idx:idx+count])
            face_idx.append(face_idx[0])
            face_pts = pts[face_idx]

# ── Lights, camera, skeleton, physics ──

def draw_light(ax, prim, matrix):
    center = transform_point(matrix, [0, 0, 0])
    if UsdLux.DistantLight(prim):
        ax.scatter3D([center[0]], [center[1]], [center[2]],
                     color=COLORS["light_distant"], s=120, marker='*',
                     edgecolors='black', linewidths=0.5, zorder=10)
        # Try to get direction (may not exist in all USD versions)
        try:
            dl = UsdLux.DistantLight(prim)
            dir_attr = dl.GetAttr("light:direction")
            if dir_attr:
                d = dir_attr.Get()
                if d:
                    direction = np.array([d[0], d[1], d[2]])
                    direction = direction / (np.linalg.norm(direction) + 1e-10)
                    scale = 2.0
                    ax.quiver(center[0], center[1], center[2],
                              -direction[0]*scale, -direction[1]*scale, -direction[2]*scale,
                              color=COLORS["light_distant"], arrow_length_ratio=0.2, linewidth=2)
        except Exception:
            pass
    elif UsdLux.DomeLight(prim):
        ax.scatter3D([center[0]], [center[1]], [center[2]],
                     color=COLORS["light_dome"], s=80, marker='o',
                     edgecolors='black', linewidths=0.5, zorder=10)
        r = 1.0
        u = np.linspace(0, 2*np.pi, 12)
        v = np.linspace(0, np.pi, 8)
        x = r * np.outer(np.cos(u), np.sin(v))
        y = r * np.outer(np.sin(u), np.sin(v))
        z = r * np.outer(np.ones(np.size(u)), np.cos(v))
        pts = np.column_stack([x.ravel(), y.ravel(), z.ravel()])
        pts = transform_points(matrix, pts)
        xt = pts[:,0].reshape(x.shape)
        yt = pts[:,1].reshape(y.shape)
        zt = pts[:,2].reshape(z.shape)
        for i in range(0, len(u), 4):
            ax.plot3D(xt[i,:], yt[i,:], zt[i,:], color=COLORS["light_dome"], linewidth=0.4, alpha=0.3)
        for j in range(0, len(v), 3):
            ax.plot3D(xt[:,j], yt[:,j], zt[:,j], color=COLORS["light_dome"], linewidth=0.4, alpha=0.3)
    elif UsdLux.RectLight(prim):
        rl = UsdLux.RectLight(prim)
        w = rl.GetWidthAttr().Get() or 1.0
        h = rl.GetHeightAttr().Get() or 1.0
        hw, hh = w/2, h/2
        corners = np.array([[-hw,-hh,0],[hw,-hh,0],[hw,hh,0],[-hw,hh,0]])
        corners = transform_points(matrix, corners)
        poly = Poly3DCollection([corners], alpha=0.3, facecolor=COLORS["light_rect"],
                                edgecolor=COLORS["light_rect"])
        ax.add_collection3d(poly)
        for i in range(4):
            e = [i, (i+1)%4]
            ax.plot3D(corners[e,0], corners[e,1], corners[e,2],
                      color=COLORS["light_rect"], linewidth=1.5, alpha=0.9)
    elif UsdLux.SphereLight(prim):
        sl = UsdLux.SphereLight(prim)
        radius = sl.GetRadiusAttr().Get() or 0.5
        ax.scatter3D([center[0]], [center[1]], [center[2]],
                     color=COLORS["light_sphere"], s=80, marker='o',
                     edgecolors='black', linewidths=0.5, zorder=10)
        u = np.linspace(0, 2*np.pi, 8)
        v = np.linspace(0, np.pi, 6)
        x = radius * np.outer(np.cos(u), np.sin(v))
        y = radius * np.outer(np.sin(u), np.sin(v))


def draw_camera(ax, prim, matrix):
    center = transform_point(matrix, [0, 0, 0])
    ax.scatter3D([center[0]], [center[1]], [center[2]],
                 color=COLORS["camera"], s=60, marker='^',
                 edgecolors='black', linewidths=0.5, zorder=10)


def draw_skeleton(ax, prim, matrix):
    skel = UsdSkel.Skeleton(prim)
    joints = skel.GetJointsAttr().Get()
    if not joints:
        return
    xforms = None
    try:
        bind_attr = skel.GetBindTransformsAttr()
        xforms = bind_attr.Get()
    except Exception:
        pass
    if not xforms:
        try:
            rest_attr = skel.GetRestTransformsAttr()
            xforms = rest_attr.Get()
        except Exception:
            pass
    if not xforms:
        for j in joints:
            p = transform_point(matrix, [0, 0, 0])
            ax.scatter3D([p[0]], [p[1]], [p[2]],
                         color=COLORS["skeleton_joint"], s=30, zorder=10)
        return
    joint_positions = []
    for xf in xforms:
        try:
            t = xf.ExtractTranslation()
            p = transform_point(matrix, [t[0], t[1], t[2]])
        except Exception:
            p = transform_point(matrix, [xf[3], xf[7], xf[11]])
        joint_positions.append(p)
    joint_positions = np.array(joint_positions)
    ax.scatter3D(joint_positions[:,0], joint_positions[:,1], joint_positions[:,2],
                 color=COLORS["skeleton_joint"], s=40, zorder=10,
                 edgecolors='black', linewidths=0.3)
    joint_paths = [str(j) for j in joints]
    for i, path in enumerate(joint_paths):
        if '/' in path:
            parent_path = path.rsplit('/', 1)[0]
            if parent_path in joint_paths:
                parent_idx = joint_paths.index(parent_path)
                p1 = joint_positions[parent_idx]
                p2 = joint_positions[i]
                ax.plot3D([p1[0], p2[0]], [p1[1], p2[1]], [p1[2], p2[2]],
                         color=COLORS["skeleton_bone"], linewidth=2.5, alpha=0.8)


def draw_physics_joint(ax, prim, matrix):
    center = transform_point(matrix, [0, 0, 0])
    ax.scatter3D([center[0]], [center[1]], [center[2]],
                 color=COLORS["physics_joint"], s=50, marker='D',
                 edgecolors='black', linewidths=0.5, zorder=10)
    try:
        body0_rel = prim.GetRelationship("physics:body0")
        body1_rel = prim.GetRelationship("physics:body1")
        b0_targets = body0_rel.GetTargets() if body0_rel else []
        b1_targets = body1_rel.GetTargets() if body1_rel else []
        if b0_targets and b1_targets:
            stage = prim.GetStage()
            b0_prim = stage.GetPrimAtPath(b0_targets[0])
            b1_prim = stage.GetPrimAtPath(b1_targets[0])
            if b0_prim and b1_prim:
                m0 = get_world_transform(b0_prim)
                m1 = get_world_transform(b1_prim)
                p0 = transform_point(m0, [0, 0, 0])
                p1 = transform_point(m1, [0, 0, 0])
                ax.plot3D([p0[0], center[0], p1[0]],
                          [p0[1], center[1], p1[1]],
                          [p0[2], center[2], p1[2]],
                          color=COLORS["physics_joint"], linewidth=1.5, alpha=0.5, linestyle='--')
    except Exception:
        pass


def draw_collision_indicator(ax, prim, matrix):
    if not UsdPhysics.CollisionAPI(prim):
        return
    center = transform_point(matrix, [0, 0, 0])
    ax.scatter3D([center[0]], [center[1]], [center[2]],
                 color=COLORS["physics_body"], s=20, marker='s',
                 alpha=0.5, zorder=5)


# ── Main visualization ──

def visualize_stage(usda_path, save=False, show=True, output_dir=None):
    stage = Usd.Stage.Open(usda_path)
    if not stage:
        print(f"  ERROR: Could not open {usda_path}")
        return False

    fig = plt.figure(figsize=(12, 9))
    ax = fig.add_subplot(111, projection='3d')
    title = os.path.basename(usda_path)
    ax.set_title(f"USD Scene: {title}", fontsize=14, fontweight='bold', pad=20)

    all_points = []

    for prim in stage.Traverse():
        matrix = get_world_transform(prim)

        if prim.IsA(UsdGeom.Cube):
            draw_cube(ax, prim, matrix)
            half = (UsdGeom.Cube(prim).GetSizeAttr().Get() or 1.0) / 2.0
            all_points.append(transform_point(matrix, [half, half, half]))
            all_points.append(transform_point(matrix, [-half, -half, -half]))
        elif prim.IsA(UsdGeom.Sphere):
            draw_sphere(ax, prim, matrix)
            r = UsdGeom.Sphere(prim).GetRadiusAttr().Get() or 1.0
            all_points.append(transform_point(matrix, [r, r, r]))
            all_points.append(transform_point(matrix, [-r, -r, -r]))
        elif prim.IsA(UsdGeom.Plane):
            draw_plane(ax, prim, matrix)
            w = UsdGeom.Plane(prim).GetWidthAttr().Get() or 1.0
            l = UsdGeom.Plane(prim).GetLengthAttr().Get() or 1.0
            all_points.append(transform_point(matrix, [w/2, l/2, 0]))
            all_points.append(transform_point(matrix, [-w/2, -l/2, 0]))
        elif prim.IsA(UsdGeom.Cylinder):
            draw_cylinder(ax, prim, matrix)
            h = UsdGeom.Cylinder(prim).GetHeightAttr().Get() or 1.0
            r = UsdGeom.Cylinder(prim).GetRadiusAttr().Get() or 1.0
            all_points.append(transform_point(matrix, [r, r, h/2]))
            all_points.append(transform_point(matrix, [-r, -r, -h/2]))
        elif prim.IsA(UsdGeom.Mesh):
            draw_mesh(ax, prim, matrix)
            mesh = UsdGeom.Mesh(prim)
            pts = mesh.GetPointsAttr().Get()
            if pts:
                for p in pts:
                    all_points.append(transform_point(matrix, [p[0], p[1], p[2]]))

        if UsdLux.DistantLight(prim) or UsdLux.DomeLight(prim) or \
           UsdLux.RectLight(prim) or UsdLux.SphereLight(prim):
            draw_light(ax, prim, matrix)
            all_points.append(transform_point(matrix, [0, 0, 0]))

        if prim.IsA(UsdGeom.Camera):
            draw_camera(ax, prim, matrix)
            all_points.append(transform_point(matrix, [0, 0, 0]))

        if UsdSkel.Skeleton(prim):
            draw_skeleton(ax, prim, matrix)
            skel = UsdSkel.Skeleton(prim)
            try:
                bx = skel.GetBindTransformsAttr().Get()
                if not bx:
                    bx = skel.GetRestTransformsAttr().Get()
                if bx:
                    for xf in bx:
                        t = xf.ExtractTranslation()
                        all_points.append(transform_point(matrix, [t[0], t[1], t[2]]))
            except Exception:
                pass

    # Set axis limits based on scene bounds
    if all_points:
        all_points = np.array(all_points)
        mins = all_points.min(axis=0)
        maxs = all_points.max(axis=0)
        center = (mins + maxs) / 2.0
        extent = (maxs - mins).max() / 2.0
        margin = max(extent * 0.3, 1.0)
        ax.set_xlim(center[0] - extent - margin, center[0] + extent + margin)
        ax.set_ylim(center[1] - extent - margin, center[1] + extent + margin)
        ax.set_zlim(center[2] - extent - margin, center[2] + extent + margin)
    else:
        ax.set_xlim(-5, 5)
        ax.set_ylim(-5, 5)
        ax.set_zlim(-5, 5)

    ax.set_xlabel('X', fontsize=10)
    ax.set_ylabel('Y', fontsize=10)
    ax.set_zlabel('Z', fontsize=10)

    try:
        ax.set_box_aspect([1, 1, 1])
    except AttributeError:
        pass

    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0],[0], marker='s', color=COLORS["cube"], label='Cube',
               markersize=8, linestyle='-', linewidth=1.5),
        Line2D([0],[0], marker='o', color=COLORS["sphere"], label='Sphere',
               markersize=8, linestyle='-', linewidth=1.5),
        Line2D([0],[0], marker='s', color=COLORS["plane"], label='Plane',
               markersize=8, linestyle='-', linewidth=1.5),
        Line2D([0],[0], marker='*', color=COLORS["light_distant"], label='Light',
               markersize=10, linestyle='None'),
        Line2D([0],[0], marker='^', color=COLORS["camera"], label='Camera',
               markersize=8, linestyle='None'),
        Line2D([0],[0], marker='o', color=COLORS["skeleton_joint"], label='Skeleton',
               markersize=8, linestyle='None'),
        Line2D([0],[0], marker='D', color=COLORS["physics_joint"], label='Physics Joint',
               markersize=8, linestyle='None'),
    ]
    ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(0.0, 1.0), fontsize=8)

    plt.tight_layout()

    if save:
        if output_dir is None:
            output_dir = os.path.dirname(usda_path)
        os.makedirs(output_dir, exist_ok=True)
        base_name = os.path.splitext(os.path.basename(usda_path))[0]
        png_path = os.path.join(output_dir, f"{base_name}_viz.png")
        plt.savefig(png_path, dpi=150, bbox_inches='tight')
        print(f"  Saved: {png_path}")

    if show:
        print("  Opening interactive 3D viewer... (close window to continue)")
        plt.show()

    plt.close(fig)
    return True

def find_all_usda_files(base_dir):
    results = []
    for root, dirs, files in os.walk(base_dir):
        for f in files:
            if f.endswith(".usda"):
                results.append(os.path.join(root, f))
    return sorted(results)


def main():
    parser = argparse.ArgumentParser(
        description="Visualize a USD stage (.usda) in 3D using matplotlib")
    parser.add_argument("usda_path", nargs="?", default=None,
                        help="Path to .usda file to visualize")
    parser.add_argument("--all", action="store_true",
                        help="Visualize all .usda files in tutorials/")
    parser.add_argument("--save", action="store_true",
                        help="Save visualization as PNG")
    parser.add_argument("--no-show", action="store_true",
                        help="Do not open interactive window (use with --save)")
    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tutorials_dir = os.path.join(base_dir, "tutorials")

    if args.all:
        usda_files = find_all_usda_files(tutorials_dir)
        if not usda_files:
            print("No .usda files found under tutorials/")
            sys.exit(1)
        print(f"Found {len(usda_files)} .usda files:")
        for f in usda_files:
            print(f"\nVisualizing: {os.path.relpath(f, base_dir)}")
            visualize_stage(f, save=args.save, show=not args.no_show)
    else:
        if not args.usda_path:
            print("No .usda file specified. Available files:")
            usda_files = find_all_usda_files(tutorials_dir)
            for f in usda_files:
                print(f"  {os.path.relpath(f, base_dir)}")
            print("\nUsage: python tools\\visualize.py <path-to-usda-file> [--save] [--no-show]")
            print("       python tools\\visualize.py --all --save --no-show")
            sys.exit(1)

        usda_path = args.usda_path
        if not os.path.isabs(usda_path):
            usda_path = os.path.join(base_dir, usda_path)
        if not os.path.exists(usda_path):
            print(f"ERROR: File not found: {usda_path}")
            sys.exit(1)

        print(f"Visualizing: {usda_path}")
        visualize_stage(usda_path, save=args.save, show=not args.no_show)


if __name__ == "__main__":
    main()
