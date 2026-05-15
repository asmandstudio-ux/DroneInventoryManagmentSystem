import { Topbar } from "@/components/layout/Topbar";
import { WarehouseViewerClient } from "./WarehouseViewerClient";

export default async function WarehouseViewerPage(props: { params: Promise<{ warehouseId: string }> }) {
  const { warehouseId } = await props.params;

  return (
    <>
      <Topbar title={`Warehouse: ${warehouseId}`} />
      <div className="flex-1 overflow-auto p-6">
        <WarehouseViewerClient warehouseId={warehouseId} />
      </div>
    </>
  );
}
