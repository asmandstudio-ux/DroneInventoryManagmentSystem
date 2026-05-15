"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type { PresignedDownload, ReportJob } from "@/lib/types";

export function useReportJobs() {
  return useQuery({
    queryKey: ["report-jobs"],
    queryFn: () => apiFetch<ReportJob[]>("/reports"),
    refetchInterval: 5000
  });
}

export function useCreateReportJob() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: { report_type: string; params: Record<string, unknown> }) =>
      apiFetch<ReportJob>("/reports", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["report-jobs"] })
  });
}

export function useReportDownload(jobId: string) {
  return useQuery({
    queryKey: ["report-download", jobId],
    queryFn: () => apiFetch<PresignedDownload>(`/reports/${jobId}/download`),
    enabled: Boolean(jobId)
  });
}

