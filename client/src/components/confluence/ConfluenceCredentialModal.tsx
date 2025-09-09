'use client';

import { useState, useEffect } from 'react';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Alert, AlertDescription } from '@/components/ui/Alert';
import apiClient from '@/lib/api';
import { ConfluenceCredential, ConfluenceType } from '@/types/confluence';

interface ConfluenceCredentialModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  credential?: ConfluenceCredential | null;
  mode: 'create' | 'edit';
}

export default function ConfluenceCredentialModal({ 
  isOpen, 
  onClose, 
  onSuccess, 
  credential, 
  mode 
}: ConfluenceCredentialModalProps) {
  const [formData, setFormData] = useState({
    confluence_type: 'cloud' as ConfluenceType,
    base_url: '',
    email: '',
    api_token: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [isTestingConnection, setIsTestingConnection] = useState(false);

  useEffect(() => {
    if (isOpen) {
      if (mode === 'edit' && credential) {
        setFormData({
          confluence_type: credential.confluence_type,
          base_url: credential.base_url,
          email: credential.email || '',
          api_token: '' // Don't pre-fill API token for security
        });
      } else {
        setFormData({
          confluence_type: 'cloud',
          base_url: '',
          email: '',
          api_token: ''
        });
      }
      setError('');
    }
  }, [isOpen, mode, credential]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError('');

    try {
      await apiClient.addConfluenceAuth({
        confluence_type: formData.confluence_type,
        base_url: formData.base_url,
        email: formData.email,
        api_token: formData.api_token
      });

      onSuccess();
      onClose();
    } catch (error: any) {
      setError(error.response?.data?.detail || `Failed to ${mode} Confluence credential`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const getPlaceholderUrl = (type: ConfluenceType) => {
    switch (type) {
      case 'cloud':
        return 'https://yourcompany.atlassian.net';
      case 'server':
        return 'https://confluence.yourcompany.com';
      case 'data_center':
        return 'https://confluence.yourcompany.com';
      default:
        return 'https://yourcompany.atlassian.net';
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={mode === 'create' ? 'Add Confluence Credential' : 'Edit Confluence Credential'}
      size="lg"
    >
      <form onSubmit={handleSubmit} className="space-y-6">
        {error && (
          <Alert variant="error">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Confluence Type */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Confluence Type
          </label>
          <select
            value={formData.confluence_type}
            onChange={(e) => handleInputChange('confluence_type', e.target.value)}
            className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-2"
            required
          >
            <option value="cloud">Confluence Cloud</option>
            <option value="server">Confluence Server</option>
            <option value="data_center">Confluence Data Center</option>
          </select>
        </div>

        {/* Base URL */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Base URL
          </label>
          <Input
            type="url"
            value={formData.base_url}
            onChange={(e) => handleInputChange('base_url', e.target.value)}
            placeholder={getPlaceholderUrl(formData.confluence_type)}
            required
          />
          <p className="mt-1 text-xs text-gray-500">
            The full URL to your Confluence instance
          </p>
        </div>

        {/* Email */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Email Address
          </label>
          <Input
            type="email"
            value={formData.email}
            onChange={(e) => handleInputChange('email', e.target.value)}
            placeholder="your-email@company.com"
            required
          />
          <p className="mt-1 text-xs text-gray-500">
            Your Confluence account email address
          </p>
        </div>

        {/* API Token */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            API Token {mode === 'edit' && <span className="text-gray-500">(leave blank to keep current)</span>}
          </label>
          <Input
            type="password"
            value={formData.api_token}
            onChange={(e) => handleInputChange('api_token', e.target.value)}
            placeholder={mode === 'edit' ? 'Leave blank to keep current token' : 'Your Confluence API token'}
            required={mode === 'create'}
          />
          <div className="mt-1 text-xs text-gray-500 space-y-1">
            {formData.confluence_type === 'cloud' && (
              <p>
                Generate an API token at: 
                <a 
                  href="https://id.atlassian.com/manage-profile/security/api-tokens" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-800 ml-1"
                >
                  Atlassian Account Security
                </a>
              </p>
            )}
            {(formData.confluence_type === 'server' || formData.confluence_type === 'data_center') && (
              <p>Get your API token from your Confluence administrator</p>
            )}
          </div>
        </div>

        {/* Help Text */}
        <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
          <h4 className="text-sm font-medium text-blue-900 mb-2">
            How to get your Confluence credentials:
          </h4>
          <ul className="text-xs text-blue-800 space-y-1">
            {formData.confluence_type === 'cloud' && (
              <>
                <li>1. Go to your Atlassian Account Security page</li>
                <li>2. Click "Create API token"</li>
                <li>3. Give it a label (e.g., "RADEX Integration")</li>
                <li>4. Copy the generated token</li>
              </>
            )}
            {(formData.confluence_type === 'server' || formData.confluence_type === 'data_center') && (
              <>
                <li>1. Contact your Confluence administrator</li>
                <li>2. Request an API token for integration</li>
                <li>3. Provide your email address</li>
                <li>4. Use the provided token here</li>
              </>
            )}
          </ul>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-end space-x-3 pt-6 border-t border-gray-200">
          <Button
            type="button"
            variant="ghost"
            onClick={onClose}
            disabled={isSubmitting || isTestingConnection}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            disabled={isSubmitting || isTestingConnection}
            className="min-w-[120px]"
          >
            {isSubmitting ? (
              <div className="flex items-center">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                {mode === 'create' ? 'Adding...' : 'Updating...'}
              </div>
            ) : (
              mode === 'create' ? 'Add Credential' : 'Update Credential'
            )}
          </Button>
        </div>
      </form>
    </Modal>
  );
}