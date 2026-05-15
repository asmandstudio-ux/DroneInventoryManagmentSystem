"use client";

import * as React from "react";
import Link from "next/link";
import type { WarehouseMapLocation, WarehouseMapLocations } from "@/lib/types";
import { useScanJob, useScanResult, useScanResultBarcodes, useScanResultEvidenceDownload } from "@/queries/scan";
import { Dialog } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";

type Props = {
  open: boolean;
  warehouseId: string;
  warehouseMapId: string;
  locations: WarehouseMapLocations;
  location: WarehouseMapLocation | null;
  onClose: () => void;
  onDelete: (locationId: string) => void;
  onSave: (nextLocations: WarehouseMapLocations) => void;
};

export function LocationDetailsModal({
  open,
  warehouseId,
  warehouseMapId,
  locations,
  location,
  onClose,
  onDelete,
  onSave
}: Props) {
  const [draft, setDraft] = React.useState<WarehouseMapLocation | null>(location);

  React.useEffect(() => {
    setDraft(location);
  }, [location]);

  const scanJob = useScanJob(draft?.scanJobId);
  const scanResultId = draft?.scanResultId ?? scanJob.data?.scan_result_id ?? null;
  const scanResult = useScanResult(scanResultId);
  const evidence = useScanResultEvidenceDownload(scanResultId);
  const barcodes = useScanResultBarcodes(scanResultId);

  const isDirty = React.useMemo(() => {
    if (!location || !draft) return false;
    // Field-level comparison is clearer than deep-equals libraries; this object is small.
    return JSON.stringify(location) !== JSON.stringify(draft);
  }, [draft, location]);

  const handleClose = React.useCallback(() => {
    if (isDirty) {
      const ok = window.confirm("Discard unsaved changes?");
      if (!ok) return;
    }
    onClose();
  }, [isDirty, onClose]);

  if (!location || !draft) {
    return (
      <Dialog open={open} onClose={handleClose} title="Location details">
        <div className="text-sm text-zinc-300">No location selected.</div>
      </Dialog>
    );
  }

  const setText = (key: keyof WarehouseMapLocation) => (value: string) => {
    const cleaned = value.trim();
    setDraft({ ...draft, [key]: cleaned.length > 0 ? cleaned : null } as WarehouseMapLocation);
  };

  const setNullableString = (key: keyof WarehouseMapLocation) => (value: string) => {
    setDraft({ ...draft, [key]: value.length > 0 ? value : null } as WarehouseMapLocation);
  };

  const setNumber = (key: keyof WarehouseMapLocation, opts?: { min?: number; max?: number }) => (raw: string) => {
    if (raw === "") {
      setDraft({ ...draft, [key]: null } as WarehouseMapLocation);
      return;
    }
    const parsed = Number(raw);
    if (!Number.isFinite(parsed)) return;
    const clamped = Math.max(opts?.min ?? -Infinity, Math.min(opts?.max ?? Infinity, parsed));
    setDraft({ ...draft, [key]: clamped } as WarehouseMapLocation);
  };

  const footer = (
    <div className="flex items-center justify-between gap-2">
      <Button
        variant="danger"
        onClick={() => {
          const ok = window.confirm(`Delete marker "${draft.label}"? This cannot be undone.`);
          if (!ok) return;
          onDelete(draft.id);
        }}
      >
        Delete marker
      </Button>
      <div className="flex items-center justify-end gap-2">
        <Button variant="secondary" onClick={handleClose}>
          Cancel
        </Button>
        <Button
          onClick={() => {
            const nextLocations: WarehouseMapLocations = {
              ...locations,
              updatedAt: new Date().toISOString(),
              locations: locations.locations.map((l) => (l.id === draft.id ? draft : l))
            };

            onSave(nextLocations);
          }}
        >
          Save changes
        </Button>
      </div>
    </div>
  );

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      title={draft.label}
      description={`Warehouse: ${warehouseId} • Map: ${warehouseMapId} • Marker: ${draft.id} • Zone: ${draft.zone ?? "—"}`}
      footer={footer}
    >
      <div className="space-y-4">
        <div className="grid gap-3 md:grid-cols-2">
          <label className="space-y-1">
            <div className="text-xs text-zinc-400">Label</div>
            <Input
              value={draft.label}
              onChange={(e) => setDraft({ ...draft, label: e.target.value })}
              aria-label="Location label"
            />
          </label>

          <label className="space-y-1">
            <div className="text-xs text-zinc-400">Zone</div>
            <Input
              value={draft.zone ?? ""}
              onChange={(e) => setText("zone")(e.target.value)}
              placeholder="receiving / storage / quality"
              aria-label="Location zone"
            />
          </label>
        </div>

        <label className="space-y-1">
          <div className="text-xs text-zinc-400">Notes</div>
          <textarea
            className="min-h-20 w-full rounded-md border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-100 outline-none focus-visible:ring-2 focus-visible:ring-zinc-600"
            value={draft.notes ?? ""}
            onChange={(e) => setNullableString("notes")(e.target.value)}
            placeholder="Operator notes for this scan point…"
            aria-label="Location notes"
          />
        </label>

        <div className="grid gap-3 md:grid-cols-2">
          <label className="space-y-1">
            <div className="text-xs text-zinc-400">Barcode</div>
            <Input
              value={draft.barcode ?? ""}
              onChange={(e) => setText("barcode")(e.target.value)}
              placeholder="A17"
              aria-label="Barcode"
            />
          </label>

          <label className="space-y-1">
            <div className="text-xs text-zinc-400">Scan Job ID</div>
            <Input
              value={draft.scanJobId ?? ""}
              onChange={(e) => setText("scanJobId")(e.target.value)}
              placeholder="UUID"
              aria-label="Scan job id"
            />
          </label>

          <label className="space-y-1">
            <div className="text-xs text-zinc-400">Scan Result ID</div>
            <Input
              value={draft.scanResultId ?? ""}
              onChange={(e) => setText("scanResultId")(e.target.value)}
              placeholder="UUID"
              aria-label="Scan result id"
            />
          </label>

          <label className="space-y-1">
            <div className="text-xs text-zinc-400">Pallet Count</div>
            <Input
              type="number"
              min={0}
              step={1}
              inputMode="numeric"
              value={draft.palletCount ?? ""}
              onChange={(e) => setNumber("palletCount", { min: 0 })(e.target.value)}
              placeholder="24"
              aria-label="Pallet count"
            />
          </label>

          <label className="space-y-1">
            <div className="text-xs text-zinc-400">Capacity %</div>
            <Input
              type="number"
              min={0}
              max={100}
              step={1}
              inputMode="numeric"
              value={draft.capacityPct ?? ""}
              onChange={(e) => setNumber("capacityPct", { min: 0, max: 100 })(e.target.value)}
              placeholder="80"
              aria-label="Capacity percent"
            />
          </label>
        </div>

        <div className="rounded-md border border-zinc-800 bg-zinc-950 p-3">
          <div className="flex items-center justify-between gap-2">
            <div className="text-xs font-semibold text-zinc-100">Linked scan</div>
            {scanResultId ? (
              <Link
                href={`/dashboard/scans/${scanResultId}`}
                className="text-xs text-indigo-300 hover:text-indigo-200"
              >
                Open scan →
              </Link>
            ) : null}
          </div>
          <div className="mt-1 text-xs text-zinc-400">
            {scanResultId ? (
              <>
                Result: {scanResultId}
                {scanResult.data?.captured_at ? ` • Captured: ${scanResult.data.captured_at}` : ""}
              </>
            ) : (
              "No scan linked"
            )}
          </div>

          {scanResultId && (scanResult.isLoading || evidence.isLoading) ? (
            <div className="mt-3 space-y-2">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-48 w-full" />
            </div>
          ) : evidence.isError ? (
            <div role="alert" className="mt-3 rounded-md border border-red-900/60 bg-red-950/40 px-3 py-2 text-xs text-red-200">
              {evidence.error instanceof Error ? evidence.error.message : "Failed to load evidence"}
            </div>
          ) : evidence.data?.url ? (
            <div className="mt-3">
              <div className="text-xs text-zinc-400">Evidence</div>
              <img
                src={evidence.data.url}
                alt="Scan evidence"
                className="mt-1 max-h-64 w-full rounded-md border border-zinc-800 object-contain"
              />
            </div>
          ) : null}

          {scanResultId && barcodes.isLoading ? (
            <div className="mt-3 space-y-2">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-24 w-full" />
            </div>
          ) : barcodes.isError ? (
            <div role="alert" className="mt-3 rounded-md border border-red-900/60 bg-red-950/40 px-3 py-2 text-xs text-red-200">
              {barcodes.error instanceof Error ? barcodes.error.message : "Failed to load barcodes"}
            </div>
          ) : Array.isArray(barcodes.data) && barcodes.data.length > 0 ? (
            <div className="mt-3">
              <div className="text-xs text-zinc-400">Barcodes</div>
              <div className="mt-1 max-h-40 overflow-auto rounded-md border border-zinc-800 bg-zinc-950 px-3 py-2 font-mono text-xs text-zinc-100">
                {barcodes.data.map((b) => (
                  <div key={b.id}>{b.value}</div>
                ))}
              </div>
            </div>
          ) : scanResultId ? (
            <div className="mt-3 text-xs text-zinc-500">No decoded barcodes.</div>
          ) : null}
        </div>
      </div>
    </Dialog>
  );
}
