'use client';

import { useState, useEffect, useCallback } from 'react';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Alert, AlertDescription } from '@/components/ui/Alert';
import apiClient from '@/lib/api';
import { 
  Search, 
  User, 
  X, 
  Plus, 
  Eye,
  Edit,
  Trash2,
  Crown
} from 'lucide-react';

interface User {
  id: string;
  username: string;
  email: string;
  is_active: boolean;
}

interface FolderPermission {
  id: string;
  user_id: string;
  folder_id: string;
  can_read: boolean;
  can_write: boolean;
  can_delete: boolean;
  is_admin: boolean;
  granted_by: string;
  created_at: string;
  user?: {
    id: string;
    username: string;
    email: string;
  };
}

interface ShareFolderModalProps {
  isOpen: boolean;
  onClose: () => void;
  folderId: string;
  folderName: string;
}

export default function ShareFolderModal({ isOpen, onClose, folderId, folderName }: ShareFolderModalProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<User[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [existingPermissions, setExistingPermissions] = useState<FolderPermission[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Permission state for new user
  const [newPermissions, setNewPermissions] = useState({
    can_read: true,
    can_write: false,
    can_delete: false,
    is_admin: false
  });

  const loadExistingPermissions = useCallback(async () => {
    try {
      setIsLoading(true);
      const permissions = await apiClient.getFolderPermissions(folderId);
      setExistingPermissions(permissions);
    } catch {
      setError('Failed to load existing permissions');
    } finally {
      setIsLoading(false);
    }
  }, [folderId]);

  useEffect(() => {
    if (isOpen) {
      loadExistingPermissions();
      setError('');
      setSuccess('');
      setSearchQuery('');
      setSearchResults([]);
    }
  }, [isOpen, folderId, loadExistingPermissions]);

  const searchUsers = async (query: string) => {
    if (query.length < 2) {
      setSearchResults([]);
      return;
    }

    try {
      setIsSearching(true);
      const trimmedQuery = query.trim();
      
      // First try to find by email (if query looks like an email)
      if (trimmedQuery.includes('@')) {
        try {
          const user = await apiClient.findUser({ email: trimmedQuery });
          setSearchResults([user]);
          return;
        } catch {
          // If email not found, continue to username search
        }
      }
      
      // Try to find by username
      try {
        const user = await apiClient.findUser({ username: trimmedQuery });
        setSearchResults([user]);
      } catch {
        // If exact matches fail, no results found
        setSearchResults([]);
      }
    } catch (error: unknown) {
      console.error('Failed to find user:', error);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (searchQuery.trim()) {
        searchUsers(searchQuery.trim());
      } else {
        setSearchResults([]);
      }
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [searchQuery]);

  const handleGrantPermission = async (userId: string) => {
    try {
      setError('');
      setSuccess('');
      
      const permissionData = {
        user_id: userId,
        ...newPermissions
      };

      await apiClient.grantFolderPermission(folderId, permissionData);
      setSuccess('Permission granted successfully');
      setSearchQuery('');
      setSearchResults([]);
      await loadExistingPermissions();
    } catch {
      setError('Failed to grant permission');
    }
  };

  const handleRevokePermission = async (userId: string) => {
    if (!confirm('Are you sure you want to revoke this user\'s access to this folder?')) {
      return;
    }

    try {
      setError('');
      setSuccess('');
      
      await apiClient.revokeFolderPermission(folderId, userId);
      setSuccess('Permission revoked successfully');
      await loadExistingPermissions();
    } catch {
      setError('Failed to revoke permission');
    }
  };

  const getPermissionBadges = (permission: FolderPermission) => {
    const badges = [];
    
    if (permission.is_admin) {
      badges.push(<span key="admin" className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-purple-100 text-purple-800">Admin</span>);
    } else {
      if (permission.can_read) {
        badges.push(<span key="read" className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">Read</span>);
      }
      if (permission.can_write) {
        badges.push(<span key="write" className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">Write</span>);
      }
      if (permission.can_delete) {
        badges.push(<span key="delete" className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800">Delete</span>);
      }
    }

    return badges.length > 0 ? badges : [<span key="none" className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-800">No Access</span>];
  };

  const isUserAlreadyShared = (userId: string) => {
    return existingPermissions.some(p => p.user_id === userId);
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={`Share "${folderName}"`} size="lg">
      <div className="space-y-6">
        {/* Error/Success Alerts */}
        {error && (
          <Alert variant="error">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        
        {success && (
          <Alert variant="success">
            <AlertDescription>{success}</AlertDescription>
          </Alert>
        )}

        {/* Add New User Section */}
        <div className="border rounded-lg p-4">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Add User</h3>
          
          {/* User Search */}
          <div className="space-y-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <Input
                placeholder="Enter exact email or username..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>

            {/* Search Results */}
            {searchResults.length > 0 && (
              <div className="border border-gray-200 rounded-lg max-h-60 overflow-y-auto">
                {searchResults.map((user) => (
                  <div key={user.id} className="p-3 border-b border-gray-100 last:border-b-0 hover:bg-gray-50">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center">
                          <User className="w-4 h-4 text-gray-600" />
                        </div>
                        <div>
                          <div className="text-sm font-medium text-gray-900">{user.username}</div>
                          <div className="text-sm text-gray-500">{user.email}</div>
                        </div>
                      </div>
                      <div>
                        {isUserAlreadyShared(user.id) ? (
                          <span className="text-sm text-gray-500">Already has access</span>
                        ) : (
                          <Button
                            size="sm"
                            onClick={() => handleGrantPermission(user.id)}
                            disabled={!user.is_active}
                          >
                            <Plus className="w-4 h-4 mr-1" />
                            Add
                          </Button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {isSearching && (
              <div className="text-sm text-gray-500 text-center py-2">Searching users...</div>
            )}

            {searchQuery.length >= 2 && !isSearching && searchResults.length === 0 && (
              <div className="text-sm text-gray-500 text-center py-2">
                No user found with that exact email or username
              </div>
            )}
          </div>

          {/* Permission Selection */}
          <div className="mt-4 pt-4 border-t border-gray-200">
            <h4 className="text-sm font-medium text-gray-900 mb-3">Default Permissions for New Users</h4>
            <div className="space-y-2">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={newPermissions.can_read}
                  onChange={(e) => setNewPermissions({...newPermissions, can_read: e.target.checked})}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <Eye className="w-4 h-4 ml-2 mr-1 text-blue-600" />
                <span className="text-sm text-gray-700">Can View</span>
              </label>
              
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={newPermissions.can_write}
                  onChange={(e) => setNewPermissions({...newPermissions, can_write: e.target.checked})}
                  className="rounded border-gray-300 text-green-600 focus:ring-green-500"
                />
                <Edit className="w-4 h-4 ml-2 mr-1 text-green-600" />
                <span className="text-sm text-gray-700">Can Edit</span>
              </label>
              
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={newPermissions.can_delete}
                  onChange={(e) => setNewPermissions({...newPermissions, can_delete: e.target.checked})}
                  className="rounded border-gray-300 text-red-600 focus:ring-red-500"
                />
                <Trash2 className="w-4 h-4 ml-2 mr-1 text-red-600" />
                <span className="text-sm text-gray-700">Can Delete</span>
              </label>
              
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={newPermissions.is_admin}
                  onChange={(e) => setNewPermissions({...newPermissions, is_admin: e.target.checked})}
                  className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                />
                <Crown className="w-4 h-4 ml-2 mr-1 text-purple-600" />
                <span className="text-sm text-gray-700">Admin (Full Access)</span>
              </label>
            </div>
          </div>
        </div>

        {/* Current Permissions */}
        <div className="border rounded-lg p-4">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Current Access</h3>
          
          {isLoading ? (
            <div className="text-center py-4">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
              <p className="text-sm text-gray-500 mt-2">Loading permissions...</p>
            </div>
          ) : existingPermissions.length === 0 ? (
            <p className="text-sm text-gray-500 text-center py-4">No users have been granted access yet</p>
          ) : (
            <div className="space-y-3">
              {existingPermissions.map((permission) => (
                <div key={permission.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center">
                      <User className="w-4 h-4 text-gray-600" />
                    </div>
                    <div>
                      <div className="text-sm font-medium text-gray-900">
                        {permission.user?.username || 'Unknown User'}
                      </div>
                      <div className="text-sm text-gray-500">
                        {permission.user?.email || 'No email available'}
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <div className="flex flex-wrap gap-1">
                      {getPermissionBadges(permission)}
                    </div>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => handleRevokePermission(permission.user_id)}
                      className="text-red-600 hover:text-red-700 hover:bg-red-50"
                    >
                      <X className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
          <Button variant="ghost" onClick={onClose}>
            Close
          </Button>
        </div>
      </div>
    </Modal>
  );
}