import axios, { AxiosInstance } from 'axios';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: BASE_URL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = this.getToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          this.removeToken();
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  private getToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('auth_token');
  }

  private removeToken(): void {
    if (typeof window === 'undefined') return;
    localStorage.removeItem('auth_token');
  }

  public setToken(token: string): void {
    if (typeof window === 'undefined') return;
    localStorage.setItem('auth_token', token);
  }

  // Auth endpoints
  async register(data: { email: string; username: string; password: string }) {
    const response = await this.client.post('/api/v1/auth/register', data);
    return response.data;
  }

  async login(username: string, password: string) {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    
    const response = await this.client.post('/api/v1/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });
    return response.data;
  }

  async getCurrentUser() {
    const response = await this.client.get('/api/v1/auth/me');
    return response.data;
  }

  async refreshToken() {
    const response = await this.client.post('/api/v1/auth/refresh');
    return response.data;
  }

  // Folder endpoints
  async getFolders() {
    const response = await this.client.get('/api/v1/folders');
    return response.data;
  }

  async createFolder(data: { name: string; parent_id?: string }) {
    const response = await this.client.post('/api/v1/folders', data);
    return response.data;
  }

  async getFolder(id: string) {
    const response = await this.client.get(`/api/v1/folders/${id}`);
    return response.data;
  }

  async updateFolder(id: string, data: { name: string }) {
    const response = await this.client.put(`/api/v1/folders/${id}`, data);
    return response.data;
  }

  async deleteFolder(id: string) {
    await this.client.delete(`/api/v1/folders/${id}`);
  }

  async getFolderPermissions(id: string) {
    const response = await this.client.get(`/api/v1/folders/${id}/permissions`);
    return response.data;
  }

  async grantFolderPermission(folderId: string, data: { 
    user_id: string; 
    can_read?: boolean; 
    can_write?: boolean; 
    can_delete?: boolean; 
    is_admin?: boolean; 
  }) {
    const response = await this.client.post(`/api/v1/folders/${folderId}/permissions`, data);
    return response.data;
  }

  async revokeFolderPermission(folderId: string, userId: string) {
    await this.client.delete(`/api/v1/folders/${folderId}/permissions/${userId}`);
  }

  // Document endpoints
  async uploadDocument(folderId: string, file: File) {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await this.client.post(`/api/v1/folders/${folderId}/documents`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  }

  async getFolderDocuments(folderId: string) {
    const response = await this.client.get(`/api/v1/folders/${folderId}/documents`);
    return response.data;
  }

  async getDocument(id: string) {
    const response = await this.client.get(`/api/v1/documents/${id}`);
    return response.data;
  }

  async downloadDocument(id: string) {
    const response = await this.client.get(`/api/v1/documents/${id}/download`, {
      responseType: 'blob'
    });
    return response;
  }

  async deleteDocument(id: string) {
    await this.client.delete(`/api/v1/documents/${id}`);
  }

  // RAG endpoints
  async queryRAG(data: { query: string; folder_ids: string[]; limit?: number }) {
    const response = await this.client.post('/api/v1/rag/query', data);
    return response.data;
  }

  async getRAGFolders() {
    const response = await this.client.get('/api/v1/rag/folders');
    return response.data;
  }

  async suggestQueries(data: { folder_ids: string[] }) {
    const response = await this.client.post('/api/v1/rag/suggest-queries', data);
    return response.data;
  }

  async checkRAGHealth() {
    const response = await this.client.get('/api/v1/rag/health');
    return response.data;
  }

  // User management endpoints (admin only)
  async listUsers(params?: {
    email?: string;
    username?: string;
    is_active?: boolean;
    is_superuser?: boolean;
    limit?: number;
    offset?: number;
  }) {
    const response = await this.client.get('/api/v1/users/', { params });
    return response.data;
  }

  async searchUsers(query: string, limit?: number) {
    const response = await this.client.get('/api/v1/users/search', { 
      params: { q: query, limit } 
    });
    return response.data;
  }

  async createUser(data: {
    email: string;
    username: string;
    password: string;
    is_active?: boolean;
    is_superuser?: boolean;
  }) {
    const response = await this.client.post('/api/v1/users/', data);
    return response.data;
  }

  async getUserById(userId: string) {
    const response = await this.client.get(`/api/v1/users/${userId}`);
    return response.data;
  }

  async updateUser(userId: string, data: {
    email?: string;
    username?: string;
    password?: string;
    is_active?: boolean;
    is_superuser?: boolean;
  }) {
    const response = await this.client.put(`/api/v1/users/${userId}`, data);
    return response.data;
  }

  async deleteUser(userId: string) {
    await this.client.delete(`/api/v1/users/${userId}`);
  }

  async findUser(params: { email?: string; username?: string }) {
    const response = await this.client.get('/api/v1/users/find', { params });
    return response.data;
  }

  // Confluence endpoints
  async addConfluenceAuth(data: {
    confluence_type: string;
    base_url: string;
    email?: string;
    api_token?: string;
    oauth_token?: string;
    oauth_refresh_token?: string;
    token_expires_at?: string;
  }) {
    const response = await this.client.post('/api/v1/confluence/auth', data);
    return response.data;
  }

  async getConfluenceCredentials() {
    const response = await this.client.get('/api/v1/confluence/auth');
    return response.data;
  }

  async deleteConfluenceCredential(credentialId: string) {
    await this.client.delete(`/api/v1/confluence/auth/${credentialId}`);
  }

  async checkConfluenceAuthStatus(credentialId: string) {
    const response = await this.client.get(`/api/v1/confluence/auth/status/${credentialId}`);
    return response.data;
  }

  async getConfluenceSpaces(credentialId: string) {
    const response = await this.client.get('/api/v1/confluence/spaces', {
      params: { credential_id: credentialId }
    });
    return response.data;
  }

  async getConfluenceSpacePages(credentialId: string, spaceKey: string) {
    const response = await this.client.get(`/api/v1/confluence/spaces/${spaceKey}/pages`, {
      params: { credential_id: credentialId }
    });
    return response.data;
  }

  async searchConfluence(data: {
    credential_id: string;
    query: string;
    search_type?: "cql" | "text";
    limit?: number;
  }) {
    const response = await this.client.post('/api/v1/confluence/search', data);
    return response.data;
  }

  async createConfluenceImport(data: {
    credential_id: string;
    folder_id: string;
    import_type: string;
    space_key?: string;
    page_id?: string;
    include_attachments?: boolean;
    include_comments?: boolean;
    recursive?: boolean;
  }) {
    const response = await this.client.post('/api/v1/confluence/import', data);
    return response.data;
  }

  async getConfluenceImportStatus(importId: string) {
    const response = await this.client.get(`/api/v1/confluence/import/${importId}/status`);
    return response.data;
  }

  async createConfluenceBatchImport(data: {
    credential_id: string;
    folder_id: string;
    imports: Array<{
      import_type: string;
      space_key?: string;
      page_id?: string;
    }>;
  }) {
    const response = await this.client.post('/api/v1/confluence/import/batch', data);
    return response.data;
  }

  async syncConfluenceContent(importId: string) {
    const response = await this.client.post(`/api/v1/confluence/sync/${importId}`);
    return response.data;
  }

  async getConfluenceSyncHistory(folderId?: string, limit?: number) {
    const params: Record<string, string | number> = {};
    if (folderId) params.folder_id = folderId;
    if (limit) params.limit = limit;
    
    const response = await this.client.get('/api/v1/confluence/sync/history', { params });
    return response.data;
  }
}

export const apiClient = new ApiClient();
export default apiClient;