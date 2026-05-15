"use client";

import * as React from "react";
import { Canvas, useLoader, type ThreeEvent } from "@react-three/fiber";
import { OrbitControls, Grid, Html, useCursor, useGLTF } from "@react-three/drei";
import * as THREE from "three";
import { PLYLoader } from "three/examples/jsm/loaders/PLYLoader.js";
import { OBJLoader } from "three/examples/jsm/loaders/OBJLoader.js";
import type { OrbitControls as OrbitControlsImpl } from "three-stdlib";
import type { WarehouseMapLocation, WarehouseMapLocations } from "@/lib/types";
import {
  useCreateWarehouseMap,
  useConfirmWarehouseMapMeshUpload,
  useDeleteWarehouseMap,
  usePresignWarehouseMapMeshUpload,
  useUpdateWarehouseMap,
  useWarehouseMap,
  useWarehouseMapMeshDownload,
  useWarehouseMaps
} from "@/queries/warehouseMaps";
import { LocationDetailsModal } from "@/components/warehouses/LocationDetailsModal";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";

type Props = {
  warehouseId: string;
};

function computeBounds(locations: WarehouseMapLocation[]) {
  const box = new THREE.Box3();
  for (const l of locations) {
    box.expandByPoint(new THREE.Vector3(l.position.x, l.position.y, l.position.z));
  }
  if (box.isEmpty()) {
    box.setFromCenterAndSize(new THREE.Vector3(0, 0, 0), new THREE.Vector3(10, 1, 10));
  }
  return box;
}

function WireframeGLTFModel({
  url,
  onShiftClick
}: {
  url: string;
  onShiftClick?: (point: { x: number; y: number; z: number }) => void;
}) {
  const gltf = useGLTF(url);

  const scene = React.useMemo(() => {
    const cloned = gltf.scene.clone(true);
    const material = new THREE.MeshBasicMaterial({ color: "#52525b", wireframe: true });
    cloned.traverse((obj) => {
      if ((obj as THREE.Mesh).isMesh) {
        const mesh = obj as THREE.Mesh;
        mesh.material = material;
        mesh.castShadow = false;
        mesh.receiveShadow = false;
      }
    });
    return cloned;
  }, [gltf.scene]);

  return (
    <primitive
      object={scene}
      onPointerDown={(e: ThreeEvent<PointerEvent>) => {
        if (!e.shiftKey) return;
        e.stopPropagation();
        if (onShiftClick) onShiftClick({ x: e.point.x, y: e.point.y, z: e.point.z });
      }}
    />
  );
}

function WireframePLYModel({
  url,
  onShiftClick
}: {
  url: string;
  onShiftClick?: (point: { x: number; y: number; z: number }) => void;
}) {
  const geometry = useLoader(PLYLoader, url);
  const material = React.useMemo(() => new THREE.MeshBasicMaterial({ color: "#52525b", wireframe: true }), []);

  return (
    <mesh
      geometry={geometry}
      material={material}
      onPointerDown={(e: ThreeEvent<PointerEvent>) => {
        if (!e.shiftKey) return;
        e.stopPropagation();
        if (onShiftClick) onShiftClick({ x: e.point.x, y: e.point.y, z: e.point.z });
      }}
    />
  );
}

function WireframeOBJModel({
  url,
  onShiftClick
}: {
  url: string;
  onShiftClick?: (point: { x: number; y: number; z: number }) => void;
}) {
  const obj = useLoader(OBJLoader, url);

  const scene = React.useMemo(() => {
    const cloned = obj.clone(true);
    const material = new THREE.MeshBasicMaterial({ color: "#52525b", wireframe: true });
    cloned.traverse((o) => {
      if ((o as THREE.Mesh).isMesh) {
        const mesh = o as THREE.Mesh;
        mesh.material = material;
        mesh.castShadow = false;
        mesh.receiveShadow = false;
      }
    });
    return cloned;
  }, [obj]);

  return (
    <primitive
      object={scene}
      onPointerDown={(e: ThreeEvent<PointerEvent>) => {
        if (!e.shiftKey) return;
        e.stopPropagation();
        if (onShiftClick) onShiftClick({ x: e.point.x, y: e.point.y, z: e.point.z });
      }}
    />
  );
}

