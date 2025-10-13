import { FirebaseUser } from '@/lib/firebase';

export enum AuthProvider {
  GOOGLE = 'google',
  MICROSOFT = 'microsoft',
  OKTA = 'okta',
  PASSWORD = 'password',
}

export interface User {
  id: string;
  email: string;
  username: string | null;
  firebase_uid: string | null;
  auth_provider: AuthProvider | null;
  display_name: string | null;
  photo_url: string | null;
  email_verified: boolean;
  is_active: boolean;
  is_superuser: boolean;
  last_login_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  username: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface FirebaseLoginRequest {
  id_token: string;
}

export interface AuthContextType {
  user: User | null;
  token: string | null;
  firebaseUser: FirebaseUser | null;
  login: (username: string, password: string) => Promise<void>;
  register: (email: string, username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  loginWithGoogle: () => Promise<void>;
  loginWithMicrosoft: () => Promise<void>;
  loginWithOkta: () => Promise<void>;
  isAuthenticated: boolean;
  isLoading: boolean;
}