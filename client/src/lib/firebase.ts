/**
 * Firebase Configuration and Initialization
 *
 * This file initializes Firebase with the configuration from environment variables
 * and exports Firebase Auth instance with configured providers.
 */

import { initializeApp, getApps, FirebaseApp } from 'firebase/app';
import {
  getAuth,
  Auth,
  GoogleAuthProvider,
  OAuthProvider,
  signInWithPopup,
  signInWithRedirect,
  getRedirectResult,
  signOut as firebaseSignOut,
  onAuthStateChanged,
  User as FirebaseUser,
} from 'firebase/auth';

// Firebase configuration from environment variables
const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
  measurementId: process.env.NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID,
};

// Initialize Firebase (only once)
let app: FirebaseApp;
let auth: Auth;

if (typeof window !== 'undefined') {
  // Only initialize on client-side
  if (!getApps().length) {
    app = initializeApp(firebaseConfig);
  } else {
    app = getApps()[0];
  }

  auth = getAuth(app);
}

// Configure authentication providers
const googleProvider = new GoogleAuthProvider();
googleProvider.setCustomParameters({
  prompt: 'select_account',
});

// Microsoft provider (using OAuthProvider)
const microsoftProvider = new OAuthProvider('microsoft.com');
microsoftProvider.setCustomParameters({
  prompt: 'select_account',
});

// Okta provider (using OAuthProvider for OIDC)
// Note: The provider ID should match what's configured in Firebase Console
const oktaProviderId = 'oidc.okta';  // Okta OIDC provider ID from Firebase
const oktaProvider = new OAuthProvider(oktaProviderId);

/**
 * Sign in with Google
 */
export const signInWithGoogle = async (): Promise<FirebaseUser> => {
  try {
    const result = await signInWithPopup(auth, googleProvider);
    return result.user;
  } catch (error: unknown) {
    console.error('Google sign-in error:', error);
    throw new Error(error instanceof Error ? error.message : 'Failed to sign in with Google');
  }
};

/**
 * Sign in with Microsoft
 */
export const signInWithMicrosoft = async (): Promise<FirebaseUser> => {
  try {
    const result = await signInWithPopup(auth, microsoftProvider);
    return result.user;
  } catch (error: unknown) {
    console.error('Microsoft sign-in error:', error);
    throw new Error(error instanceof Error ? error.message : 'Failed to sign in with Microsoft');
  }
};

/**
 * Sign in with Okta (OIDC)
 * Try popup first, fallback to redirect
 */
export const signInWithOkta = async (): Promise<FirebaseUser> => {
  try {
    console.log('Initiating Okta sign-in with popup...');
    console.log('Auth domain:', auth.config.authDomain);
    console.log('Provider ID:', oktaProviderId);

    // Try popup flow first (more reliable for development)
    const result = await signInWithPopup(auth, oktaProvider);
    console.log('Okta sign-in successful:', result.user.uid);
    return result.user;
  } catch (error: unknown) {
    console.error('Okta popup sign-in failed, trying redirect...', error instanceof Error ? error.message : 'Failed to sign in with Okta');

    // If popup fails, try redirect
    try {
      await signInWithRedirect(auth, oktaProvider);
      // This will redirect the page, so we won't reach here
      throw new Error('Redirect initiated');
    } catch (redirectError: unknown) {
      console.error('Okta redirect sign-in error:', redirectError);
      throw new Error(redirectError instanceof Error ? redirectError.message : 'Failed to sign in with Okta');
    }
  }
};

/**
 * Handle redirect result (for Okta OIDC)
 * Call this in your app initialization to handle redirect results
 */
export const handleRedirectResult = async (): Promise<unknown> => {
  try {
    console.log('Checking for redirect result...');
    const result = await getRedirectResult(auth);
    if (result) {
      console.log('Redirect result found:', {
        uid: result.user.uid,
        email: result.user.email,
        providerId: result.providerId,
      });
    } else {
      console.log('No redirect result found');
    }
    return result;
  } catch (error: unknown) {
    console.error('Redirect result error:', error instanceof Error ? error.message : 'Failed to handle redirect result');
    throw new Error(error instanceof Error ? error.message : 'Failed to handle redirect result');
  }
};

/**
 * Sign out current user
 */
export const signOut = async (): Promise<void> => {
  try {
    await firebaseSignOut(auth);
  } catch (error: unknown) {
    console.error('Sign out error:', error);
    throw new Error(error instanceof Error ? error.message : 'Failed to sign out');
  }
};

/**
 * Get current Firebase user
 */
export const getCurrentUser = (): FirebaseUser | null => {
  return auth.currentUser;
};

/**
 * Get Firebase ID token for current user
 */
export const getIdToken = async (forceRefresh: boolean = false): Promise<string | null> => {
  const user = auth.currentUser;
  if (!user) return null;

  try {
    const token = await user.getIdToken(forceRefresh);
    return token;
  } catch (error: unknown) {
    console.error('Get ID token error:', error instanceof Error ? error.message : 'Failed to get ID token');
    return null;
  }
};

/**
 * Listen to auth state changes
 */
export const onAuthStateChange = (callback: (user: FirebaseUser | null) => void) => {
  return onAuthStateChanged(auth, callback);
};

// Export auth instance
export { auth };
export type { FirebaseUser };
