'use client';

import Link from 'next/link';
import { Button } from '@/components/ui/Button';
import { Shield, ArrowLeft } from 'lucide-react';

export default function NotAuthorized() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="text-center">
          <Shield className="mx-auto h-16 w-16 text-red-500" />
          <h2 className="mt-6 text-3xl font-bold text-gray-900">Access Denied</h2>
          <p className="mt-4 text-lg text-gray-600">
            You don't have permission to access the admin panel.
          </p>
          <p className="mt-2 text-sm text-gray-500">
            Only administrators can access this area.
          </p>
        </div>
        
        <div className="mt-8 text-center">
          <Link href="/dashboard">
            <Button className="inline-flex items-center">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Go to Dashboard
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}