'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Alert, AlertDescription } from '@/components/ui/Alert';
import { 
  Users, 
  Settings, 
  BarChart3, 
  Database,
  Shield,
  Server,
  Activity,
  UserCheck,
  UserX,
  Search,
  Filter,
  MoreVertical,
  Crown,
  ArrowLeft,
  Plus,
  Edit,
  Trash2
} from 'lucide-react';
import Link from 'next/link';
import apiClient from '@/lib/api';
import UserFormModal from '@/components/admin/UserFormModal';

interface AdminUser {
  id: string;
  username: string;
  email: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
  updated_at: string;
}

interface SystemStats {
  total_users: number;
  active_users: number;
  total_folders: number;
  total_documents: number;
  storage_used: string;
  system_health: 'healthy' | 'warning' | 'error';
}

export default function AdminPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [activeTab, setActiveTab] = useState('users');
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [stats, setStats] = useState<SystemStats>({
    total_users: 0,
    active_users: 0,
    total_folders: 0,
    total_documents: 0,
    storage_used: '0 MB',
    system_health: 'healthy'
  });
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState<'all' | 'active' | 'inactive'>('all');
  const [error, setError] = useState('');
  const [selectedUser, setSelectedUser] = useState<AdminUser | null>(null);
  const [showUserModal, setShowUserModal] = useState(false);
  const [userModalMode, setUserModalMode] = useState<'create' | 'edit'>('create');

  useEffect(() => {
    // Check if user is logged in
    if (!user) {
      router.push('/login');
      return;
    }

    // Load admin data if user is superuser
    if (user.is_superuser) {
      loadAdminData();
    } else {
      setIsLoading(false);
    }
  }, [user, router]);

  const loadAdminData = async () => {
    try {
      setIsLoading(true);
      
      // Load users from API
      const usersData = await apiClient.listUsers({ limit: 100 });
      setUsers(usersData);
      
      // Calculate stats from loaded data
      const totalUsers = usersData.length;
      const activeUsers = usersData.filter((u: AdminUser) => u.is_active).length;
      
      setStats({
        total_users: totalUsers,
        active_users: activeUsers,
        total_folders: 0, // TODO: Implement folder count API
        total_documents: 0, // TODO: Implement document count API
        storage_used: '0 MB', // TODO: Implement storage usage API
        system_health: 'healthy'
      });
    } catch (error) {
      console.error('Failed to load admin data:', error);
      setError('Failed to load admin data');
    } finally {
      setIsLoading(false);
    }
  };

  const handleUserStatusToggle = async (userId: string, currentStatus: boolean) => {
    try {
      setError('');
      await apiClient.updateUser(userId, { is_active: !currentStatus });
      
      // Reload users to get updated data
      await loadUsersWithFilters();
    } catch (error) {
      console.error('Failed to update user status:', error);
      setError('Failed to update user status');
    }
  };

  const handleCreateUser = () => {
    setUserModalMode('create');
    setSelectedUser(null);
    setShowUserModal(true);
  };

  const handleEditUser = (user: AdminUser) => {
    setUserModalMode('edit');
    setSelectedUser(user);
    setShowUserModal(true);
  };

  const handleDeleteUser = async (userId: string, username: string) => {
    if (!confirm(`Are you sure you want to delete user "${username}"? This action cannot be undone.`)) {
      return;
    }

    try {
      setError('');
      await apiClient.deleteUser(userId);
      await loadUsersWithFilters();
    } catch (error: any) {
      console.error('Failed to delete user:', error);
      setError(error.response?.data?.detail || 'Failed to delete user');
    }
  };

  const handleUserModalSuccess = () => {
    loadUsersWithFilters();
    setShowUserModal(false);
    setSelectedUser(null);
  };

  const loadUsersWithFilters = async () => {
    try {
      setIsLoading(true);
      setError('');
      
      const params: any = { limit: 100 };
      
      // Add status filter
      if (filterStatus !== 'all') {
        params.is_active = filterStatus === 'active';
      }
      
      // Load users with filters
      const usersData = await apiClient.listUsers(params);
      
      // Client-side search if query exists
      let filteredUsers = usersData;
      if (searchQuery.trim()) {
        filteredUsers = usersData.filter((user: AdminUser) => 
          user.username.toLowerCase().includes(searchQuery.toLowerCase()) ||
          user.email.toLowerCase().includes(searchQuery.toLowerCase())
        );
      }
      
      setUsers(filteredUsers);
      
      // Update stats with all users (not filtered)
      if (filterStatus === 'all' && !searchQuery.trim()) {
        const totalUsers = usersData.length;
        const activeUsers = usersData.filter((u: AdminUser) => u.is_active).length;
        
        setStats(prev => ({
          ...prev,
          total_users: totalUsers,
          active_users: activeUsers
        }));
      }
    } catch (error) {
      console.error('Failed to load users:', error);
      setError('Failed to load users');
    } finally {
      setIsLoading(false);
    }
  };

  // Trigger search when filters change
  useEffect(() => {
    if (user?.is_superuser) {
      loadUsersWithFilters();
    }
  }, [searchQuery, filterStatus, user?.is_superuser]);

  const filteredUsers = users;

  const StatCard = ({ title, value, icon: Icon, color }: {
    title: string;
    value: string | number;
    icon: any;
    color: string;
  }) => (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center">
        <div className={`p-3 rounded-lg ${color} mr-4`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
        </div>
      </div>
    </div>
  );

  // Show loading while checking permissions or loading data
  if (isLoading || !user) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  // Show unauthorized message for non-admin users
  if (!user.is_superuser) {
    return (
      <div className="min-h-[60vh] flex flex-col justify-center items-center">
        <div className="text-center max-w-md">
          <Shield className="mx-auto h-16 w-16 text-red-500 mb-6" />
          <h2 className="text-3xl font-bold text-gray-900 mb-4">Access Denied</h2>
          <p className="text-lg text-gray-600 mb-4">
            You don't have permission to access the admin panel.
          </p>
          <p className="text-sm text-gray-500 mb-8">
            Only administrators can access this area.
          </p>
          
          <Link href="/dashboard">
            <Button className="inline-flex items-center">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Go to Dashboard
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center space-x-3">
        <div className="p-2 bg-purple-100 rounded-lg">
          <Crown className="w-6 h-6 text-purple-600" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Admin Panel</h1>
          <p className="text-gray-600">Manage users, system settings, and monitor platform health</p>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Users"
          value={stats.total_users}
          icon={Users}
          color="bg-blue-600"
        />
        <StatCard
          title="Active Users"
          value={stats.active_users}
          icon={UserCheck}
          color="bg-green-600"
        />
        <StatCard
          title="Total Folders"
          value={stats.total_folders}
          icon={Database}
          color="bg-purple-600"
        />
        <StatCard
          title="Storage Used"
          value={stats.storage_used}
          icon={Server}
          color="bg-orange-600"
        />
      </div>

      {/* System Health Alert */}
      {stats.system_health !== 'healthy' && (
        <Alert variant={stats.system_health === 'warning' ? 'warning' : 'error'}>
          <Activity className="h-4 w-4" />
          <AlertDescription>
            System health status: {stats.system_health.toUpperCase()}
          </AlertDescription>
        </Alert>
      )}

      {/* Navigation Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8">
          {[
            { id: 'users', label: 'User Management', icon: Users },
            { id: 'system', label: 'System Settings', icon: Settings },
            { id: 'monitoring', label: 'Monitoring', icon: BarChart3 },
          ].map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'users' && (
        <div className="space-y-6">
          {/* User Management Controls */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6">
              <h2 className="text-lg font-semibold text-gray-900">User Management</h2>
              <div className="flex space-x-3 mt-4 sm:mt-0">
                <Button onClick={handleCreateUser} className="flex items-center">
                  <Plus className="w-4 h-4 mr-2" />
                  Create User
                </Button>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                  <Input
                    placeholder="Search users..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10 w-64"
                  />
                </div>
                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value as 'all' | 'active' | 'inactive')}
                  className="px-3 py-2 border border-gray-300 rounded-md text-sm text-gray-900 bg-white focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-transparent"
                >
                  <option value="all">All Users</option>
                  <option value="active">Active Only</option>
                  <option value="inactive">Inactive Only</option>
                </select>
              </div>
            </div>

            {/* Users Table */}
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      User
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Role
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Created
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredUsers.map((user) => (
                    <tr key={user.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-gray-900">{user.username}</div>
                          <div className="text-sm text-gray-500">{user.email}</div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          user.is_superuser 
                            ? 'bg-purple-100 text-purple-800' 
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {user.is_superuser ? 'Admin' : 'User'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          user.is_active 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {user.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(user.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <div className="flex items-center justify-end space-x-2">
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => handleEditUser(user)}
                            className="text-blue-600 hover:text-blue-700 hover:bg-blue-50"
                          >
                            <Edit className="w-4 h-4" />
                          </Button>
                          <Button
                            size="sm"
                            variant={user.is_active ? "danger" : "default"}
                            onClick={() => handleUserStatusToggle(user.id, user.is_active)}
                          >
                            {user.is_active ? (
                              <UserX className="w-4 h-4" />
                            ) : (
                              <UserCheck className="w-4 h-4" />
                            )}
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => handleDeleteUser(user.id, user.username)}
                            className="text-red-600 hover:text-red-700 hover:bg-red-50"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'system' && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-6">System Settings</h2>
          <div className="space-y-6">
            <Alert>
              <Settings className="h-4 w-4" />
              <AlertDescription>
                System configuration features will be implemented in future updates.
              </AlertDescription>
            </Alert>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="border border-gray-200 rounded-lg p-4">
                <h3 className="font-medium text-gray-900 mb-2">OpenAI Integration</h3>
                <p className="text-sm text-gray-600">Configure OpenAI API settings for RAG functionality.</p>
                <Button variant="secondary" className="mt-3">Configure</Button>
              </div>
              
              <div className="border border-gray-200 rounded-lg p-4">
                <h3 className="font-medium text-gray-900 mb-2">MinIO Storage</h3>
                <p className="text-sm text-gray-600">Manage document storage and backup settings.</p>
                <Button variant="secondary" className="mt-3">Configure</Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'monitoring' && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-6">System Monitoring</h2>
          <div className="space-y-6">
            <Alert>
              <BarChart3 className="h-4 w-4" />
              <AlertDescription>
                Advanced monitoring and analytics features will be implemented in future updates.
              </AlertDescription>
            </Alert>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="border border-gray-200 rounded-lg p-4 text-center">
                <Activity className="w-8 h-8 text-green-600 mx-auto mb-2" />
                <h3 className="font-medium text-gray-900">System Health</h3>
                <p className="text-2xl font-bold text-green-600 mt-2">Healthy</p>
              </div>
              
              <div className="border border-gray-200 rounded-lg p-4 text-center">
                <Server className="w-8 h-8 text-blue-600 mx-auto mb-2" />
                <h3 className="font-medium text-gray-900">API Uptime</h3>
                <p className="text-2xl font-bold text-blue-600 mt-2">99.9%</p>
              </div>
              
              <div className="border border-gray-200 rounded-lg p-4 text-center">
                <Database className="w-8 h-8 text-purple-600 mx-auto mb-2" />
                <h3 className="font-medium text-gray-900">Database</h3>
                <p className="text-2xl font-bold text-purple-600 mt-2">Online</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* User Form Modal */}
      <UserFormModal
        isOpen={showUserModal}
        onClose={() => {
          setShowUserModal(false);
          setSelectedUser(null);
        }}
        onSuccess={handleUserModalSuccess}
        user={selectedUser}
        mode={userModalMode}
      />
    </div>
  );
}