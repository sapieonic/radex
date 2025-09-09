export type ConfluenceType = "cloud" | "server" | "data_center";
export type ImportType = "page" | "space" | "page_tree";
export type SyncStatus = "pending" | "in_progress" | "completed" | "failed" | "partial";

export interface ConfluenceCredential {
  id: string;
  confluence_type: ConfluenceType;
  base_url: string;
  email: string | null;
  created_at: string;
  updated_at: string;
  is_valid: boolean;
}

export interface ConfluenceAuthRequest {
  confluence_type: ConfluenceType;
  base_url: string;
  email?: string;
  api_token?: string;
  oauth_token?: string;
  oauth_refresh_token?: string;
  token_expires_at?: string;
}

export interface ConfluenceSpace {
  key: string;
  name: string;
  description?: string;
  homepage_id?: string;
}

export interface ConfluencePage {
  id: string;
  title: string;
  space_key: string;
  parent_id?: string;
  version: number;
  created_date?: string;
  modified_date?: string;
  has_children: boolean;
  has_attachments: boolean;
}

export interface ConfluenceSearchRequest {
  credential_id: string;
  query: string;
  search_type?: "cql" | "text";
  limit?: number;
}

export interface ConfluenceSearchResult {
  id: string;
  title: string;
  space_key: string;
  space_name: string;
  excerpt?: string;
  url?: string;
  last_modified?: string;
}

export interface ConfluenceImportRequest {
  credential_id: string;
  folder_id: string;
  import_type: ImportType;
  space_key?: string;
  page_id?: string;
  include_attachments?: boolean;
  include_comments?: boolean;
  recursive?: boolean;
}

export interface ConfluenceImport {
  id: string;
  import_type: ImportType;
  sync_status: SyncStatus;
  total_pages: number;
  processed_pages: number;
  error_message?: string;
  created_at: string;
  last_sync_at?: string;
  space_key?: string;
  page_id?: string;
  folder_id: string;
}

export interface ConfluenceImportStatus {
  id: string;
  status: SyncStatus;
  total_pages: number;
  processed_pages: number;
  error_message?: string;
  created_at: string;
  last_sync_at?: string;
  progress_percentage: number;
}

export interface ConfluenceBatchImportRequest {
  credential_id: string;
  folder_id: string;
  imports: Array<{
    import_type: ImportType;
    space_key?: string;
    page_id?: string;
  }>;
}

export interface ConfluenceBatchImportResponse {
  job_ids: string[];
  total_jobs: number;
  status: string;
}

export interface ConfluenceSyncRequest {
  import_id: string;
  force_full_sync?: boolean;
}

export interface ConfluenceSyncResponse {
  import_id: string;
  status: string;
  pages_updated: number;
  pages_added: number;
  pages_deleted: number;
  sync_started_at: string;
  sync_completed_at?: string;
}