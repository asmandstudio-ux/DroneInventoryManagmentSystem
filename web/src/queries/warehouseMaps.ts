"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type { PresignedDownload, WarehouseMap, WarehouseMapMeshConfirm, WarehouseMapMeshPresign } from "@/lib/types";

export function useWarehouseMaps(warehouseId: string) {
  return useQuery({
    queryKey: ["warehouse-maps", warehouseId],
    queryFn: () => apiFetch<WarehouseMap[]>(`/warehouses/${encodeURIComponent(warehouseId)}/maps`),
    enabled: Boolean(warehouseId)
  });
}

export function useWarehouseMap(warehouseId: string, warehouseMapId: string) {
  return useQuery({
    queryKey: ["warehouse-map", warehouseId, warehouseMapId],
    queryFn: () =>
      apiFetch<WarehouseMap>(`/warehouses/${encodeURIComponent(warehouseId)}/maps/${encodeURIComponent(warehouseMapId)}`),
    enabled: Boolean(warehouseId && warehouseMapId)
  });
}

export function useCreateWarehouseMap(warehouseId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: { name: string; locations: Record<string, unknown> }) =>
      apiFetch<WarehouseMap>(`/warehouses/${encodeURIComponent(warehouseId)}/maps`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["warehouse-maps", warehouseId] })
  });
}

export function useUpdateWarehouseMap(warehouseId: string, warehouseMapId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: { name?: string; locations?: Record<string, unknown> }) =>
      apiFetch<WarehouseMap>(`/warehouses/${encodeURIComponent(warehouseId)}/maps/${encodeURIComponent(warehouseMapId)}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      }),
    onSuccess: (next) => {
      qc.setQueryData(["warehouse-map", warehouseId, warehouseMapId], next);
      qc.invalidateQueries({ queryKey: ["warehouse-maps", warehouseId] });
    }
  });
}

export function useDeleteWarehouseMap(warehouseId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (warehouseMapId: string) =>
      apiFetch<void>(`/warehouses/${encodeURIComponent(warehouseId)}/maps/${encodeURIComponent(warehouseMapId)}`, {
        method: "DELETE"
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["warehouse-maps", warehouseId] })
  });
}

export function useWarehouseMapMeshDownload(warehouseId: string, warehouseMapId: string, enabled: boolean) {
  return useQuery({
    queryKey: ["warehouse-map-mesh-download", warehouseId, warehouseMapId],
    queryFn: () =>
      apiFetch<PresignedDownload>(
        `/warehouses/${encodeURIComponent(warehouseId)}/maps/${encodeURIComponent(warehouseMapId)}/mesh/download`
      ),
    enabled: Boolean(enabled && warehouseId && warehouseMapId)
  });
}

export function usePresignWarehouseMapMeshUpload(warehouseId: string, warehouseMapId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: { content_type: string; filename?: string | null }) =>
      apiFetch<WarehouseMapMeshPresign>(
        `/warehouses/${encodeURIComponent(warehouseId)}/maps/${encodeURIComponent(warehouseMapId)}/mesh/presign`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        }
      ),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["warehouse-map", warehouseId, warehouseMapId] });
      qc.invalidateQueries({ queryKey: ["warehouse-maps", warehouseId] });
    }
  });
}

export function useConfirmWarehouseMapMeshUpload(warehouseId: string, warehouseMapId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: { etag?: string | null; bytes?: number | null }) =>
      apiFetch<WarehouseMapMeshConfirm>(
        `/warehouses/${encodeURIComponent(warehouseId)}/maps/${encodeURIComponent(warehouseMapId)}/mesh/confirm`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        }
      ),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["warehouse-map", warehouseId, warehouseMapId] });
      qc.invalidateQueries({ queryKey: ["warehouse-maps", warehouseId] });
      qc.invalidateQueries({ queryKey: ["warehouse-map-mesh-download", warehouseId, warehouseMapId] });
    }
  });
}
