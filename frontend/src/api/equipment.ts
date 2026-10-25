// 備品参照・備品登録管理API呼び出し（備品管理）
//
// 【概要】
// backend/app/main.pyが公開する備品検索・一覧取得、備品詳細取得、備品予約状況取得、
// 備品登録、備品編集、備品無効化、備品再有効化、備品CSV一括登録エンドポイントを呼び出す。

import { apiRequest, apiUploadRequest } from "./client";
import type {
  EquipmentBulkImportResponse,
  EquipmentCreateRequest,
  EquipmentListItemResponse,
  EquipmentResponse,
  EquipmentUpdateRequest,
  ReservationPeriodResponse,
} from "../types/api";

export interface SearchEquipmentParams {
  category?: string;
  keyword?: string;
  is_active?: boolean;
}

export function searchEquipment(params: SearchEquipmentParams = {}): Promise<EquipmentListItemResponse[]> {
  const searchParams = new URLSearchParams();
  if (params.category !== undefined && params.category !== "") {
    searchParams.set("category", params.category);
  }
  if (params.keyword !== undefined && params.keyword !== "") {
    searchParams.set("keyword", params.keyword);
  }
  if (params.is_active !== undefined) {
    searchParams.set("is_active", String(params.is_active));
  }
  const query = searchParams.toString();
  return apiRequest<EquipmentListItemResponse[]>(query === "" ? "/equipment" : `/equipment?${query}`);
}

export function getEquipment(assetNumber: string): Promise<EquipmentListItemResponse> {
  return apiRequest<EquipmentListItemResponse>(`/equipment/${assetNumber}`);
}

export function getEquipmentReservations(assetNumber: string): Promise<ReservationPeriodResponse[]> {
  return apiRequest<ReservationPeriodResponse[]>(`/equipment/${assetNumber}/reservations`);
}

export function createEquipment(equipmentCreateRequest: EquipmentCreateRequest): Promise<EquipmentResponse> {
  return apiRequest<EquipmentResponse>("/equipment", { method: "POST", body: equipmentCreateRequest });
}

export function updateEquipment(
  assetNumber: string,
  equipmentUpdateRequest: EquipmentUpdateRequest,
): Promise<EquipmentResponse> {
  return apiRequest<EquipmentResponse>(`/equipment/${assetNumber}`, {
    method: "PUT",
    body: equipmentUpdateRequest,
  });
}

export function disableEquipment(assetNumber: string): Promise<EquipmentResponse> {
  return apiRequest<EquipmentResponse>(`/equipment/${assetNumber}/disable`, { method: "PUT" });
}

export function enableEquipment(assetNumber: string): Promise<EquipmentResponse> {
  return apiRequest<EquipmentResponse>(`/equipment/${assetNumber}/enable`, { method: "PUT" });
}

export function bulkImportEquipment(csvFile: File): Promise<EquipmentBulkImportResponse> {
  const formData = new FormData();
  formData.append("file", csvFile);
  return apiUploadRequest<EquipmentBulkImportResponse>("/equipment/bulk-import", formData);
}
