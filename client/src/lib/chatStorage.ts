import { UIChatMessage, StoredConversation, ConversationStorage } from '@/types/rag';

const STORAGE_KEY = 'rag_chat_history';
const MAX_CONVERSATIONS = 50;

/**
 * Generate a hash from folder IDs for localStorage key
 */
export function generateFolderHash(folderIds: string[]): string {
  const sorted = [...folderIds].sort();
  return sorted.join(',');
}

/**
 * Get conversation storage from localStorage
 */
function getStorage(): ConversationStorage {
  if (typeof window === 'undefined') return {};

  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored ? JSON.parse(stored) : {};
  } catch (error) {
    console.error('Failed to parse chat storage:', error);
    return {};
  }
}

/**
 * Save conversation storage to localStorage
 */
function saveStorage(storage: ConversationStorage): void {
  if (typeof window === 'undefined') return;

  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(storage));
  } catch (error) {
    console.error('Failed to save chat storage:', error);
  }
}

/**
 * Enforce max conversations limit using LRU eviction
 */
function enforceStorageLimit(storage: ConversationStorage): ConversationStorage {
  const entries = Object.entries(storage);

  if (entries.length <= MAX_CONVERSATIONS) {
    return storage;
  }

  // Sort by lastUpdated (oldest first)
  entries.sort((a, b) => {
    const aConv = a[1] as StoredConversation;
    const bConv = b[1] as StoredConversation;
    return aConv.lastUpdated - bConv.lastUpdated;
  });

  // Keep only the most recent MAX_CONVERSATIONS
  const limitedEntries = entries.slice(-MAX_CONVERSATIONS);

  return Object.fromEntries(limitedEntries);
}

/**
 * Load conversation for specific folder selection
 */
export function loadConversation(folderIds: string[]): UIChatMessage[] {
  if (folderIds.length === 0) return [];

  const hash = generateFolderHash(folderIds);
  const storage = getStorage();
  const conversation = storage[hash];

  if (!conversation) return [];

  // Parse timestamp strings back to Date objects
  return conversation.messages.map(msg => ({
    ...msg,
    timestamp: new Date(msg.timestamp)
  }));
}

/**
 * Save conversation for specific folder selection
 */
export function saveConversation(folderIds: string[], messages: UIChatMessage[]): void {
  if (folderIds.length === 0) return;

  const hash = generateFolderHash(folderIds);
  let storage = getStorage();

  storage[hash] = {
    messages: messages.map(msg => ({
      ...msg,
      timestamp: msg.timestamp instanceof Date
        ? msg.timestamp.toISOString()
        : (typeof msg.timestamp === "string"
           ? msg.timestamp
           : new Date(msg.timestamp).toISOString())
    })),
    lastUpdated: Date.now(),
    folderIds
  };

  // Enforce storage limit
  storage = enforceStorageLimit(storage);

  saveStorage(storage);
}

/**
 * Clear conversation for specific folder selection
 */
export function clearConversation(folderIds: string[]): void {
  if (folderIds.length === 0) return;

  const hash = generateFolderHash(folderIds);
  const storage = getStorage();

  delete storage[hash];

  saveStorage(storage);
}

/**
 * Clear all conversations
 */
export function clearAllConversations(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(STORAGE_KEY);
}

/**
 * Get total number of stored conversations
 */
export function getConversationCount(): number {
  const storage = getStorage();
  return Object.keys(storage).length;
}
