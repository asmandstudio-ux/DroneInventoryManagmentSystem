"use client";

import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type { BarcodeRead, PresignedDownload, ScanJob, ScanResult } from "@/lib/types";

export function useScanJob(scanJobId: string | null | undefined) {
  return useQuery({
    queryKey: ["scan-job", scanJobId ?? ""],
    queryFn: () => apiFetch<ScanJob>(`/scan-jobs/${encodeURIComponent(scanJobId as string)}`),
    enabled: Boolean(scanJobId)
  });
}

export function useScanResult(scanResultId: string | null | undefined) {
  return useQuery({
    queryKey: ["scan-result", scanResultId ?? ""],
    queryFn: () => apiFetch<ScanResult>(`/scan-results/${encodeURIComponent(scanResultId as string)}`),
    enabled: Boolean(scanResultId)
  });
}

export function useScanResultEvidenceDownload(scanResultId: string | null | undefined) {
  return useQuery({
    queryKey: ["scan-result-evidence", scanResultId ?? ""],
    queryFn: () =>
      apiFetch<PresignedDownload>(`/scan-results/${encodeURIComponent(scanResultId as string)}/evidence/download`),
    enabled: Boolean(scanResultId)
  });
}

export function useScanResultBarcodes(scanResultId: string | null | undefined) {
  return useQuery({
    queryKey: ["scan-result-barcodes", scanResultId ?? ""],
    queryFn: () => apiFetch<BarcodeRead[]>(`/scan-results/${encodeURIComponent(scanResultId as string)}/barcodes`),
    enabled: Boolean(scanResultId)
  });
}
