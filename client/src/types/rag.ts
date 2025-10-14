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
  folder_id: string;
  chunk_text: string;
  relevance_score: number;
  page_number?: number;
  metadata?: Record<string, unknown>;
}

// Chat-specific types matching OpenAI format
export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

// UI-specific chat message with additional metadata
export interface UIChatMessage extends ChatMessage {
  id: string;
  timestamp: string | Date;
  sources?: RAGSource[];
}

export interface ChatRequest {
  messages: ChatMessage[];
  folder_ids: string[];
  limit?: number;
  min_relevance_score?: number;
}

export interface ChatResponse {
  role: 'assistant';
  content: string;
  sources: RAGSource[];
  total_chunks: number;
  processing_time: number;
  reformulated_query?: string;
}

export interface QuerySuggestion {
  suggestion: string;
  category: string;
}

// LocalStorage types
export interface StoredConversation {
  messages: UIChatMessage[];
  lastUpdated: number;
  folderIds: string[];
}

export interface ConversationStorage {
  [folderHash: string]: StoredConversation;
}