'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { Folder as FolderType } from '@/types/folder';
import { Document } from '@/types/document';
import apiClient from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { 
  Folder, 
  FileText, 
  Upload, 
  MoreVertical, 
  Edit2, 
  Trash2,
  Download,
  Calendar,
  User,
  Shield,
  Share2
} from 'lucide-react';
import { format } from 'date-fns';
import { useDropzone } from 'react-dropzone';
import ShareFolderModal from '@/components/folders/ShareFolderModal';

export default function FolderDetailPage() {
  const params = useParams();
  const folderId = params.id as string;
  
  const [folder, setFolder] = useState<FolderType | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isEditingName, setIsEditingName] = useState(false);
  const [newName, setNewName] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [showShareModal, setShowShareModal] = useState(false);

  useEffect(() => {
    if (folderId) {
      loadFolderData();
    }
  }, [folderId]);

  const loadFolderData = async () => {
    try {
      setIsLoading(true);
      const [folderData, documentsData] = await Promise.all([
        apiClient.getFolder(folderId),
        apiClient.getFolderDocuments(folderId)
      ]);
      setFolder(folderData);
      setDocuments(documentsData);
    } catch (error) {
      console.error('Failed to load folder data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpdateFolderName = async () => {
    if (!newName.trim() || !folder) return;

    try {
      await apiClient.updateFolder(folder.id, { name: newName });
      setFolder({ ...folder, name: newName });
      setIsEditingName(false);
      setNewName('');
    } catch (error) {
      console.error('Failed to update folder name:', error);
    }
  };

  const handleDeleteDocument = async (documentId: string) => {
    if (!window.confirm('Are you sure you want to delete this document?')) return;

    try {
      await apiClient.deleteDocument(documentId);
      setDocuments(documents.filter(doc => doc.id !== documentId));
    } catch (error) {
      console.error('Failed to delete document:', error);
    }
  };

  const handleDownload = async (documentId: string, filename: string) => {
    try {
      const response = await apiClient.downloadDocument(documentId);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to download document:', error);
    }
  };

  const onDrop = async (acceptedFiles: File[]) => {
    setIsUploading(true);
    
    try {
      for (const file of acceptedFiles) {
        await apiClient.uploadDocument(folderId, file);
      }
      await loadFolderData(); // Reload to show new documents
    } catch (error) {
      console.error('Failed to upload files:', error);
    } finally {
      setIsUploading(false);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
      'text/markdown': ['.md'],
      'text/html': ['.html', '.htm']
    }
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-600 bg-green-100';
      case 'processing': return 'text-yellow-600 bg-yellow-100';
      case 'failed': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="bg-white rounded-lg shadow p-6 animate-pulse">
          <div className="w-48 h-8 bg-gray-200 rounded mb-2"></div>
          <div className="w-32 h-4 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (!folder) {
    return (
      <div className="text-center py-12">
        <h1 className="text-2xl font-bold text-gray-900">Folder not found</h1>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Folder Header */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-blue-100 rounded-lg">
              <Folder className="w-8 h-8 text-blue-600" />
            </div>
            <div>
              {isEditingName ? (
                <div className="flex items-center space-x-2">
                  <Input
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                    placeholder={folder.name}
                    className="text-lg font-bold"
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') handleUpdateFolderName();
                    }}
                  />
                  <Button size="sm" onClick={handleUpdateFolderName}>
                    Save
                  </Button>
                  <Button 
                    size="sm" 
                    variant="ghost" 
                    onClick={() => {
                      setIsEditingName(false);
                      setNewName('');
                    }}
                  >
                    Cancel
                  </Button>
                </div>
              ) : (
                <div className="flex items-center space-x-2">
                  <h1 className="text-2xl font-bold text-gray-900">{folder.name}</h1>
                  <button
                    onClick={() => {
                      setIsEditingName(true);
                      setNewName(folder.name);
                    }}
                    className="p-1 text-gray-400 hover:text-gray-600"
                  >
                    <Edit2 className="w-4 h-4" />
                  </button>
                </div>
              )}
              <p className="text-gray-600">{documents.length} documents</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <Button 
              variant="secondary"
              onClick={() => setShowShareModal(true)}
            >
              <Share2 className="w-4 h-4 mr-2" />
              Share
            </Button>
            <Button variant="secondary">
              <Shield className="w-4 h-4 mr-2" />
              Permissions
            </Button>
            <button className="p-2 text-gray-400 hover:text-gray-600">
              <MoreVertical className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Upload Area */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Upload Documents</h2>
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
            isDragActive 
              ? 'border-blue-500 bg-blue-50' 
              : 'border-gray-300 hover:border-gray-400'
          }`}
        >
          <input {...getInputProps()} />
          <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          {isDragActive ? (
            <p className="text-blue-600">Drop the files here...</p>
          ) : (
            <div>
              <p className="text-gray-600 mb-2">
                Drag and drop files here, or click to select
              </p>
              <p className="text-sm text-gray-500">
                Supports PDF, DOC, DOCX, TXT, MD, HTML files
              </p>
            </div>
          )}
          {isUploading && (
            <div className="mt-4">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto"></div>
              <p className="text-sm text-gray-600 mt-2">Uploading...</p>
            </div>
          )}
        </div>
      </div>

      {/* Documents List */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">Documents</h2>
        </div>
        
        {documents.length === 0 ? (
          <div className="p-12 text-center">
            <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No documents yet</h3>
            <p className="text-gray-600">Upload documents to get started</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {documents.map((document) => (
              <div key={document.id} className="p-6 hover:bg-gray-50 transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <FileText className="w-8 h-8 text-gray-400" />
                    <div>
                      <h3 className="font-medium text-gray-900">{document.filename}</h3>
                      <div className="flex items-center space-x-4 text-sm text-gray-500">
                        <span>{formatFileSize(document.file_size)}</span>
                        <span>•</span>
                        <div className="flex items-center">
                          <Calendar className="w-3 h-3 mr-1" />
                          {format(new Date(document.created_at), 'MMM d, yyyy')}
                        </div>
                        <span>•</span>
                        <span
                          className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(document.embedding_status || 'pending')}`}
                        >
                          {document.embedding_status || 'pending'}
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => handleDownload(document.id, document.filename)}
                    >
                      <Download className="w-4 h-4" />
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => handleDeleteDocument(document.id)}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
                
                {document.error_message && (
                  <div className="mt-2 text-sm text-red-600 bg-red-50 p-2 rounded">
                    {document.error_message}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Share Folder Modal */}
      {folder && (
        <ShareFolderModal
          isOpen={showShareModal}
          onClose={() => setShowShareModal(false)}
          folderId={folder.id}
          folderName={folder.name}
        />
      )}
    </div>
  );
}