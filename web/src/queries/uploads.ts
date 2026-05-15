"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type { ConfirmUpload, PresignUpload } from "@/lib/types";

export function usePresignEvidenceUpload() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: { scan_result_id: string; content_type: string; filename?: string | null }) =>
      apiFetch<PresignUpload>("/uploads/presign", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      }),
    onSuccess: (_res, payload) => {
      qc.invalidateQueries({ queryKey: ["scan-result", payload.scan_result_id] });
      qc.invalidateQueries({ queryKey: ["scan-results"] });
    }
  });
}

export function useConfirmEvidenceUpload() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: { scan_result_id: string; etag?: string | null; bytes?: number | null }) =>
      apiFetch<ConfirmUpload>("/uploads/confirm", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      }),
    onSuccess: (_res, payload) => {
      qc.invalidateQueries({ queryKey: ["scan-result", payload.scan_result_id] });
      qc.invalidateQueries({ queryKey: ["scan-barcodes", payload.scan_result_id] });
      qc.invalidateQueries({ queryKey: ["scan-results"] });
    }
  });
}
