"use client";

import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type { ScanResult } from "@/lib/types";

export function useScanResults(missionId: string) {
  return useQuery({
    queryKey: ["scan-results", { missionId }],
    queryFn: () => apiFetch<ScanResult[]>(`/scan-results?mission_id=${encodeURIComponent(missionId)}`),
    enabled: Boolean(missionId),
    refetchInterval: 5000
  });
}

