from __future__ import annotations

import argparse
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import open3d as o3d


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_geometry(path: Path) -> o3d.geometry.TriangleMesh:
    mesh = o3d.io.read_triangle_mesh(str(path))
    if mesh.is_empty():
        raise ValueError("Failed to read mesh (empty)")
    if not mesh.has_vertex_normals():
        mesh.compute_vertex_normals()
    return mesh


def _sample_points(mesh: o3d.geometry.TriangleMesh, n: int) -> o3d.geometry.PointCloud:
    pcd = mesh.sample_points_uniformly(number_of_points=n)
    if pcd.is_empty():
        raise ValueError("Failed to sample points (empty)")
    return pcd


def _fit_plane(
    pcd: o3d.geometry.PointCloud,
    *,
    distance_threshold: float,
    ransac_n: int,
    num_iterations: int,
) -> tuple[np.ndarray, o3d.geometry.PointCloud]:
    plane_model, inliers = pcd.segment_plane(
        distance_threshold=distance_threshold, ransac_n=ransac_n, num_iterations=num_iterations
    )
    inlier_cloud = pcd.select_by_index(inliers)
    if inlier_cloud.is_empty():
        raise ValueError("Plane segmentation produced no inliers")
    return np.array(plane_model, dtype=float), inlier_cloud


def _downsample_points(pcd: o3d.geometry.PointCloud, voxel_size: float) -> o3d.geometry.PointCloud:
    if voxel_size <= 0:
        return pcd
    return pcd.voxel_down_sample(voxel_size=voxel_size)


def _pick_markers(pcd: o3d.geometry.PointCloud, max_markers: int, seed: int) -> np.ndarray:
    pts = np.asarray(pcd.points)
    if pts.size == 0:
        raise ValueError("No points to pick markers from")
    if max_markers <= 0 or pts.shape[0] <= max_markers:
        return pts
    rng = np.random.default_rng(seed)
    idx = rng.choice(pts.shape[0], size=max_markers, replace=False)
    return pts[idx]


def _to_locations(points: np.ndarray) -> dict[str, object]:
    locations = []
    for i, p in enumerate(points, start=1):
        locations.append(
            {
                "id": uuid.uuid4().hex,
                "label": f"Auto {i}",
                "position": {"x": float(p[0]), "y": float(p[1]), "z": float(p[2])},
                "zone": None,
                "notes": None,
                "barcode": None,
                "scanResultId": None,
                "scanJobId": None,
                "palletCount": None,
                "capacityPct": None,
            }
        )
    return {"updatedAt": _iso_now(), "locations": locations}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="in_path", required=True)
    parser.add_argument("--out", dest="out_path", required=True)
    parser.add_argument("--sample-points", type=int, default=200_000)
    parser.add_argument("--distance-threshold", type=float, default=0.02)
    parser.add_argument("--ransac-n", type=int, default=3)
    parser.add_argument("--iterations", type=int, default=1_000)
    parser.add_argument("--voxel-size", type=float, default=0.10)
    parser.add_argument("--max-markers", type=int, default=250)
    parser.add_argument("--seed", type=int, default=1337)
    args = parser.parse_args()

    in_path = Path(args.in_path)
    out_path = Path(args.out_path)

    mesh = _load_geometry(in_path)
    pcd = _sample_points(mesh, n=args.sample_points)
    plane, inliers = _fit_plane(
        pcd,
        distance_threshold=args.distance_threshold,
        ransac_n=args.ransac_n,
        num_iterations=args.iterations,
    )

    inliers = _downsample_points(inliers, voxel_size=args.voxel_size)
    markers = _pick_markers(inliers, max_markers=args.max_markers, seed=args.seed)

    payload = _to_locations(markers)
    payload["_meta"] = {
        "source": str(in_path),
        "plane": {"a": float(plane[0]), "b": float(plane[1]), "c": float(plane[2]), "d": float(plane[3])},
        "sample_points": int(args.sample_points),
        "distance_threshold": float(args.distance_threshold),
        "ransac_n": int(args.ransac_n),
        "iterations": int(args.iterations),
        "voxel_size": float(args.voxel_size),
        "max_markers": int(args.max_markers),
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

