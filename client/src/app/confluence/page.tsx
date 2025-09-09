'use client';

import { useState } from 'react';
import ConfluenceCredentials from '@/components/confluence/ConfluenceCredentials';
import ConfluenceImportStatus from '@/components/confluence/ConfluenceImportStatus';
import { Cloud, Settings, Activity } from 'lucide-react';

type Tab = 'credentials' | 'status';

export default function ConfluencePage() {
  const [activeTab, setActiveTab] = useState<Tab>('credentials');

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center space-x-4">
          <div className="p-3 bg-blue-100 rounded-lg">
            <Cloud className="w-8 h-8 text-blue-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Confluence Integration</h1>
            <p className="text-gray-600">
              Manage your Confluence connections and import content into your folders
            </p>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="bg-white rounded-lg shadow">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8 px-6">
            <button
              onClick={() => setActiveTab('credentials')}
              className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center ${
                activeTab === 'credentials'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <Settings className="w-4 h-4 mr-2" />
              Credentials & Settings
            </button>
            <button
              onClick={() => setActiveTab('status')}
              className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center ${
                activeTab === 'status'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <Activity className="w-4 h-4 mr-2" />
              Import Status
            </button>
          </nav>
        </div>

        <div className="p-6">
          {activeTab === 'credentials' ? (
            <ConfluenceCredentials />
          ) : (
            <ConfluenceImportStatus />
          )}
        </div>
      </div>
    </div>
  );
}