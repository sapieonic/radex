'use client';

import { useState, useEffect } from 'react';
import { Modal } from './ui/Modal';
import { Button } from './ui/Button';
import {
  ChevronRight,
  Folder,
  File,
  Check,
  Search,
  AlertCircle,
  Cloud,
  Building2,
} from 'lucide-react';
import { apiClient } from '@/lib/api';
import type {
  DriveItem,
  DriveInfo,
  SiteInfo,
  BreadcrumbItem,
  SyncImportResponse,
} from '@/types/sharepoint';

interface SharePointFilePickerProps {
  isOpen: boolean;
  onClose: () => void;
  connectionId: string | null;
  folderId: string;
  onImportComplete: (result: SyncImportResponse) => void;
}

type Tab = 'onedrive' | 'sharepoint';

export function SharePointFilePicker({
  isOpen,
  onClose,
  connectionId,
  folderId,
  onImportComplete,
}: SharePointFilePickerProps) {
  const [activeTab, setActiveTab] = useState<Tab>('onedrive');
  const [loading, setLoading] = useState(false);
  const [importing, setImporting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // OneDrive state
  const [driveInfo, setDriveInfo] = useState<DriveInfo | null>(null);
  const [items, setItems] = useState<DriveItem[]>([]);
  const [breadcrumbs, setBreadcrumbs] = useState<BreadcrumbItem[]>([
    { id: 'root', name: 'My OneDrive' },
  ]);

  // SharePoint state
  const [siteSearch, setSiteSearch] = useState('');
  const [sites, setSites] = useState<SiteInfo[]>([]);
  const [selectedSite, setSelectedSite] = useState<SiteInfo | null>(null);
  const [drives, setDrives] = useState<DriveInfo[]>([]);
  const [selectedDrive, setSelectedDrive] = useState<DriveInfo | null>(null);

  // Selection state
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (isOpen && connectionId) {
      if (activeTab === 'onedrive') {
        loadOneDrive();
      }
    }
  }, [isOpen, connectionId, activeTab]);

  const loadOneDrive = async () => {
    if (!connectionId) return;

    try {
      setLoading(true);
      setError(null);

      // Get drive info
      const drive = await apiClient.getOneDriveRoot(connectionId);
      setDriveInfo(drive);

      // Load root items
      const response = await apiClient.getDriveChildren(connectionId, drive.id, 'root');
      setItems(response.items);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load OneDrive');
      console.error('Failed to load OneDrive:', err);
    } finally {
      setLoading(false);
    }
  };

  const navigateToFolder = async (item: DriveItem) => {
    if (!connectionId || !driveInfo) return;
    if (item.type !== 'folder') return;

    try {
      setLoading(true);
      setError(null);

      const response = await apiClient.getDriveChildren(
        connectionId,
        driveInfo.id,
        item.id
      );
      setItems(response.items);

      // Update breadcrumbs
      setBreadcrumbs([...breadcrumbs, { id: item.id, name: item.name }]);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to navigate to folder');
    } finally {
      setLoading(false);
    }
  };

  const navigateToBreadcrumb = async (index: number) => {
    if (!connectionId || !driveInfo) return;

    const targetBreadcrumb = breadcrumbs[index];

    try {
      setLoading(true);
      setError(null);

      const response = await apiClient.getDriveChildren(
        connectionId,
        driveInfo.id,
        targetBreadcrumb.id
      );
      setItems(response.items);

      // Update breadcrumbs
      setBreadcrumbs(breadcrumbs.slice(0, index + 1));
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to navigate');
    } finally {
      setLoading(false);
    }
  };

  const searchSites = async () => {
    if (!connectionId || !siteSearch.trim()) return;

    try {
      setLoading(true);
      setError(null);

      const response = await apiClient.searchSharePointSites(connectionId, siteSearch);
      setSites(response.sites);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to search sites');
    } finally {
      setLoading(false);
    }
  };

  const selectSite = async (site: SiteInfo) => {
    if (!connectionId) return;

    try {
      setLoading(true);
      setError(null);
      setSelectedSite(site);

      const response = await apiClient.getSiteDrives(connectionId, site.id);
      setDrives(response.drives);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load site drives');
    } finally {
      setLoading(false);
    }
  };

  const selectDriveForBrowsing = async (drive: DriveInfo) => {
    if (!connectionId) return;

    try {
      setLoading(true);
      setError(null);
      setSelectedDrive(drive);

      const response = await apiClient.getDriveChildren(connectionId, drive.id, 'root');
      setItems(response.items);
      setBreadcrumbs([{ id: 'root', name: drive.name }]);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load drive');
    } finally {
      setLoading(false);
    }
  };

  const toggleFileSelection = (item: DriveItem) => {
    if (item.type !== 'file') return;

    const key = `${item.drive_id}:${item.id}`;
    const newSelection = new Set(selectedFiles);

    if (newSelection.has(key)) {
      newSelection.delete(key);
    } else {
      newSelection.add(key);
    }

    setSelectedFiles(newSelection);
  };

  const handleImport = async () => {
    if (!connectionId || selectedFiles.size === 0) return;

    try {
      setImporting(true);
      setError(null);

      // Build import request
      const itemsToImport = items
        .filter((item) => {
          const key = `${item.drive_id}:${item.id}`;
          return selectedFiles.has(key);
        })
        .map((item) => ({
          drive_id: item.drive_id,
          item_id: item.id,
          e_tag: item.e_tag,
        }));

      const result = await apiClient.importFromSharePoint({
        connection_id: connectionId,
        folder_id: folderId,
        items: itemsToImport,
      });

      onImportComplete(result);
      setSelectedFiles(new Set());
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to import files');
    } finally {
      setImporting(false);
    }
  };

  const renderBreadcrumbs = () => (
    <div className="flex items-center space-x-2 text-sm text-gray-600 mb-4">
      {breadcrumbs.map((crumb, index) => (
        <div key={crumb.id} className="flex items-center">
          {index > 0 && <ChevronRight className="w-4 h-4 mx-1" />}
          <button
            onClick={() => navigateToBreadcrumb(index)}
            className={`hover:text-blue-600 ${
              index === breadcrumbs.length - 1 ? 'font-semibold text-gray-900' : ''
            }`}
            disabled={loading}
          >
            {crumb.name}
          </button>
        </div>
      ))}
    </div>
  );

  const renderFileList = () => {
    if (loading) {
      return (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      );
    }

    if (items.length === 0) {
      return (
        <div className="text-center py-12 text-gray-500">
          <Folder className="w-12 h-12 mx-auto mb-2 text-gray-400" />
          <p>No files or folders found</p>
        </div>
      );
    }

    return (
      <div className="border border-gray-200 rounded-lg divide-y divide-gray-200 max-h-96 overflow-y-auto">
        {items.map((item) => {
          const key = `${item.drive_id}:${item.id}`;
          const isSelected = selectedFiles.has(key);
          const isFile = item.type === 'file';

          return (
            <div
              key={item.id}
              className={`flex items-center p-3 hover:bg-gray-50 ${
                isFile ? 'cursor-pointer' : ''
              }`}
              onClick={() => {
                if (item.type === 'folder') {
                  navigateToFolder(item);
                }
              }}
            >
              {isFile && (
                <input
                  type="checkbox"
                  checked={isSelected}
                  onChange={() => toggleFileSelection(item)}
                  onClick={(e) => e.stopPropagation()}
                  disabled={item.is_synced}
                  className="mr-3 h-4 w-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
                />
              )}

              <div className="flex-shrink-0 mr-3">
                {item.type === 'folder' ? (
                  <Folder className="w-5 h-5 text-blue-500" />
                ) : (
                  <File className="w-5 h-5 text-gray-500" />
                )}
              </div>

              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {item.name}
                </p>
                <div className="flex items-center space-x-2 text-xs text-gray-500">
                  {item.size && <span>{formatFileSize(item.size)}</span>}
                  {item.last_modified && (
                    <span>{new Date(item.last_modified).toLocaleDateString()}</span>
                  )}
                  {item.is_synced && (
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                      <Check className="w-3 h-3 mr-1" />
                      Synced
                    </span>
                  )}
                </div>
              </div>

              {item.type === 'folder' && (
                <ChevronRight className="w-5 h-5 text-gray-400 flex-shrink-0" />
              )}
            </div>
          );
        })}
      </div>
    );
  };

  const renderOneDriveTab = () => (
    <div>
      {renderBreadcrumbs()}
      {renderFileList()}
    </div>
  );

  const renderSharePointTab = () => {
    if (!selectedDrive) {
      if (!selectedSite) {
        // Site search view
        return (
          <div>
            <div className="mb-4">
              <div className="flex space-x-2">
                <input
                  type="text"
                  value={siteSearch}
                  onChange={(e) => setSiteSearch(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && searchSites()}
                  placeholder="Search for SharePoint sites..."
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <Button onClick={searchSites} disabled={loading || !siteSearch.trim()}>
                  <Search className="w-4 h-4" />
                </Button>
              </div>
            </div>

            {loading ? (
              <div className="flex justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              </div>
            ) : sites.length > 0 ? (
              <div className="border border-gray-200 rounded-lg divide-y divide-gray-200">
                {sites.map((site) => (
                  <button
                    key={site.id}
                    onClick={() => selectSite(site)}
                    className="w-full flex items-center p-3 hover:bg-gray-50 text-left"
                  >
                    <Building2 className="w-5 h-5 text-blue-500 mr-3" />
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900">{site.display_name}</p>
                      {site.description && (
                        <p className="text-xs text-gray-500">{site.description}</p>
                      )}
                    </div>
                    <ChevronRight className="w-5 h-5 text-gray-400" />
                  </button>
                ))}
              </div>
            ) : (
              <div className="text-center py-12 text-gray-500">
                <Search className="w-12 h-12 mx-auto mb-2 text-gray-400" />
                <p>Search for SharePoint sites to browse</p>
              </div>
            )}
          </div>
        );
      }

      // Drive selection view
      return (
        <div>
          <div className="mb-4">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setSelectedSite(null);
                setDrives([]);
              }}
            >
              ← Back to sites
            </Button>
            <h3 className="mt-2 font-semibold text-gray-900">{selectedSite.display_name}</h3>
          </div>

          {loading ? (
            <div className="flex justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : drives.length > 0 ? (
            <div className="border border-gray-200 rounded-lg divide-y divide-gray-200">
              {drives.map((drive) => (
                <button
                  key={drive.id}
                  onClick={() => selectDriveForBrowsing(drive)}
                  className="w-full flex items-center p-3 hover:bg-gray-50 text-left"
                >
                  <Folder className="w-5 h-5 text-blue-500 mr-3" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">{drive.name}</p>
                    {drive.description && (
                      <p className="text-xs text-gray-500">{drive.description}</p>
                    )}
                  </div>
                  <ChevronRight className="w-5 h-5 text-gray-400" />
                </button>
              ))}
            </div>
          ) : (
            <div className="text-center py-12 text-gray-500">
              <Folder className="w-12 h-12 mx-auto mb-2 text-gray-400" />
              <p>No document libraries found</p>
            </div>
          )}
        </div>
      );
    }

    // File browsing view (same as OneDrive)
    return (
      <div>
        <div className="mb-4">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setSelectedDrive(null);
              setItems([]);
              setBreadcrumbs([{ id: 'root', name: 'My OneDrive' }]);
            }}
          >
            ← Back to drives
          </Button>
        </div>
        {renderBreadcrumbs()}
        {renderFileList()}
      </div>
    );
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Import from Microsoft 365" size="xl">
      <div className="space-y-4">
        {/* Tabs */}
        <div className="border-b border-gray-200">
          <nav className="flex space-x-4">
            <button
              onClick={() => setActiveTab('onedrive')}
              className={`pb-3 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'onedrive'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <Cloud className="w-4 h-4 inline-block mr-2" />
              My OneDrive
            </button>
            <button
              onClick={() => setActiveTab('sharepoint')}
              className={`pb-3 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'sharepoint'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <Building2 className="w-4 h-4 inline-block mr-2" />
              SharePoint Sites
            </button>
          </nav>
        </div>

        {/* Error display */}
        {error && (
          <div className="flex items-center p-3 bg-red-50 border border-red-200 rounded-lg">
            <AlertCircle className="w-5 h-5 text-red-500 mr-2" />
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        {/* Tab content */}
        <div className="min-h-[400px]">
          {activeTab === 'onedrive' ? renderOneDriveTab() : renderSharePointTab()}
        </div>

        {/* Actions */}
        <div className="flex items-center justify-between pt-4 border-t border-gray-200">
          <div className="text-sm text-gray-600">
            {selectedFiles.size > 0 && (
              <span>
                {selectedFiles.size} file{selectedFiles.size !== 1 ? 's' : ''} selected
              </span>
            )}
          </div>
          <div className="flex space-x-2">
            <Button variant="outline" onClick={onClose} disabled={importing}>
              Cancel
            </Button>
            <Button
              onClick={handleImport}
              disabled={selectedFiles.size === 0 || importing}
            >
              {importing ? 'Importing...' : 'Import Selected'}
            </Button>
          </div>
        </div>
      </div>
    </Modal>
  );
}

function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}
