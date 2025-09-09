'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Alert, AlertDescription } from '@/components/ui/Alert';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import apiClient from '@/lib/api';
import { ConfluenceCredential, ConfluenceSpace, ConfluencePage } from '@/types/confluence';
import { 
  Search, 
  ChevronRight, 
  ChevronDown, 
  FileText, 
  Folder, 
  FolderOpen,
  Globe,
  Users,
  Calendar,
  ChevronLeft
} from 'lucide-react';

interface ConfluenceSpaceBrowserProps {
  credentials: ConfluenceCredential[];
  selectedCredential: string | null;
  onCredentialSelect: (credentialId: string) => void;
  onSpaceSelect: (space: ConfluenceSpace) => void;
  onPageSelect: (page: ConfluencePage) => void;
  selectedItems: Set<string>;
  onToggleSelection: (id: string, type: 'space' | 'page') => void;
}

export default function ConfluenceSpaceBrowser({
  credentials,
  selectedCredential,
  onCredentialSelect,
  onSpaceSelect,
  onPageSelect,
  selectedItems,
  onToggleSelection
}: ConfluenceSpaceBrowserProps) {
  const [spaces, setSpaces] = useState<ConfluenceSpace[]>([]);
  const [pages, setPages] = useState<ConfluencePage[]>([]);
  const [isLoadingSpaces, setIsLoadingSpaces] = useState(false);
  const [isLoadingPages, setIsLoadingPages] = useState(false);
  const [error, setError] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSpace, setSelectedSpace] = useState<string | null>(null);
  const [expandedPages, setExpandedPages] = useState<Set<string>>(new Set());
  const [view, setView] = useState<'spaces' | 'pages'>('spaces');

  useEffect(() => {
    if (selectedCredential) {
      loadSpaces();
    } else {
      setSpaces([]);
      setPages([]);
      setView('spaces');
      setSelectedSpace(null);
    }
  }, [selectedCredential]);

  const loadSpaces = async () => {
    if (!selectedCredential) return;

    setIsLoadingSpaces(true);
    setError('');
    
    try {
      const spacesData = await apiClient.getConfluenceSpaces(selectedCredential);
      setSpaces(spacesData);
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to load Confluence spaces');
    } finally {
      setIsLoadingSpaces(false);
    }
  };

  const loadPages = async (spaceKey: string) => {
    if (!selectedCredential) return;

    setIsLoadingPages(true);
    setError('');
    
    try {
      const pagesData = await apiClient.getConfluenceSpacePages(selectedCredential, spaceKey);
      setPages(pagesData);
      setView('pages');
      setSelectedSpace(spaceKey);
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to load space pages');
    } finally {
      setIsLoadingPages(false);
    }
  };

  const handleBackToSpaces = () => {
    setView('spaces');
    setSelectedSpace(null);
    setPages([]);
  };

  const handleSpaceClick = (space: ConfluenceSpace) => {
    onSpaceSelect(space);
    loadPages(space.key);
  };

  const handlePageClick = (page: ConfluencePage) => {
    onPageSelect(page);
  };

  const filteredSpaces = spaces.filter(space =>
    space.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    space.key.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const filteredPages = pages.filter(page =>
    page.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const renderSpacesList = () => (
    <div className="space-y-2">
      {filteredSpaces.map((space) => (
        <div
          key={space.key}
          className={`border rounded-lg p-4 hover:bg-gray-50 cursor-pointer transition-colors ${
            selectedItems.has(`space:${space.key}`) ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
          }`}
          onClick={() => handleSpaceClick(space)}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="flex items-center">
                <input
                  type="checkbox"
                  checked={selectedItems.has(`space:${space.key}`)}
                  onChange={(e) => {
                    e.stopPropagation();
                    onToggleSelection(`space:${space.key}`, 'space');
                  }}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 mr-3"
                />
                <Globe className="w-5 h-5 text-blue-500" />
              </div>
              <div>
                <h3 className="font-medium text-gray-900">{space.name}</h3>
                <p className="text-sm text-gray-500">{space.key}</p>
                {space.description && (
                  <p className="text-xs text-gray-600 mt-1 truncate max-w-md">
                    {space.description}
                  </p>
                )}
              </div>
            </div>
            <ChevronRight className="w-4 h-4 text-gray-400" />
          </div>
        </div>
      ))}
    </div>
  );

  const renderPagesList = () => (
    <div className="space-y-2">
      {filteredPages.map((page) => (
        <div
          key={page.id}
          className={`border rounded-lg p-4 hover:bg-gray-50 cursor-pointer transition-colors ${
            selectedItems.has(`page:${page.id}`) ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
          }`}
          onClick={() => handlePageClick(page)}
        >
          <div className="flex items-center space-x-3">
            <div className="flex items-center">
              <input
                type="checkbox"
                checked={selectedItems.has(`page:${page.id}`)}
                onChange={(e) => {
                  e.stopPropagation();
                  onToggleSelection(`page:${page.id}`, 'page');
                }}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 mr-3"
              />
              <FileText className="w-5 h-5 text-green-500" />
            </div>
            <div className="flex-1">
              <h3 className="font-medium text-gray-900">{page.title}</h3>
              <div className="flex items-center space-x-4 mt-1">
                <span className="text-xs text-gray-500">
                  Version {page.version}
                </span>
                {page.modified_date && (
                  <span className="text-xs text-gray-500">
                    Modified: {new Date(page.modified_date).toLocaleDateString()}
                  </span>
                )}
                {page.has_children && (
                  <span className="inline-flex items-center text-xs text-blue-600">
                    <Folder className="w-3 h-3 mr-1" />
                    Has children
                  </span>
                )}
                {page.has_attachments && (
                  <span className="inline-flex items-center text-xs text-purple-600">
                    📎 Attachments
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );

  return (
    <div className="space-y-4">
      {/* Credential Selector */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Select Confluence Credential
        </label>
        <select
          value={selectedCredential || ''}
          onChange={(e) => onCredentialSelect(e.target.value)}
          className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-2"
          required
        >
          <option value="">Choose a credential...</option>
          {credentials.map((credential) => (
            <option key={credential.id} value={credential.id}>
              {credential.base_url} ({credential.email})
            </option>
          ))}
        </select>
      </div>

      {selectedCredential && (
        <>
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <Input
              type="text"
              placeholder={view === 'spaces' ? 'Search spaces...' : 'Search pages...'}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>

          {/* Navigation */}
          {view === 'pages' && (
            <div className="flex items-center space-x-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={handleBackToSpaces}
                className="flex items-center"
              >
                <ChevronLeft className="w-4 h-4 mr-1" />
                Back to Spaces
              </Button>
              <span className="text-sm text-gray-500">
                / {spaces.find(s => s.key === selectedSpace)?.name}
              </span>
            </div>
          )}

          {error && (
            <Alert variant="error">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Content */}
          <div className="max-h-96 overflow-y-auto">
            {view === 'spaces' ? (
              isLoadingSpaces ? (
                <div className="flex items-center justify-center py-8">
                  <LoadingSpinner />
                </div>
              ) : filteredSpaces.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  {searchQuery ? 'No spaces found matching your search' : 'No spaces found'}
                </div>
              ) : (
                renderSpacesList()
              )
            ) : (
              isLoadingPages ? (
                <div className="flex items-center justify-center py-8">
                  <LoadingSpinner />
                </div>
              ) : filteredPages.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  {searchQuery ? 'No pages found matching your search' : 'No pages found in this space'}
                </div>
              ) : (
                renderPagesList()
              )
            )}
          </div>

          {/* Selection Summary */}
          {selectedItems.size > 0 && (
            <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
              <p className="text-sm text-blue-800">
                {selectedItems.size} item{selectedItems.size !== 1 ? 's' : ''} selected for import
              </p>
            </div>
          )}
        </>
      )}
    </div>
  );
}