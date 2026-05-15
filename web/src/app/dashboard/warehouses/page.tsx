"use client";

import Link from "next/link";
import { Topbar } from "@/components/layout/Topbar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useWarehouses } from "@/queries/warehouses";

export default function WarehousesPage() {
  const { data, isLoading, error, refetch } = useWarehouses();

  return (
    <>
      <Topbar title="Warehouses" />
      <div className="flex-1 overflow-auto p-6">
        {isLoading ? (
          <Card className="p-4">
            <div className="text-sm text-zinc-200">Loading warehouses…</div>
          </Card>
        ) : error ? (
          <Card className="p-4">
            <div className="text-sm font-semibold text-zinc-100">Failed to load warehouses</div>
            <div className="mt-1 text-xs text-zinc-400">{(error as Error).message}</div>
            <div className="mt-3">
              <button
                type="button"
                className="rounded-md border border-zinc-800 bg-zinc-950 px-3 py-2 text-xs text-zinc-200 hover:bg-zinc-900"
                onClick={() => refetch()}
              >
                Retry
              </button>
            </div>
          </Card>
        ) : (
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            {(data ?? []).map((w) => (
              <Card key={w.id} className="hover:border-zinc-700">
                <CardHeader>
                  <CardTitle>{w.name}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="text-sm text-zinc-300">{w.code}</div>
                  <div className="text-xs text-zinc-500">Warehouse ID: {w.id}</div>
                  <Link
                    href={`/dashboard/warehouses/${encodeURIComponent(w.id)}`}
                    className="inline-flex text-sm font-medium text-sky-300 hover:text-sky-200"
                  >
                    Open 3D map viewer →
                  </Link>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </>
  );
}
