# Warehouse Mapping (COLMAP → Mesh → Upload)

This folder contains an optional pipeline to generate a 3D mesh from warehouse photos and upload it into the app’s “Warehouse Map” viewer.

## What the app accepts

- Mesh uploads supported by the viewer: `.glb`, `.gltf`, `.ply`, `.obj`
- Recommended output from the pipeline for fastest iteration: `.ply`

## Pipeline overview

1. Capture photos (or video frames) of the warehouse area you want to map.
2. Run COLMAP to reconstruct and export a mesh.
3. (Optional) Run Open3D cleanup to simplify the mesh and remove artifacts.
4. Upload the resulting file in the Warehouse Map viewer and place markers (Shift+click).

## 1) Run COLMAP in Docker

COLMAP provides pre-built Docker images on Docker Hub under `colmap/colmap`. The upstream project README explicitly references “Pre-built Docker images are available at https://hub.docker.com/r/colmap/colmap.” [1]

### Quick start (automatic reconstruction)

```bash
docker run --rm -it -v "$(pwd):/work" colmap/colmap:latest bash
```

Inside the container:

```bash
mkdir -p /work/colmap_ws
colmap automatic_reconstructor --image_path /work/images --workspace_path /work/colmap_ws
```

The official Docker docs show this same pattern (“run the run script … mounted … then run `colmap automatic_reconstructor ...`”). [2]

### Export a mesh

Depending on the COLMAP version and reconstruction settings, dense output commonly includes a fused point cloud in the workspace. You can convert point clouds to meshes using any meshing tool you prefer.

If you already have a `.ply` mesh (or can export one), you can upload it directly into the app.

## 2) Optional Open3D cleanup (simplify + fix normals)

Install the tool requirements in a separate virtualenv:

```bash
python -m venv .venv-mesh
source .venv-mesh/bin/activate  # macOS/Linux
# .venv-mesh\Scripts\activate   # Windows PowerShell
pip install -r requirements.txt
```

Then:

```bash
python open3d_cleanup.py --in mesh.ply --out mesh.cleaned.ply --target-tris 500000
```

## 2b) Optional Open3D floor-plane markers export

This generates a `locations` JSON file compatible with the Warehouse Map viewer’s marker import.

```bash
python open3d_floor_markers.py --in mesh.cleaned.ply --out markers.json
```

## 3) Upload + marker workflow in the app

1. Open Dashboard → Warehouses → pick a warehouse → “Warehouse Map”.
2. Upload the mesh file (GLB/GLTF/PLY/OBJ).
3. Hold Shift and click the mesh to add markers.
4. Click a marker to attach scan/job IDs, barcodes, notes, etc.

## References

[1] COLMAP README (mentions Docker Hub image `colmap/colmap`): https://github.com/colmap/colmap/  
[2] COLMAP Docker docs (example invocation of `colmap automatic_reconstructor` inside container): https://github.com/colmap/colmap/blob/main/docker/README.md
