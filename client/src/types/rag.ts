export interface RAGQuery {
  query: string;
  folder_ids: string[];
  limit?: number;
}

export interface RAGResponse {
  answer: string;
  sources: RAGSource[];
  query_time: number;
  folder_ids: string[];
}

export interface RAGSource {
  document_id: string;
  document_name: string;
  folder_name: string;
  chunk_text: string;
  relevance_score: number;
  page_number?: number;
}

export interface ChatMessage {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: RAGSource[];
}

export interface QuerySuggestion {
  suggestion: string;
  category: string;
}