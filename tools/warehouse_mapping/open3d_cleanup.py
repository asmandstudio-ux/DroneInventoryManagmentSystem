import argparse
from pathlib import Path

import numpy as np
import open3d as o3d


def _read_any(path: Path) -> tuple[o3d.geometry.TriangleMesh, bool]:
    mesh = o3d.io.read_triangle_mesh(str(path))
    if mesh is not None and len(mesh.vertices) > 0 and len(mesh.triangles) > 0:
        return mesh, True

    pcd = o3d.io.read_point_cloud(str(path))
    if pcd is None or len(pcd.points) == 0:
        raise ValueError(f"Failed to read mesh/pointcloud from: {path}")

    pcd.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.2, max_nn=50))
    pcd.normalize_normals()
    mesh, _ = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(pcd, depth=9)
    bbox = pcd.get_axis_aligned_bounding_box()
    mesh = mesh.crop(bbox)
    return mesh, False


def cleanup_mesh(mesh: o3d.geometry.TriangleMesh) -> o3d.geometry.TriangleMesh:
    mesh.remove_duplicated_vertices()
    mesh.remove_duplicated_triangles()
    mesh.remove_degenerate_triangles()
    mesh.remove_unreferenced_vertices()
    mesh.remove_non_manifold_edges()
    mesh.compute_triangle_normals()
    mesh.compute_vertex_normals()
    return mesh


def simplify(mesh: o3d.geometry.TriangleMesh, target_tris: int) -> o3d.geometry.TriangleMesh:
    if target_tris <= 0:
        return mesh
    if len(mesh.triangles) <= target_tris:
        return mesh
    simplified = mesh.simplify_quadric_decimation(target_tris)
    simplified.remove_degenerate_triangles()
    simplified.remove_unreferenced_vertices()
    simplified.compute_triangle_normals()
    simplified.compute_vertex_normals()
    return simplified


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--in", dest="inp", required=True, help="Input mesh (.ply/.obj/.glb/.gltf) or point cloud (.ply/.pcd)")
    p.add_argument("--out", dest="out", required=True, help="Output mesh path (recommended: .ply)")
    p.add_argument("--target-tris", dest="target_tris", type=int, default=0, help="If set, simplify to ~N triangles")
    args = p.parse_args()

    inp = Path(args.inp).expanduser().resolve()
    out = Path(args.out).expanduser().resolve()

    mesh, was_mesh = _read_any(inp)
    mesh = cleanup_mesh(mesh)
    mesh = simplify(mesh, args.target_tris)

    out.parent.mkdir(parents=True, exist_ok=True)

    if out.suffix.lower() in {".ply", ".obj", ".stl", ".off"}:
        ok = o3d.io.write_triangle_mesh(str(out), mesh, write_ascii=False, compressed=True)
    else:
        ok = o3d.io.write_triangle_mesh(str(out), mesh)

    if not ok:
        raise RuntimeError(f"Failed to write mesh to: {out}")

    kind = "mesh" if was_mesh else "pointcloud->poisson mesh"
    print(f"Wrote cleaned {kind}: {out} (triangles={len(mesh.triangles)}, vertices={len(mesh.vertices)})")


if __name__ == "__main__":
    main()

