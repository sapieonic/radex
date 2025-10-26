'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { apiClient } from '@/lib/api';
import { Cloud, AlertCircle, CheckCircle } from 'lucide-react';

export default function SharePointCallback() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('Connecting to Microsoft 365...');

  useEffect(() => {
    const handleCallback = async () => {
      const code = searchParams.get('code');
      const state = searchParams.get('state');
      const error = searchParams.get('error');
      const errorDescription = searchParams.get('error_description');

      // Check for OAuth errors
      if (error) {
        setStatus('error');
        setMessage(errorDescription || `OAuth error: ${error}`);
        setTimeout(() => {
          router.push('/folders');
        }, 3000);
        return;
      }

      // Check for missing parameters
      if (!code || !state) {
        setStatus('error');
        setMessage('Invalid callback - missing authorization code or state');
        setTimeout(() => {
          router.push('/folders');
        }, 3000);
        return;
      }

      try {
        // Exchange code for connection
        const response = await apiClient.completeSharePointAuth(code, state);

        setStatus('success');
        setMessage('Successfully connected to Microsoft 365!');

        // Store connection ID in session storage for immediate use
        if (typeof window !== 'undefined') {
          sessionStorage.setItem('sp_connection_id', response.connection_id);
        }

        // Redirect to folders page after brief delay
        setTimeout(() => {
          router.push('/folders?sp_auth=success');
        }, 1500);
      } catch (err: any) {
        console.error('OAuth callback error:', err);
        setStatus('error');
        setMessage(err.response?.data?.detail || 'Failed to complete authentication');

        setTimeout(() => {
          router.push('/folders?sp_auth=error');
        }, 3000);
      }
    };

    handleCallback();
  }, [searchParams, router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8">
        <div className="flex flex-col items-center">
          {status === 'loading' && (
            <>
              <div className="relative">
                <Cloud className="w-16 h-16 text-blue-500 mb-4" />
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="animate-spin rounded-full h-20 w-20 border-b-2 border-blue-600"></div>
                </div>
              </div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">
                Connecting to Microsoft 365
              </h2>
              <p className="text-center text-gray-600">{message}</p>
            </>
          )}

          {status === 'success' && (
            <>
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
                <CheckCircle className="w-10 h-10 text-green-600" />
              </div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">
                Connection Successful!
              </h2>
              <p className="text-center text-gray-600">{message}</p>
              <p className="text-sm text-gray-500 mt-2">Redirecting...</p>
            </>
          )}

          {status === 'error' && (
            <>
              <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-4">
                <AlertCircle className="w-10 h-10 text-red-600" />
              </div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">
                Connection Failed
              </h2>
              <p className="text-center text-gray-600 mb-2">{message}</p>
              <p className="text-sm text-gray-500">Redirecting back...</p>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
