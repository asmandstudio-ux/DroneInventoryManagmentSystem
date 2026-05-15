"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { Topbar } from "@/components/layout/Topbar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/table";
import { useMissions } from "@/queries/missions";
import { useScanResults } from "@/queries/scanResults";
import type { Mission, ScanResult } from "@/lib/types";

export default function ScansPage() {
  const missionsQuery = useMissions({ limit: 100 });
  const missions = useMemo(() => missionsQuery.data ?? [], [missionsQuery.data]);

  const [missionId, setMissionId] = useState<string>("");

  // Pick a sensible default mission once we have data.
  useEffect(() => {
    if (missionId) return;
    const first = missions[0];
    if (first) setMissionId(first.id);
  }, [missions, missionId]);

  const scanResultsQuery = useScanResults(missionId);
  const scans = useMemo(() => scanResultsQuery.data ?? [], [scanResultsQuery.data]);

  const selectedMission = useMemo(
    () => missions.find((m) => m.id === missionId) ?? null,
    [missions, missionId]
  );

  return (
    <>
      <Topbar
        title="Scans"
        right={
          <div className="flex items-center gap-2">
            <div className="w-72">
              <Select
                aria-label="Select mission"
                value={missionId}
                onChange={(e) => setMissionId(e.target.value)}
                disabled={missionsQuery.isLoading || missions.length === 0}
              >
                {missions.length === 0 ? <option value="">No missions</option> : null}
                {missions.map((m: Mission) => (
                  <option key={m.id} value={m.id}>
                    {m.title} ({m.status})
                  </option>
                ))}
              </Select>
            </div>
            {missionId ? (
              <Link className="text-sm text-indigo-300 hover:text-indigo-200" href={`/dashboard/missions/${missionId}`}>
                Mission details
              </Link>
            ) : null}
          </div>
        }
      />

      <div className="flex-1 overflow-auto p-6">
        <Card>
          <CardHeader>
            <CardTitle>
              Scan results{selectedMission ? <span className="text-zinc-400"> · {selectedMission.title}</span> : null}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {missionsQuery.isLoading ? (
              <div className="space-y-3">
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-10 w-full" />
              </div>
            ) : missionsQuery.isError ? (
              <div role="alert" className="rounded-md border border-red-900/60 bg-red-950/40 px-3 py-2 text-sm text-red-200">
                {missionsQuery.error instanceof Error ? missionsQuery.error.message : "Failed to load missions"}
              </div>
            ) : !missionId ? (
              <div className="text-sm text-zinc-400">Select a mission to view its scan results.</div>
            ) : scanResultsQuery.isLoading ? (
              <div className="space-y-3">
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-10 w-full" />
              </div>
            ) : scanResultsQuery.isError ? (
              <div role="alert" className="rounded-md border border-red-900/60 bg-red-950/40 px-3 py-2 text-sm text-red-200">
                {scanResultsQuery.error instanceof Error ? scanResultsQuery.error.message : "Failed to load scan results"}
              </div>
            ) : scans.length === 0 ? (
              <div className="text-sm text-zinc-400">No scan results found for this mission.</div>
            ) : (
              <Table>
                <THead>
                  <TR>
                    <TH>Captured</TH>
                    <TH>Drone</TH>
                    <TH>Evidence</TH>
                  </TR>
                </THead>
                <TBody>
                  {scans.map((s: ScanResult) => (
                    <TR key={s.id}>
                      <TD className="text-zinc-300">
                        <Link className="text-indigo-300 hover:text-indigo-200" href={`/dashboard/scans/${s.id}`}>
                          {new Date(s.captured_at).toLocaleString()}
                        </Link>
                      </TD>
                      <TD className="text-zinc-300">{s.drone_id ?? "—"}</TD>
                      <TD className="text-zinc-400">
                        {s.evidence_object_key ? (
                          <span title={s.evidence_object_key} className="truncate">
                            {s.evidence_object_key}
                          </span>
                        ) : (
                          "—"
                        )}
                      </TD>
                    </TR>
                  ))}
                </TBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>
    </>
  );
}
