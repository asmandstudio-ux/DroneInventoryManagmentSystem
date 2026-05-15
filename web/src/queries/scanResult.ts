"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type { BarcodeRead, PresignedDownload, ScanJob, ScanResult } from "@/lib/types";

export function useScanResult(scanResultId: string) {
  return useQuery({
    queryKey: ["scan-result", scanResultId],
    queryFn: () => apiFetch<ScanResult>(`/scan-results/${scanResultId}`),
    enabled: Boolean(scanResultId),
    refetchInterval: 5000
  });
}

export function useScanBarcodes(scanResultId: string) {
  return useQuery({
    queryKey: ["scan-barcodes", scanResultId],
    queryFn: () => apiFetch<BarcodeRead[]>(`/scan-results/${scanResultId}/barcodes`),
    enabled: Boolean(scanResultId),
    refetchInterval: 5000
  });
}

export function useScanEvidenceDownload(scanResultId: string) {
  return useQuery({
    queryKey: ["scan-evidence-download", scanResultId],
    queryFn: () => apiFetch<PresignedDownload>(`/scan-results/${scanResultId}/evidence/download`),
    enabled: Boolean(scanResultId)
  });
}

export function useProcessScanResult() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (scanResultId: string) =>
      apiFetch<ScanJob>(`/scan-results/${scanResultId}/process`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: "{}"
      }),
    onSuccess: (_job, scanResultId) => {
      qc.invalidateQueries({ queryKey: ["scan-result", scanResultId] });
      qc.invalidateQueries({ queryKey: ["scan-barcodes", scanResultId] });
      qc.invalidateQueries({ queryKey: ["scan-results"] });
    }
  });
}
