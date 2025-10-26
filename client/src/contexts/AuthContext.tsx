'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { User, AuthContextType } from '@/types/auth';
import apiClient from '@/lib/api';
import {
  onAuthStateChange,
  signInWithGoogle,
  signInWithMicrosoft,
  signInWithOkta,
  signUpWithEmailPassword,
  signInWithEmailPassword,
  signOut as firebaseSignOut,
  getIdToken,
  handleRedirectResult,
  FirebaseUser,
} from '@/lib/firebase';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [firebaseUser, setFirebaseUser] = useState<FirebaseUser | null>(null);
  const [token, setTokenState] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Initialize Firebase auth state listener
  useEffect(() => {
    let mounted = true;

    // Handle redirect result first (for Okta OIDC)
    const initAuth = async () => {
      try {
        // Check for redirect result first
        const redirectResult = await handleRedirectResult() as { user: { uid: string } };
        if (redirectResult) {
          console.log('Redirect result received:', redirectResult?.user?.uid);
        }
      } catch (error) {
        console.error('Error handling redirect result:', error);
      }

      // Then set up auth state listener
      const unsubscribe = onAuthStateChange(async (fbUser) => {
        if (!mounted) return;

        setFirebaseUser(fbUser);

        if (fbUser) {
          // User is signed in with Firebase
          try {
            console.log('Firebase user authenticated:', fbUser.uid);
            // Get Firebase ID token
            const idToken = await getIdToken();

            if (idToken) {
              console.log('Authenticating with backend...');
              // Authenticate with backend
              const userData = await apiClient.firebaseLogin(idToken);
              console.log('Backend authentication successful:', userData.email);
              setUser(userData);
              setTokenState(idToken);
              apiClient.setToken(idToken);
            }
          } catch (error) {
            console.error('Failed to authenticate with backend:', error);
            setUser(null);
            setTokenState(null);
          }
        } else {
          // User is signed out
          console.log('User signed out');
          setUser(null);
          setTokenState(null);
          apiClient.setToken(null);
        }

        setIsLoading(false);
      });

      return unsubscribe;
    };

    let unsubscribe: (() => void) | undefined;
    initAuth().then((unsub) => {
      unsubscribe = unsub;
    });

    return () => {
      mounted = false;
      if (unsubscribe) {
        unsubscribe();
      }
    };
  }, []);

  const loginWithGoogle = async () => {
    try {
      setIsLoading(true);
      await signInWithGoogle();
      // Firebase auth state listener will handle the rest
    } catch (error) {
      setIsLoading(false);
      throw error;
    }
  };

  const loginWithMicrosoft = async () => {
    try {
      setIsLoading(true);
      await signInWithMicrosoft();
      // Firebase auth state listener will handle the rest
    } catch (error) {
      setIsLoading(false);
      throw error;
    }
  };

  const loginWithOkta = async () => {
    try {
      setIsLoading(true);
      await signInWithOkta();
      // Redirect flow - user will be redirected to Okta
    } catch (error) {
      setIsLoading(false);
      throw error;
    }
  };

  // Manual login with email/password via Firebase
  const login = async (email: string, password: string) => {
    try {
      setIsLoading(true);
      await signInWithEmailPassword(email, password);
      // Firebase auth state listener will handle the rest
    } catch (error) {
      setIsLoading(false);
      throw error;
    }
  };

  // Manual registration with email/password via Firebase
  const register = async (email: string, username: string, password: string) => {
    try {
      setIsLoading(true);
      // Create user in Firebase with email/password
      // Use username as display name
      await signUpWithEmailPassword(email, password, username);
      // Firebase auth state listener will handle the rest
    } catch (error) {
      setIsLoading(false);
      throw error;
    }
  };

  const logout = async () => {
    try {
      await firebaseSignOut();
      setUser(null);
      setTokenState(null);
      setFirebaseUser(null);
      apiClient.setToken(null);
    } catch (error) {
      console.error('Logout error:', error);
      throw error;
    }
  };

  const value: AuthContextType = {
    user,
    token,
    login,
    register,
    logout,
    loginWithGoogle,
    loginWithMicrosoft,
    loginWithOkta,
    firebaseUser,
    isAuthenticated: !!user,
    isLoading,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}