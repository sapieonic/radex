'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/Button';
import { Alert, AlertDescription } from '@/components/ui/Alert';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import ConfluenceCredentialModal from './ConfluenceCredentialModal';
import apiClient from '@/lib/api';
import { ConfluenceCredential } from '@/types/confluence';
import { Plus, Edit2, Trash2, CheckCircle, XCircle, Cloud, Server, Database } from 'lucide-react';

export default function ConfluenceCredentials() {
  const [credentials, setCredentials] = useState<ConfluenceCredential[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<'create' | 'edit'>('create');
  const [selectedCredential, setSelectedCredential] = useState<ConfluenceCredential | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  useEffect(() => {
    loadCredentials();
  }, []);

  const loadCredentials = async () => {
    setIsLoading(true);
    setError('');
    
    try {
      const response = await apiClient.getConfluenceCredentials();
      setCredentials(response.credentials);
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to load Confluence credentials');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateNew = () => {
    setModalMode('create');
    setSelectedCredential(null);
    setIsModalOpen(true);
  };

  const handleEdit = (credential: ConfluenceCredential) => {
    setModalMode('edit');
    setSelectedCredential(credential);
    setIsModalOpen(true);
  };

  const handleDelete = async (credentialId: string) => {
    if (!confirm('Are you sure you want to delete this Confluence credential? This will also remove all associated import history.')) {
      return;
    }

    setDeletingId(credentialId);
    
    try {
      await apiClient.deleteConfluenceCredential(credentialId);
      await loadCredentials();
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to delete credential');
    } finally {
      setDeletingId(null);
    }
  };

  const handleModalSuccess = async () => {
    await loadCredentials();
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'cloud':
        return <Cloud className="w-5 h-5 text-blue-500" />;
      case 'server':
        return <Server className="w-5 h-5 text-green-500" />;
      case 'data_center':
        return <Database className="w-5 h-5 text-purple-500" />;
      default:
        return <Cloud className="w-5 h-5 text-gray-500" />;
    }
  };

  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'cloud':
        return 'Confluence Cloud';
      case 'server':
        return 'Confluence Server';
      case 'data_center':
        return 'Confluence Data Center';
      default:
        return type;
    }
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
          <h2 className="text-2xl font-bold text-gray-900">Confluence Credentials</h2>
          <p className="text-gray-600">Manage your Confluence server connections</p>
        </div>
        <Button onClick={handleCreateNew}>
          <Plus className="w-4 h-4 mr-2" />
          Add Credential
        </Button>
      </div>

      {error && (
        <Alert variant="error">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {credentials.length === 0 ? (
        <div className="text-center py-12">
          <Cloud className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Confluence credentials</h3>
          <p className="text-gray-600 mb-4">
            Add your first Confluence credential to start importing content
          </p>
          <Button onClick={handleCreateNew}>
            <Plus className="w-4 h-4 mr-2" />
            Add Your First Credential
          </Button>
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {credentials.map((credential) => (
            <div
              key={credential.id}
              className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center space-x-2">
                  {getTypeIcon(credential.confluence_type)}
                  <div>
                    <h3 className="font-medium text-gray-900">
                      {getTypeLabel(credential.confluence_type)}
                    </h3>
                    <p className="text-sm text-gray-500">{credential.base_url}</p>
                  </div>
                </div>
                <div className="flex items-center space-x-1">
                  {credential.is_valid ? (
                    <CheckCircle className="w-5 h-5 text-green-500" />
                  ) : (
                    <XCircle className="w-5 h-5 text-red-500" />
                  )}
                </div>
              </div>

              <div className="space-y-2 mb-4">
                <div>
                  <span className="text-sm text-gray-500">Email:</span>
                  <p className="text-sm font-medium text-gray-900">{credential.email}</p>
                </div>
                <div>
                  <span className="text-sm text-gray-500">Status:</span>
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ml-2 ${
                    credential.is_valid 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {credential.is_valid ? 'Connected' : 'Connection Failed'}
                  </span>
                </div>
                <div>
                  <span className="text-sm text-gray-500">Added:</span>
                  <p className="text-sm text-gray-900">
                    {new Date(credential.created_at).toLocaleDateString()}
                  </p>
                </div>
              </div>

              <div className="flex space-x-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleEdit(credential)}
                  className="flex-1"
                >
                  <Edit2 className="w-4 h-4 mr-2" />
                  Edit
                </Button>
                <Button
                  variant="danger"
                  size="sm"
                  onClick={() => handleDelete(credential.id)}
                  disabled={deletingId === credential.id}
                  className="flex-1"
                >
                  {deletingId === credential.id ? (
                    <div className="flex items-center">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Deleting...
                    </div>
                  ) : (
                    <>
                      <Trash2 className="w-4 h-4 mr-2" />
                      Delete
                    </>
                  )}
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      <ConfluenceCredentialModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={handleModalSuccess}
        credential={selectedCredential}
        mode={modalMode}
      />
    </div>
  );
}