'use client';

import { useState, useEffect } from 'react';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Alert, AlertDescription } from '@/components/ui/Alert';
import apiClient from '@/lib/api';
import { Eye, EyeOff, Crown, UserCheck } from 'lucide-react';

interface AdminUser {
  id: string;
  username: string;
  email: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
  updated_at: string;
}

interface UserFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  user?: AdminUser | null;
  mode: 'create' | 'edit';
}

export default function UserFormModal({ isOpen, onClose, onSuccess, user, mode }: UserFormModalProps) {
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    password: '',
    is_active: true,
    is_superuser: false
  });
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isOpen) {
      if (mode === 'edit' && user) {
        setFormData({
          email: user.email,
          username: user.username,
          password: '', // Don't pre-fill password
          is_active: user.is_active,
          is_superuser: user.is_superuser
        });
      } else {
        setFormData({
          email: '',
          username: '',
          password: '',
          is_active: true,
          is_superuser: false
        });
      }
      setError('');
      setShowPassword(false);
    }
  }, [isOpen, mode, user]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError('');

    try {
      if (mode === 'create') {
        await apiClient.createUser({
          email: formData.email,
          username: formData.username,
          password: formData.password,
          is_active: formData.is_active,
          is_superuser: formData.is_superuser
        });
      } else if (mode === 'edit' && user) {
        const updateData: Record<string, unknown> = {
          email: formData.email,
          username: formData.username,
          is_active: formData.is_active,
          is_superuser: formData.is_superuser
        };
        
        // Only include password if it's provided
        if (formData.password.trim()) {
          updateData.password = formData.password;
        }

        await apiClient.updateUser(user.id, updateData);
      }

      onSuccess();
      onClose();
    } catch {
      setError(`Failed to ${mode} user`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleInputChange = (field: string, value: string | boolean) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={mode === 'create' ? 'Create New User' : `Edit User: ${user?.username}`}
      size="md"
    >
      <form onSubmit={handleSubmit} className="space-y-6">
        {error && (
          <Alert variant="error">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Email Field */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Email Address
          </label>
          <Input
            type="email"
            value={formData.email}
            onChange={(e) => handleInputChange('email', e.target.value)}
            placeholder="user@example.com"
            required
          />
        </div>

        {/* Username Field */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Username
          </label>
          <Input
            type="text"
            value={formData.username}
            onChange={(e) => handleInputChange('username', e.target.value)}
            placeholder="username"
            required
            minLength={3}
            maxLength={100}
          />
        </div>

        {/* Password Field */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Password {mode === 'edit' && <span className="text-gray-500">(leave blank to keep current)</span>}
          </label>
          <div className="relative">
            <Input
              type={showPassword ? 'text' : 'password'}
              value={formData.password}
              onChange={(e) => handleInputChange('password', e.target.value)}
              placeholder={mode === 'edit' ? 'Leave blank to keep current password' : 'Enter password'}
              required={mode === 'create'}
              minLength={8}
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              {showPassword ? (
                <EyeOff className="w-4 h-4" />
              ) : (
                <Eye className="w-4 h-4" />
              )}
            </button>
          </div>
          {mode === 'create' && (
            <p className="mt-1 text-xs text-gray-500">Minimum 8 characters required</p>
          )}
        </div>

        {/* User Status */}
        <div className="space-y-4">
          <h3 className="text-sm font-medium text-gray-700">User Settings</h3>
          
          <div className="space-y-3">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={formData.is_active}
                onChange={(e) => handleInputChange('is_active', e.target.checked)}
                className="rounded border-gray-300 text-green-600 focus:ring-green-500"
              />
              <UserCheck className="w-4 h-4 ml-2 mr-2 text-green-600" />
              <span className="text-sm text-gray-700">Active User</span>
              <span className="ml-2 text-xs text-gray-500">
                (User can log in and access the system)
              </span>
            </label>
            
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={formData.is_superuser}
                onChange={(e) => handleInputChange('is_superuser', e.target.checked)}
                className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
              />
              <Crown className="w-4 h-4 ml-2 mr-2 text-purple-600" />
              <span className="text-sm text-gray-700">Administrator</span>
              <span className="ml-2 text-xs text-gray-500">
                (Full system access including user management)
              </span>
            </label>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-end space-x-3 pt-6 border-t border-gray-200">
          <Button
            type="button"
            variant="ghost"
            onClick={onClose}
            disabled={isSubmitting}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            disabled={isSubmitting}
            className="min-w-[100px]"
          >
            {isSubmitting ? (
              <div className="flex items-center">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                {mode === 'create' ? 'Creating...' : 'Updating...'}
              </div>
            ) : (
              mode === 'create' ? 'Create User' : 'Update User'
            )}
          </Button>
        </div>
      </form>
    </Modal>
  );
}