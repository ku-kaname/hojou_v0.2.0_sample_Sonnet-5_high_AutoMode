// 備品参照API呼び出し（備品管理）
//
// 【概要】
// backend/app/main.pyが公開する備品検索・一覧取得、備品詳細取得、備品予約状況取得
// エンドポイントを呼び出す。

import { apiRequest } from "./client";
import type { EquipmentListItemResponse, ReservationPeriodResponse } from "../types/api";

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
