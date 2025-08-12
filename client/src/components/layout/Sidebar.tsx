'use client';

import { useState, useEffect } from 'react';
import { Folder, FolderPlus, ChevronRight, ChevronDown } from 'lucide-react';
import { Folder as FolderType } from '@/types/folder';
import apiClient from '@/lib/api';
import { Button } from '@/components/ui/Button';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

interface FolderTreeProps {
  folders: FolderType[];
  level?: number;
  onFolderSelect: (folder: FolderType) => void;
}

function FolderTree({ folders, level = 0, onFolderSelect }: FolderTreeProps) {
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set());

  const toggleExpanded = (folderId: string) => {
    const newExpanded = new Set(expandedFolders);
    if (newExpanded.has(folderId)) {
      newExpanded.delete(folderId);
    } else {
      newExpanded.add(folderId);
    }
    setExpandedFolders(newExpanded);
  };

  const rootFolders = folders.filter(f => f.parent_id === null);
  
  const getChildFolders = (parentId: string) => {
    return folders.filter(f => f.parent_id === parentId);
  };

  const renderFolder = (folder: FolderType, currentLevel: number) => {
    const childFolders = getChildFolders(folder.id);
    const hasChildren = childFolders.length > 0;
    const isExpanded = expandedFolders.has(folder.id);

    return (
      <div key={folder.id}>
        <div
          className={`flex items-center space-x-2 py-2 px-2 hover:bg-gray-100 cursor-pointer rounded-md`}
          style={{ paddingLeft: `${currentLevel * 16 + 8}px` }}
          onClick={() => onFolderSelect(folder)}
        >
          {hasChildren && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                toggleExpanded(folder.id);
              }}
              className="p-1 hover:bg-gray-200 rounded"
            >
              {isExpanded ? (
                <ChevronDown className="w-3 h-3" />
              ) : (
                <ChevronRight className="w-3 h-3" />
              )}
            </button>
          )}
          {!hasChildren && <div className="w-5" />}
          <Folder className="w-4 h-4 text-blue-600" />
          <span className="text-sm font-medium text-gray-700 truncate">
            {folder.name}
          </span>
        </div>
        {hasChildren && isExpanded && (
          <div>
            {childFolders.map(child => renderFolder(child, currentLevel + 1))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-1">
      {rootFolders.map(folder => renderFolder(folder, level))}
    </div>
  );
}

export default function Sidebar({ isOpen, onClose }: SidebarProps) {
  const [folders, setFolders] = useState<FolderType[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newFolderName, setNewFolderName] = useState('');

  useEffect(() => {
    loadFolders();
  }, []);

  const loadFolders = async () => {
    try {
      setIsLoading(true);
      const data = await apiClient.getFolders();
      setFolders(data);
    } catch (error) {
      console.error('Failed to load folders:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateFolder = async () => {
    if (!newFolderName.trim()) return;

    try {
      await apiClient.createFolder({ name: newFolderName });
      setNewFolderName('');
      setShowCreateForm(false);
      loadFolders();
    } catch (error) {
      console.error('Failed to create folder:', error);
    }
  };

  const handleFolderSelect = (folder: FolderType) => {
    window.location.href = `/folders/${folder.id}`;
  };

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 md:hidden"
          onClick={onClose}
        />
      )}
      
      {/* Sidebar */}
      <div
        className={`fixed md:static inset-y-0 left-0 z-50 w-64 bg-white border-r border-gray-200 transform transition-transform duration-300 ease-in-out md:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex flex-col h-full">
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">Folders</h2>
              <Button
                size="sm"
                onClick={() => setShowCreateForm(true)}
                className="text-xs"
              >
                <FolderPlus className="w-4 h-4" />
              </Button>
            </div>
            
            {showCreateForm && (
              <div className="mt-3 space-y-2">
                <input
                  type="text"
                  value={newFolderName}
                  onChange={(e) => setNewFolderName(e.target.value)}
                  placeholder="Folder name"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm text-gray-900 bg-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-transparent"
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      handleCreateFolder();
                    }
                  }}
                />
                <div className="flex space-x-2">
                  <Button size="sm" onClick={handleCreateFolder}>
                    Create
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => {
                      setShowCreateForm(false);
                      setNewFolderName('');
                    }}
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            )}
          </div>
          
          <div className="flex-1 overflow-y-auto p-4">
            {isLoading ? (
              <div className="text-sm text-gray-500">Loading folders...</div>
            ) : folders.length === 0 ? (
              <div className="text-sm text-gray-500">No folders yet</div>
            ) : (
              <FolderTree folders={folders} onFolderSelect={handleFolderSelect} />
            )}
          </div>
        </div>
      </div>
    </>
  );
}