"""Google Drive上の翻訳済みPDF保存・読込

Streamlit Secrets に以下を設定して使用：
  - GDRIVE_FOLDER_ID: 保存先Google DriveフォルダID
  - GDRIVE_SERVICE_ACCOUNT_JSON: サービスアカウントの認証情報JSON（文字列）

サービスアカウントは Drive フォルダに対して「編集者」権限を持っている必要あり。
未設定の場合 `is_available()` が False を返し、Drive連携機能はスキップされる。
"""

from __future__ import annotations

import io
import json
from dataclasses import dataclass
from pathlib import Path

import streamlit as st


SCOPES = ["https://www.googleapis.com/auth/drive.file"]


@dataclass
class DriveFile:
    """Drive上のファイル情報"""
    id: str
    name: str
    created_at: str  # ISO形式
    size_bytes: int
    web_view_link: str


def _load_service_account_info() -> dict | None:
    """Streamlit Secrets からサービスアカウント情報を取得（複数形式対応）

    対応する形式:
      1. TOMLセクション [gdrive_service_account] でフィールド分割
      2. GDRIVE_SERVICE_ACCOUNT_JSON にJSON文字列で格納
    """
    # 形式1: TOMLセクション
    try:
        section = st.secrets.get("gdrive_service_account", None)
        if section:
            return dict(section)
    except Exception:
        pass

    # 形式2: JSON文字列 or dict
    try:
        sa_value = st.secrets.get("GDRIVE_SERVICE_ACCOUNT_JSON", None)
    except Exception:
        return None
    if not sa_value:
        return None

    if isinstance(sa_value, dict):
        return dict(sa_value)
    if isinstance(sa_value, str):
        try:
            return json.loads(sa_value)
        except json.JSONDecodeError as e:
            raise RuntimeError(
                "GDRIVE_SERVICE_ACCOUNT_JSON のJSON解析に失敗しました。"
                "Streamlit Secretsで `\"\"\"` ではなく `'''` で囲むか、"
                "TOMLセクション形式 [gdrive_service_account] で記述してください。"
                f" 原因: {e}"
            ) from e
    return None


def is_available() -> bool:
    """Drive連携が設定済みか判定"""
    try:
        folder = st.secrets.get("GDRIVE_FOLDER_ID", None)
        if not folder:
            return False
        sa_info = _load_service_account_info()
        return sa_info is not None
    except Exception:
        return False


@st.cache_resource
def _get_service():
    """Drive APIクライアント（cache_resourceでアプリ起動中は使い回し）"""
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    sa_info = _load_service_account_info()
    if sa_info is None:
        raise RuntimeError("サービスアカウント情報が未設定です")
    creds = service_account.Credentials.from_service_account_info(sa_info, scopes=SCOPES)
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def upload_pdf(local_path, drive_filename: str) -> DriveFile:
    """ローカルPDFをDriveにアップロード"""
    from googleapiclient.http import MediaFileUpload

    folder_id = st.secrets["GDRIVE_FOLDER_ID"]
    service = _get_service()

    file_metadata = {
        "name": drive_filename,
        "parents": [folder_id],
    }
    media = MediaFileUpload(str(local_path), mimetype="application/pdf", resumable=False)

    result = service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id,name,size,createdTime,webViewLink",
        supportsAllDrives=True,
    ).execute()

    return DriveFile(
        id=result["id"],
        name=result["name"],
        created_at=result.get("createdTime", ""),
        size_bytes=int(result.get("size", 0) or 0),
        web_view_link=result.get("webViewLink", ""),
    )


def list_files(limit: int = 200) -> list[DriveFile]:
    """Driveフォルダ内のPDFファイル一覧（新しい順）"""
    folder_id = st.secrets["GDRIVE_FOLDER_ID"]
    service = _get_service()

    query = (
        f"'{folder_id}' in parents and trashed=false and mimeType='application/pdf'"
    )
    result = service.files().list(
        q=query,
        orderBy="createdTime desc",
        pageSize=limit,
        fields="files(id,name,size,createdTime,webViewLink)",
        supportsAllDrives=True,
        includeItemsFromAllDrives=True,
    ).execute()

    items = result.get("files", [])
    return [
        DriveFile(
            id=f["id"],
            name=f["name"],
            created_at=f.get("createdTime", ""),
            size_bytes=int(f.get("size", 0) or 0),
            web_view_link=f.get("webViewLink", ""),
        )
        for f in items
    ]


def download_file(file_id: str) -> bytes:
    """Driveからファイルをダウンロードしてバイト列を返す"""
    from googleapiclient.http import MediaIoBaseDownload

    service = _get_service()
    request = service.files().get_media(fileId=file_id, supportsAllDrives=True)
    buf = io.BytesIO()
    downloader = MediaIoBaseDownload(buf, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    buf.seek(0)
    return buf.read()


def delete_file(file_id: str):
    """Driveからファイルを削除"""
    service = _get_service()
    service.files().delete(fileId=file_id, supportsAllDrives=True).execute()
