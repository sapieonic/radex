'use client';

import { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/Button';
import { Alert, AlertDescription } from '@/components/ui/Alert';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import apiClient from '@/lib/api';
import { ConfluenceImport, ConfluenceImportStatus as ImportStatus } from '@/types/confluence';
import { 
  RefreshCw, 
  CheckCircle, 
  XCircle, 
  Clock, 
  AlertCircle,
  Play,
  Pause,
  Calendar,
  Folder,
  Globe,
  FileText,
  RotateCcw
} from 'lucide-react';

interface ConfluenceImportStatusProps {
  folderId?: string;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

export default function ConfluenceImportStatus({ 
  folderId, 
  autoRefresh = true, 
  refreshInterval = 5000 
}: ConfluenceImportStatusProps) {
  const [imports, setImports] = useState<ConfluenceImport[]>([]);
  const [importStatuses, setImportStatuses] = useState<Map<string, ImportStatus>>(new Map());
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [isAutoRefreshing, setIsAutoRefreshing] = useState(autoRefresh);
  const intervalRef = useRef<NodeJS.Timeout>();

  useEffect(() => {
    loadImportHistory();
    
    if (isAutoRefreshing) {
      startAutoRefresh();
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [folderId, isAutoRefreshing, refreshInterval]);

  const loadImportHistory = async () => {
    setIsLoading(true);
    setError('');
    
    try {
      const response = await apiClient.getConfluenceSyncHistory(folderId, 20);
      setImports(response);
      
      // Load detailed status for each import
      const statusPromises = response.map(async (importItem: ConfluenceImport) => {
        try {
          const status = await apiClient.getConfluenceImportStatus(importItem.id);
          return { id: importItem.id, status };
        } catch (error) {
          return { id: importItem.id, status: null };
        }
      });

      const statusResults = await Promise.all(statusPromises);
      const statusMap = new Map();
      statusResults.forEach(({ id, status }) => {
        if (status) {
          statusMap.set(id, status);
        }
      });
      setImportStatuses(statusMap);

    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to load import history');
    } finally {
      setIsLoading(false);
    }
  };

  const startAutoRefresh = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }
    
    intervalRef.current = setInterval(() => {
      loadImportHistory();
    }, refreshInterval);
  };

  const toggleAutoRefresh = () => {
    setIsAutoRefreshing(!isAutoRefreshing);
  };

  const handleManualRefresh = () => {
    loadImportHistory();
  };

  const handleSyncImport = async (importId: string) => {
    try {
      await apiClient.syncConfluenceContent(importId);
      // Refresh the list to show updated status
      setTimeout(() => loadImportHistory(), 1000);
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to start sync');
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-500" />;
      case 'in_progress':
        return <LoadingSpinner size="sm" />;
      case 'partial':
        return <AlertCircle className="w-5 h-5 text-yellow-500" />;
      case 'pending':
      default:
        return <Clock className="w-5 h-5 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'in_progress':
        return 'bg-blue-100 text-blue-800';
      case 'partial':
        return 'bg-yellow-100 text-yellow-800';
      case 'pending':
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getProgressPercentage = (importId: string) => {
    const status = importStatuses.get(importId);
    if (!status || status.total_pages === 0) return 0;
    return (status.processed_pages / status.total_pages) * 100;
  };

  const getImportTypeIcon = (type: string) => {
    switch (type) {
      case 'space':
        return <Globe className="w-4 h-4 text-blue-500" />;
      case 'page':
        return <FileText className="w-4 h-4 text-green-500" />;
      case 'page_tree':
        return <Folder className="w-4 h-4 text-purple-500" />;
      default:
        return <FileText className="w-4 h-4 text-gray-500" />;
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Import Status</h3>
          <p className="text-sm text-gray-600">
            Monitor your Confluence import progress
          </p>
        </div>
        <div className="flex space-x-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={toggleAutoRefresh}
            className={isAutoRefreshing ? 'text-green-600' : 'text-gray-600'}
          >
            {isAutoRefreshing ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
            <span className="ml-1">
              {isAutoRefreshing ? 'Auto-refresh ON' : 'Auto-refresh OFF'}
            </span>
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleManualRefresh}
          >
            <RefreshCw className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {error && (
        <Alert variant="error">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {imports.length === 0 ? (
        <div className="text-center py-12">
          <Clock className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <h4 className="text-lg font-medium text-gray-900 mb-2">No import history</h4>
          <p className="text-gray-600">
            Start importing content from Confluence to see the status here
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {imports.map((importItem) => {
            const status = importStatuses.get(importItem.id);
            const progressPercentage = getProgressPercentage(importItem.id);
            
            return (
              <div
                key={importItem.id}
                className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    {getImportTypeIcon(importItem.import_type)}
                    <div>
                      <h4 className="font-medium text-gray-900">
                        {importItem.import_type === 'space' ? 'Space Import' : 'Page Import'}
                        {importItem.space_key && (
                          <span className="text-sm text-gray-500 ml-2">
                            ({importItem.space_key})
                          </span>
                        )}
                      </h4>
                      <div className="flex items-center space-x-4 text-sm text-gray-500 mt-1">
                        <span className="flex items-center">
                          <Calendar className="w-3 h-3 mr-1" />
                          {formatDate(importItem.created_at)}
                        </span>
                        {importItem.last_sync_at && (
                          <span>
                            Last sync: {formatDate(importItem.last_sync_at)}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-3">
                    {getStatusIcon(importItem.sync_status)}
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(importItem.sync_status)}`}>
                      {importItem.sync_status.replace('_', ' ').toUpperCase()}
                    </span>
                  </div>
                </div>

                {/* Progress Bar */}
                {(importItem.total_pages > 0) && (
                  <div className="mb-4">
                    <div className="flex justify-between text-sm text-gray-600 mb-1">
                      <span>
                        Progress: {importItem.processed_pages} / {importItem.total_pages} pages
                      </span>
                      <span>{Math.round(progressPercentage)}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full transition-all duration-300 ${
                          importItem.sync_status === 'completed'
                            ? 'bg-green-500'
                            : importItem.sync_status === 'failed'
                            ? 'bg-red-500'
                            : 'bg-blue-500'
                        }`}
                        style={{ width: `${progressPercentage}%` }}
                      />
                    </div>
                  </div>
                )}

                {/* Error Message */}
                {importItem.error_message && (
                  <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
                    <p className="text-sm text-red-800">
                      <strong>Error:</strong> {importItem.error_message}
                    </p>
                  </div>
                )}

                {/* Status Details */}
                {status && (
                  <div className="mb-4 p-3 bg-gray-50 rounded-md">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <span className="text-gray-500">Total Pages:</span>
                        <p className="font-medium">{status.total_pages}</p>
                      </div>
                      <div>
                        <span className="text-gray-500">Processed:</span>
                        <p className="font-medium">{status.processed_pages}</p>
                      </div>
                      <div>
                        <span className="text-gray-500">Progress:</span>
                        <p className="font-medium">{Math.round(status.progress_percentage)}%</p>
                      </div>
                      <div>
                        <span className="text-gray-500">Status:</span>
                        <p className="font-medium capitalize">{status.status.replace('_', ' ')}</p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Actions */}
                <div className="flex space-x-2">
                  {(importItem.sync_status === 'completed' || importItem.sync_status === 'failed') && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleSyncImport(importItem.id)}
                    >
                      <RotateCcw className="w-4 h-4 mr-2" />
                      Sync Again
                    </Button>
                  )}
                  
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleManualRefresh}
                  >
                    <RefreshCw className="w-4 h-4 mr-2" />
                    Refresh Status
                  </Button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}