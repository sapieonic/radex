'use client';

import { useEffect, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Folder, FileText, MessageSquare, HardDrive } from 'lucide-react';
import apiClient from '@/lib/api';
import { Button } from '@/components/ui/Button';
import Link from 'next/link';

interface DashboardStats {
  totalFolders: number;
  totalDocuments: number;
  recentQueries: number;
  storageUsed: string;
}

export default function DashboardPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState<DashboardStats>({
    totalFolders: 0,
    totalDocuments: 0,
    recentQueries: 0,
    storageUsed: '0 MB',
  });
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setIsLoading(true);
      const folders = await apiClient.getFolders();
      
      setStats({
        totalFolders: folders.length,
        totalDocuments: 0, // TODO: Implement proper document count via separate API call
        recentQueries: 0, // TODO: Implement query history
        storageUsed: '0 MB', // TODO: Calculate storage usage
      });
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const statsCards = [
    {
      title: 'Total Documents',
      value: stats.totalDocuments.toString(),
      icon: FileText,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
    },
    {
      title: 'Accessible Folders',
      value: stats.totalFolders.toString(),
      icon: Folder,
      color: 'text-green-600',
      bgColor: 'bg-green-100',
    },
    {
      title: 'Recent Queries',
      value: stats.recentQueries.toString(),
      icon: MessageSquare,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100',
    },
    {
      title: 'Storage Used',
      value: stats.storageUsed,
      icon: HardDrive,
      color: 'text-orange-600',
      bgColor: 'bg-orange-100',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Welcome Section */}
      <div className="bg-white rounded-lg shadow p-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          Welcome back, {user?.username}!
        </h1>
        <p className="text-gray-600">
          Manage your documents and explore your knowledge base with AI-powered search.
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statsCards.map((card) => {
          const IconComponent = card.icon;
          return (
            <div key={card.title} className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <div className={`p-3 rounded-lg ${card.bgColor} mr-4`}>
                  <IconComponent className={`w-6 h-6 ${card.color}`} />
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-600">{card.title}</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {isLoading ? '...' : card.value}
                  </p>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link href="/folders">
            <Button className="w-full justify-start" variant="secondary">
              <Folder className="w-5 h-5 mr-2" />
              Manage Folders
            </Button>
          </Link>
          <Button className="w-full justify-start" variant="secondary">
            <FileText className="w-5 h-5 mr-2" />
            Upload Documents
          </Button>
          <Link href="/chat">
            <Button className="w-full justify-start" variant="secondary">
              <MessageSquare className="w-5 h-5 mr-2" />
              Start RAG Query
            </Button>
          </Link>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h2>
        <div className="text-center py-8 text-gray-500">
          <MessageSquare className="w-12 h-12 mx-auto mb-4 text-gray-300" />
          <p>No recent activity</p>
          <p className="text-sm">Your recent document uploads and queries will appear here</p>
        </div>
      </div>
    </div>
  );
}