'use client';

import { useState, useEffect } from 'react';
import { Modal } from './ui/Modal';
import { Button } from './ui/Button';
import { Upload, Cloud } from 'lucide-react';
import { apiClient } from '@/lib/api';
import type { ProvidersConfigResponse } from '@/types/sharepoint';

interface SourceSelectionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectLocal: () => void;
  onSelectSharePoint: () => void;
}

export function SourceSelectionModal({
  isOpen,
  onClose,
  onSelectLocal,
  onSelectSharePoint,
}: SourceSelectionModalProps) {
  const [providersConfig, setProvidersConfig] = useState<ProvidersConfigResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (isOpen) {
      loadProvidersConfig();
    }
  }, [isOpen]);

  const loadProvidersConfig = async () => {
    try {
      setLoading(true);
      const config = await apiClient.getProvidersConfig();
      setProvidersConfig(config);
    } catch (error) {
      console.error('Failed to load providers config:', error);
    } finally {
      setLoading(false);
    }
  };

  const sharePointProvider = providersConfig?.providers?.find(
    (p) => p.provider === 'sharepoint'
  );
  const isSharePointEnabled = sharePointProvider?.is_enabled ?? false;

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Select Source" size="md">
      <div className="space-y-4">
        <p className="text-sm text-gray-600">
          Choose where to upload files from:
        </p>

        {loading ? (
          <div className="flex justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {/* Local Computer Option */}
            <button
              onClick={() => {
                onClose();
                onSelectLocal();
              }}
              className="flex items-start p-4 border-2 border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors text-left group"
            >
              <div className="flex-shrink-0 mt-1">
                <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center group-hover:bg-blue-100">
                  <Upload className="w-6 h-6 text-gray-600 group-hover:text-blue-600" />
                </div>
              </div>
              <div className="ml-4 flex-1">
                <h3 className="text-base font-semibold text-gray-900 group-hover:text-blue-600">
                  Local Computer
                </h3>
                <p className="mt-1 text-sm text-gray-500">
                  Upload files directly from your device
                </p>
              </div>
            </button>

            {/* Microsoft 365 Option */}
            {isSharePointEnabled ? (
              <button
                onClick={() => {
                  onClose();
                  onSelectSharePoint();
                }}
                className="flex items-start p-4 border-2 border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors text-left group"
              >
                <div className="flex-shrink-0 mt-1">
                  <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center group-hover:bg-blue-100">
                    <Cloud className="w-6 h-6 text-gray-600 group-hover:text-blue-600" />
                  </div>
                </div>
                <div className="ml-4 flex-1">
                  <h3 className="text-base font-semibold text-gray-900 group-hover:text-blue-600">
                    {sharePointProvider?.display_name || 'Microsoft 365'}
                  </h3>
                  <p className="mt-1 text-sm text-gray-500">
                    Import files from OneDrive or SharePoint
                  </p>
                </div>
              </button>
            ) : (
              <div className="p-4 border-2 border-gray-100 rounded-lg bg-gray-50 opacity-60">
                <div className="flex items-start">
                  <div className="flex-shrink-0 mt-1">
                    <div className="w-12 h-12 bg-gray-200 rounded-lg flex items-center justify-center">
                      <Cloud className="w-6 h-6 text-gray-400" />
                    </div>
                  </div>
                  <div className="ml-4 flex-1">
                    <h3 className="text-base font-semibold text-gray-500">
                      Microsoft 365 (OneDrive & SharePoint)
                    </h3>
                    <p className="mt-1 text-sm text-gray-400">
                      Not available - contact your administrator
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        <div className="pt-4 flex justify-end">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
        </div>
      </div>
    </Modal>
  );
}
