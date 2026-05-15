"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useMemo } from "react";
import { Topbar } from "@/components/layout/Topbar";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/table";
import { cn } from "@/lib/cn";
import { useMission } from "@/queries/missions";
import { useScanResults } from "@/queries/scanResults";
import type { MissionStatus, ScanResult } from "@/lib/types";

function statusTone(status: MissionStatus) {
  switch (status) {
    case "completed":
      return "success";
    case "launching":
    case "in_flight":
    case "returning":
      return "info";
    case "queued":
      return "neutral";
    case "failed":
      return "danger";
    case "aborted":
      return "warning";
    default:
      return "neutral";
  }
}

function getMissionIdFromParams(params: Record<string, string | string[] | undefined>) {
  const raw = params.missionId;
  if (Array.isArray(raw)) return raw[0] ?? "";
  return raw ?? "";
}

export default function MissionDetailsPage() {
  const params = useParams<Record<string, string | string[]>>();
  const missionId = useMemo(() => getMissionIdFromParams(params), [params]);

  const missionQuery = useMission(missionId);
  const scanResultsQuery = useScanResults(missionId);

  const mission = missionQuery.data;
  const scans = scanResultsQuery.data ?? [];

  const actionLink = useMemo(
    () =>
      cn(
        "inline-flex items-center justify-center gap-2 rounded-md font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-zinc-300",
        "h-8 px-3 text-sm"
      ),
    []
  );

  return (
    <>
      <Topbar
        title={mission ? `Mission: ${mission.title}` : "Mission"}
        right={
          <div className="flex items-center gap-2">
            <Link href="/dashboard" className={cn(actionLink, "bg-zinc-800 text-zinc-100 hover:bg-zinc-700")}>
              Back
            </Link>
            <Link href="/dashboard/scans" className={cn(actionLink, "bg-transparent text-zinc-100 hover:bg-zinc-900")}>
              All scans
            </Link>
          </div>
        }
      />

      <div className="flex-1 overflow-auto p-6">
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <Card className="lg:col-span-1">
            <CardHeader>
              <CardTitle>Mission details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {missionQuery.isLoading ? (
                <div className="space-y-2">
                  <Skeleton className="h-6 w-2/3" />
                  <Skeleton className="h-4 w-1/2" />
                  <Skeleton className="h-4 w-3/4" />
                </div>
              ) : missionQuery.isError ? (
                <div role="alert" className="rounded-md border border-red-900/60 bg-red-950/40 px-3 py-2 text-sm text-red-200">
                  {missionQuery.error instanceof Error ? missionQuery.error.message : "Failed to load mission"}
                </div>
              ) : !mission ? (
                <div className="text-sm text-zinc-400">Mission not found.</div>
              ) : (
                <>
                  <div className="flex items-center justify-between">
                    <div className="text-sm text-zinc-400">Status</div>
                    <Badge tone={statusTone(mission.status)}>{mission.status}</Badge>
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="text-sm text-zinc-400">Drone</div>
                    <div className="text-sm text-zinc-100">{mission.drone_id ?? "—"}</div>
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="text-sm text-zinc-400">Priority</div>
                    <div className="text-sm text-zinc-100">{mission.priority}</div>
                  </div>

                  <div className="space-y-1">
                    <div className="text-sm text-zinc-400">Created</div>
                    <div className="text-sm text-zinc-100">{new Date(mission.created_at).toLocaleString()}</div>
                  </div>

                  {mission.description ? (
                    <div className="space-y-1">
                      <div className="text-sm text-zinc-400">Description</div>
                      <div className="text-sm text-zinc-100">{mission.description}</div>
                    </div>
                  ) : null}
                </>
              )}
            </CardContent>
          </Card>

          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>Scan results</CardTitle>
            </CardHeader>
            <CardContent>
              {scanResultsQuery.isLoading ? (
                <div className="space-y-3">
                  <Skeleton className="h-10 w-full" />
                  <Skeleton className="h-10 w-full" />
                </div>
              ) : scanResultsQuery.isError ? (
                <div role="alert" className="rounded-md border border-red-900/60 bg-red-950/40 px-3 py-2 text-sm text-red-200">
                  {scanResultsQuery.error instanceof Error ? scanResultsQuery.error.message : "Failed to load scan results"}
                </div>
              ) : scans.length === 0 ? (
                <div className="text-sm text-zinc-400">No scans recorded for this mission yet.</div>
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
      </div>
    </>
  );
}
