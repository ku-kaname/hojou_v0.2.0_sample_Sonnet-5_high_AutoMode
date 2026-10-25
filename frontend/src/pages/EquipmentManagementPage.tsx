// 備品管理画面（S09、F14・F15）
//
// 【概要】
// 管理者が備品の登録・編集・無効化・再有効化・CSV一括登録を行う画面。
// 一覧表示、新規登録フォーム、選択した備品の編集フォーム、CSV一括登録フォームを1画面上にまとめる。

import { useCallback, useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import {
  bulkImportEquipment,
  createEquipment,
  disableEquipment,
  enableEquipment,
  searchEquipment,
  updateEquipment,
} from "../api/equipment";
import { ApiError } from "../api/client";
import type { ApiRowError } from "../api/client";
import type { EquipmentListItemResponse } from "../types/api";

export function EquipmentManagementPage() {
  const [equipmentList, setEquipmentList] = useState<EquipmentListItemResponse[]>([]);
  const [listErrorMessage, setListErrorMessage] = useState<string | null>(null);
  const [isLoadingEquipment, setIsLoadingEquipment] = useState(true);

  const [newAssetNumber, setNewAssetNumber] = useState("");
  const [newName, setNewName] = useState("");
  const [newCategory, setNewCategory] = useState("");
  const [newDescription, setNewDescription] = useState("");
  const [newLocation, setNewLocation] = useState("");
  const [createErrorMessage, setCreateErrorMessage] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);

  const [selectedAssetNumber, setSelectedAssetNumber] = useState<string | null>(null);
  const [editName, setEditName] = useState("");
  const [editCategory, setEditCategory] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const [editLocation, setEditLocation] = useState("");
  const [editErrorMessage, setEditErrorMessage] = useState<string | null>(null);
  const [isSavingEdit, setIsSavingEdit] = useState(false);

  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [csvErrorMessage, setCsvErrorMessage] = useState<string | null>(null);
  const [csvRowErrors, setCsvRowErrors] = useState<ApiRowError[]>([]);
  const [csvSuccessMessage, setCsvSuccessMessage] = useState<string | null>(null);
  const [isImportingCsv, setIsImportingCsv] = useState(false);
  const csvFileInputRef = useRef<HTMLInputElement | null>(null);

  const loadEquipmentList = useCallback(async () => {
    setIsLoadingEquipment(true);
    setListErrorMessage(null);
    try {
      const fetchedEquipmentList = await searchEquipment({});
      setEquipmentList(fetchedEquipmentList);
    } catch (error) {
      setListErrorMessage(error instanceof ApiError ? error.message : "備品一覧の取得に失敗しました");
    } finally {
      setIsLoadingEquipment(false);
    }
  }, []);

  useEffect(() => {
    void loadEquipmentList();
  }, [loadEquipmentList]);

  async function handleCreateEquipment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setCreateErrorMessage(null);
    setIsCreating(true);
    try {
      await createEquipment({
        asset_number: newAssetNumber,
        name: newName,
        category: newCategory,
        description: newDescription === "" ? null : newDescription,
        location: newLocation === "" ? null : newLocation,
      });
      setNewAssetNumber("");
      setNewName("");
      setNewCategory("");
      setNewDescription("");
      setNewLocation("");
      await loadEquipmentList();
    } catch (error) {
      setCreateErrorMessage(error instanceof ApiError ? error.message : "備品の登録に失敗しました");
    } finally {
      setIsCreating(false);
    }
  }

  function handleSelectEquipment(equipment: EquipmentListItemResponse) {
    setSelectedAssetNumber(equipment.asset_number);
    setEditName(equipment.name);
    setEditCategory(equipment.category);
    setEditDescription(equipment.description ?? "");
    setEditLocation(equipment.location ?? "");
    setEditErrorMessage(null);
  }

  async function handleSaveEdit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (selectedAssetNumber === null) {
      return;
    }
    setEditErrorMessage(null);
    setIsSavingEdit(true);
    try {
      await updateEquipment(selectedAssetNumber, {
        name: editName,
        category: editCategory,
        description: editDescription === "" ? null : editDescription,
        location: editLocation === "" ? null : editLocation,
      });
      await loadEquipmentList();
    } catch (error) {
      setEditErrorMessage(error instanceof ApiError ? error.message : "備品の編集に失敗しました");
    } finally {
      setIsSavingEdit(false);
    }
  }

  async function handleToggleActive(equipment: EquipmentListItemResponse) {
    setListErrorMessage(null);
    try {
      if (equipment.is_active) {
        await disableEquipment(equipment.asset_number);
      } else {
        await enableEquipment(equipment.asset_number);
      }
      await loadEquipmentList();
    } catch (error) {
      setListErrorMessage(error instanceof ApiError ? error.message : "備品の状態変更に失敗しました");
    }
  }

  async function handleImportCsv(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (csvFile === null) {
      return;
    }
    setCsvErrorMessage(null);
    setCsvRowErrors([]);
    setCsvSuccessMessage(null);
    setIsImportingCsv(true);
    try {
      const bulkImportResponse = await bulkImportEquipment(csvFile);
      setCsvSuccessMessage(`${bulkImportResponse.registered_count}件の備品を登録しました`);
      setCsvFile(null);
      if (csvFileInputRef.current !== null) {
        csvFileInputRef.current.value = "";
      }
      await loadEquipmentList();
    } catch (error) {
      if (error instanceof ApiError && error.rowErrors !== undefined) {
        setCsvRowErrors(error.rowErrors);
        setCsvErrorMessage(error.message);
      } else {
        setCsvErrorMessage(error instanceof ApiError ? error.message : "CSV一括登録に失敗しました");
      }
    } finally {
      setIsImportingCsv(false);
    }
  }

  return (
    <div className="equipment-management-page">
      <h1>備品管理</h1>

      <section>
        <h2>備品一覧</h2>
        {isLoadingEquipment && <p>読み込み中...</p>}
        {listErrorMessage !== null && <p className="error-message">{listErrorMessage}</p>}
        {!isLoadingEquipment && equipmentList.length === 0 && <p>備品が登録されていません</p>}
        {equipmentList.length > 0 && (
          <table>
            <thead>
              <tr>
                <th>資産番号</th>
                <th>備品名</th>
                <th>分類</th>
                <th>保管場所</th>
                <th>状態</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {equipmentList.map((equipment) => (
                <tr key={equipment.asset_number}>
                  <td>{equipment.asset_number}</td>
                  <td>{equipment.name}</td>
                  <td>{equipment.category}</td>
                  <td>{equipment.location ?? "-"}</td>
                  <td>{equipment.is_active ? "有効" : "無効"}</td>
                  <td>
                    <button type="button" onClick={() => handleSelectEquipment(equipment)}>
                      編集
                    </button>
                    <button type="button" onClick={() => void handleToggleActive(equipment)}>
                      {equipment.is_active ? "無効化" : "再有効化"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section>
        <h2>備品登録</h2>
        <form onSubmit={handleCreateEquipment}>
          <div>
            <label htmlFor="new_asset_number">資産番号</label>
            <input
              id="new_asset_number"
              type="text"
              value={newAssetNumber}
              onChange={(event) => setNewAssetNumber(event.target.value)}
              minLength={1}
              maxLength={32}
              pattern="[A-Za-z0-9-]+"
              required
            />
          </div>
          <div>
            <label htmlFor="new_equipment_name">備品名</label>
            <input
              id="new_equipment_name"
              type="text"
              value={newName}
              onChange={(event) => setNewName(event.target.value)}
              maxLength={100}
              required
            />
          </div>
          <div>
            <label htmlFor="new_equipment_category">分類</label>
            <input
              id="new_equipment_category"
              type="text"
              value={newCategory}
              onChange={(event) => setNewCategory(event.target.value)}
              maxLength={50}
              required
            />
          </div>
          <div>
            <label htmlFor="new_equipment_description">説明</label>
            <input
              id="new_equipment_description"
              type="text"
              value={newDescription}
              onChange={(event) => setNewDescription(event.target.value)}
              maxLength={500}
            />
          </div>
          <div>
            <label htmlFor="new_equipment_location">保管場所</label>
            <input
              id="new_equipment_location"
              type="text"
              value={newLocation}
              onChange={(event) => setNewLocation(event.target.value)}
              maxLength={100}
            />
          </div>
          {createErrorMessage !== null && <p className="error-message">{createErrorMessage}</p>}
          <button type="submit" disabled={isCreating}>
            登録する
          </button>
        </form>
      </section>

      {selectedAssetNumber !== null && (
        <section>
          <h2>備品編集（{selectedAssetNumber}）</h2>
          <form onSubmit={handleSaveEdit}>
            <div>
              <label htmlFor="edit_equipment_name">備品名</label>
              <input
                id="edit_equipment_name"
                type="text"
                value={editName}
                onChange={(event) => setEditName(event.target.value)}
                maxLength={100}
                required
              />
            </div>
            <div>
              <label htmlFor="edit_equipment_category">分類</label>
              <input
                id="edit_equipment_category"
                type="text"
                value={editCategory}
                onChange={(event) => setEditCategory(event.target.value)}
                maxLength={50}
                required
              />
            </div>
            <div>
              <label htmlFor="edit_equipment_description">説明</label>
              <input
                id="edit_equipment_description"
                type="text"
                value={editDescription}
                onChange={(event) => setEditDescription(event.target.value)}
                maxLength={500}
              />
            </div>
            <div>
              <label htmlFor="edit_equipment_location">保管場所</label>
              <input
                id="edit_equipment_location"
                type="text"
                value={editLocation}
                onChange={(event) => setEditLocation(event.target.value)}
                maxLength={100}
              />
            </div>
            {editErrorMessage !== null && <p className="error-message">{editErrorMessage}</p>}
            <button type="submit" disabled={isSavingEdit}>
              保存する
            </button>
          </form>
        </section>
      )}

      <section>
        <h2>備品CSV一括登録</h2>
        <p>ヘッダー行（資産番号・備品名・分類・説明・保管場所の順）を含むCSVファイルを選択してください。</p>
        <form onSubmit={handleImportCsv}>
          <div>
            <label htmlFor="csv_file">CSVファイル</label>
            <input
              id="csv_file"
              type="file"
              accept=".csv"
              ref={csvFileInputRef}
              onChange={(event) => setCsvFile(event.target.files !== null ? event.target.files[0] : null)}
              required
            />
          </div>
          {csvErrorMessage !== null && <p className="error-message">{csvErrorMessage}</p>}
          {csvSuccessMessage !== null && <p className="success-message">{csvSuccessMessage}</p>}
          {csvRowErrors.length > 0 && (
            <table>
              <thead>
                <tr>
                  <th>行番号</th>
                  <th>エラー内容</th>
                </tr>
              </thead>
              <tbody>
                {csvRowErrors.map((rowError, index) => (
                  <tr key={`${rowError.row_number}-${index}`}>
                    <td>{rowError.row_number}</td>
                    <td>{rowError.error_message}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          <button type="submit" disabled={isImportingCsv || csvFile === null}>
            一括登録する
          </button>
        </form>
      </section>
    </div>
  );
}
