"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useMemo, useState } from "react";
import { Topbar } from "@/components/layout/Topbar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/table";
import { cn } from "@/lib/cn";
import { useConfirmEvidenceUpload, usePresignEvidenceUpload } from "@/queries/uploads";
import { useProcessScanResult, useScanBarcodes, useScanResult } from "@/queries/scanResult";
import { apiFetch } from "@/lib/api";
import type { BarcodeRead, PresignedDownload } from "@/lib/types";

function getScanIdFromParams(params: Record<string, string | string[] | undefined>) {
  const raw = params.scanId;
  if (Array.isArray(raw)) return raw[0] ?? "";
  return raw ?? "";
}

export default function ScanDetailsPage() {
  const params = useParams<Record<string, string | string[]>>();
  const scanId = useMemo(() => getScanIdFromParams(params), [params]);

  const scanQuery = useScanResult(scanId);
  const barcodesQuery = useScanBarcodes(scanId);

  const presign = usePresignEvidenceUpload();
  const confirm = useConfirmEvidenceUpload();
  const processScan = useProcessScanResult();

  const scan = scanQuery.data;
  const barcodes = barcodesQuery.data ?? [];

  const [file, setFile] = useState<File | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  const actionLink = useMemo(
    () =>
      cn(
        "inline-flex items-center justify-center gap-2 rounded-md font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-zinc-300",
        "h-8 px-3 text-sm"
      ),
    []
  );

  const onPickFile = useCallback((f: File | null) => {
    setUploadError(null);
    setFile(f);
  }, []);

  const onUpload = useCallback(async () => {
    if (!file) return;
    if (!scanId) return;

    setUploadError(null);
    try {
      const contentType = file.type || "application/octet-stream";

      const presigned = await presign.mutateAsync({
        scan_result_id: scanId,
        content_type: contentType,
        filename: file.name
      });

      const putHeaders = new Headers(presigned.headers);
      if (!putHeaders.has("Content-Type")) putHeaders.set("Content-Type", contentType);

      const putRes = await fetch(presigned.url, {
        method: "PUT",
        headers: putHeaders,
        body: file
      });

      if (!putRes.ok) {
        throw new Error(`Evidence upload failed (${putRes.status})`);
      }

      await confirm.mutateAsync({
        scan_result_id: scanId,
        bytes: file.size
      });
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : "Upload failed");
    }
  }, [confirm, file, presign, scanId]);

  const onDownload = useCallback(async () => {
    if (!scanId) return;
    setDownloadError(null);
    try {
      const payload = await apiFetch<PresignedDownload>(`/scan-results/${scanId}/evidence/download`);
      window.open(payload.url, "_blank", "noopener,noreferrer");
    } catch (err) {
      setDownloadError(err instanceof Error ? err.message : "Failed to download evidence");
    }
  }, [scanId]);

  const onProcess = useCallback(async () => {
    if (!scanId) return;
    await processScan.mutateAsync(scanId);
  }, [processScan, scanId]);

  const hasEvidence = Boolean(scan?.evidence_object_key);
  const uploadConfirmed = Boolean(scan?.evidence_uploaded_at);

  return (
    <>
      <Topbar
        title="Scan"
        right={
          <div className="flex items-center gap-2">
            <Link href="/dashboard/scans" className={cn(actionLink, "bg-zinc-800 text-zinc-100 hover:bg-zinc-700")}>
              Back
            </Link>
            {scan?.mission_id ? (
              <Link
                href={`/dashboard/missions/${scan.mission_id}`}
                className={cn(actionLink, "bg-transparent text-zinc-100 hover:bg-zinc-900")}
              >
                Mission
              </Link>
            ) : null}
          </div>
        }
      />

      <div className="flex-1 overflow-auto p-6">
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <Card className="lg:col-span-1">
            <CardHeader>
              <CardTitle>Scan details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {scanQuery.isLoading ? (
                <div className="space-y-2">
                  <Skeleton className="h-6 w-2/3" />
                  <Skeleton className="h-4 w-1/2" />
                  <Skeleton className="h-4 w-3/4" />
                </div>
              ) : scanQuery.isError ? (
                <div role="alert" className="rounded-md border border-red-900/60 bg-red-950/40 px-3 py-2 text-sm text-red-200">
                  {scanQuery.error instanceof Error ? scanQuery.error.message : "Failed to load scan"}
                </div>
              ) : !scan ? (
                <div className="text-sm text-zinc-400">Scan not found.</div>
              ) : (
                <>
                  <div className="space-y-1">
                    <div className="text-sm text-zinc-400">Captured</div>
                    <div className="text-sm text-zinc-100">{new Date(scan.captured_at).toLocaleString()}</div>
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="text-sm text-zinc-400">Drone</div>
                    <div className="text-sm text-zinc-100">{scan.drone_id ?? "—"}</div>
                  </div>

                  <div className="space-y-1">
                    <div className="text-sm text-zinc-400">Evidence object</div>
                    <div className="text-xs text-zinc-200 break-all">{scan.evidence_object_key ?? "—"}</div>
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="text-sm text-zinc-400">Upload</div>
                    <Badge tone={uploadConfirmed ? "success" : hasEvidence ? "warning" : "neutral"}>
                      {uploadConfirmed ? "confirmed" : hasEvidence ? "pending confirm" : "missing"}
                    </Badge>
                  </div>

                  {scan.evidence_uploaded_at ? (
                    <div className="space-y-1">
                      <div className="text-sm text-zinc-400">Uploaded</div>
                      <div className="text-sm text-zinc-100">{new Date(scan.evidence_uploaded_at).toLocaleString()}</div>
                    </div>
                  ) : null}

                  {scan.evidence_bytes != null ? (
                    <div className="flex items-center justify-between">
                      <div className="text-sm text-zinc-400">Bytes</div>
                      <div className="text-sm text-zinc-100">{scan.evidence_bytes}</div>
                    </div>
                  ) : null}

                  {scan.evidence_etag ? (
                    <div className="space-y-1">
                      <div className="text-sm text-zinc-400">ETag</div>
                      <div className="text-xs text-zinc-200 break-all">{scan.evidence_etag}</div>
                    </div>
                  ) : null}

                  {downloadError ? (
                    <div role="alert" className="rounded-md border border-red-900/60 bg-red-950/40 px-3 py-2 text-sm text-red-200">
                      {downloadError}
                    </div>
                  ) : null}

                  <div className="flex flex-wrap gap-2">
                    <Button variant="secondary" size="sm" onClick={onDownload} disabled={!hasEvidence}>
                      Download evidence
                    </Button>
                    <Button variant="primary" size="sm" onClick={onProcess} disabled={processScan.isPending}>
                      {processScan.isPending ? "Queued…" : "Process"}
                    </Button>
                  </div>
                </>
              )}
            </CardContent>
          </Card>

          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>Evidence upload</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                <div className="space-y-1">
                  <div className="text-sm text-zinc-300">Select file</div>
                  <Input
                    type="file"
                    accept="image/jpeg,image/png"
                    onChange={(e) => onPickFile(e.target.files?.[0] ?? null)}
                  />
                  <div className="text-xs text-zinc-400">
                    {file ? `${file.name} (${file.size} bytes)` : "JPEG/PNG supported"}
                  </div>
                </div>

                <div className="flex items-end justify-start gap-2">
                  <Button variant="primary" onClick={onUpload} disabled={!file || presign.isPending || confirm.isPending}>
                    {presign.isPending || confirm.isPending ? "Uploading…" : "Upload & confirm"}
                  </Button>
                </div>
              </div>

              {uploadError ? (
                <div role="alert" className="rounded-md border border-red-900/60 bg-red-950/40 px-3 py-2 text-sm text-red-200">
                  {uploadError}
                </div>
              ) : null}
            </CardContent>
          </Card>

          <Card className="lg:col-span-3">
            <CardHeader>
              <CardTitle>Barcodes</CardTitle>
            </CardHeader>
            <CardContent>
              {barcodesQuery.isLoading ? (
                <div className="space-y-3">
                  <Skeleton className="h-10 w-full" />
                  <Skeleton className="h-10 w-full" />
                </div>
              ) : barcodesQuery.isError ? (
                <div role="alert" className="rounded-md border border-red-900/60 bg-red-950/40 px-3 py-2 text-sm text-red-200">
                  {barcodesQuery.error instanceof Error ? barcodesQuery.error.message : "Failed to load barcodes"}
                </div>
              ) : barcodes.length === 0 ? (
                <div className="text-sm text-zinc-400">No decoded barcodes yet.</div>
              ) : (
                <Table>
                  <THead>
                    <TR>
                      <TH>Value</TH>
                      <TH>Symbology</TH>
                      <TH>Confidence</TH>
                      <TH>Created</TH>
                    </TR>
                  </THead>
                  <TBody>
                    {barcodes.map((b: BarcodeRead) => (
                      <TR key={b.id}>
                        <TD className="font-medium text-zinc-100">{b.value}</TD>
                        <TD className="text-zinc-300">{b.symbology}</TD>
                        <TD className="text-zinc-300">{Math.round(b.confidence * 100)}%</TD>
                        <TD className="text-zinc-400">{new Date(b.created_at).toLocaleString()}</TD>
                      </TR>
                    ))}
                  </TBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </>
  );
}

