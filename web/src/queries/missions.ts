"use client";

import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type { Mission } from "@/lib/types";

export function useMissions(params?: { status?: string; limit?: number; offset?: number }) {
  return useQuery({
    queryKey: ["missions", params ?? {}],
    queryFn: () => {
      const q = new URLSearchParams();
      if (params?.status) q.set("status", params.status);
      if (params?.limit != null) q.set("limit", String(params.limit));
      if (params?.offset != null) q.set("offset", String(params.offset));
      const qs = q.toString();
      return apiFetch<Mission[]>(`/missions${qs ? `?${qs}` : ""}`);
    }
  });
}

export function useMission(missionId: string) {
  return useQuery({
    queryKey: ["missions", missionId],
    queryFn: () => apiFetch<Mission>(`/missions/${missionId}`),
    enabled: Boolean(missionId)
  });
}

