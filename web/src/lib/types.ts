export type Role = "operator" | "maintenance" | "supervisor" | "admin";

export type User = {
  id: string;
  email: string;
  full_name?: string | null;
  role: Role;
  created_at: string;
  updated_at: string;
};

export type MissionStatus =
  | "queued"
  | "launching"
  | "in_flight"
  | "returning"
  | "completed"
  | "aborted"
  | "failed";

export type Mission = {
  id: string;
  title: string;
  description?: string | null;
  status: MissionStatus;
  priority: number;
  drone_id?: string | null;
  waypoints: Record<string, unknown>;
  created_by_user_id: string;
  started_at?: string | null;
  completed_at?: string | null;
  created_at: string;
  updated_at: string;
};

export type ScanResult = {
  id: string;
  mission_id: string;
  drone_id?: string | null;
  captured_at: string;
  data: Record<string, unknown>;
  evidence_object_key?: string | null;
  evidence_etag?: string | null;
  evidence_bytes?: number | null;
  evidence_uploaded_at?: string | null;
};

export type ReportJobStatus = "queued" | "running" | "completed" | "failed";

export type ReportJob = {
  id: string;
  report_type: string;
  params: Record<string, unknown>;
  status: ReportJobStatus;
  created_by_user_id: string;
  result_object_key?: string | null;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
};

export type PresignedDownload = {
  url: string;
  expires_in_seconds: number;
};

export type PresignUpload = {
  method: "PUT";
  url: string;
  headers: Record<string, string>;
  expires_in_seconds: number;
  object_key: string;
};

export type ConfirmUpload = {
  scan_result_id: string;
  object_key: string;
  etag?: string | null;
  bytes?: number | null;
  uploaded_at: string;
  scan_job_id?: string | null;
};

export type BarcodeRead = {
  id: string;
  scan_result_id: string;
  symbology: string;
  value: string;
  confidence: number;
  meta: Record<string, unknown>;
  created_at: string;
};

export type ScanJobStatus = "queued" | "running" | "completed" | "failed";

export type ScanJob = {
  id: string;
  scan_result_id: string;
  status: ScanJobStatus;
  result: Record<string, unknown>;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
};

// ---------------------------------------------------------------------------
// Warehouses
// ---------------------------------------------------------------------------

export type Vector3 = { x: number; y: number; z: number };

export type Warehouse = {
  id: string;
  code: string;
  name: string;
  address?: string | null;
  meta: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type WarehouseMap = {
  id: string;
  warehouse_id: string;
  created_by_user_id: string;
  name: string;
  locations: Record<string, unknown>;
  mesh_object_key?: string | null;
  mesh_etag?: string | null;
  mesh_bytes?: number | null;
  mesh_uploaded_at?: string | null;
  created_at: string;
  updated_at: string;
};

export type WarehouseMapLocation = {
  id: string;
  label: string;
  position: Vector3;
  zone?: string | null;
  notes?: string | null;
  barcode?: string | null;
  scanResultId?: string | null;
  scanJobId?: string | null;
  palletCount?: number | null;
  capacityPct?: number | null;
};

export type WarehouseMapLocations = {
  updatedAt: string;
  locations: WarehouseMapLocation[];
};

export type WarehouseMapMeshPresign = {
  method: "PUT";
  url: string;
  headers: Record<string, string>;
  expires_in_seconds: number;
  object_key: string;
};

export type WarehouseMapMeshConfirm = {
  warehouse_map_id: string;
  object_key: string;
  etag?: string | null;
  bytes?: number | null;
  uploaded_at: string;
};
