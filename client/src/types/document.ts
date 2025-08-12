export interface Document {
  id: string;
  filename: string;
  file_type: string;
  file_size: number;
  folder_id: string;
  file_path: string;
  uploaded_by: string;
  embedding_status?: 'pending' | 'processing' | 'completed' | 'failed';
  created_at: string;
  updated_at: string;
  processed_at?: string;
  error_message?: string;
  chunk_count?: number;
  embedding_count?: number;
}

export interface DocumentWithFolder extends Document {
  folder: {
    id: string;
    name: string;
  };
}