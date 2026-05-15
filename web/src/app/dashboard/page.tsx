"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { Topbar } from "@/components/layout/Topbar";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/table";
import { useMissions } from "@/queries/missions";
import type { Mission, MissionStatus } from "@/lib/types";

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

export default function DashboardHome() {
  const [status, setStatus] = useState<string>("all");
  const missionsQuery = useMissions({ status: status === "all" ? undefined : status });

  const missions = useMemo(() => missionsQuery.data ?? [], [missionsQuery.data]);

  return (
    <>
      <Topbar
        title="Missions"
        right={
          <div className="w-48">
            <Select aria-label="Filter by status" value={status} onChange={(e) => setStatus(e.target.value)}>
              <option value="all">All statuses</option>
              <option value="queued">Queued</option>
              <option value="launching">Launching</option>
              <option value="in_flight">In flight</option>
              <option value="returning">Returning</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
              <option value="aborted">Aborted</option>
            </Select>
          </div>
        }
      />

      <div className="flex-1 overflow-auto p-6">
        <Card>
          <CardHeader>
            <CardTitle>Recent missions</CardTitle>
          </CardHeader>
          <CardContent>
            {missionsQuery.isLoading ? (
              <div className="space-y-3">
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-10 w-full" />
              </div>
            ) : missionsQuery.isError ? (
              <div role="alert" className="rounded-md border border-red-900/60 bg-red-950/40 px-3 py-2 text-sm text-red-200">
                {missionsQuery.error instanceof Error ? missionsQuery.error.message : "Failed to load missions"}
              </div>
            ) : missions.length === 0 ? (
              <div className="text-sm text-zinc-400">No missions found.</div>
            ) : (
              <Table>
                <THead>
                  <TR>
                    <TH>Title</TH>
                    <TH>Status</TH>
                    <TH>Drone</TH>
                    <TH>Priority</TH>
                    <TH>Created</TH>
                  </TR>
                </THead>
                <TBody>
                  {missions.map((m: Mission) => (
                    <TR key={m.id}>
                      <TD className="font-medium">
                        <Link className="text-indigo-300 hover:text-indigo-200" href={`/dashboard/missions/${m.id}`}>
                          {m.title}
                        </Link>
                      </TD>
                      <TD>
                        <Badge tone={statusTone(m.status)}>{m.status}</Badge>
                      </TD>
                      <TD className="text-zinc-300">{m.drone_id ?? "—"}</TD>
                      <TD className="text-zinc-300">{m.priority}</TD>
                      <TD className="text-zinc-400">{new Date(m.created_at).toLocaleString()}</TD>
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