function WarehouseWireframeModel({
  url,
  onShiftClick
}: {
  url: string;
  onShiftClick?: (point: { x: number; y: number; z: number }) => void;
}) {
  const ext = React.useMemo(() => {
    const cleaned = url.split("#")[0]?.split("?")[0] ?? url;
    const parts = cleaned.toLowerCase().split(".");
    return parts.length > 1 ? parts[parts.length - 1] : "";
  }, [url]);

  if (ext === "ply") return <WireframePLYModel url={url} onShiftClick={onShiftClick} />;
  if (ext === "obj") return <WireframeOBJModel url={url} onShiftClick={onShiftClick} />;
  return <WireframeGLTFModel url={url} onShiftClick={onShiftClick} />;
}

type MarkerProps = {
  location: WarehouseMapLocation;
  selected: boolean;
  onSelect: (locationId: string) => void;
};

function Marker({ location, selected, onSelect }: MarkerProps) {
  const [hovered, setHovered] = React.useState(false);
  useCursor(hovered);

  const color = selected ? "#f59e0b" : hovered ? "#60a5fa" : "#22c55e";

  return (
    <mesh
      position={[location.position.x, location.position.y + 0.25, location.position.z]}
      onPointerOver={(e) => {
        e.stopPropagation();
        setHovered(true);
      }}
      onPointerOut={() => setHovered(false)}
      onClick={(e) => {
        e.stopPropagation();
        onSelect(location.id);
      }}
    >
      <sphereGeometry args={[0.25, 16, 16]} />
      <meshStandardMaterial color={color} />
      {(hovered || selected) && (
        <Html position={[0, 0.65, 0]} center distanceFactor={12}>
          <div className="pointer-events-none rounded-md border border-zinc-700 bg-zinc-950/90 px-2 py-1 text-[10px] text-zinc-100 shadow">
            <div className="font-semibold">{location.label}</div>
            {location.zone ? <div className="text-zinc-400">{location.zone}</div> : null}
          </div>
        </Html>
      )}
    </mesh>
  );
}

function coerceLocations(raw: Record<string, unknown> | null | undefined): WarehouseMapLocations {
  if (raw && typeof raw === "object") {
    const updatedAt = typeof (raw as { updatedAt?: unknown }).updatedAt === "string" ? (raw as { updatedAt: string }).updatedAt : "";
    const locationsRaw = (raw as { locations?: unknown }).locations;
    if (Array.isArray(locationsRaw)) {
      return {
        updatedAt: updatedAt || new Date().toISOString(),
        locations: locationsRaw as WarehouseMapLocation[]
      };
    }
  }
  return { updatedAt: new Date().toISOString(), locations: [] };
}

