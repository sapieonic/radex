'use client';

import { useState, useEffect } from 'react';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/Button';
import { Alert, AlertDescription } from '@/components/ui/Alert';
import ConfluenceSpaceBrowser from './ConfluenceSpaceBrowser';
import apiClient from '@/lib/api';
import { 
  ConfluenceCredential, 
  ConfluenceSpace, 
  ConfluencePage, 
  ConfluenceImportRequest,
  ImportType 
} from '@/types/confluence';
import { 
  ChevronRight, 
  ChevronLeft, 
  Settings, 
  Upload,
  CheckCircle,
  Globe,
  FileText,
  Folder
} from 'lucide-react';

interface ConfluenceImportWizardProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (importIds: string[]) => void;
  folderId: string;
}

type Step = 'credentials' | 'browse' | 'configure' | 'import';

interface ImportItem {
  type: ImportType;
  spaceKey?: string;
  pageId?: string;
  title: string;
}

export default function ConfluenceImportWizard({
  isOpen,
  onClose,
  onSuccess,
  folderId
}: ConfluenceImportWizardProps) {
  const [currentStep, setCurrentStep] = useState<Step>('credentials');
  const [credentials, setCredentials] = useState<ConfluenceCredential[]>([]);
  const [selectedCredential, setSelectedCredential] = useState<string | null>(null);
  const [selectedItems, setSelectedItems] = useState<Set<string>>(new Set());
  const [selectedSpaces, setSelectedSpaces] = useState<Map<string, ConfluenceSpace>>(new Map());
  const [selectedPages, setSelectedPages] = useState<Map<string, ConfluencePage>>(new Map());
  const [importConfig, setImportConfig] = useState({
    include_attachments: true,
    include_comments: false,
    recursive: true
  });
  const [isImporting, setIsImporting] = useState(false);
  const [error, setError] = useState('');
  const [importResults, setImportResults] = useState<string[]>([]);

  useEffect(() => {
    if (isOpen) {
      loadCredentials();
      resetWizard();
    }
  }, [isOpen]);

  const resetWizard = () => {
    setCurrentStep('credentials');
    setSelectedCredential(null);
    setSelectedItems(new Set());
    setSelectedSpaces(new Map());
    setSelectedPages(new Map());
    setError('');
    setImportResults([]);
  };

  const loadCredentials = async () => {
    try {
      const response = await apiClient.getConfluenceCredentials();
      setCredentials(response.credentials.filter((cred: ConfluenceCredential) => cred.is_valid));
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to load Confluence credentials');
    }
  };

  const handleCredentialSelect = (credentialId: string) => {
    setSelectedCredential(credentialId);
  };

  const handleSpaceSelect = (space: ConfluenceSpace) => {
    setSelectedSpaces(prev => {
      const updated = new Map(prev);
      updated.set(space.key, space);
      return updated;
    });
  };

  const handlePageSelect = (page: ConfluencePage) => {
    setSelectedPages(prev => {
      const updated = new Map(prev);
      updated.set(page.id, page);
      return updated;
    });
  };

  const handleToggleSelection = (id: string, type: 'space' | 'page') => {
    setSelectedItems(prev => {
      const updated = new Set(prev);
      if (updated.has(id)) {
        updated.delete(id);
        
        // Remove from respective maps
        if (type === 'space') {
          const spaceKey = id.replace('space:', '');
          setSelectedSpaces(prev => {
            const newMap = new Map(prev);
            newMap.delete(spaceKey);
            return newMap;
          });
        } else {
          const pageId = id.replace('page:', '');
          setSelectedPages(prev => {
            const newMap = new Map(prev);
            newMap.delete(pageId);
            return newMap;
          });
        }
      } else {
        updated.add(id);
      }
      return updated;
    });
  };

  const canProceed = (step: Step): boolean => {
    switch (step) {
      case 'credentials':
        return selectedCredential !== null;
      case 'browse':
        return selectedItems.size > 0;
      case 'configure':
        return true;
      case 'import':
        return false;
      default:
        return false;
    }
  };

  const handleNext = () => {
    const steps: Step[] = ['credentials', 'browse', 'configure', 'import'];
    const currentIndex = steps.indexOf(currentStep);
    if (currentIndex < steps.length - 1 && canProceed(currentStep)) {
      setCurrentStep(steps[currentIndex + 1]);
    }
  };

  const handleBack = () => {
    const steps: Step[] = ['credentials', 'browse', 'configure', 'import'];
    const currentIndex = steps.indexOf(currentStep);
    if (currentIndex > 0) {
      setCurrentStep(steps[currentIndex - 1]);
    }
  };

  const handleImport = async () => {
    if (!selectedCredential) return;

    setIsImporting(true);
    setError('');
    
    try {
      const importRequests: ConfluenceImportRequest[] = [];

      // Create import requests for selected spaces
      selectedSpaces.forEach((space) => {
        importRequests.push({
          credential_id: selectedCredential,
          folder_id: folderId,
          import_type: 'space',
          space_key: space.key,
          include_attachments: importConfig.include_attachments,
          include_comments: importConfig.include_comments,
          recursive: importConfig.recursive
        });
      });

      // Create import requests for selected pages
      selectedPages.forEach((page) => {
        importRequests.push({
          credential_id: selectedCredential,
          folder_id: folderId,
          import_type: 'page',
          page_id: page.id,
          space_key: page.space_key,
          include_attachments: importConfig.include_attachments,
          include_comments: importConfig.include_comments,
          recursive: importConfig.recursive
        });
      });

      // Execute imports
      const importIds: string[] = [];
      for (const request of importRequests) {
        const response = await apiClient.createConfluenceImport(request);
        importIds.push(response.id);
      }

      setImportResults(importIds);
      setCurrentStep('import');
      
      // Call success callback after a short delay to show the completion step
      setTimeout(() => {
        onSuccess(importIds);
      }, 2000);

    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to start import');
    } finally {
      setIsImporting(false);
    }
  };

  const getImportSummary = (): ImportItem[] => {
    const items: ImportItem[] = [];
    
    selectedSpaces.forEach((space) => {
      items.push({
        type: 'space',
        spaceKey: space.key,
        title: space.name
      });
    });

    selectedPages.forEach((page) => {
      items.push({
        type: 'page',
        pageId: page.id,
        spaceKey: page.space_key,
        title: page.title
      });
    });

    return items;
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 'credentials':
        return (
          <div className="space-y-4">
            <div className="text-center">
              <Globe className="w-12 h-12 text-blue-500 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Select Confluence Connection
              </h3>
              <p className="text-gray-600">
                Choose which Confluence instance to import from
              </p>
            </div>

            {credentials.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-gray-500 mb-4">
                  No valid Confluence credentials found. Please add and verify a credential first.
                </p>
                <Button variant="secondary" onClick={onClose}>
                  Manage Credentials
                </Button>
              </div>
            ) : (
              <div className="space-y-2">
                {credentials.map((credential) => (
                  <div
                    key={credential.id}
                    className={`border rounded-lg p-4 cursor-pointer transition-colors ${
                      selectedCredential === credential.id
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:bg-gray-50'
                    }`}
                    onClick={() => handleCredentialSelect(credential.id)}
                  >
                    <div className="flex items-center space-x-3">
                      <input
                        type="radio"
                        checked={selectedCredential === credential.id}
                        onChange={() => handleCredentialSelect(credential.id)}
                        className="text-blue-600 focus:ring-blue-500"
                      />
                      <div>
                        <h4 className="font-medium text-gray-900">{credential.base_url}</h4>
                        <p className="text-sm text-gray-500">{credential.email}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        );

      case 'browse':
        return (
          <div className="space-y-4">
            <div className="text-center">
              <Folder className="w-12 h-12 text-green-500 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Browse and Select Content
              </h3>
              <p className="text-gray-600">
                Choose the spaces or pages you want to import
              </p>
            </div>

            <ConfluenceSpaceBrowser
              credentials={credentials}
              selectedCredential={selectedCredential}
              onCredentialSelect={handleCredentialSelect}
              onSpaceSelect={handleSpaceSelect}
              onPageSelect={handlePageSelect}
              selectedItems={selectedItems}
              onToggleSelection={handleToggleSelection}
            />
          </div>
        );

      case 'configure':
        return (
          <div className="space-y-6">
            <div className="text-center">
              <Settings className="w-12 h-12 text-purple-500 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Configure Import Options
              </h3>
              <p className="text-gray-600">
                Set your import preferences
              </p>
            </div>

            {/* Import Summary */}
            <div className="bg-gray-50 rounded-lg p-4">
              <h4 className="font-medium text-gray-900 mb-3">Selected for Import:</h4>
              <div className="space-y-2 max-h-40 overflow-y-auto">
                {getImportSummary().map((item, index) => (
                  <div key={index} className="flex items-center space-x-2 text-sm">
                    {item.type === 'space' ? (
                      <Globe className="w-4 h-4 text-blue-500" />
                    ) : (
                      <FileText className="w-4 h-4 text-green-500" />
                    )}
                    <span className="font-medium">
                      {item.type === 'space' ? 'Space:' : 'Page:'}
                    </span>
                    <span className="text-gray-700">{item.title}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Import Options */}
            <div className="space-y-4">
              <h4 className="font-medium text-gray-900">Import Options:</h4>
              
              <div className="space-y-3">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={importConfig.include_attachments}
                    onChange={(e) => setImportConfig(prev => ({
                      ...prev,
                      include_attachments: e.target.checked
                    }))}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="ml-3 text-sm text-gray-700">
                    Include attachments
                  </span>
                </label>

                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={importConfig.include_comments}
                    onChange={(e) => setImportConfig(prev => ({
                      ...prev,
                      include_comments: e.target.checked
                    }))}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="ml-3 text-sm text-gray-700">
                    Include comments
                  </span>
                </label>

                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={importConfig.recursive}
                    onChange={(e) => setImportConfig(prev => ({
                      ...prev,
                      recursive: e.target.checked
                    }))}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="ml-3 text-sm text-gray-700">
                    Import child pages (recursive)
                  </span>
                </label>
              </div>
            </div>
          </div>
        );

      case 'import':
        return (
          <div className="space-y-4 text-center">
            <CheckCircle className="w-16 h-16 text-green-500 mx-auto" />
            <h3 className="text-lg font-medium text-gray-900">
              Import Started Successfully!
            </h3>
            <p className="text-gray-600">
              {importResults.length} import job{importResults.length !== 1 ? 's' : ''} created. 
              You can monitor the progress in the import status section.
            </p>
            <div className="bg-green-50 border border-green-200 rounded-md p-4">
              <p className="text-sm text-green-800">
                Import jobs are processing in the background. Large imports may take several minutes to complete.
              </p>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  const getStepTitle = () => {
    switch (currentStep) {
      case 'credentials': return 'Choose Connection';
      case 'browse': return 'Select Content';
      case 'configure': return 'Configure Import';
      case 'import': return 'Import Complete';
      default: return '';
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Import from Confluence - ${getStepTitle()}`}
      size="xl"
    >
      <div className="space-y-6">
        {/* Progress Bar */}
        <div className="flex items-center space-x-4">
          {['credentials', 'browse', 'configure', 'import'].map((step, index) => (
            <div key={step} className="flex items-center">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                currentStep === step
                  ? 'bg-blue-600 text-white'
                  : index < ['credentials', 'browse', 'configure', 'import'].indexOf(currentStep)
                  ? 'bg-green-600 text-white'
                  : 'bg-gray-200 text-gray-600'
              }`}>
                {index < ['credentials', 'browse', 'configure', 'import'].indexOf(currentStep) ? '✓' : index + 1}
              </div>
              {index < 3 && (
                <div className={`w-8 h-1 mx-2 ${
                  index < ['credentials', 'browse', 'configure', 'import'].indexOf(currentStep)
                    ? 'bg-green-600'
                    : 'bg-gray-200'
                }`} />
              )}
            </div>
          ))}
        </div>

        {error && (
          <Alert variant="error">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Step Content */}
        {renderStepContent()}

        {/* Navigation Buttons */}
        <div className="flex justify-between pt-6 border-t border-gray-200">
          <Button
            variant="ghost"
            onClick={currentStep === 'credentials' ? onClose : handleBack}
            disabled={isImporting}
          >
            {currentStep === 'credentials' ? (
              'Cancel'
            ) : (
              <>
                <ChevronLeft className="w-4 h-4 mr-2" />
                Back
              </>
            )}
          </Button>

          <div className="space-x-3">
            {currentStep === 'import' && (
              <Button onClick={onClose}>
                Done
              </Button>
            )}
            
            {currentStep === 'configure' && (
              <Button
                onClick={handleImport}
                disabled={isImporting}
                className="min-w-[120px]"
              >
                {isImporting ? (
                  <div className="flex items-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Starting...
                  </div>
                ) : (
                  <>
                    <Upload className="w-4 h-4 mr-2" />
                    Start Import
                  </>
                )}
              </Button>
            )}

            {currentStep !== 'configure' && currentStep !== 'import' && (
              <Button
                onClick={handleNext}
                disabled={!canProceed(currentStep)}
              >
                Next
                <ChevronRight className="w-4 h-4 ml-2" />
              </Button>
            )}
          </div>
        </div>
      </div>
    </Modal>
  );
}