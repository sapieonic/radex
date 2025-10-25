'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import apiClient from '@/lib/api';

interface AuthConfig {
  enable_google_login: boolean;
  enable_microsoft_login: boolean;
  enable_okta_login: boolean;
  enable_manual_signup: boolean;
}

export default function LoginForm() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [provider, setProvider] = useState<string | null>(null);
  const [isSignupMode, setIsSignupMode] = useState(false);
  const [authConfig, setAuthConfig] = useState<AuthConfig>({
    enable_google_login: true,
    enable_microsoft_login: false,
    enable_okta_login: false,
    enable_manual_signup: true,
  });

  // Manual login/signup form fields
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const { loginWithGoogle, loginWithMicrosoft, loginWithOkta, login, register, isAuthenticated, user } = useAuth();
  const router = useRouter();

  // Fetch auth configuration on mount
  useEffect(() => {
    const fetchAuthConfig = async () => {
      try {
        const config = await apiClient.getAuthConfig();
        setAuthConfig(config);
      } catch (error) {
        console.error('Failed to fetch auth config:', error);
      }
    };
    fetchAuthConfig();
  }, []);

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
      router.push('/dashboard');
    } catch (error: unknown) {
      console.error('Okta login error:', error);
      if (error instanceof Error && !error.message.includes('Redirect initiated')) {
        setError(error.message);
      }
      setIsLoading(false);
      setProvider(null);
    }
  };

  const handleManualLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      await login(username, password);
      router.push('/dashboard');
    } catch (error: unknown) {
      console.error('Login error:', error);
      setError(error instanceof Error ? error.message : 'Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleManualSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      setIsLoading(false);
      return;
    }

    try {
      await register(email, username, password);
      router.push('/dashboard');
    } catch (error: unknown) {
      console.error('Registration error:', error);
      setError(error instanceof Error ? error.message : 'Registration failed');
    } finally {
      setIsLoading(false);
    }
  };

  const hasOAuthProviders = authConfig.enable_google_login || authConfig.enable_microsoft_login || authConfig.enable_okta_login;

  return (
    <div className="min-h-screen flex">
      {/* Left Section - App Information */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-blue-600 via-blue-700 to-indigo-800 p-12 flex-col justify-between text-white">
        <div>
          <h1 className="text-5xl font-bold mb-4">RADEX</h1>
          <p className="text-xl text-blue-100">RAG Document Explorer with RBAC</p>
        </div>

        <div className="space-y-8">
          <div>
            <h2 className="text-3xl font-bold mb-6">Intelligent Document Management</h2>
            <ul className="space-y-4 text-lg">
              <li className="flex items-start">
                <svg className="w-6 h-6 mr-3 mt-1 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <span>AI-Powered document search and question answering</span>
              </li>
              <li className="flex items-start">
                <svg className="w-6 h-6 mr-3 mt-1 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <span>Role-based access control for secure collaboration</span>
              </li>
              <li className="flex items-start">
                <svg className="w-6 h-6 mr-3 mt-1 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <span>Hierarchical folder organization with granular permissions</span>
              </li>
              <li className="flex items-start">
                <svg className="w-6 h-6 mr-3 mt-1 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <span>Support for PDF, Word, Text, Markdown, and HTML documents</span>
              </li>
            </ul>
          </div>
        </div>

        <div className="text-sm text-blue-200">
          © 2024 RADEX. Powered by OpenAI & FastAPI.
        </div>
      </div>

      {/* Right Section - Login Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center bg-gray-50 p-8">
        <div className="max-w-md w-full">
          {/* Mobile logo */}
          <div className="lg:hidden text-center mb-8">
            <h1 className="text-4xl font-bold text-blue-600">RADEX</h1>
            <p className="text-sm text-gray-600 mt-2">RAG Document Explorer with RBAC</p>
          </div>

          <div className="bg-white p-8 rounded-2xl shadow-xl">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              {isSignupMode ? 'Create Account' : 'Welcome Back'}
            </h2>
            <p className="text-gray-600 mb-6">
              {isSignupMode ? 'Sign up to get started' : 'Sign in to your account'}
            </p>

            {/* Manual Login/Signup Form */}
            {authConfig.enable_manual_signup && (
              <form onSubmit={isSignupMode ? handleManualSignup : handleManualLogin} className="space-y-4 mb-6">
                {isSignupMode && (
                  <div>
                    <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                      Email
                    </label>
                    <Input
                      id="email"
                      type="email"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="Enter your email"
                      className="w-full"
                    />
                  </div>
                )}

                <div>
                  <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-1">
                    Username
                  </label>
                  <Input
                    id="username"
                    type="text"
                    required
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="Enter your username"
                    className="w-full"
                  />
                </div>

                <div>
                  <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
                    Password
                  </label>
                  <Input
                    id="password"
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter your password"
                    className="w-full"
                  />
                </div>

                {isSignupMode && (
                  <div>
                    <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-1">
                      Confirm Password
                    </label>
                    <Input
                      id="confirmPassword"
                      type="password"
                      required
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="Confirm your password"
                      className="w-full"
                    />
                  </div>
                )}

                <Button
                  type="submit"
                  disabled={isLoading}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white"
                >
                  {isLoading ? 'Please wait...' : (isSignupMode ? 'Sign Up' : 'Sign In')}
                </Button>

                <div className="text-center">
                  <button
                    type="button"
                    onClick={() => {
                      setIsSignupMode(!isSignupMode);
                      setError('');
                    }}
                    className="text-sm text-blue-600 hover:text-blue-700 font-medium"
                  >
                    {isSignupMode ? 'Already have an account? Sign In' : "Don't have an account? Sign Up"}
                  </button>
                </div>
              </form>
            )}

            {/* Divider */}
            {authConfig.enable_manual_signup && hasOAuthProviders && (
              <div className="relative my-6">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-gray-300"></div>
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-4 bg-white text-gray-500">Or continue with</span>
                </div>
              </div>
            )}

            {/* OAuth Providers */}
            <div className="space-y-3">
              {authConfig.enable_google_login && (
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
              )}

              {authConfig.enable_microsoft_login && (
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
              )}

              {authConfig.enable_okta_login && (
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
              )}
            </div>

            {error && (
              <div className="mt-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
                <p className="text-sm font-medium">{error}</p>
              </div>
            )}

            <div className="mt-6 pt-6 border-t border-gray-200">
              <p className="text-center text-xs text-gray-500">
                By signing in, you agree to our Terms of Service and Privacy Policy
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
