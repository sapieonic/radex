'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/Button';

export default function LoginForm() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [provider, setProvider] = useState<string | null>(null);

  const { loginWithGoogle, loginWithMicrosoft, loginWithOkta, isAuthenticated, user } = useAuth();
  const router = useRouter();

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated && user) {
      console.log('User already authenticated, redirecting to dashboard');
      router.push('/dashboard');
    }
  }, [isAuthenticated, user, router]);

  const handleGoogleLogin = async () => {
    try {
      setIsLoading(true);
      setProvider('google');
      setError('');
      await loginWithGoogle();
      router.push('/dashboard');
    } catch (error: unknown) {
      console.error('Google login error:', error);
      setError(error instanceof Error ? error.message : 'Failed to sign in with Google');
    } finally {
      setIsLoading(false);
      setProvider(null);
    }
  };

  const handleMicrosoftLogin = async () => {
    try {
      setIsLoading(true);
      setProvider('microsoft');
      setError('');
      await loginWithMicrosoft();
      router.push('/dashboard');
    } catch (error: unknown) {
      console.error('Microsoft login error:', error);
      setError(error instanceof Error ? error.message : 'Failed to sign in with Microsoft');
    } finally {
      setIsLoading(false);
      setProvider(null);
    }
  };

  const handleOktaLogin = async () => {
    try {
      setIsLoading(true);
      setProvider('okta');
      setError('');
      await loginWithOkta();
      // If popup succeeds, redirect to dashboard
      // If redirect is used, the page will redirect before we get here
      router.push('/dashboard');
    } catch (error: unknown) {
      console.error('Okta login error:', error);
      // Don't show error if it's just initiating redirect
      if (error instanceof Error && !error.message.includes('Redirect initiated')) {
        setError(error.message);
      }
      setIsLoading(false);
      setProvider(null);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="max-w-md w-full space-y-8 bg-white p-10 rounded-2xl shadow-xl">
        <div>
          <h1 className="text-center text-4xl font-bold text-blue-600">RADEX</h1>
          <p className="text-center text-sm text-gray-600 mt-2">
            RAG Document Explorer with RBAC
          </p>
          <h2 className="mt-8 text-center text-2xl font-bold text-gray-900">
            Sign in to your account
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Choose your preferred sign-in method
          </p>
        </div>

        <div className="mt-8 space-y-4">
          {/* Google Sign In */}
          <Button
            onClick={handleGoogleLogin}
            disabled={isLoading}
            className="w-full flex items-center justify-center gap-3 bg-white text-gray-700 border-2 border-gray-300 hover:bg-gray-50 hover:border-gray-400 transition-all"
          >
            {provider === 'google' ? (
              <span className="animate-spin h-5 w-5 border-2 border-gray-600 border-t-transparent rounded-full" />
            ) : (
              <svg className="h-5 w-5" viewBox="0 0 24 24">
                <path
                  fill="#4285F4"
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                />
                <path
                  fill="#34A853"
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                />
                <path
                  fill="#FBBC05"
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                />
                <path
                  fill="#EA4335"
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                />
              </svg>
            )}
            <span className="font-medium">
              {provider === 'google' ? 'Signing in...' : 'Continue with Google'}
            </span>
          </Button>

          {/* Microsoft Sign In */}
          <Button
            onClick={handleMicrosoftLogin}
            disabled={isLoading}
            className="w-full flex items-center justify-center gap-3 bg-white text-gray-700 border-2 border-gray-300 hover:bg-gray-50 hover:border-gray-400 transition-all"
          >
            {provider === 'microsoft' ? (
              <span className="animate-spin h-5 w-5 border-2 border-gray-600 border-t-transparent rounded-full" />
            ) : (
              <svg className="h-5 w-5" viewBox="0 0 23 23">
                <path fill="#f3f3f3" d="M0 0h23v23H0z" />
                <path fill="#f35325" d="M1 1h10v10H1z" />
                <path fill="#81bc06" d="M12 1h10v10H12z" />
                <path fill="#05a6f0" d="M1 12h10v10H1z" />
                <path fill="#ffba08" d="M12 12h10v10H12z" />
              </svg>
            )}
            <span className="font-medium">
              {provider === 'microsoft' ? 'Signing in...' : 'Continue with Microsoft'}
            </span>
          </Button>

          {/* Okta Sign In */}
          <Button
            onClick={handleOktaLogin}
            disabled={isLoading}
            className="w-full flex items-center justify-center gap-3 bg-white text-gray-700 border-2 border-gray-300 hover:bg-gray-50 hover:border-gray-400 transition-all"
          >
            {provider === 'okta' ? (
              <span className="animate-spin h-5 w-5 border-2 border-gray-600 border-t-transparent rounded-full" />
            ) : (
              <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none">
                <path
                  d="M12 2C6.477 2 2 6.477 2 12s4.477 10 10 10 10-4.477 10-10S17.523 2 12 2zm0 18c-4.411 0-8-3.589-8-8s3.589-8 8-8 8 3.589 8 8-3.589 8-8 8z"
                  fill="#007DC1"
                />
                <circle cx="12" cy="12" r="4" fill="#007DC1" />
              </svg>
            )}
            <span className="font-medium">
              {provider === 'okta' ? 'Redirecting...' : 'Continue with Okta'}
            </span>
          </Button>

          {error && (
            <div className="mt-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
              <p className="text-sm font-medium">{error}</p>
            </div>
          )}
        </div>

        <div className="mt-8 pt-6 border-t border-gray-200">
          <p className="text-center text-xs text-gray-500">
            By signing in, you agree to our Terms of Service and Privacy Policy
          </p>
        </div>

        <div className="mt-4 text-center">
          <p className="text-sm text-gray-600">
            Secure authentication powered by{' '}
            <span className="font-semibold text-blue-600">Firebase</span>
          </p>
        </div>
      </div>
    </div>
  );
}
