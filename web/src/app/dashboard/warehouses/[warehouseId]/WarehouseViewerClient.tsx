"use client";

import dynamic from "next/dynamic";
import { Card } from "@/components/ui/card";

const WarehouseMapViewer = dynamic(() => import("@/components/warehouses/WarehouseMapViewer"), {
  ssr: false,
  loading: () => (
    <Card className="p-4">
      <div className="text-sm text-zinc-200">Loading 3D viewer…</div>
      <div className="mt-1 text-xs text-zinc-500">Initializing WebGL + three.js</div>
    </Card>
  )
});

export function WarehouseViewerClient({ warehouseId }: { warehouseId: string }) {
  return <WarehouseMapViewer warehouseId={warehouseId} />;
}

