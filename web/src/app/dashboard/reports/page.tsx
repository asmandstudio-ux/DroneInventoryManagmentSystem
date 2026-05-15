"use client";

import { useMemo, useState } from "react";
import { Topbar } from "@/components/layout/Topbar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/table";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/providers/AuthProvider";
import { useCreateReportJob, useReportJobs } from "@/queries/reports";
import type { PresignedDownload, ReportJob, ReportJobStatus } from "@/lib/types";

function statusTone(status: ReportJobStatus) {
  switch (status) {
    case "completed":
      return "success";
    case "running":
      return "info";
    case "queued":
      return "neutral";
    case "failed":
      return "danger";
    default:
      return "neutral";
  }
}

export default function ReportsPage() {
  const { user } = useAuth();
  const jobsQuery = useReportJobs();
  const createJob = useCreateReportJob();

  const [reportType, setReportType] = useState("mission_export");
  const [paramsJson, setParamsJson] = useState('{"format":"json"}');
  const [createError, setCreateError] = useState<string | null>(null);

  const jobs = useMemo(() => jobsQuery.data ?? [], [jobsQuery.data]);

  async function onCreate() {
    setCreateError(null);
    try {
      const params = JSON.parse(paramsJson) as Record<string, unknown>;
      await createJob.mutateAsync({ report_type: reportType, params });
    } catch (err) {
      setCreateError(err instanceof Error ? err.message : "Failed to create report job");
    }
  }

  async function onDownload(jobId: string) {
    const payload = await apiFetch<PresignedDownload>(`/reports/${jobId}/download`);
    window.open(payload.url, "_blank", "noopener,noreferrer");
  }

  return (
    <>
      <Topbar title="Reports" />
      <div className="flex-1 overflow-auto p-6">
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <Card className="lg:col-span-1">
            <CardHeader>
              <CardTitle>Create report</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="text-sm text-zinc-300">
                Reports are currently supervisor-only. Your role: <span className="font-medium">{user?.role ?? "—"}</span>
              </div>

              <div className="space-y-1">
                <label className="text-sm text-zinc-300" htmlFor="reportType">
                  Report type
                </label>
                <Input id="reportType" value={reportType} onChange={(e) => setReportType(e.target.value)} />
              </div>

              <div className="space-y-1">
                <label className="text-sm text-zinc-300" htmlFor="params">
                  Params (JSON)
                </label>
                <textarea
                  id="params"
                  className="h-28 w-full rounded-md border border-zinc-800 bg-zinc-950 p-3 text-sm text-zinc-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-zinc-300"
                  value={paramsJson}
                  onChange={(e) => setParamsJson(e.target.value)}
                />
              </div>

              {createError ? (
                <div role="alert" className="rounded-md border border-red-900/60 bg-red-950/40 px-3 py-2 text-sm text-red-200">
                  {createError}
                </div>
              ) : null}

              <Button variant="primary" onClick={onCreate} disabled={createJob.isPending}>
                {createJob.isPending ? "Creating…" : "Create"}
              </Button>
            </CardContent>
          </Card>

          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>My report jobs</CardTitle>
            </CardHeader>
            <CardContent>
              {jobsQuery.isLoading ? (
                <div className="text-sm text-zinc-400">Loading report jobs…</div>
              ) : jobsQuery.isError ? (
                <div role="alert" className="rounded-md border border-red-900/60 bg-red-950/40 px-3 py-2 text-sm text-red-200">
                  {jobsQuery.error instanceof Error ? jobsQuery.error.message : "Failed to load report jobs"}
                </div>
              ) : jobs.length === 0 ? (
                <div className="text-sm text-zinc-400">No report jobs yet.</div>
              ) : (
                <Table>
                  <THead>
                    <TR>
                      <TH>Type</TH>
                      <TH>Status</TH>
                      <TH>Updated</TH>
                      <TH className="w-28">Download</TH>
                    </TR>
                  </THead>
                  <TBody>
                    {jobs.map((job: ReportJob) => (
                      <TR key={job.id}>
                        <TD className="font-medium">{job.report_type}</TD>
                        <TD>
                          <Badge tone={statusTone(job.status)}>{job.status}</Badge>
                        </TD>
                        <TD className="text-zinc-400">{new Date(job.updated_at).toLocaleString()}</TD>
                        <TD>
                          <Button
                            variant="secondary"
                            size="sm"
                            disabled={job.status !== "completed" || !job.result_object_key}
                            onClick={() => onDownload(job.id)}
                          >
                            Download
                          </Button>
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

