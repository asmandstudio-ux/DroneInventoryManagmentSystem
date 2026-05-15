"use client";

import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type { Warehouse } from "@/lib/types";

export function useWarehouses() {
  return useQuery({
    queryKey: ["warehouses"],
    queryFn: () => apiFetch<Warehouse[]>("/warehouses")
  });
}

export function useWarehouse(warehouseId: string) {
  return useQuery({
    queryKey: ["warehouse", warehouseId],
    queryFn: () => apiFetch<Warehouse>(`/warehouses/${encodeURIComponent(warehouseId)}`),
    enabled: Boolean(warehouseId)
  });
}
