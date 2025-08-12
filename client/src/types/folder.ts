export interface Folder {
  id: string;
  name: string;
  parent_id: string | null;
  owner_id: string;
  created_at: string;
  updated_at: string;
  document_count?: number;
  children?: Folder[];
  permission_type?: 'read' | 'write' | 'admin';
}

export interface CreateFolderRequest {
  name: string;
  parent_id?: string;
}

export interface UpdateFolderRequest {
  name: string;
}

export interface FolderPermission {
  id: string;
  user_id: string;
  folder_id: string;
  permission_type: 'read' | 'write' | 'admin';
  granted_by: string;
  created_at: string;
  user?: {
    id: string;
    username: string;
    email: string;
  };
}

export interface GrantPermissionRequest {
  user_id: string;
  permission_type: 'read' | 'write' | 'admin';
}