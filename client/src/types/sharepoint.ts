/**
 * TypeScript types for SharePoint/OneDrive provider
 */

export interface ProviderInfo {
  provider: string;
  display_name: string;
  is_enabled: boolean;
  is_configured: boolean;
}

export interface ProvidersConfigResponse {
  providers: ProviderInfo[];
}

export interface SharePointAuthStartResponse {
  auth_url: string;
  state: string;
}

export interface SharePointAuthCallbackResponse {
  connection_id: string;
  tenant_id: string;
  created_at: string;
}

export interface ProviderConnectionInfo {
  id: string;
  provider: string;
  tenant_id: string;
  created_at: string;
  updated_at: string;
}

export interface ProviderConnectionsResponse {
  connections: ProviderConnectionInfo[];
}

export type DriveItemType = 'file' | 'folder';

export interface DriveItem {
  id: string;
  name: string;
  type: DriveItemType;
  size?: number;
  web_url?: string;
  last_modified?: string;
  e_tag?: string;
  mime_type?: string;
  drive_id: string;
  parent_reference?: Record<string, any>;
  is_synced: boolean;
}

export interface DriveItemsResponse {
  items: DriveItem[];
  next_link?: string;
}

export interface DriveInfo {
  id: string;
  name: string;
  description?: string;
  drive_type: string;
  web_url?: string;
  owner?: Record<string, any>;
}

export interface DrivesResponse {
  drives: DriveInfo[];
}

export interface SiteInfo {
  id: string;
  name: string;
  display_name: string;
  web_url: string;
  description?: string;
}

export interface SitesResponse {
  sites: SiteInfo[];
}

export interface SharePointItemToSync {
  drive_id: string;
  item_id: string;
  e_tag?: string;
}

export interface SyncImportRequest {
  connection_id: string;
  folder_id: string;
  items: SharePointItemToSync[];
}

export interface SyncedItemInfo {
  sharepoint_item_id: string;
  document_id: string;
  filename: string;
  status: 'success' | 'skipped' | 'failed';
  message?: string;
}

export interface SyncImportResponse {
  total: number;
  succeeded: number;
  skipped: number;
  failed: number;
  results: SyncedItemInfo[];
}

export interface BreadcrumbItem {
  id: string;
  name: string;
}