export default function WarehouseMapViewer({ warehouseId }: Props) {
  const maps = useWarehouseMaps(warehouseId);
  const [mapId, setMapId] = React.useState<string>("");
  const map = useWarehouseMap(warehouseId, mapId);
  const createMap = useCreateWarehouseMap(warehouseId);
  const updateMap = useUpdateWarehouseMap(warehouseId, mapId);
  const deleteMap = useDeleteWarehouseMap(warehouseId);
  const meshDownload = useWarehouseMapMeshDownload(warehouseId, mapId, Boolean(map.data?.mesh_object_key));
  const presignMesh = usePresignWarehouseMapMeshUpload(warehouseId, mapId);
  const confirmMesh = useConfirmWarehouseMapMeshUpload(warehouseId, mapId);

  const [selectedId, setSelectedId] = React.useState<string | null>(null);
  const modelUrl = meshDownload.data?.url ?? null;
  const [localLocations, setLocalLocations] = React.useState<WarehouseMapLocations>({
    updatedAt: new Date().toISOString(),
    locations: []
  });

  const controlsRef = React.useRef<OrbitControlsImpl | null>(null);
  const lastStableLocationsRef = React.useRef<WarehouseMapLocations | null>(null);
  const [saveError, setSaveError] = React.useState<string | null>(null);
  const activeListItemRef = React.useRef<HTMLButtonElement | null>(null);

  const [createMapOpen, setCreateMapOpen] = React.useState(false);
  const [renameMapOpen, setRenameMapOpen] = React.useState(false);
  const [deleteMapOpen, setDeleteMapOpen] = React.useState(false);
  const [mapNameDraft, setMapNameDraft] = React.useState("");

  const fileInputRef = React.useRef<HTMLInputElement | null>(null);
  const [uploadError, setUploadError] = React.useState<string | null>(null);
  const markersInputRef = React.useRef<HTMLInputElement | null>(null);
  const [importError, setImportError] = React.useState<string | null>(null);

  React.useEffect(() => {
    const list = maps.data ?? [];
    const ids = new Set(list.map((m) => m.id));
    const first = list[0]?.id ?? "";
    setMapId((prev) => {
      if (prev && ids.has(prev)) return prev;
      return first;
    });
  }, [maps.data]);

  React.useEffect(() => {
    setSelectedId(null);
    if (map.data) {
      const coerced = coerceLocations(map.data.locations);
      setLocalLocations(coerced);
      lastStableLocationsRef.current = coerced;
    }
  }, [mapId, map.data]);

  React.useEffect(() => {
    if (!createMapOpen && !renameMapOpen) return;
    const currentName = maps.data?.find((m) => m.id === mapId)?.name ?? map.data?.name ?? "";
    if (createMapOpen) {
      setMapNameDraft(currentName ? `${currentName} copy` : "New map");
    } else if (renameMapOpen) {
      setMapNameDraft(currentName || "Warehouse map");
    }
    // Intentionally omit mapNameDraft to avoid overwriting user typing.
  }, [createMapOpen, renameMapOpen, mapId, maps.data, map.data?.name]);

  React.useEffect(() => {
    if (!selectedId) return;
    activeListItemRef.current?.scrollIntoView({ block: "nearest" });
  }, [selectedId]);

  const bounds = computeBounds(localLocations.locations);
  const center = bounds.getCenter(new THREE.Vector3());
  const size = bounds.getSize(new THREE.Vector3());
  const floorSize = Math.max(size.x, size.z, 12);

  const selected = localLocations.locations.find((l) => l.id === selectedId) ?? null;

  const centerView = React.useCallback(() => {
    const controls = controlsRef.current;
    if (!controls) return;
    controls.target.set(center.x, center.y, center.z);
    controls.update();
  }, [center.x, center.y, center.z]);

  if (maps.isLoading || map.isLoading) {
    return (
      <Card className="p-4">
        <div className="text-sm text-zinc-200">Loading warehouse map…</div>
        <div className="mt-1 text-xs text-zinc-500">Fetching warehouse maps from the API</div>
      </Card>
    );
  }

  if (maps.error) {
    return (
      <Card className="p-4">
        <div className="text-sm font-semibold text-zinc-100">Failed to load warehouse map</div>
        <div className="mt-1 text-xs text-zinc-400">
          {(maps.error as Error | undefined)?.message ?? "Unknown error"}
        </div>
        <div className="mt-3">
          <Button variant="secondary" onClick={() => maps.refetch()}>
            Retry
          </Button>
        </div>
      </Card>
    );
  }

  if (!mapId) {
    return (
      <Card className="p-4">
        <div className="text-sm font-semibold text-zinc-100">No 3D maps yet</div>
        <div className="mt-1 text-xs text-zinc-400">Create a warehouse map to start placing scan markers.</div>
        <div className="mt-4">
          <Button onClick={() => setCreateMapOpen(true)}>Create map</Button>
        </div>

        <Dialog
          open={createMapOpen}
          onClose={() => {
            if (createMap.isPending) return;
            setCreateMapOpen(false);
          }}
          title="Create warehouse map"
          description="Maps store scan-marker positions and an optional 3D mesh for the warehouse layout."
          footer={
            <div className="flex items-center justify-end gap-2">
              <Button
                variant="secondary"
                onClick={() => setCreateMapOpen(false)}
                disabled={createMap.isPending}
              >
                Cancel
              </Button>
              <Button
                onClick={() => {
                  const name = mapNameDraft.trim() || "Warehouse map";
                  createMap.mutate(
                    { name, locations: { updatedAt: new Date().toISOString(), locations: [] } },
                    {
                      onSuccess: (created) => {
                        setCreateMapOpen(false);
                        setMapId(created.id);
                      }
                    }
                  );
                }}
                disabled={createMap.isPending}
              >
                {createMap.isPending ? "Creating…" : "Create"}
              </Button>
            </div>
          }
        >
          <label className="space-y-1">
            <div className="text-xs text-zinc-400">Map name</div>
            <Input value={mapNameDraft} onChange={(e) => setMapNameDraft(e.target.value)} autoFocus />
          </label>
        </Dialog>
      </Card>
    );
  }

  if (map.error || !map.data) {
    return (
      <Card className="p-4">
        <div className="text-sm font-semibold text-zinc-100">Failed to load warehouse map</div>
        <div className="mt-1 text-xs text-zinc-400">{(map.error as Error | undefined)?.message ?? "Unknown error"}</div>
        <div className="mt-3">
          <Button variant="secondary" onClick={() => map.refetch()}>
            Retry
          </Button>
        </div>
      </Card>
    );
  }

  const persistLocations = (nextLocations: WarehouseMapLocations, opts?: { close?: boolean }) => {
    setSaveError(null);
    const prev = localLocations;
    setLocalLocations(nextLocations);
    updateMap.mutate(
      { locations: nextLocations as unknown as Record<string, unknown> },
      {
        onSuccess: () => {
          lastStableLocationsRef.current = nextLocations;
          if (opts?.close) setSelectedId(null);
        },
        onError: (err) => {
          setSaveError((err as Error | undefined)?.message ?? "Failed to save marker updates");
          setLocalLocations(lastStableLocationsRef.current ?? prev);
        }
      }
    );
  };

  const exportMarkers = () => {
    const payload = JSON.stringify(localLocations, null, 2);
    const blob = new Blob([payload], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `warehouse_${warehouseId}_map_${mapId}_markers.json`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  };

  const newId = () => {
    const id = globalThis.crypto?.randomUUID?.();
    if (id) return id;
    return `loc_${Math.random().toString(16).slice(2)}${Date.now().toString(16)}`;
  };

  const addMarkerAt = (point: { x: number; y: number; z: number }) => {
    const next: WarehouseMapLocation = {
      id: newId(),
      label: `Location ${localLocations.locations.length + 1}`,
      position: { x: point.x, y: point.y, z: point.z },
      zone: null,
      notes: null,
      barcode: null,
      scanJobId: null,
      scanResultId: null,
      palletCount: null,
      capacityPct: null
    };
    const nextLocations: WarehouseMapLocations = {
      updatedAt: new Date().toISOString(),
      locations: [...localLocations.locations, next]
    };
    persistLocations(nextLocations);
    setSelectedId(next.id);
  };

  const deleteMarker = (locationId: string) => {
    const nextLocations: WarehouseMapLocations = {
      updatedAt: new Date().toISOString(),
      locations: localLocations.locations.filter((l) => l.id !== locationId)
    };
    setSelectedId(null);
    persistLocations(nextLocations, { close: true });
  };

  const uploadMesh = async (file: File) => {
    setUploadError(null);
    const ext = (file.name.split(".").pop() ?? "").trim().toLowerCase();
    if (ext === "zip") throw new Error(".zip meshes are not supported");
    const contentType =
      ext === "glb"
        ? "model/gltf-binary"
        : ext === "gltf"
          ? "model/gltf+json"
          : "application/octet-stream";
    const presigned = await presignMesh.mutateAsync({ content_type: contentType, filename: file.name });
    const putRes = await fetch(presigned.url, {
      method: "PUT",
      headers: { ...(presigned.headers ?? {}), "Content-Type": contentType },
      body: file
    });
    if (!putRes.ok) throw new Error(await putRes.text());
    const etag = putRes.headers.get("etag");
    await confirmMesh.mutateAsync({ etag, bytes: file.size });
  };

  const importMarkers = async (file: File) => {
    setImportError(null);
    const text = await file.text();
    const parsed = JSON.parse(text) as unknown;
    const rawLocations = Array.isArray(parsed)
      ? parsed
      : parsed && typeof parsed === "object" && Array.isArray((parsed as { locations?: unknown }).locations)
        ? ((parsed as { locations: unknown[] }).locations as unknown[])
        : null;

    if (!rawLocations) throw new Error("Invalid markers JSON: expected an array or an object with { locations: [...] }");

    const imported: WarehouseMapLocation[] = rawLocations.map((raw, idx) => {
      const o = raw as Record<string, unknown>;
      const pos = (o.position as Record<string, unknown> | undefined) ?? {};
      const x = typeof pos.x === "number" ? pos.x : 0;
      const y = typeof pos.y === "number" ? pos.y : 0;
      const z = typeof pos.z === "number" ? pos.z : 0;
      const id = typeof o.id === "string" && o.id.length > 0 ? o.id : newId();
      const label = typeof o.label === "string" && o.label.length > 0 ? o.label : `Imported ${idx + 1}`;
      return {
        id,
        label,
        position: { x, y, z },
        zone: typeof o.zone === "string" ? o.zone : null,
        notes: typeof o.notes === "string" ? o.notes : null,
        barcode: typeof o.barcode === "string" ? o.barcode : null,
        scanJobId: typeof o.scanJobId === "string" ? o.scanJobId : null,
        scanResultId: typeof o.scanResultId === "string" ? o.scanResultId : null,
        palletCount: typeof o.palletCount === "number" ? o.palletCount : null,
        capacityPct: typeof o.capacityPct === "number" ? o.capacityPct : null
      };
    });

    const nextLocations: WarehouseMapLocations = {
      updatedAt: new Date().toISOString(),
      locations: [...localLocations.locations, ...imported]
    };
    persistLocations(nextLocations);
  };

  return (
    <div className="grid gap-3 lg:grid-cols-[1fr_320px]">
      <Card className="relative h-[70vh] min-h-[520px] overflow-hidden">
        <div className="absolute left-3 top-3 z-10 flex flex-wrap items-center gap-2">
          <Button variant="secondary" size="sm" onClick={centerView} aria-label="Center camera on the map">
            Center view
          </Button>
        </div>
        <div className="pointer-events-none absolute bottom-3 left-3 z-10 max-w-[min(520px,85%)] rounded-md border border-zinc-800 bg-zinc-950/80 px-3 py-2 text-[11px] text-zinc-200">
          <div className="font-medium">Tip</div>
          <div className="text-zinc-400">Shift+click the mesh or floor plane to add a marker. Click a marker to edit.</div>
        </div>
        <Canvas
          camera={{ position: [center.x + 12, 10, center.z + 12], fov: 50 }}
          gl={{ antialias: true }}
        >
          <ambientLight intensity={0.8} />
          <directionalLight position={[10, 15, 10]} intensity={0.8} />

          {/* Scene helpers */}
          <Grid
            infiniteGrid
            cellSize={1}
            cellThickness={1}
            sectionSize={5}
            sectionThickness={1.5}
            fadeDistance={35}
            fadeStrength={1.5}
          />
          <OrbitControls ref={controlsRef} makeDefault target={[center.x, center.y, center.z]} />

          {/* Warehouse floor (fallback visual reference if no mesh is available) */}
          <mesh
            position={[center.x, center.y - 0.01, center.z]}
            rotation={[-Math.PI / 2, 0, 0]}
            onPointerDown={(e) => {
              if (!e.shiftKey) return;
              e.stopPropagation();
              addMarkerAt({ x: e.point.x, y: e.point.y, z: e.point.z });
            }}
          >
            <planeGeometry args={[floorSize, floorSize]} />
            <meshStandardMaterial color="#09090b" />
          </mesh>

          {/* Warehouse mesh (wireframe) */}
          {modelUrl ? (
            <React.Suspense
              fallback={
                <Html center>
                  <div className="rounded-md border border-zinc-800 bg-zinc-950/90 px-3 py-2 text-xs text-zinc-100 shadow">
                    Loading mesh…
                  </div>
                </Html>
              }
            >
              <WarehouseWireframeModel url={modelUrl} onShiftClick={addMarkerAt} />
            </React.Suspense>
          ) : null}

          {!modelUrl && localLocations.locations.length === 0 ? (
            <Html center>
              <div className="pointer-events-none max-w-xs rounded-md border border-zinc-800 bg-zinc-950/90 px-3 py-2 text-center text-xs text-zinc-200 shadow">
                <div className="font-semibold">No mesh + no markers</div>
                <div className="mt-1 text-[11px] text-zinc-400">
                  Upload a mesh on the right, then Shift+click to place scan points.
                </div>
              </div>
            </Html>
          ) : null}

          {/* Markers */}
          {localLocations.locations.map((loc) => (
            <Marker
              key={loc.id}
              location={loc}
              selected={loc.id === selectedId}
              onSelect={(id) => setSelectedId(id)}
            />
          ))}
        </Canvas>
      </Card>

      <Card className="p-4">
        <div className="text-sm font-semibold text-zinc-100">Warehouse</div>
        <div className="mt-1 text-xs text-zinc-400">
          {warehouseId} • {localLocations.locations.length} scan points
        </div>
        <div className="mt-3 text-xs text-zinc-400">
          <div className="flex items-center justify-between gap-2">
            <div>Map</div>
            <div className="flex items-center gap-2">
              <Select
                className="h-8 max-w-[200px] px-2 text-xs"
                value={mapId}
                onChange={(e) => setMapId(e.target.value)}
                aria-label="Warehouse map"
              >
                {(maps.data ?? []).map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.name}
                  </option>
                ))}
              </Select>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setCreateMapOpen(true)}
                aria-label="Create new map"
              >
                New
              </Button>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setRenameMapOpen(true)}
                disabled={!mapId}
                aria-label="Rename current map"
              >
                Rename
              </Button>
              <Button
                variant="danger"
                size="sm"
                onClick={() => setDeleteMapOpen(true)}
                disabled={!mapId}
                aria-label="Delete current map"
              >
                Delete
              </Button>
            </div>
          </div>
          <div>Mesh: {modelUrl ? "available" : map.data.mesh_object_key ? "loading…" : "not uploaded"}</div>
        </div>

        {updateMap.isPending ? (
          <div className="mt-3 rounded-md border border-zinc-800 bg-zinc-950 px-2 py-2 text-xs text-zinc-200">
            Saving marker changes…
          </div>
        ) : null}
        {saveError ? (
          <div className="mt-3 rounded-md border border-red-900/50 bg-red-950/20 px-2 py-2 text-xs text-red-200">
            <div className="font-semibold">Save failed</div>
            <div className="mt-1 text-[11px] text-red-300">{saveError}</div>
            <div className="mt-2">
              <Button variant="secondary" size="sm" onClick={() => setSaveError(null)}>
                Dismiss
              </Button>
            </div>
          </div>
        ) : null}

        <div className="mt-4 space-y-2">
          <div className="flex items-center justify-between gap-2">
            <div className="text-xs font-semibold text-zinc-200">Mesh</div>
            <input
              ref={fileInputRef}
              type="file"
              accept=".glb,.gltf,.ply,.obj,model/gltf-binary,model/gltf+json,application/octet-stream"
              className="hidden"
              onChange={async (e) => {
                const file = e.target.files?.[0];
                if (!file) return;
                try {
                  await uploadMesh(file);
                } catch (err) {
                  setUploadError((err as Error | undefined)?.message ?? "Upload failed");
                } finally {
                  e.target.value = "";
                }
              }}
            />
            <Button
              variant="secondary"
              size="sm"
              disabled={!mapId || presignMesh.isPending || confirmMesh.isPending}
              onClick={() => fileInputRef.current?.click()}
            >
              Upload
            </Button>
          </div>
          {uploadError ? <div className="text-xs text-red-400">{uploadError}</div> : null}
          <div className="text-[11px] text-zinc-500">Shift+click the mesh to add a marker.</div>
        </div>

        <div className="mt-4 space-y-2">
          <div className="flex items-center justify-between gap-2">
            <div className="text-xs font-semibold text-zinc-200">Markers</div>
            <div className="flex items-center gap-2">
              <Button
                variant="secondary"
                size="sm"
                disabled={!mapId || localLocations.locations.length === 0}
                onClick={exportMarkers}
              >
                Export
              </Button>
              <input
                ref={markersInputRef}
                type="file"
                accept=".json,application/json,text/plain"
                className="hidden"
                onChange={async (e) => {
                  const file = e.target.files?.[0];
                  if (!file) return;
                  try {
                    await importMarkers(file);
                  } catch (err) {
                    setImportError((err as Error | undefined)?.message ?? "Import failed");
                  } finally {
                    e.target.value = "";
                  }
                }}
              />
              <Button variant="secondary" size="sm" disabled={!mapId} onClick={() => markersInputRef.current?.click()}>
                Import
              </Button>
            </div>
          </div>
          {importError ? <div className="text-xs text-red-400">{importError}</div> : null}
        </div>

        <div className="mt-4 space-y-2">
          <div className="max-h-[44vh] space-y-1 overflow-auto pr-1">
            {localLocations.locations.length === 0 ? (
              <div className="rounded-md border border-zinc-800 bg-zinc-950 px-3 py-3 text-xs text-zinc-400">
                No markers yet. Shift+click the mesh or floor plane to add your first scan point.
              </div>
            ) : (
              localLocations.locations.map((l) => {
                const active = l.id === selectedId;
                return (
                  <button
                    key={l.id}
                    type="button"
                    ref={active ? activeListItemRef : undefined}
                    onClick={() => setSelectedId(l.id)}
                    className={[
                      "w-full rounded-md border px-2 py-2 text-left text-xs",
                      active
                        ? "border-zinc-600 bg-zinc-900 text-zinc-50"
                        : "border-zinc-800 bg-zinc-950 text-zinc-300 hover:bg-zinc-900"
                    ].join(" ")}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <div className="font-medium">{l.label}</div>
                      <div className="text-[10px] text-zinc-500">{l.zone ?? ""}</div>
                    </div>
                    <div className="mt-1 font-mono text-[10px] text-zinc-500">
                      ({l.position.x.toFixed(1)}, {l.position.y.toFixed(1)}, {l.position.z.toFixed(1)})
                    </div>
                  </button>
                );
              })
            )}
          </div>
        </div>
      </Card>

      <Dialog
        open={createMapOpen}
        onClose={() => {
          if (createMap.isPending) return;
          setCreateMapOpen(false);
        }}
        title="Create warehouse map"
        description="Create a new map for this warehouse. Each map has its own markers and optional mesh."
        footer={
          <div className="flex items-center justify-end gap-2">
            <Button variant="secondary" onClick={() => setCreateMapOpen(false)} disabled={createMap.isPending}>
              Cancel
            </Button>
            <Button
              onClick={() => {
                const name = mapNameDraft.trim() || "Warehouse map";
                createMap.mutate(
                  { name, locations: { updatedAt: new Date().toISOString(), locations: [] } },
                  {
                    onSuccess: (created) => {
                      setCreateMapOpen(false);
                      setMapId(created.id);
                    }
                  }
                );
              }}
              disabled={createMap.isPending}
            >
              {createMap.isPending ? "Creating…" : "Create"}
            </Button>
          </div>
        }
      >
        <label className="space-y-1">
          <div className="text-xs text-zinc-400">Map name</div>
          <Input value={mapNameDraft} onChange={(e) => setMapNameDraft(e.target.value)} autoFocus />
        </label>
      </Dialog>

      <Dialog
        open={renameMapOpen}
        onClose={() => {
          if (updateMap.isPending) return;
          setRenameMapOpen(false);
        }}
        title="Rename map"
        description="Renaming a map keeps markers and mesh unchanged."
        footer={
          <div className="flex items-center justify-end gap-2">
            <Button variant="secondary" onClick={() => setRenameMapOpen(false)} disabled={updateMap.isPending}>
              Cancel
            </Button>
            <Button
              onClick={() => {
                const name = mapNameDraft.trim() || "Warehouse map";
                updateMap.mutate(
                  { name },
                  {
                    onSuccess: () => setRenameMapOpen(false)
                  }
                );
              }}
              disabled={updateMap.isPending}
            >
              {updateMap.isPending ? "Saving…" : "Save"}
            </Button>
          </div>
        }
      >
        <label className="space-y-1">
          <div className="text-xs text-zinc-400">Map name</div>
          <Input value={mapNameDraft} onChange={(e) => setMapNameDraft(e.target.value)} autoFocus />
        </label>
      </Dialog>

      <Dialog
        open={deleteMapOpen}
        onClose={() => {
          if (deleteMap.isPending) return;
          setDeleteMapOpen(false);
        }}
        title="Delete map"
        description="Deleting a map permanently removes its markers and mesh reference. This cannot be undone."
        footer={
          <div className="flex items-center justify-end gap-2">
            <Button variant="secondary" onClick={() => setDeleteMapOpen(false)} disabled={deleteMap.isPending}>
              Cancel
            </Button>
            <Button
              variant="danger"
              onClick={() => {
                if (!mapId) return;
                deleteMap.mutate(mapId, {
                  onSuccess: () => {
                    setDeleteMapOpen(false);
                    // Force re-selection from the refreshed list to avoid displaying a stale mapId.
                    setSelectedId(null);
                    setMapId("");
                  }
                });
              }}
              disabled={deleteMap.isPending}
            >
              {deleteMap.isPending ? "Deleting…" : "Delete"}
            </Button>
          </div>
        }
      >
        <div className="text-sm text-zinc-200">Delete the currently selected map?</div>
      </Dialog>

      <LocationDetailsModal
        open={Boolean(selectedId)}
        warehouseId={warehouseId}
        warehouseMapId={mapId}
        locations={localLocations}
        location={selected}
        onClose={() => setSelectedId(null)}
        onDelete={(locationId) => deleteMarker(locationId)}
        onSave={(nextLocations) => persistLocations(nextLocations, { close: true })}
      />
    </div>
  );
}
