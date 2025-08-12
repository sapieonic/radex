'use client';

import { useState, useEffect, useRef } from 'react';
import { ChatMessage, RAGResponse } from '@/types/rag';
import { Folder } from '@/types/folder';
import apiClient from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { 
  Send, 
  Folder as FolderIcon, 
  MessageSquare, 
  User, 
  Bot, 
  Copy, 
  CheckSquare,
  Square,
  ChevronDown,
  ChevronUp,
  FileText
} from 'lucide-react';

export default function ChatPage() {
  const [folders, setFolders] = useState<Folder[]>([]);
  const [selectedFolders, setSelectedFolders] = useState<Set<string>>(new Set());
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isFoldersLoading, setIsFoldersLoading] = useState(true);
  const [expandedCitations, setExpandedCitations] = useState<Set<string>>(new Set());
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadRAGFolders();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const loadRAGFolders = async () => {
    try {
      setIsFoldersLoading(true);
      const data = await apiClient.getRAGFolders();
      setFolders(data);
    } catch (error) {
      console.error('Failed to load RAG folders:', error);
    } finally {
      setIsFoldersLoading(false);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleFolderToggle = (folderId: string) => {
    const newSelected = new Set(selectedFolders);
    if (newSelected.has(folderId)) {
      newSelected.delete(folderId);
    } else {
      newSelected.add(folderId);
    }
    setSelectedFolders(newSelected);
  };

  const handleSelectAll = () => {
    setSelectedFolders(new Set(folders.map(f => f.id)));
  };

  const handleSelectNone = () => {
    setSelectedFolders(new Set());
  };

  const handleSubmitQuery = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || selectedFolders.size === 0 || isLoading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: query.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setQuery('');
    setIsLoading(true);

    try {
      const response: RAGResponse = await apiClient.queryRAG({
        query: userMessage.content,
        folder_ids: Array.from(selectedFolders),
        limit: 5,
      });

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: response.answer,
        timestamp: new Date(),
        sources: response.sources,
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error: unknown) {
      console.error('Failed to query RAG:', error);
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: 'Sorry, I encountered an error processing your query.',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const copyMessage = (content: string) => {
    navigator.clipboard.writeText(content);
  };

  const toggleCitations = (messageId: string) => {
    const newExpanded = new Set(expandedCitations);
    if (newExpanded.has(messageId)) {
      newExpanded.delete(messageId);
    } else {
      newExpanded.add(messageId);
    }
    setExpandedCitations(newExpanded);
  };

  return (
    <div className="h-[calc(100vh-8rem)] flex">
      {/* Left Sidebar - Folder Selection */}
      <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Select Folders</h2>
          
          <div className="flex space-x-2 mb-4">
            <Button size="sm" variant="secondary" onClick={handleSelectAll}>
              Select All
            </Button>
            <Button size="sm" variant="ghost" onClick={handleSelectNone}>
              Select None
            </Button>
          </div>
          
          <div className="text-sm text-gray-600">
            Selected: {selectedFolders.size} folder{selectedFolders.size !== 1 ? 's' : ''}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          {isFoldersLoading ? (
            <div className="space-y-3">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="flex items-center space-x-3 animate-pulse">
                  <div className="w-4 h-4 bg-gray-200 rounded"></div>
                  <div className="w-4 h-4 bg-gray-200 rounded"></div>
                  <div className="flex-1 h-4 bg-gray-200 rounded"></div>
                </div>
              ))}
            </div>
          ) : folders.length === 0 ? (
            <div className="text-center text-gray-500">
              <FolderIcon className="w-12 h-12 mx-auto mb-2 text-gray-300" />
              <p>No queryable folders available</p>
            </div>
          ) : (
            <div className="space-y-2">
              {folders.map((folder) => (
                <div
                  key={folder.id}
                  className="flex items-center space-x-3 p-2 rounded-lg hover:bg-gray-50 cursor-pointer"
                  onClick={() => handleFolderToggle(folder.id)}
                >
                  {selectedFolders.has(folder.id) ? (
                    <CheckSquare className="w-4 h-4 text-blue-600" />
                  ) : (
                    <Square className="w-4 h-4 text-gray-400" />
                  )}
                  <FolderIcon className="w-4 h-4 text-blue-600" />
                  <div className="flex-1">
                    <div className="font-medium text-sm text-gray-900">{folder.name}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Right Side - Chat Interface */}
      <div className="flex-1 flex flex-col">
        {/* Chat Header */}
        <div className="bg-white border-b border-gray-200 p-4">
          <h1 className="text-xl font-semibold text-gray-900">RAG Chat</h1>
          <p className="text-gray-600">Ask questions about your documents</p>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
          {messages.length === 0 ? (
            <div className="text-center text-gray-500 mt-12">
              <MessageSquare className="w-16 h-16 mx-auto mb-4 text-gray-300" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Start a conversation</h3>
              <p>Select folders and ask questions about your documents</p>
            </div>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div className={`flex space-x-3 max-w-3xl ${message.type === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}>
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                    message.type === 'user' ? 'bg-blue-600' : 'bg-gray-600'
                  }`}>
                    {message.type === 'user' ? (
                      <User className="w-4 h-4 text-white" />
                    ) : (
                      <Bot className="w-4 h-4 text-white" />
                    )}
                  </div>
                  
                  <div className={`rounded-lg px-4 py-3 ${
                    message.type === 'user' 
                      ? 'bg-blue-600 text-white' 
                      : 'bg-white border border-gray-200 text-gray-900'
                  }`}>
                    <div className="text-sm whitespace-pre-wrap">{message.content}</div>
                    
                    {message.sources && message.sources.length > 0 && (
                      <div className="mt-3">
                        <button
                          onClick={() => toggleCitations(message.id)}
                          className="flex items-center space-x-2 text-xs font-medium text-blue-600 hover:text-blue-700 transition-colors"
                        >
                          <FileText className="w-4 h-4" />
                          <span>{message.sources.length} source{message.sources.length !== 1 ? 's' : ''}</span>
                          {expandedCitations.has(message.id) ? (
                            <ChevronUp className="w-3 h-3" />
                          ) : (
                            <ChevronDown className="w-3 h-3" />
                          )}
                        </button>
                        
                        {expandedCitations.has(message.id) && (
                          <div className="mt-3 pt-3 border-t border-gray-200">
                            <div className="space-y-2">
                              {message.sources.map((source, index) => (
                                <div key={index} className="text-xs bg-gray-50 p-2 rounded border border-gray-200">
                                  <div className="font-medium text-gray-900 mb-1">
                                    {source.document_name}
                                  </div>
                                  <div className="text-gray-700 mb-1">
                                    <span className="font-medium">Folder:</span> {source.folder_name}
                                  </div>
                                  <div className="text-gray-600 line-clamp-3 italic">
                                    &quot;{source.chunk_text}&quot;
                                  </div>
                                  <div className="text-blue-600 mt-1 font-medium">
                                    {(source.relevance_score * 100).toFixed(0)}% match
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                    
                    <div className="flex items-center justify-between mt-2 pt-2 border-t border-gray-100">
                      <div className={`text-xs ${message.type === 'user' ? 'text-blue-100' : 'text-gray-500'}`}>
                        {message.timestamp.toLocaleTimeString()}
                      </div>
                      <button
                        onClick={() => copyMessage(message.content)}
                        className={`${message.type === 'user' ? 'text-blue-200 hover:text-white' : 'text-gray-400 hover:text-gray-600'} transition-colors`}
                      >
                        <Copy className="w-3 h-3" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
          
          {isLoading && (
            <div className="flex justify-start">
              <div className="flex space-x-3 max-w-3xl">
                <div className="w-8 h-8 rounded-full bg-gray-600 flex items-center justify-center">
                  <Bot className="w-4 h-4 text-white" />
                </div>
                <div className="bg-white border border-gray-200 rounded-lg px-4 py-3">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="bg-white border-t border-gray-200 p-4">
          {selectedFolders.size === 0 && (
            <div className="mb-3 text-sm text-amber-600 bg-amber-50 border border-amber-200 rounded p-3">
              Please select at least one folder to query.
            </div>
          )}
          
          <form onSubmit={handleSubmitQuery} className="flex space-x-3">
            <div className="flex-1">
              <Input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder={
                  selectedFolders.size === 0 
                    ? 'Select folders to start asking questions...' 
                    : 'Ask a question about your documents...'
                }
                disabled={selectedFolders.size === 0 || isLoading}
                className="w-full"
              />
            </div>
            <Button
              type="submit"
              disabled={!query.trim() || selectedFolders.size === 0 || isLoading}
            >
              <Send className="w-4 h-4" />
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
}